/* Shared GLightbox adapter. Carousel pages fetch the existing pinned library
 * only on first activation; Photography retains its existing eager dependency.
 */
(() => {
  if (window.ImageViewers) return;
  let pending;
  let requested = false;
  let loaded = false;
  let active;
  let intent = 0;
  let cancelIntent;
  function cancel() {
    intent++;
    const cleanup = cancelIntent; cancelIntent = null;
    cleanup?.();
  }
  window.addEventListener('pagehide', cancel);
  window.addEventListener('blur', cancel);
  document.addEventListener('visibilitychange', () => { if (document.hidden) cancel(); });
  // Capture runs before a new image's target handler claims its own intent.
  // A later Tab, press or unrelated click cancels a still-loading opening.
  document.addEventListener('pointerdown', cancel, { capture: true, passive: true });
  document.addEventListener('keydown', cancel, true);
  const reduce = matchMedia('(prefers-reduced-motion: reduce)');
  function load() {
    if (pending) return pending;
    if (loaded || (!requested && typeof GLightbox === 'function')) return Promise.resolve();
    requested = true;
    const css = document.createElement('link');
    css.rel = 'stylesheet';
    css.href = 'https://cdn.jsdelivr.net/npm/glightbox@3.3.1/dist/css/glightbox.min.css';
    const script = document.createElement('script');
    script.src = 'https://cdn.jsdelivr.net/npm/glightbox@3.3.1/dist/js/glightbox.min.js';
    script.async = true;
    pending = Promise.all([css, script].map(node => new Promise((resolve, reject) => {
      node.onload = resolve;
      node.onerror = () => reject(new Error('Image viewer unavailable'));
    })));
    const timer = setTimeout(() => { css.dispatchEvent(new Event('error')); script.dispatchEvent(new Event('error')); }, 8000);
    pending = pending.then(() => {
      clearTimeout(timer);
      if (typeof GLightbox !== 'function') throw new Error('Image viewer unavailable');
      loaded = true;
    }).catch(error => {
      clearTimeout(timer); css.remove(); script.remove(); pending = null;
      throw error;
    });
    document.head.append(css, script);
    return pending;
  }
  document.addEventListener('keydown', event => {
    if (!active || event.key !== 'Tab') return;
    const dialog = document.querySelector('.glightbox-container');
    if (!dialog) return;
    const controls = Array.from(dialog.querySelectorAll('button, a[href], [tabindex="0"]'))
      .filter(control => !control.disabled && !control.classList.contains('disabled')
        && control.getClientRects().length && !control.closest('[inert]'));
    if (!controls.length) return;
    event.preventDefault(); event.stopPropagation();
    const index = controls.indexOf(document.activeElement);
    controls[index < 0 ? (event.shiftKey ? controls.length - 1 : 0)
      : (index + (event.shiftKey ? -1 : 1) + controls.length) % controls.length].focus();
  }, true);
  function create(options = {}) {
    if (typeof GLightbox !== 'function') return null;
    const { label = 'Image viewer', className = 'photography-lightbox', ...config } = options;
    const instance = GLightbox({
      moreLength: 0,
      openEffect: reduce.matches ? 'none' : 'zoom',
      closeEffect: reduce.matches ? 'none' : 'zoom',
      slideEffect: reduce.matches ? 'none' : 'slide',
      ...(reduce.matches ? { cssEfects: {
        slide: { in: 'none', out: 'none' }, slideBack: { in: 'none', out: 'none' }
      } } : {}),
      ...config
    });
    let trigger;
    const background = [];
    function expose(index = instance.getActiveSlideIndex()) {
      const dialog = document.querySelector('.glightbox-container');
      if (!dialog) return;
      const slides = Array.from(dialog.querySelectorAll('.gslide'));
      const focused = document.activeElement?.closest('.gslide');
      if (focused && focused !== slides[index]) dialog.querySelector('.gclose')?.focus({ preventScroll: true });
      slides.forEach((slide, i) => { slide.inert = i !== index; slide.setAttribute('aria-hidden', String(i !== index)); });
    }
    instance.on('slide_before_change', ({ current }) => expose(current.index));
    instance.on('slide_after_load', ({ slide }) => {
      const description = slide.querySelector('.gslide-description');
      if (description) {
        description.tabIndex = 0;
        description.setAttribute('role', 'region');
        description.setAttribute('aria-label', 'Photo details');
      }
      expose();
    });
    instance.on('slide_changed', () => expose());
    instance.on('open', () => {
      active = instance;
      const dialog = document.querySelector('.glightbox-container');
      dialog.classList.add(className);
      dialog.setAttribute('aria-label', label);
      dialog.setAttribute('aria-modal', 'true');
      expose();
      dialog.addEventListener('error', event => {
        const image = event.target;
        const slide = image.closest?.('.gslide');
        if (!(image instanceof HTMLImageElement) || !slide || slide.querySelector('.photo-viewer-error')) return;
        const message = document.createElement('p');
        message.className = 'photo-viewer-error'; message.setAttribute('role', 'status');
        message.textContent = 'This photograph is unavailable.';
        image.after(message);
        const description = slide.querySelector('.gslide-description');
        if (description) {
          description.tabIndex = 0;
          description.setAttribute('role', 'region');
          description.setAttribute('aria-label', 'Photo details');
        }
        if (slide === instance.getActiveSlide()) instance.goToSlide(instance.getActiveSlideIndex());
      }, true);
      Array.from(document.body.children).forEach(node => {
        if (node instanceof HTMLElement && node !== dialog && !node.inert) {
          node.inert = true; background.push(node);
        }
      });
      dialog.querySelector('.gclose')?.focus();
    });
    instance.on('close', () => {
      background.splice(0).forEach(node => { node.inert = false; });
      active = null;
      if (trigger?.isConnected && !trigger.closest('[inert]')) trigger.focus({ preventScroll: true });
    });
    // Keep the public GLightbox API available to existing gallery consumers.
    instance.setReturnFocus = element => { trigger = element; };
    return instance;
  }
  window.ImageViewers = {
    load, create,
    begin(cleanup) { cancel(); cancelIntent = cleanup; return intent; },
    current: value => value === intent,
    finish(value) { if (value === intent) cancelIntent = null; }
  };
})();
