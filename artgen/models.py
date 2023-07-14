from django.db import models
from django.contrib import admin
from .tasks import process_article_task


class Site(models.Model):
    name = models.CharField(max_length=100)
    folder_location = models.CharField(max_length=100)
    domain = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name or self.domain


class Article(models.Model):
    query = models.CharField(max_length=100)
    site = models.ForeignKey(Site, on_delete=models.CASCADE)
    content = models.TextField(blank=True)

    def save(self, *args, **kwargs):
        # Trigger Celery task upon article creation
        if not self.pk:
            process_article_task.delay(self.id, self.query, self.site)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.query

