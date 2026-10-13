---
title: Travel
layout: default
---

<div class="travel-grid">
   {% assign sorted_travel_posts = site.travel | sort: "date" | reverse %}
   {% for post in sorted_travel_posts %}
   {% assign clean_url = post.url | replace: '.md', '' %}
   {% assign like_key = clean_url | remove: '/' | replace: 'travel', 'travel-' %}
<div class="travel-card">
   <a href="{{ clean_url }}">
     <img src="{{ post.image }}" alt="{{ post.title }}" class="travel-thumb">
   </a>
   <h3><a href="{{ clean_url }}">{{ post.title }}</a></h3>
   <div class="travel-date">{{ post.date | date: "%B %Y" }}</div>
   <p>{{ post.description }}</p>
   <a href="{{ clean_url }}" class="read-more">Read more →</a>
   <div class="travel-actions">
      <button class="like-button" data-id="{{ like_key }}" title="Like this post">
         <i class="fa-regular fa-heart"></i>
      </button>
      <span class="like-count">0</span>
      <button 
        class="share-button" 
        data-id="{{ like_key }}" 
        onclick="sharePost('{{ site.url }}{{ clean_url }}', '{{ like_key }}')"
        title="Share this post">
        <i class="fa-solid fa-share-nodes"></i>
      </button>
      <span class="share-count">0</span>
   </div>
</div>
   {% endfor %}
</div>

---