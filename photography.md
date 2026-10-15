---
title: Photography
layout: content
---

<!-- GLightbox CSS -->
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/glightbox@3.3.1/dist/css/glightbox.min.css" />
<!-- GLightbox JS -->
<script defer src="https://cdn.jsdelivr.net/npm/glightbox@3.3.1/dist/js/glightbox.min.js"></script>

<section class="photography-page" aria-label="{{ page.title }}">
<p class="gallery-hint">Open a photo to view it full size and read all details. Hover or focus for a brief summary.</p>
<div class="masonry-gallery">
{% for photo in site.data.photography %}
  {% include photo-tile.html photo=photo number=forloop.index %}
{% endfor %}
</div>
</section>

<script defer src="{{ '/assets/js/photography-portfolio-1.js' | relative_url }}"></script>
