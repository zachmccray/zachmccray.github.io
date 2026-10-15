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
    container.setAttribute('aria-label', title ? `Photo carousel: ${title}` : 'Photo carousel');
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
    [[previous, 'Previous photo', '←'], [next, 'Next photo', '→']].forEach(([button, label, arrow]) => {
      button.type = 'button';
      button.setAttribute('aria-label', label);
      button.setAttribute('aria-controls', container.id);
      const icon = document.createElement('span');
      icon.setAttribute('aria-hidden', 'true');
      icon.textContent = arrow;
      button.appendChild(icon);
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
      snapshot = { loop, period, widths, centers, viewport, start: centers[0] - widths[0] / 2 };
      container.scrollLeft = overflow ? centers[saved.index] + saved.fraction * widths[saved.index] - viewport / 2 : 0;
      controls.hidden = !overflow;
      status();
    }
    function scheduleLayout() {
      pendingLayout = true;
      if (!frame) frame = requestAnimationFrame(layout);
    }
    function normalize() {
      if (!snapshot?.loop || pointerDown || scrolling) return;
      const center = container.scrollLeft + container.clientWidth / 2;
      const delta = Math.floor((center - snapshot.start) / snapshot.period) * snapshot.period;
      if (Math.abs(delta) > 1) container.scrollLeft -= delta;
    }
    function finish() {
      clearTimeout(idle);
      if (pointerDown) return;
      scrolling = false;
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
      pointerDown = true;
      pointers.set(event.pointerId, release);
    }, { passive: true });
    container.addEventListener('lostpointercapture', release, { passive: true });
    function move(direction, endpoint) {
      if (!snapshot) return;
      scrolling = false; normalize();
      const current = anchor().index;
      let target = endpoint ?? current + direction;
      let center;
      if (snapshot.loop) {
        const cycle = Math.floor(target / originals.length);
        target = (target % originals.length + originals.length) % originals.length;
        center = snapshot.centers[target] + cycle * snapshot.period;
      } else {
        target = Math.max(0, Math.min(target, originals.length - 1)); center = snapshot.centers[target];
      }
      container.scrollTo({ left: center - container.clientWidth / 2, behavior: reducedMotion.matches ? 'instant' : 'smooth' });
      if (reducedMotion.matches) finish();
    }
    previous.addEventListener('click', () => move(-1));
    next.addEventListener('click', () => move(1));
    container.addEventListener('keydown', event => {
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
