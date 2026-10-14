---
layout: default
title: My Courses
nav_exclude: true
---

<h1 class="content-title">{{ page.title }}</h1>

{% for course in site.data.coursework %}
  {% include course-list.md %}
{% endfor %}

----
