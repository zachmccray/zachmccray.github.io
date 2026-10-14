// Lifecycle adapter for the pinned theme. Its generator, index builder and UI
// stay native; no global XHR/Lunr patches and no parallel search implementation.
(() => {
  const CACHE_KEY = 'site-search-index-v1';
  const CACHE_SCHEMA = 'jtd-9a7e403-builder-1';
  let libraryPromise;

  function loadLibrary(url) {
    if (window.lunr) return Promise.resolve();
    if (libraryPromise) return libraryPromise;
    libraryPromise = new Promise((resolve, reject) => {
      const script = document.createElement('script');
      script.src = url;
      script.async = true;
      const timer = setTimeout(() => finish(new Error('Search library timed out')), 15000);
      function finish(error) {
        clearTimeout(timer);
        script.onload = script.onerror = null;
        if (error) {
          script.remove();
          reject(error);
        } else resolve();
      }
      script.onload = () => finish(window.lunr ? null : new Error('Search library unavailable'));
      script.onerror = () => finish(new Error('Search library unavailable'));
      document.head.appendChild(script);
    }).catch(error => {
      libraryPromise = null;
      throw error;
    });
    return libraryPromise;
  }

  window.siteSearch = {
    start({ dataUrl, lunrUrl, prepare, build, render }) {
      const input = document.getElementById('search-input');
      const results = document.getElementById('search-results');
      if (!input || !results) return;
      const root = document.documentElement;
      const announcement = document.createElement('div');
      announcement.className = 'search-announcement';
      announcement.setAttribute('role', 'status');
      announcement.setAttribute('aria-live', 'polite');
      input.closest('.search').appendChild(announcement);
      input.setAttribute('role', 'combobox');
      input.setAttribute('aria-autocomplete', 'list');
      input.setAttribute('aria-haspopup', 'listbox');
      input.setAttribute('aria-expanded', 'false');
      results.setAttribute('role', 'region');
      results.setAttribute('aria-label', 'Search results');
      let state = 'idle';
      let lastAnnouncement = '';

      function announce(message) {
        if (message !== lastAnnouncement) announcement.textContent = message;
        lastAnnouncement = message;
      }
      function replay() {
        // The native renderer listens to keyup, including its ranking/highlights.
        // Also support input events from paste, autofill and touch keyboards.
        input.dispatchEvent(new KeyboardEvent('keyup', { bubbles: true }));
      }
      function pending(message, retry = false) {
        results.replaceChildren();
        const status = document.createElement('p');
        status.className = 'search-status';
        status.textContent = message;
        results.appendChild(status);
        if (retry) {
          const button = document.createElement('button');
          button.type = 'button';
          button.className = 'search-retry';
          button.textContent = 'Retry search';
          button.addEventListener('click', () => {
            input.focus({ preventScroll: true });
            load();
          });
          results.appendChild(button);
        }
        if ((input.value || retry) && input.closest('.search').contains(document.activeElement)) root.classList.add('search-active');
        announce(message);
      }
      function syncAccessibility() {
        const listbox = results.querySelector('.search-results-list');
        if (listbox) {
          listbox.id = 'search-results-listbox';
          listbox.setAttribute('role', 'listbox');
        }
        const links = Array.from(results.querySelectorAll('.search-result'));
        links.forEach((link, i) => {
          link.id = `search-result-${i + 1}`;
          link.setAttribute('role', 'option');
          link.tabIndex = -1;
          link.setAttribute('aria-selected', String(link.classList.contains('active')));
          link.setAttribute('aria-label', link.querySelector('.search-result-title')?.innerText || link.innerText);
          link.parentElement.setAttribute('role', 'presentation');
        });
        const visible = root.classList.contains('search-active');
        const expanded = visible && !!listbox;
        if (expanded) input.setAttribute('aria-controls', listbox.id);
        else input.removeAttribute('aria-controls');
        input.setAttribute('aria-expanded', String(expanded));
        const active = expanded && results.querySelector('.search-result.active');
        if (active && document.activeElement === input) {
          input.setAttribute('aria-activedescendant', active.id);
          // Scroll only the dropdown, leaving the article's scroll position intact.
          const box = active.getBoundingClientRect();
          const frame = results.getBoundingClientRect();
          if (box.bottom > frame.bottom) results.scrollTop += box.bottom - frame.bottom;
          else if (box.top < frame.top) results.scrollTop -= frame.top - box.top;
        } else input.removeAttribute('aria-activedescendant');
        if (!visible) announce('');
        else if (state === 'ready' && input.value) {
          announce(links.length ? `${links.length} search results. Use the arrow keys to choose a result, then Enter.` : 'No results found.');
        }
      }
      new MutationObserver(syncAccessibility).observe(results, {
        subtree: true, childList: true, attributes: true, attributeFilter: ['class']
      });
      new MutationObserver(syncAccessibility).observe(root, { attributes: true, attributeFilter: ['class'] });

      async function load() {
        if (state === 'loading' || state === 'ready') return;
        state = 'loading';
        results.setAttribute('aria-busy', 'true');
        pending('Loading search…');
        const controller = new AbortController();
        const timer = setTimeout(() => controller.abort(), 15000);
        try {
          const [response] = await Promise.all([
            fetch(dataUrl, { signal: controller.signal }), loadLibrary(lunrUrl)
          ]);
          if (!response.ok) throw new Error('Search data unavailable');
          const text = await response.text();
          const docs = JSON.parse(text);
          if (!docs || typeof docs !== 'object' || !Object.keys(docs).length
              || !Object.values(docs).every(doc => typeof doc.title === 'string'
                && typeof doc.content === 'string' && typeof doc.url === 'string')) {
            throw new Error('Invalid search data');
          }
          prepare();
          const version = `${CACHE_SCHEMA}:${lunr.version}:${prepare.toString()}:${build.toString()}`;
          let index;
          let cached;
          try {
            cached = JSON.parse(sessionStorage.getItem(CACHE_KEY));
            // Always validate against newly fetched data: numeric IDs must match.
            if (cached?.version === version && cached.data === text) {
              const saved = cached.index;
              const fields = saved?.fields;
              const vectors = saved?.fieldVectors;
              if (saved?.version !== lunr.version || !Array.isArray(fields)
                  || !fields.includes('title') || !fields.includes('content')
                  || !Array.isArray(vectors) || vectors.length !== fields.length * Object.keys(docs).length
                  || !vectors.every(([ref]) => {
                    const slash = ref.indexOf('/');
                    return fields.includes(ref.slice(0, slash)) && Object.prototype.hasOwnProperty.call(docs, ref.slice(slash + 1));
                  })) throw new Error('Incompatible index');
              index = lunr.Index.load(cached.index);
            }
          } catch (_) {
            cached = null;
            // Disabled storage, quota limits and corrupt entries never block search.
          }
          if (!index) index = build(docs);
          render(index, docs);
          state = 'ready';
          results.setAttribute('aria-busy', 'false');
          results.replaceChildren();
          announce('Search ready.');
          if (input.value && document.activeElement === input) replay();
          syncAccessibility();
          // Store after the first interaction frame; this is a session cache only.
          if (!cached || cached.version !== version || cached.data !== text) {
            const store = () => {
              try {
                const serialized = JSON.stringify({ version, data: text, index: index.toJSON() });
                if (serialized.length < 2 * 1024 * 1024) sessionStorage.setItem(CACHE_KEY, serialized);
              } catch (_) { /* Search remains usable without storage. */ }
            };
            if ('requestIdleCallback' in window) requestIdleCallback(store, { timeout: 1000 });
            else setTimeout(store, 0);
          }
        } catch (_) {
          state = 'error';
          results.setAttribute('aria-busy', 'false');
          pending('Search could not load. Please retry.', true);
        } finally {
          clearTimeout(timer);
          controller.abort();
        }
      }
      input.addEventListener('focus', () => {
        if (state === 'idle') load();
        else if (state === 'error' && input.value) pending('Search could not load. Please retry.', true);
      });
      input.addEventListener('input', () => {
        if (state === 'ready') replay();
        else if (state === 'idle') load();
        else if (state === 'loading') pending('Loading search…');
        else pending('Search could not load. Please retry.', true);
      });
      if (document.activeElement === input || input.value) load();
    }
  };
})();
