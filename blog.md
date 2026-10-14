---
title: Blog
layout: content
---

<section class="blog-page" aria-label="Blog Timeline">
<h2 class="content-heading no_anchor" id="blog-timeline" tabindex="-1">Blog Timeline</h2>

<!-- Filter & Sort Controls -->
<div class="blog-controls">
  <div class="blog-control">
  <label for="year-filter">Filter by Year:</label>
  <select id="year-filter">
    <option value="all">All</option>
    {% assign years = site.posts | map: "date" %}
    {% assign year_list = "" %}
    {% for date in years %}
      {% assign year = date | date: "%Y" %}
      {% unless year_list contains year %}
        <option value="{{ year }}">{{ year }}</option>
        {% assign year_list = year_list | append: year | append: "," %}
      {% endunless %}
    {% endfor %}
  </select>

  </div>
  <div class="blog-control">
  <label for="sort-filter">Sort by:</label>
  <select id="sort-filter">
    <option value="date-desc">Date (Newest First)</option>
    <option value="date-asc">Date (Oldest First)</option>
    <option value="title-asc">Title (A–Z)</option>
    <option value="title-desc">Title (Z–A)</option>
  </select>
  </div>
</div>

<!-- Timeline -->
<div class="timeline">
  {% for post in site.posts %}
    {% assign year = post.date | date: "%Y" %}

    {% if post.importance == "major" %}
      <div class="timeline-event major blog-entry" 
           data-year="{{ year }}" 
           data-date="{{ post.date | date_to_xmlschema }}">
        {% if post.image %}
          <div class="event-thumb">
            <img src="{{ post.image }}" alt="{{ post.title }}">
          </div>
        {% endif %}
        <div class="event-content">
          <a href="{{ post.url }}" class="event-link">
            <h3 class="event-title no_anchor">{{ post.title }}</h3>
            <p class="event-date">{{ post.date | date: "%B %-d, %Y" }}</p>
            {% if post.location %}
              <p class="event-location">{{ post.location }}</p>
            {% endif %}
            {% if post.description %}
              <p class="event-desc">{{ post.description }}</p>
            {% endif %}
          </a>
        </div>
      </div>

    {% else %}
      <div class="timeline-event minor blog-entry" 
           data-year="{{ year }}" 
           data-date="{{ post.date | date_to_xmlschema }}">
        {% if post.image %}
          <div class="event-thumb">
            <img src="{{ post.image }}" alt="{{ post.title }}">
          </div>
        {% endif %}
        <div class="event-content">
          {% if post.title %}
            <p class="event-title">{{ post.title }}</p>
          {% endif %}
          <p class="event-date">{{ post.date | date: "%B %-d, %Y" }}</p>
          {% if post.location %}
            <p class="event-location">{{ post.location }}</p>
          {% endif %}
          {% if post.description %}
            <p class="event-desc">{{ post.description }}</p>
          {% endif %}
        </div>
      </div>
    {% endif %}

  {% endfor %}
</div>

</section>
