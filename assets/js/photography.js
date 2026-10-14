// Use the existing image sequence and library; no masonry measurements or clones.
const photographyReduceMotion = matchMedia('(prefers-reduced-motion: reduce)').matches;
const lightbox = typeof GLightbox === 'function' ? GLightbox({
  selector: '.photography-page a.glightbox',
  moreLength: 0,
  openEffect: photographyReduceMotion ? 'none' : 'zoom',
  closeEffect: photographyReduceMotion ? 'none' : 'zoom',
  slideEffect: photographyReduceMotion ? 'none' : 'slide',
  // The library forces "slide" on mobile at open. Its supported effect map
  // keeps that path motion-free too, without replacing library internals.
  ...(photographyReduceMotion ? { cssEfects: {
    slide: { in: 'none', out: 'none' },
    slideBack: { in: 'none', out: 'none' }
  } } : {})
}) : null;

(() => {
  const gallery = document.querySelector('.photography-page .masonry-gallery');
  if (!gallery) return;
  gallery.closest('.photography-page').classList.add('has-gallery-controls');
  let activeInfo = null;
  let hold = null;
  let suppressClick = false;
  let returnFocus = null;

  function hideInfo() {
    if (activeInfo) {
      activeInfo.classList.remove('is-visible', 'is-scrollable');
      activeInfo.removeAttribute('tabindex');
    }
    activeInfo = null;
  }

  function showInfo(tile) {
    hideInfo();
    const info = tile.querySelector('.photo-info');
    if (!info || !info.children.length) return;
    const image = tile.querySelector('img').getBoundingClientRect();
    const inset = 12;
    const headerBottom = document.querySelector('.site-header')?.getBoundingClientRect().bottom || 0;
    const topInset = Math.max(inset, Math.min(headerBottom + inset, innerHeight - 2 * inset));
    info.style.width = `${Math.min(Math.max(image.width, 224), 320, innerWidth - 2 * inset)}px`;
    info.style.maxHeight = `${innerHeight - topInset - inset}px`;
    // Keep full, wrapping metadata readable even when the photograph is very short.
    const panel = info.getBoundingClientRect();
    const preferredTop = panel.height > image.height ? image.top : image.bottom - panel.height;
    info.style.left = `${Math.max(inset, Math.min(image.left, innerWidth - panel.width - inset))}px`;
    info.style.top = `${Math.max(topInset, Math.min(preferredTop, innerHeight - panel.height - inset))}px`;
    if (info.scrollHeight > info.clientHeight) {
      info.tabIndex = 0;
      info.classList.add('is-scrollable');
    }
    info.classList.add('is-visible');
    activeInfo = info;
  }

  function cancelHold() {
    if (hold) clearTimeout(hold.timer);
    hold = null;
  }

  gallery.addEventListener('pointerover', event => {
    if (event.pointerType !== 'mouse') return;
    const tile = event.target.closest('.photo-tile');
    if (tile && !tile.contains(event.relatedTarget)) showInfo(tile);
  });
  gallery.addEventListener('pointerout', event => {
    if (event.pointerType !== 'mouse') return;
    const tile = event.target.closest('.photo-tile');
    if (tile && !tile.contains(event.relatedTarget)) hideInfo();
  });
  gallery.addEventListener('focusin', event => {
    const tile = event.target.closest('.photo-tile');
    if (tile) showInfo(tile);
  });
  gallery.addEventListener('focusout', event => {
    const tile = event.target.closest('.photo-tile');
    if (tile && !tile.contains(event.relatedTarget)) hideInfo();
  });
  gallery.addEventListener('pointerdown', event => {
    suppressClick = false;
    cancelHold();
    if (!['touch', 'pen'].includes(event.pointerType) || !event.target.closest('a.glightbox')) return;
    hold = { x: event.clientX, y: event.clientY, shown: false };
    hold.timer = setTimeout(() => {
      hold.shown = true;
      showInfo(event.target.closest('.photo-tile'));
    }, 400);
  });
  gallery.addEventListener('pointermove', event => {
    if (hold && Math.hypot(event.clientX - hold.x, event.clientY - hold.y) > 10) {
      hideInfo();
      cancelHold();
    }
  });
  gallery.addEventListener('pointerup', () => {
    suppressClick = !!hold?.shown;
    cancelHold();
  });
  gallery.addEventListener('pointercancel', () => {
    cancelHold();
    hideInfo();
  });
  gallery.addEventListener('contextmenu', event => {
    if (hold?.shown || suppressClick) event.preventDefault();
  });
  gallery.addEventListener('click', event => {
    const trigger = event.target.closest('a.glightbox');
    if (!trigger) {
      const info = event.target.closest('.photo-info');
      if (info) info.closest('.photo-tile').querySelector('a.glightbox').click();
      return;
    }
    if (suppressClick && event.detail !== 0) {
      suppressClick = false;
      event.preventDefault();
      event.stopImmediatePropagation();
      return;
    }
    returnFocus = trigger;
    hideInfo();
  }, true);
  document.addEventListener('pointerdown', event => {
    if (!event.target.closest('.photo-tile')) hideInfo();
  });
  window.addEventListener('resize', hideInfo);
  window.addEventListener('scroll', event => {
    if (!activeInfo || activeInfo.contains(event.target)) return;
    const tile = document.activeElement.closest('.photo-tile') || gallery.querySelector('.photo-tile:hover');
    if (tile) showInfo(tile);
    else hideInfo();
  }, true);

  document.addEventListener('keydown', event => {
    if (!lightbox?.lightboxOpen) {
      if (event.key === 'Escape' && activeInfo) {
        activeInfo.closest('.photo-tile').querySelector('a.glightbox').focus({ preventScroll: true });
        hideInfo();
        event.preventDefault();
      }
      return;
    }
    if (event.key !== 'Tab') return;
    const dialog = document.querySelector('.glightbox-container');
    if (!dialog) return;
    const controls = Array.from(dialog.querySelectorAll('button, a[href], [tabindex="0"]'))
      .filter(control => !control.disabled && !control.classList.contains('disabled') && control.getClientRects().length);
    if (!controls.length) return;
    event.preventDefault();
    event.stopPropagation();
    const index = controls.indexOf(document.activeElement);
    const next = index < 0 ? (event.shiftKey ? controls.length - 1 : 0)
      : (index + (event.shiftKey ? -1 : 1) + controls.length) % controls.length;
    controls[next].focus();
  }, true);

  if (!lightbox) return;
  // Let the library render its usual temporary caption from existing metadata.
  // Original data-description fields and the sole gallery metadata nodes stay intact.
  lightbox.on('slide_before_load', ({ trigger, slideConfig }) => {
    const info = trigger?.closest?.('.photo-tile')?.querySelector('.photo-info');
    if (!info) return;
    const description = document.createElement('p');
    description.textContent = trigger.dataset.description || '';
    slideConfig.description = (description.textContent ? description.outerHTML : '') + info.innerHTML.trim();
  });
  lightbox.on('slide_after_load', ({ slide }) => {
    const description = slide.querySelector('.gslide-description');
    if (description) {
      description.tabIndex = 0;
      description.setAttribute('role', 'region');
      description.setAttribute('aria-label', 'Photo details');
    }
  });
  const background = [];
  lightbox.on('open', () => {
    hideInfo();
    const dialog = document.querySelector('.glightbox-container');
    dialog.classList.add('photography-lightbox');
    dialog.setAttribute('aria-label', 'Photography image viewer');
    dialog.setAttribute('aria-modal', 'true');
    Array.from(document.body.children).forEach(node => {
      if (node instanceof HTMLElement && node !== dialog && !node.inert) {
        node.inert = true;
        background.push(node);
      }
    });
    dialog.querySelector('.gclose').focus();
  });
  lightbox.on('close', () => {
    background.splice(0).forEach(node => { node.inert = false; });
    if (returnFocus?.isConnected) returnFocus.focus({ preventScroll: true });
  });
})();
