// The gallery keeps its existing pinned library; modal behavior is shared.
const lightbox = window.ImageViewers?.create({
  selector: '.photography-page a.glightbox', label: 'Photography image viewer'
}) || null;

(() => {
  const gallery = document.querySelector('.photography-page .masonry-gallery');
  if (!gallery) return;
  gallery.querySelectorAll('a.glightbox img').forEach(image => {
    const failed = () => image.closest('a').classList.add('is-unavailable');
    image.addEventListener('error', failed, { once: true });
    if (image.complete && !image.naturalWidth) failed();
  });
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

  // Observe images, never summary/link height: no feedback loop or invented
  // intrinsic dimensions. Fit only complete lines inside 40% of the photograph.
  const summaries = new ResizeObserver(entries => {
    entries.forEach(({ target, contentRect }) => {
      const link = target.closest('a.glightbox');
      const summary = link.querySelector('.photo-summary');
      const line = summary?.firstElementChild;
      if (!line) return;
      const lineHeight = parseFloat(getComputedStyle(line).lineHeight);
      const lines = Math.max(0, Math.min(summary.children.length,
        Math.floor((contentRect.height * .4 - 8) / lineHeight)));
      link.dataset.summaryLines = String(lines);
    });
  });
  gallery.querySelectorAll('a.glightbox img').forEach(image => {
    summaries.observe(image);
  });
  gallery.addEventListener('click', event => {
    const trigger = event.target.closest('a.glightbox');
    if (trigger) lightbox.setReturnFocus(trigger);
  }, true);
  lightbox.on('slide_before_load', ({ trigger, slideConfig }) => {
    const info = trigger?.closest?.('.photo-tile')?.querySelector('.photo-info');
    if (!info) return;
    const title = document.createElement('span');
    title.textContent = trigger.dataset.title || '';
    slideConfig.title = title.innerHTML;
    slideConfig.description = info.innerHTML.trim();
  });
})();
