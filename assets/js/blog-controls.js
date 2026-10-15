document.addEventListener("DOMContentLoaded", function () {
  const yearFilter = document.getElementById("year-filter");
  const sortFilter = document.getElementById("sort-filter");

  if (!yearFilter || !sortFilter) return;
  let appliedYear;
  let appliedSort;

  function getTitle(entry) {
    // Try to get title from h3 (major posts)
    let titleEl = entry.querySelector("h3");
    if (titleEl) return titleEl.textContent.trim();
    // Fallback to event-title for minor posts
    titleEl = entry.querySelector(".event-title");
    if (titleEl) return titleEl.textContent.trim();
    return ""; // safety
  }

  function filterAndSort() {
    const selectedYear = yearFilter.value;
    const sortValue = sortFilter.value;
    appliedYear = selectedYear;
    appliedSort = sortValue;
    const entries = Array.from(document.querySelectorAll(".blog-entry"));

    // Filter
    entries.forEach(entry => {
      const entryYear = entry.getAttribute("data-year");
      const visible = selectedYear === "all" || entryYear === selectedYear;
      // Keep the page's grid layout; filtering should not impose a display mode.
      entry.hidden = !visible;
    });

    // Sort visible entries
    const visibleEntries = entries.filter(entry => !entry.hidden);

    visibleEntries.sort((a, b) => {
      if (sortValue === "date-desc") {
        return new Date(b.dataset.date) - new Date(a.dataset.date);
      } else if (sortValue === "date-asc") {
        return new Date(a.dataset.date) - new Date(b.dataset.date);
      } else if (sortValue === "title-asc") {
        return getTitle(a).toLowerCase().localeCompare(getTitle(b).toLowerCase());
      } else if (sortValue === "title-desc") {
        return getTitle(b).toLowerCase().localeCompare(getTitle(a).toLowerCase());
      }
    });

    const container = document.querySelector(".timeline") || document.querySelector(".blog-list");
    visibleEntries.forEach(entry => container.appendChild(entry));
  }

  yearFilter.addEventListener("change", filterAndSort);
  sortFilter.addEventListener("change", filterAndSort);
  filterAndSort();
  // History can restore selects after DOMContentLoaded. Apply those values
  // after native form restoration, without rebuilding an unchanged BFCache
  // page or sorting twice on an ordinary first visit.
  window.addEventListener('pageshow', () => {
    if (yearFilter.value !== appliedYear || sortFilter.value !== appliedSort) filterAndSort();
  });

  // Preserve historical URLs and alt text, while making a failed thumbnail a
  // quiet, stable placeholder rather than a broken-image icon or changing gutter.
  document.querySelectorAll('.blog-page .event-thumb img').forEach(image => {
    const markMissing = () => image.closest('.event-thumb').classList.add('is-unavailable');
    image.addEventListener('error', markMissing, { once: true });
    if (image.complete && !image.naturalWidth) markMissing();
  });

  // ============================
  // Lightbox + Zoom + Swipe
  // ============================

  const overlay = document.getElementById("lightbox-overlay");
  const fullImg = document.getElementById("lightbox-img");
  const closeBtn = document.getElementById("lightbox-close");
  const lightboxContainer = document.getElementById("lightbox-container");

  if (!overlay || !fullImg || !lightboxContainer) return;

  let isZoomed = false;
  let didDrag = false;
  let startX, startY, scrollLeft, scrollTop;

  window.openLightbox = function (img) {
    fullImg.src = img.src;
    overlay.style.display = "flex";
    fullImg.classList.remove("zoomed");
    isZoomed = false;
    document.body.classList.add("lightbox-open");

    // Reset scroll
    lightboxContainer.scrollLeft = 0;
    lightboxContainer.scrollTop = 0;
  };

  function closeLightbox() {
    overlay.style.display = "none";
    fullImg.classList.remove("zoomed");
    isZoomed = false;
    document.body.classList.remove("lightbox-open");
  }

  if (closeBtn) {
    closeBtn.onclick = closeLightbox;
  }

  window.addEventListener("keydown", function (e) {
    if (e.key === "Escape") closeLightbox();
  });

  overlay.addEventListener("click", function (e) {
    if (!fullImg.contains(e.target)) closeLightbox();
  });

  // Pan support
  fullImg.addEventListener("mousedown", function (e) {
    if (!isZoomed) return;

    e.preventDefault();
    didDrag = false;
    startX = e.pageX;
    startY = e.pageY;
    scrollLeft = lightboxContainer.scrollLeft;
    scrollTop = lightboxContainer.scrollTop;

    function onMouseMove(e) {
      const dx = e.pageX - startX;
      const dy = e.pageY - startY;
      lightboxContainer.scrollLeft = scrollLeft - dx;
      lightboxContainer.scrollTop = scrollTop - dy;
      didDrag = true;
    }

    function onMouseUp() {
      document.removeEventListener("mousemove", onMouseMove);
      document.removeEventListener("mouseup", onMouseUp);
    }

    document.addEventListener("mousemove", onMouseMove);
    document.addEventListener("mouseup", onMouseUp);
  });

  // Zoom toggle (only if no drag)
  fullImg.addEventListener("click", function () {
    if (didDrag) {
      didDrag = false;
      return;
    }

    if (!isZoomed) {
      fullImg.classList.add("zoomed");
      isZoomed = true;
    } else {
      fullImg.classList.remove("zoomed");
      isZoomed = false;
      lightboxContainer.scrollLeft = 0;
      lightboxContainer.scrollTop = 0;
    }
  });

  // Mobile swipe down to close
  let touchStartY = null;
  overlay.addEventListener("touchstart", function (e) {
    if (e.touches.length === 1) {
      touchStartY = e.touches[0].clientY;
    }
  });

  overlay.addEventListener("touchend", function (e) {
    if (touchStartY !== null && e.changedTouches.length === 1) {
      const deltaY = e.changedTouches[0].clientY - touchStartY;
      if (deltaY > 100) closeLightbox();
      touchStartY = null;
    }
  });
});
