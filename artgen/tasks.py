from celery import shared_task

@shared_task
	def create_article_task(site, topic):
		return True