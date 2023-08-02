import os
from celery import shared_task
from generate.generate import generate
from subprocess import run


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

@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={'max_retries': 5})
def queue_articles(self):
    from artgen.models import Article
    articles_to_process = Article.objects.filter(markdown_file='')

    # send unwritten articles for writing
    for article in articles_to_process:
        current_app.send_task('artgen.tasks.process_article_task', kwargs={'id': article.id})

@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={'max_retries': 5})
def update_site_repos(self):
    from artgen.models import Article
    # update git repos for all sites
    submodules = list(Article.objects.values_list('website__hugo_dir', flat=True))

    commit_message = "Updating site content to git"

    for submodule in submodules:
        self.stdout.write(self.style.SUCCESS(f'Pushing for module {submodule}'))
        # Navigate to the submodule folder
        run(f'cd {submodule}', shell=True)

        # Stage and commit changes
        run('git add .', shell=True)
        run(f'git commit -m "{commit_message}"', shell=True)

        # Push the changes to the remote repository
        run('git push origin master', shell=True)

    self.stdout.write(self.style.SUCCESS('Successfully committed and pushed changes in all submodules.'))
