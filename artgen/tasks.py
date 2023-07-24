import os
from celery import shared_task
from generate.generate import generate

@shared_task
def process_article_task(id, query, site):
	post_dir = os.path.join(site.hugo_dir, 'content', 'posts')
	data_dir = site.data_dir
	image_dir = os.path.join(site.hugo_dir, 'static', 'images')
	topic = site.topic

	markdown_file = generate(topic, query, post_dir, data_dir, image_dir)

	return (id, query, site)
