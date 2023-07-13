from celery import shared_task

@shared_task
def process_article_task(id, query, site):
	return (id, query, site)
