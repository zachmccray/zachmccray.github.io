/* Progressive supporting-list disclosures; native section links and history.
 * The server renders every word. Without this enhancement all lists stay open.
 */
(() => {
  const controls = [];
  const root = document.querySelector('[data-supporting-lists]');
  const headings = root?.querySelectorAll('[data-support-heading]') || [];
  let expand;
  function updateExpand() {
    if (expand) expand.textContent = controls.every(c => !c.panel.hidden)
      ? 'Collapse supporting lists' : 'Expand supporting lists';
  }
  headings.forEach(heading => {
    const panel = document.getElementById(heading.dataset.supportHeading);
    if (!panel) return;
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'support-button';
    button.setAttribute('aria-controls', panel.id);
    const label = document.createElement('span');
    Array.from(heading.childNodes).forEach(node => {
      if (!(node instanceof Element && node.classList.contains('anchor-heading'))) label.append(node);
    });
    button.append(label);
    button.insertAdjacentHTML('beforeend', '<svg aria-hidden="true" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="m6 9 6 6 6-6"/></svg>');
    heading.append(button);
    function set(open) {
      // Never leave keyboard focus inside a newly hidden panel.
      if (!open && panel.contains(document.activeElement)) button.focus({ preventScroll: true });
      panel.hidden = !open;
      button.setAttribute('aria-expanded', String(open));
      updateExpand();
    }
    set(false);
    button.addEventListener('click', () => set(panel.hidden));
    controls.push({ heading, panel, set });
  });
  if (controls.length) {
    expand = document.createElement('button');
    expand.type = 'button';
    expand.className = 'expand-support';
    expand.addEventListener('click', () => {
      const open = controls.some(c => c.panel.hidden);
      controls.forEach(c => c.set(open));
    });
    root.querySelector('[data-support-toolbar]')?.append(expand);
    updateExpand();
  }
  let localSectionLink = false;
  let localFragmentLink = false;
  let restoringFragment = false;
  function reveal(target, fromSectionLink = false) {
    if (!target) return;
    for (let node = target.parentElement; node; node = node.parentElement) {
      if (node instanceof HTMLDetailsElement) node.open = true;
    }
    controls.forEach(c => {
      const topic = target.closest('.hobby-topic') || target.closest('.hobby-group');
      if (target === c.heading || c.panel.contains(target)
          || (!fromSectionLink && target.matches('h2,h3') && topic?.contains(c.heading))) c.set(true);
    });
  }
  function targetFromHash() {
    try {
      const target = document.getElementById(decodeURIComponent(location.hash.slice(1)));
      return target?.closest('.content-body,.post-body') ? target : null;
    }
    catch (_) { return null; }
  }
  function arrive(fromSectionLink = false, focus = false) {
    const target = targetFromHash();
    if (!target) return;
    reveal(target, fromSectionLink);
    // scrollIntoView resolves the newly opened panel's layout synchronously.
    // No deferred focus callback may steal the visitor's next Tab/search action.
    target.scrollIntoView({ block: 'start', behavior: 'instant' });
    if (focus) {
      if (!target.hasAttribute('tabindex')) target.tabIndex = -1;
      target.focus({ preventScroll: true });
    }
  }
  document.addEventListener('click', event => {
    const link = event.target.closest('a[href]');
    if (!link || event.button !== 0 || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
    const url = new URL(link.href, location.href);
    if (url.origin !== location.origin || url.pathname !== location.pathname || !url.hash) return;
    let target;
    try { target = document.getElementById(decodeURIComponent(url.hash.slice(1))); } catch (_) { return; }
    if (!target?.closest('.content-body,.post-body')) return;
    const inSectionNav = !!link.closest('.section-nav');
    reveal(target, inSectionNav);
    localSectionLink = inSectionNav;
    localFragmentLink = true;
    // Do not preventDefault or push/replace history: native hash entries work.
    if (url.hash === location.hash) {
      arrive(inSectionNav, true);
      localFragmentLink = false;
    }
  });
  window.addEventListener('popstate', () => {
    if (!localFragmentLink) {
      restoringFragment = true;
      // Reveal before the browser restores its saved native scroll offset.
      reveal(targetFromHash());
    }
  });
  window.addEventListener('hashchange', () => {
    if (restoringFragment) reveal(targetFromHash());
    else arrive(localSectionLink, true);
    localSectionLink = false;
    localFragmentLink = false;
    restoringFragment = false;
  });
  // BFCache retains the whole DOM. On a reconstructed Back/Forward entry, reveal
  // the target without overriding native restoration; a new URL/reload scrolls.
  if (performance.getEntriesByType('navigation')[0]?.type === 'back_forward') reveal(targetFromHash());
  else arrive(false, false);
})();
