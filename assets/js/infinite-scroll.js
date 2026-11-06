/* Native strips with viewport-sized edge buffers, not repeated whole galleries.
 * Wrap at scroll end/idle; never cancel native touch/trackpad momentum.
 */
(() => {
  if (window.ImageCarousels) return;
  const instances = new WeakMap();
  const reducedMotion = matchMedia('(prefers-reduced-motion: reduce)');
  const pointers = new Map();
  ['pointerup', 'pointercancel'].forEach(type => document.addEventListener(type, event => {
    const release = pointers.get(event.pointerId);
    pointers.delete(event.pointerId);
    release?.();
  }, { passive: true }));
  window.addEventListener('blur', () => {
    const releases = Array.from(pointers.values());
    pointers.clear();
    releases.forEach(release => release());
  });
  let serial = 0;
  function create(container) {
    const track = container.querySelector('.image-scroll-track');
    const originals = track ? Array.from(track.children) : [];
    if (!originals.length) return;
    container.tabIndex = 0;
    container.setAttribute('role', 'region');
    if (!container.id) container.id = `photo-carousel-${++serial}`;
    const headings = Array.from(document.querySelectorAll('main h2, main h3'))
      .filter(h => h.compareDocumentPosition(container) & Node.DOCUMENT_POSITION_FOLLOWING);
    const title = headings.at(-1)?.textContent.trim();
    const number = Array.from(document.querySelectorAll('.image-scroll-hyper')).indexOf(container) + 1;
    container.setAttribute('aria-label', title ? `Photo carousel ${number}: ${title}` : `Photo carousel ${number}`);
    const controls = document.createElement('div');
    controls.className = 'carousel-controls';
    controls.hidden = true;
    const previous = document.createElement('button');
    const next = document.createElement('button');
    const position = document.createElement('span');
    position.className = 'carousel-position';
    position.id = `${container.id}-position`;
    position.setAttribute('role', 'status');
    position.setAttribute('aria-live', 'polite');
    [[previous, 'Previous photo', 'm14 6-6 6 6 6'], [next, 'Next photo', 'm10 6 6 6-6 6']].forEach(([button, label, path]) => {
      button.type = 'button';
      button.setAttribute('aria-label', label);
      button.setAttribute('aria-controls', container.id);
      button.innerHTML = `<svg aria-hidden="true" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75"><path d="${path}"/></svg>`;
    });
    controls.append(previous, position, next);
    container.after(controls);
    container.setAttribute('aria-describedby', position.id);
    let snapshot = null;
    let pointerDown = false;
    let scrolling = false;
    let pendingLayout = false;
    let frame = 0;
    let idle = 0;
    let lastSizeKey = '';
    let commandTarget = null;
    let hold = null;
    let holdTimer = 0;
    let holdFrame = 0;
    let suppressClick = false;
    let tap = null;
    let viewer = null;
    const viewerStatus = document.createElement('p');
    viewerStatus.className = 'carousel-viewer-status';
    viewerStatus.setAttribute('role', 'status');
    controls.after(viewerStatus);
    originals.forEach((item, index) => {
      item.dataset.carouselIndex = String(index);
      const image = item.querySelector('img');
      if (!image) return;
      // Original links are a viewer-failure fallback. Keyboard users open the
      // selected photo from the strip, rather than tabbing through hidden copies.
      let link = image.closest('a');
      if (!link) {
        link = document.createElement('a');
        link.href = image.currentSrc || image.src;
        image.before(link); link.append(image);
      }
      link.tabIndex = -1;
    });
    function anchor() {
      if (!snapshot) return { index: 0, fraction: 0 };
      // Use the geometry belonging to this snapshot. ResizeObserver runs after
      // the viewport has already changed; using its new width selects a neighbor.
      let center = container.scrollLeft + snapshot.viewport / 2;
      if (snapshot.loop) center = snapshot.start + ((center - snapshot.start) % snapshot.period + snapshot.period) % snapshot.period;
      let index = 0;
      snapshot.centers.forEach((value, i) => {
        if (Math.abs(value - center) < Math.abs(snapshot.centers[index] - center)) index = i;
      });
      return { index, fraction: (center - snapshot.centers[index]) / snapshot.widths[index] };
    }
    function status() {
      if (!snapshot) return;
      position.textContent = `Photo ${anchor().index + 1} of ${originals.length}`;
      const max = container.scrollWidth - container.clientWidth;
      previous.disabled = !snapshot.loop && container.scrollLeft <= 1;
      next.disabled = !snapshot.loop && container.scrollLeft >= max - 1;
    }
    function copy(item, width) {
      const clone = item.cloneNode(true);
      clone.dataset.carouselClone = '';
      clone.setAttribute('aria-hidden', 'true');
      clone.inert = true;
      // This is measured rendered geometry, not invented intrinsic dimensions.
      clone.style.width = `${width}px`;
      clone.removeAttribute('id');
      clone.querySelectorAll('[id]').forEach(node => node.removeAttribute('id'));
      [clone, ...clone.querySelectorAll('a, button, input, select, textarea, [tabindex]')]
        .forEach(node => { if (node.matches('a, button, input, select, textarea, [tabindex]')) node.tabIndex = -1; });
      clone.querySelectorAll('img').forEach(image => {
        image.loading = 'lazy'; image.decoding = 'async';
        image.addEventListener('error', () => clone.classList.add('is-unavailable'), { once: true });
      });
      return clone;
    }
    function layout() {
      frame = 0;
      if (pointerDown || scrolling) { pendingLayout = true; return; }
      pendingLayout = false;
      const saved = anchor();
      const widths = originals.map(item => item.getBoundingClientRect().width);
      const viewport = container.clientWidth;
      if (!viewport || widths.some(width => !width)) return;
      const gap = parseFloat(getComputedStyle(track).columnGap) || 0;
      const period = widths.reduce((sum, width) => sum + width, 0) + originals.length * gap;
      const pending = originals.some(item => item.classList.contains('is-pending'));
      const key = [viewport, gap, pending, ...widths].join('/');
      if (key === lastSizeKey) return;
      lastSizeKey = key;
      track.querySelectorAll('[data-carousel-clone]').forEach(clone => clone.remove());
      // Each buffer covers two viewports and copies each source at most once
      // per side. A collection shorter than two screens stays finite.
      const loop = originals.length >= 3 && period > viewport * 2
        && !pending;
      const overflow = period - gap > viewport;
      container.classList.toggle('is-looping', loop);
      container.classList.toggle('is-static', !overflow);
      track.style.paddingLeft = !loop && overflow ? `${Math.max(0, (viewport - widths[0]) / 2)}px` : '0px';
      track.style.paddingRight = !loop && overflow ? `${Math.max(0, (viewport - widths.at(-1)) / 2)}px` : '0px';
      if (loop) {
        const head = document.createDocumentFragment();
        const tail = document.createDocumentFragment();
        let covered = 0;
        for (let i = 0; covered < viewport * 2 && i < originals.length; i++) {
          head.appendChild(copy(originals[i], widths[i])); covered += widths[i] + gap;
        }
        covered = 0;
        for (let i = originals.length - 1; covered < viewport * 2 && i >= 0; i--) {
          tail.prepend(copy(originals[i], widths[i])); covered += widths[i] + gap;
        }
        track.prepend(tail); track.append(head);
      }
      const left = container.getBoundingClientRect().left;
      const centers = originals.map(item => {
        const rect = item.getBoundingClientRect();
        return rect.left - left + container.scrollLeft + rect.width / 2;
      });
      const slots = Array.from(track.children).map(item => {
        const rect = item.getBoundingClientRect();
        return { index: Number(item.dataset.carouselIndex),
          left: rect.left - left + container.scrollLeft,
          right: rect.right - left + container.scrollLeft };
      });
      snapshot = { loop, period, widths, centers, slots, viewport, start: centers[0] - widths[0] / 2 };
      container.scrollLeft = overflow ? centers[saved.index] + saved.fraction * widths[saved.index] - viewport / 2 : 0;
      controls.hidden = !overflow;
      status();
    }
    function scheduleLayout() {
      stopHold();
      pendingLayout = true;
      if (!frame) frame = requestAnimationFrame(layout);
    }
    function normalize(controlled = false) {
      if (!snapshot?.loop || (!controlled && (pointerDown || scrolling))) return;
      const center = container.scrollLeft + container.clientWidth / 2;
      const delta = Math.floor((center - snapshot.start) / snapshot.period) * snapshot.period;
      if (Math.abs(delta) > 1) container.scrollLeft -= delta;
    }
    function finish() {
      clearTimeout(idle);
      if (pointerDown || hold?.started) return;
      scrolling = false;
      commandTarget = null;
      if (pendingLayout) layout(); else normalize();
      status();
    }
    container.addEventListener('scroll', () => {
      scrolling = true; clearTimeout(idle);
      // No geometry reads/layout writes per scroll event. Quiet-time fallback
      // supports browsers without scrollend; pointer contact defers both paths.
      idle = setTimeout(finish, 180);
    }, { passive: true });
    container.addEventListener('scrollend', finish);
    const release = () => {
      pointerDown = Array.from(pointers.values()).includes(release);
      clearTimeout(idle); idle = setTimeout(finish, 180);
    };
    container.addEventListener('pointerdown', event => {
      if (event.button !== 0) return;
      stopHold();
      tap = { id: event.pointerId, x: event.clientX, y: event.clientY,
        left: container.scrollLeft, moved: false, inMotion: scrolling,
        mouse: event.pointerType === 'mouse' };
      pointerDown = true;
      pointers.set(event.pointerId, release);
    }, { passive: true });
    container.addEventListener('lostpointercapture', release, { passive: true });
    container.addEventListener('pointermove', event => {
      if (!tap || tap.id !== event.pointerId) return;
      const dx = event.clientX - tap.x, dy = event.clientY - tap.y;
      if (Math.abs(dx) > 8 || Math.abs(dy) > 8) tap.moved = true;
      if (tap.mouse && event.buttons === 1 && Math.abs(dx) > Math.abs(dy) && Math.abs(dx) > 8) {
        container.setPointerCapture(event.pointerId);
        container.scrollLeft = tap.left - dx;
      }
    }, { passive: true });
    container.addEventListener('dragstart', event => event.preventDefault());
    container.addEventListener('pointercancel', () => { if (tap) tap.moved = true; }, { passive: true });
    container.addEventListener('wheel', () => stopHold(), { passive: true });
    function move(direction, endpoint) {
      if (!snapshot) return;
      scrolling = false; normalize();
      const current = commandTarget ?? anchor().index;
      let target = endpoint ?? current + direction;
      let center;
      if (snapshot.loop) {
        const cycle = Math.floor(target / originals.length);
        target = (target % originals.length + originals.length) % originals.length;
        center = snapshot.centers[target] + cycle * snapshot.period;
      } else {
        target = Math.max(0, Math.min(target, originals.length - 1)); center = snapshot.centers[target];
      }
      commandTarget = target;
      container.scrollTo({ left: center - container.clientWidth / 2, behavior: reducedMotion.matches ? 'instant' : 'smooth' });
      if (reducedMotion.matches) finish();
    }
    function stopHold() {
      clearTimeout(holdTimer); cancelAnimationFrame(holdFrame);
      if (!hold) return;
      suppressClick = hold.started || hold.canceled;
      const settled = hold.started || hold.canceled;
      const id = hold.pointer;
      hold = null;
      if (id !== undefined) pointers.delete(id);
      if (settled) finish();
    }
    function beginHold(direction, event) {
      stopHold(); suppressClick = false;
      hold = { direction, pointer: event.pointerId, button: event.currentTarget, started: false };
      if (event.pointerId !== undefined) {
        pointers.set(event.pointerId, stopHold);
        event.currentTarget.setPointerCapture(event.pointerId);
      }
      holdTimer = setTimeout(() => {
        if (!hold) return;
        hold.started = true;
        container.scrollTo({ left: container.scrollLeft, behavior: 'instant' });
        commandTarget = null;
        let last, stepped = 0;
        function tick(now) {
          if (!hold) return;
          if (last === undefined) last = now;
          if (reducedMotion.matches) {
            if (now - stepped >= 500) { move(hold.direction); stepped = now; }
          } else if (snapshot) {
            const speed = Math.max(120, Math.min(300, snapshot.viewport * .6));
            container.scrollLeft += hold.direction * speed * Math.min(50, now - last) / 1000;
            // Equivalent-position writes are allowed only during button-owned
            // movement. Native touch/trackpad wrapping still waits for rest.
            normalize(true);
          }
          last = now;
          holdFrame = requestAnimationFrame(tick);
        }
        holdFrame = requestAnimationFrame(tick);
      }, 350);
    }
    [[previous, -1], [next, 1]].forEach(([button, direction]) => {
      button.addEventListener('pointerdown', event => { if (event.button === 0) beginHold(direction, event); });
      button.addEventListener('pointercancel', () => { if (hold) hold.canceled = true; stopHold(); });
      button.addEventListener('lostpointercapture', stopHold);
      button.addEventListener('blur', stopHold);
      button.addEventListener('keydown', event => {
        if (!['Enter', ' '].includes(event.key)) return;
        event.preventDefault();
        if (!event.repeat) beginHold(direction, event);
      });
      button.addEventListener('keyup', event => {
        if (!['Enter', ' '].includes(event.key)) return;
        event.preventDefault();
        // A canceled/blurred hold no longer owns this release. Do not turn it
        // into an extra one-photo command after cancellation.
        if (!hold || hold.button !== button || hold.pointer !== undefined) return;
        const started = hold.started; stopHold();
        if (!started) move(direction);
      });
      button.addEventListener('click', () => {
        if (suppressClick) { suppressClick = false; return; }
        move(direction);
      });
    });
    document.addEventListener('visibilitychange', () => { if (document.hidden) stopHold(); });
    window.addEventListener('blur', stopHold);
    window.addEventListener('pagehide', stopHold);
    window.addEventListener('resize', stopHold, { passive: true });
    const escapeText = text => { const span = document.createElement('span'); span.textContent = text; return span.innerHTML; };
    async function enlarge(index) {
      stopHold();
      const image = originals[index]?.querySelector('img');
      if (!image || !window.ImageViewers || document.querySelector('.glightbox-container')) return;
      const intent = ImageViewers.begin(() => {
        viewerStatus.textContent = '';
        container.removeAttribute('aria-busy');
      });
      viewerStatus.textContent = 'Loading image viewer…';
      container.setAttribute('aria-busy', 'true');
      try {
        await ImageViewers.load();
        if (!ImageViewers.current(intent) || !container.isConnected) return;
        if (!viewer) viewer = ImageViewers.create({ selector: null,
          label: container.getAttribute('aria-label'),
          elements: originals.map(item => {
            const img = item.querySelector('img');
            const caption = item.querySelector('figcaption')?.textContent || '';
            return { href: img.closest('a')?.href || img.currentSrc || img.src,
              type: 'image', alt: img.alt, title: escapeText(img.alt), description: escapeText(caption) };
          }) });
        viewer.setReturnFocus(container);
        viewerStatus.textContent = '';
        ImageViewers.finish(intent);
        viewer.openAt(index);
      } catch (_) {
        if (!ImageViewers.current(intent)) return;
        ImageViewers.finish(intent);
        viewerStatus.textContent = 'The viewer is unavailable. ';
        const link = document.createElement('a');
        link.href = image.closest('a')?.href || image.currentSrc || image.src;
        link.textContent = 'Open the original image';
        viewerStatus.append(link);
      } finally { if (ImageViewers.current(intent)) container.removeAttribute('aria-busy'); }
    }
    container.addEventListener('click', event => {
      if (event.button !== 0 || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey || !snapshot || !window.ImageViewers) return;
      const box = container.getBoundingClientRect();
      const x = event.clientX - box.left + container.scrollLeft;
      const slot = snapshot.slots.find(item => x >= item.left && x <= item.right);
      if (!slot) return;
      event.preventDefault();
      if (tap && (tap.moved || tap.inMotion || Math.abs(container.scrollLeft - tap.left) > 8)) return;
      enlarge(slot.index);
    });
    container.addEventListener('keydown', event => {
      if (event.target === container && ['Enter', ' '].includes(event.key)) {
        event.preventDefault(); if (!event.repeat && snapshot) enlarge(anchor().index); return;
      }
      if (event.target !== container || !['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) return;
      event.preventDefault();
      if (event.key === 'Home') move(0, 0);
      else if (event.key === 'End') move(0, originals.length - 1);
      else move(event.key === 'ArrowRight' ? 1 : -1);
    });
    const resize = new ResizeObserver(scheduleLayout);
    resize.observe(container);
    originals.forEach(item => {
      resize.observe(item);
      item.querySelectorAll('img').forEach(image => {
        image.decoding = 'async';
        // Pending images can have zero width. Reserve a temporary frame and
        // stay finite until geometry is known. This is presentation geometry,
        // never intrinsic image metadata; late loads preserve the chosen photo.
        if (!image.complete) item.classList.add('is-pending');
        const loaded = () => {
          item.classList.remove('is-pending', 'is-unavailable'); scheduleLayout();
        };
        const failed = () => {
          item.classList.remove('is-pending');
          item.classList.add('is-unavailable'); scheduleLayout();
        };
        image.addEventListener('load', loaded);
        image.addEventListener('error', failed, { once: true });
        if (image.complete && !image.naturalWidth) failed();
      });
    });
    scheduleLayout();
    return { refresh: scheduleLayout };
  }
  function init(root = document) {
    root.querySelectorAll('.image-scroll-hyper').forEach(container => {
      const existing = instances.get(container);
      if (existing) existing.refresh();
      else { const instance = create(container); if (instance) instances.set(container, instance); }
    });
  }
  window.ImageCarousels = { init };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', () => init(), { once: true });
  else init();
})();
