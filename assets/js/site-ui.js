// Small adapters around the theme's existing navigation and search components.
function initializeSiteUI() {
  const root = document.documentElement;
  const sidebar = document.querySelector('.side-bar');
  const brand = document.querySelector('.site-header');
  const nav = document.getElementById('site-nav');
  const header = document.getElementById('main-header');
  const menu = document.getElementById('menu-button');
  const input = document.getElementById('search-input');
  const results = document.getElementById('search-results');
  const skip = document.querySelector('.skip-to-main');
  const main = document.getElementById('main-content');
  if (!sidebar || !brand || !nav || !header || !menu) return;

  const headerParent = header.parentElement;
  const headerNext = header.nextSibling;
  const mobile = matchMedia('(max-width: 799px)');
  root.classList.add('site-ui-ready');
  menu.setAttribute('aria-controls', 'site-nav main-header');

  // The theme removes the current link's href after scrolling its sidebar.
  const current = nav.querySelector('.nav-list-link.active');
  if (current) {
    if (!current.hasAttribute('href')) current.setAttribute('href', location.pathname);
    current.setAttribute('aria-current', 'page');
  }

  function measureNavigation() {
    const brandHeight = brand.getBoundingClientRect().height;
    // Size the input from the independent brand row, not its own bordered
    // container: feeding the container height back into the input grows it.
    const searchHeight = brandHeight;
    root.style.setProperty('--ui-brand-height', `${brandHeight}px`);
    root.style.setProperty('--ui-search-height', `${searchHeight}px`);
    root.style.setProperty('--ui-header-offset', `${(mobile.matches ? brandHeight : searchHeight) + 12}px`);
  }

  function closeMenu(returnFocus = false) {
    menu.classList.remove('nav-open');
    nav.classList.remove('nav-open');
    header.classList.remove('nav-open');
    menu.setAttribute('aria-expanded', 'false');
    root.classList.remove('search-active');
    measureNavigation();
    if (returnFocus) menu.focus({ preventScroll: true });
  }

  function placeHeader() {
    closeMenu();
    // Reuse the same search node above mobile links; no duplicate inputs/IDs.
    if (mobile.matches) sidebar.insertBefore(header, nav);
    else headerParent.insertBefore(header, headerNext);
    measureNavigation();
  }
  placeHeader();
  mobile.addEventListener('change', placeHeader);
  const sizes = new ResizeObserver(measureNavigation);
  sizes.observe(brand);
  sizes.observe(header);
  menu.addEventListener('click', measureNavigation);

  let untouched = !location.hash;
  document.addEventListener('pointerdown', () => { untouched = false; }, { once: true });
  document.addEventListener('focusin', () => { untouched = false; }, { once: true });
  document.addEventListener('keydown', event => {
    // scrollIntoView in theme startup changes Chromium's initial Tab origin.
    if (untouched && event.key === 'Tab' && !event.shiftKey && !event.ctrlKey && !event.altKey && !event.metaKey && document.activeElement === document.body && skip) {
      untouched = false;
      event.preventDefault();
      skip.focus({ preventScroll: true });
    }
    if (event.key !== 'Escape' || document.querySelector('.glightbox-container')) return;
    if (root.classList.contains('search-active')) {
      root.classList.remove('search-active');
      if (input) {
        input.value = '';
        input.focus({ preventScroll: true });
      }
    } else if (mobile.matches && menu.getAttribute('aria-expanded') === 'true') {
      event.preventDefault();
      closeMenu(true);
    }
  }, true);
  skip?.addEventListener('click', () => {
    closeMenu();
    if (main) {
      main.tabIndex = -1;
      main.focus({ preventScroll: true });
    }
  });
  nav.addEventListener('click', event => {
    if (event.target.closest('a[href]') && mobile.matches) closeMenu();
  });
  document.addEventListener('click', event => {
    if (!event.target.closest('.search')) root.classList.remove('search-active');
    if (mobile.matches && menu.getAttribute('aria-expanded') === 'true' && !sidebar.contains(event.target)) closeMenu();
  });

  if (!input || !results) return;
  input.type = 'search';
  input.setAttribute('aria-controls', 'search-results');
  results.setAttribute('role', 'region');
  results.setAttribute('aria-label', 'Search results');

  function safeSearchBlur(event) {
    if (event.relatedTarget) return;
    // Match the theme's intended dismissal, bypassing only its null dereference.
    root.classList.remove('search-active');
    event.stopImmediatePropagation();
  }
  input.addEventListener('focusout', safeSearchBlur, true);
  results.addEventListener('focusout', safeSearchBlur, true);
  results.addEventListener('click', event => {
    if (mobile.matches && event.target.closest('.search-result')) closeMenu();
  }, true);

  let searchPosition = null;
  function preserveSearchScroll(event) {
    if (['Enter', 'ArrowUp', 'ArrowDown', 'Tab'].includes(event.key)) return;
    if (event.type === 'focus' || !searchPosition) searchPosition = { left: scrollX, top: scrollY };
    // The theme's iOS workaround forces the whole page to the top. The search
    // field is now visible in the persistent header; leave the article in place.
    requestAnimationFrame(() => requestAnimationFrame(() => {
      if (searchPosition && document.activeElement === input && root.classList.contains('search-active')) scrollTo(searchPosition);
    }));
  }
  input.addEventListener('focus', preserveSearchScroll, true);
  input.addEventListener('keyup', preserveSearchScroll, true);
  input.addEventListener('blur', () => { searchPosition = null; });
  // Respect deliberate page scrolling while the search field retains focus.
  function rememberSearchScroll(event) {
    if (event.target.closest('.search')) return;
    requestAnimationFrame(() => {
      if (document.activeElement === input) searchPosition = { left: scrollX, top: scrollY };
    });
  }
  document.addEventListener('wheel', rememberSearchScroll, { passive: true });
  document.addEventListener('touchmove', rememberSearchScroll, { passive: true });
}

if (document.readyState === 'complete') initializeSiteUI();
else document.addEventListener('DOMContentLoaded', initializeSiteUI, { once: true });
