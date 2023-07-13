
from django.db import models
from django.contrib import admin
from .tasks import process_article_task

class Article(models.Model):
    SITE_CHOICES = (
        ('site1', 'Site 1'),
        ('site2', 'Site 2'),
        # Add other site choices
    )

    query = models.CharField(max_length=100)
    site = models.CharField(max_length=20, choices=SITE_CHOICES)
    content = models.TextField(blank=True)

    def save(self, *args, **kwargs):
        # Trigger Celery task upon article creation
        if not self.pk:
            process_article_task.delay(self.id, self.query, self.site)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.query

@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('query', 'site', 'content')
    readonly_fields = ('content',)