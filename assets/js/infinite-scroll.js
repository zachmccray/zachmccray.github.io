document.addEventListener('DOMContentLoaded', () => {
    const carousels = document.querySelectorAll('.image-scroll-hyper');
  
    carousels.forEach(container => {
      const track = container.querySelector('.image-scroll-track');
      if (!track || !track.children.length) return;
      const originals = Array.from(track.children);
      container.tabIndex = 0;
      container.setAttribute('role', 'region');
      const precedingHeadings = Array.from(document.querySelectorAll('main h2, main h3'))
        .filter(heading => heading.compareDocumentPosition(container) & Node.DOCUMENT_POSITION_FOLLOWING);
      const title = precedingHeadings.at(-1)?.textContent.trim();
      container.setAttribute('aria-label', title ? `Photo carousel: ${title}` : 'Photo carousel');
      container.addEventListener('keydown', event => {
        if (event.target !== container || !['ArrowLeft', 'ArrowRight'].includes(event.key)) return;
        event.preventDefault();
        container.scrollBy({ left: (event.key === 'ArrowRight' ? 1 : -1) * container.clientWidth * 0.75 });
      });
  
      const cloneSetCount = 5;
      for (let i = 0; i < cloneSetCount; i++) {
        originals.forEach(item => {
          const clone = item.cloneNode(true);
          clone.setAttribute('aria-hidden', 'true');
          clone.removeAttribute('id');
          clone.querySelectorAll('[id]').forEach(node => node.removeAttribute('id'));
          clone.querySelectorAll('a, button, input, select, textarea, [tabindex]').forEach(node => { node.tabIndex = -1; });
          track.appendChild(clone);
        });
      }
  
      // Find center of all items after cloning
      const allItems = Array.from(track.children);
      const midpoint = Math.floor(allItems.length / 2);
      const centerItem = allItems[midpoint];
  
      // Center the scroll position so the middle image is centered
      window.requestAnimationFrame(() => {
        const centerOffset = centerItem.offsetLeft;
        const containerCenter = container.offsetWidth / 2;
        const imageCenter = centerItem.offsetWidth / 2;
        container.scrollLeft = centerOffset - containerCenter + imageCenter;
      });      
  
      // Seamless infinite scroll logic
      container.addEventListener('scroll', () => {
        const maxScroll = track.scrollWidth;
        const buffer = 500;
  
        if (container.scrollLeft < buffer) {
          container.scrollLeft += centerItem.offsetLeft;
        } else if (container.scrollLeft > maxScroll - container.offsetWidth - buffer) {
          container.scrollLeft -= centerItem.offsetLeft;
        }
      });
    });
  });
