---
title: Travel
layout: content
---

<section class="travel-page" aria-label="{{ page.title }}">
<div class="travel-grid">
   {% assign sorted_travel_posts = site.travel | sort: "date" | reverse %}
   {% for post in sorted_travel_posts %}
   {% assign clean_url = post.url | replace: '.md', '' %}
   {% assign like_key = clean_url | remove: '/' | replace: 'travel', 'travel-' %}
<article class="travel-card">
   <a href="{{ clean_url }}" class="travel-cover">
     <img src="{{ post.image }}" alt="{{ post.title }}" class="travel-thumb">
   </a>
   <div class="travel-card-content">
   <h2 class="travel-card-title no_anchor" id="{{ like_key }}" tabindex="-1"><a href="{{ clean_url }}">{{ post.title }}</a></h2>
   <time class="travel-date" datetime="{{ post.date | date: "%Y-%m-%d" }}">{{ post.date | date: "%B %Y" }}</time>
   <p>{{ post.description }}</p>
   <a href="{{ clean_url }}" class="read-more">Read more →</a>
   <div class="travel-actions">
      <button class="like-button" type="button" data-id="{{ like_key }}" title="Like this post" aria-label="Like {{ post.title | escape }}" aria-pressed="false" aria-describedby="likes-{{ like_key }}" disabled>
         <i class="fa-regular fa-heart" aria-hidden="true"></i>
      </button>
      <span class="like-count" id="likes-{{ like_key }}" aria-label="0 likes" aria-live="polite">0</span>
      <button
        class="share-button" type="button" aria-label="Share {{ post.title | escape }}" aria-describedby="shares-{{ like_key }}"
        data-id="{{ like_key }}"
        onclick="sharePost('{{ site.url }}{{ clean_url }}', '{{ like_key }}')"
        title="Share this post">
        <i class="fa-solid fa-share-nodes" aria-hidden="true"></i>
      </button>
      <span class="share-count" id="shares-{{ like_key }}" aria-label="0 shares" aria-live="polite">0</span>
   </div>
   <p class="travel-feedback" role="status" aria-live="polite" aria-atomic="true"></p>
   </div>
</article>
   {% endfor %}
</div>

</section>

---
