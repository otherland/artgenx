import os
from celery import shared_task
from generate.generate import generate

@shared_task
def process_article_task(id, query, site):
	post_dir, data_dir, image_dir, topic = site
	markdown_file = generate(topic, query, post_dir, data_dir, image_dir)
	return markdown_file
