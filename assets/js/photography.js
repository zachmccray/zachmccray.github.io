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
  let returnFocus = null;

  if (!lightbox) {
    // The library is optional. Keep original-file links working and move, never
    // copy, the existing facts into native keyboard/touch-accessible disclosures.
    gallery.classList.add('gallery-fallback');
    gallery.querySelectorAll('.photo-tile').forEach(tile => {
      const info = tile.querySelector('.photo-info');
      if (!info) return;
      const details = document.createElement('details');
      details.className = 'photo-fallback-details';
      const summary = document.createElement('summary');
      summary.textContent = 'Photo details';
      summary.setAttribute('aria-label', `Photo details: ${tile.querySelector('a.glightbox').dataset.title || 'Photo'}`);
      info.classList.replace('photo-info', 'photo-fallback-content');
      info.before(details);
      details.append(summary, info);
    });
    const hint = document.querySelector('.photography-page .gallery-hint');
    if (hint) {
      hint.textContent = 'The enlarged viewer is unavailable. Open an original image, or expand its photo details.';
      hint.setAttribute('role', 'status');
    }
    return;
  }

  // The summary belongs to its tile. Very short photographs keep only a title;
  // tiles too short for one readable line leave details to the normal viewer.
  // This observes rendered geometry; it does not invent source dimensions.
  const summaries = new ResizeObserver(entries => {
    entries.forEach(({ target, contentRect }) => {
      target.classList.toggle('compact-summary', contentRect.height < 100);
      target.classList.toggle('no-summary', contentRect.height < 80);
    });
  });
  gallery.querySelectorAll('a.glightbox').forEach(link => summaries.observe(link));
  gallery.addEventListener('click', event => {
    const trigger = event.target.closest('a.glightbox');
    if (trigger) returnFocus = trigger;
  }, true);

  document.addEventListener('keydown', event => {
    if (!lightbox?.lightboxOpen) return;
    if (event.key !== 'Tab') return;
    const dialog = document.querySelector('.glightbox-container');
    if (!dialog) return;
    const controls = Array.from(dialog.querySelectorAll('button, a[href], [tabindex="0"]'))
      .filter(control => !control.disabled && !control.classList.contains('disabled') && control.getClientRects().length
        && (!control.closest('.gslide') || control.closest('.gslide').classList.contains('current')));
    if (!controls.length) return;
    event.preventDefault();
    event.stopPropagation();
    const index = controls.indexOf(document.activeElement);
    const next = index < 0 ? (event.shiftKey ? controls.length - 1 : 0)
      : (index + (event.shiftKey ? -1 : 1) + controls.length) % controls.length;
    controls[next].focus();
  }, true);

  function exposeSlide(index = lightbox.getActiveSlideIndex()) {
    const dialog = document.querySelector('.glightbox-container');
    if (!dialog) return;
    const slides = Array.from(dialog.querySelectorAll('.gslide'));
    const focused = document.activeElement?.closest('.gslide');
    if (focused && focused !== slides[index]) {
      dialog.querySelector('.gclose')?.focus({ preventScroll: true });
    }
    slides.forEach((slide, i) => {
      slide.inert = i !== index;
      slide.setAttribute('aria-hidden', String(i !== index));
    });
  }
  lightbox.on('slide_before_change', ({ current }) => exposeSlide(current.index));
  // Let the library render its usual temporary caption from existing metadata.
  // Original fields and IDs stay intact; the library creates only its usual caption.
  lightbox.on('slide_before_load', ({ trigger, slideConfig }) => {
    const info = trigger?.closest?.('.photo-tile')?.querySelector('.photo-info');
    if (!info) return;
    const title = document.createElement('span');
    title.textContent = trigger.dataset.title || '';
    slideConfig.title = title.innerHTML;
    slideConfig.description = info.innerHTML.trim();
  });
  lightbox.on('slide_after_load', ({ slide }) => {
    const description = slide.querySelector('.gslide-description');
    if (description) {
      description.tabIndex = 0;
      description.setAttribute('role', 'region');
      description.setAttribute('aria-label', 'Photo details');
    }
    exposeSlide();
  });
  lightbox.on('slide_changed', () => {
    exposeSlide();
    // A caption from the previous slide must not retain offscreen keyboard focus.
    const oldSlide = document.activeElement?.closest('.gslide');
    if (oldSlide && !oldSlide.classList.contains('current')) {
      document.querySelector('.glightbox-container .gclose')?.focus({ preventScroll: true });
    }
  });
  const background = [];
  lightbox.on('open', () => {
    const dialog = document.querySelector('.glightbox-container');
    dialog.classList.add('photography-lightbox');
    dialog.setAttribute('aria-label', 'Photography image viewer');
    dialog.setAttribute('aria-modal', 'true');
    exposeSlide();
    dialog.addEventListener('error', event => {
      const image = event.target;
      const slide = image.closest?.('.gslide');
      if (!(image instanceof HTMLImageElement) || !slide || slide.querySelector('.photo-viewer-error')) return;
      const message = document.createElement('p');
      message.className = 'photo-viewer-error';
      message.setAttribute('role', 'status');
      message.textContent = 'This photograph is unavailable.';
      image.after(message);
      const description = slide.querySelector('.gslide-description');
      if (description) {
        description.tabIndex = 0;
        description.setAttribute('role', 'region');
        description.setAttribute('aria-label', 'Photo details');
      }
      // GLightbox marks content loaded before fetching, but only finishes its
      // first transition on image load. Revisit the active, now-failed slide via
      // its public API so the error/details are visible and navigation unlocks.
      // A failed preload must never move the visitor to a different photograph.
      if (slide === lightbox.getActiveSlide()) {
        lightbox.goToSlide(lightbox.getActiveSlideIndex());
      }
    }, true);
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
