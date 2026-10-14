// Keep the existing library, image sources and gallery sequence.
  const lightbox = typeof GLightbox === "function" ? GLightbox({
    selector: '.glightbox',
    openEffect: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'none' : 'zoom',
    closeEffect: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'none' : 'zoom',
    slideEffect: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'none' : 'slide'
  }) : null;

  if (lightbox) {
    let returnFocus = null;
    const gallery = document.querySelector('.masonry-gallery');
    gallery.addEventListener('click', event => {
      const trigger = event.target.closest('a.glightbox');
      if (trigger) returnFocus = trigger;
    }, true);

    // GLightbox handles arrows, Escape, zoom and touch gestures. Add a named
    // modal, initial/return focus and a bidirectional Tab loop for its controls.
    lightbox.on('open', () => {
      const dialog = document.querySelector('.glightbox-container');
      dialog.setAttribute('aria-label', 'Photography image viewer');
      dialog.setAttribute('aria-modal', 'true');
      dialog.querySelector('.gclose').focus();
    });
    document.addEventListener('keydown', event => {
      if (!lightbox.lightboxOpen || event.key !== 'Tab') return;
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
    lightbox.on('close', () => {
      if (returnFocus && returnFocus.isConnected) returnFocus.focus({ preventScroll: true });
    });
  }
