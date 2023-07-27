from django.core.management.base import BaseCommand
from artgen.models import Article
from django.utils import timezone
from celery import current_app

class Command(BaseCommand):
    help = 'Process articles with null markdown_file field'

    def handle(self, *args, **options):
        # Get articles with null markdown_file
        articles_to_process = Article.objects.filter(markdown_file__isnull=True)

        for article in articles_to_process:
            current_app.send_task('artgen.tasks.process_article_task', args=[article.id])