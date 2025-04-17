---
layout: default
title: My Courses
nav_exclude: false
---

# 📚 Courses I've Taken

{% for course in site.data.coursework %}
  {% include course-list.md %}
{% endfor %}

----

[^1]: [It can take up to 10 minutes for changes to your site to publish after you push the changes to GitHub](https://docs.github.com/en/pages/setting-up-a-github-pages-site-with-jekyll/creating-a-github-pages-site-with-jekyll#creating-your-site).

[Text]: link