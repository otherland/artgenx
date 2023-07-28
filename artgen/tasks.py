import os
from celery import shared_task
from generate.generate import generate


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={'max_retries': 5})
def process_article_task(self, id):
    from artgen.models import Article
    try:
        article = Article.objects.get(pk=id)
        post_dir, data_dir, image_dir, subject = article.get_site_data()

        article.markdown_file = generate(article.query, subject, post_dir, data_dir, image_dir)
        article.save()

    except Exception as exc:
        if self.request.retries >= self.retry_kwargs['max_retries']:
            # If the task still fails after max retries, set the flag
            article.failed_flag = True
            article.save()
        else:
            # If the task failed but is still retrying, re-raise the exception for retry
            self.retry(exc=exc, countdown=2 ** self.request.retries)