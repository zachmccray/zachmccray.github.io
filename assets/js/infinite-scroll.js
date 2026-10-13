document.addEventListener('DOMContentLoaded', () => {
    const carousels = document.querySelectorAll('.image-scroll-hyper');
  
    carousels.forEach(container => {
      const track = container.querySelector('.image-scroll-track');
      const originals = Array.from(track.children);
  
      const cloneSetCount = 5;
      for (let i = 0; i < cloneSetCount; i++) {
        originals.forEach(item => {
          track.appendChild(item.cloneNode(true));
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