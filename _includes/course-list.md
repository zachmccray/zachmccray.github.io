<div class="course course-record" data-category="{{ course.category }}">
  <h2 class="content-heading course-heading" id="course-{{ course.name | slugify | remove: '-' }}" tabindex="-1"><span class="content-meta course-code">{{ course.name }}</span> <span class="course-title">{{ course.title }}</span></h2>
  <p class="content-meta course-instructor">{{ course.professor }}</p>
  <p class="content-prose">{{ course.description }}</p>
  <p class="content-meta course-details"><span class="course-semester">{{ course.semester }}</span> <span class="course-category">({{ course.category }})</span> <span class="course-grade">({{ course.grade }})</span></p>
</div>
