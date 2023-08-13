import datetime
import random
import os
import sys
import re
import asyncio
import subprocess
import json
from subprocess import Popen, PIPE, CalledProcessError
import Levenshtein
from .serps import get_serps
from .embed import json_to_vectorstore
from .add_images import add_images_to_article
from django.conf import settings
import openai
import time

def openai_response(prompt, retries=5, model="gpt-3.5-turbo", is_json=False):
	time.sleep(20)
	for _ in range(retries):
		try:
			chat_completion = openai.ChatCompletion.create(model=model, messages=[{"role": "user", "content": prompt}])
			response = chat_completion.choices[0].message.content
			if is_json:
				return json.loads(response)
			else:
				return response
		except json.JSONDecodeError:
			print(response)
			print("JSON is invalid, retrying...")
			continue
		except openai.error.Timeout as e:
			#Handle timeout error, e.g. retry or log
			print(f"OpenAI API request timed out: {e}")
			continue
		except openai.error.APIError as e:
			#Handle API error, e.g. retry or log
			print(f"OpenAI API returned an API Error: {e}")
			continue
		except openai.error.APIConnectionError as e:
			#Handle connection error, e.g. check network or log
			print(f"OpenAI API request failed to connect: {e}")
			continue
		except openai.error.InvalidRequestError as e:
			#Handle invalid request error, e.g. validate parameters or log
			print(f"OpenAI API request was invalid: {e}")
			continue
		except openai.error.AuthenticationError as e:
			#Handle authentication error, e.g. check credentials or log
			print(f"OpenAI API request was not authorized: {e}")
			continue
		except openai.error.PermissionError as e:
			#Handle permission error, e.g. check scope or log
			print(f"OpenAI API request was not permitted: {e}")
			continue
		except openai.error.RateLimitError as e:
			#Handle rate limit error, e.g. wait or log
			print(f"OpenAI API request exceeded rate limit: {e}")
			print('Waiting 60 seconds...')
			time.sleep(60)
			continue

	# If retries are exhausted without a valid JSON response, return None
	return None

def toSnakeCase(string):
	string = re.sub(r'(?<=[a-z])(?=[A-Z])|[^a-zA-Z]', ' ', string).strip().replace(' ', '_')
	return ''.join(string.lower())

def get_unique_strings(strings, threshold=0.7):
	unique_strings = []
	for s in strings:
		is_unique = True
		for unique_string in unique_strings:
			similarity = 1.0 - Levenshtein.distance(s, unique_string) / max(len(s), len(unique_string))
			if similarity > threshold:
				is_unique = False
				break
		if is_unique:
			unique_strings.append(s)
	return unique_strings

def generate(topic, subject, post_destination, serp_results_dir, image_directory):
	if not os.path.exists(serp_results_dir):
		print('Making directory to store serp results')
		os.makedirs(serp_results_dir)
	serp_results_filepath = os.path.join(serp_results_dir, toSnakeCase(topic) + '.json')

	if not os.path.exists(serp_results_filepath):
		print(f'Getting serp results for {topic}')
		serp_results = get_serps(topic)

		with open(serp_results_filepath, 'w') as fp:
			json.dump(serp_results, fp)
	else:
		print('Serp results already exist...')
		with open(serp_results_filepath) as fp:
			serp_results = json.load(fp)

	vector_store = json_to_vectorstore(collection_name=topic, filepath=serp_results_filepath)
	serp_headings = []
	for result in serp_results:
		for heading in result.get('header_outline',''):
			if 70 > len(heading) > 15 and heading not in serp_headings:
				serp_headings.append(heading)
	print('serp_headings', serp_headings)
	if serp_headings:
		unique_headings = get_unique_strings(serp_headings, threshold=0.7)
		serp_headings = '\n'.join(random.sample(unique_headings, min(len(unique_headings), 100)))

	openai.api_key = settings.OPENAI_API_KEY
	prompt = "For content based on the topic " + topic + """, Write an SEO title and an SEO description, H1, and url slug for this blog post. The SEO title should be no more than 60 characters long. The H1 and the title should be different. The SEO description should be no more than 155 characters long. Use the main keywords for the slug based on the topic of the post. Do not mention the country. Max 3 or 4 keywords, without stop words, and with text normalization and accent stripping. Your response should be in the JSON format based on the following structure: {"h1" : "", "keyword": "", "seoTitle": "", "": "seoDescription": "", "slug": ""}"""
	post = openai_response(prompt=prompt, is_json=True)
	
	keyword = post.get("keyword", topic)
	seoTitle = post.get("seoTitle", topic)
	# h1_tag = post.get("h1", topic)
	# seoDescription = post.get("seoDescription", topic)
	# slug = post.get("slug", topic)

	print("Post front-matter generated", post)

	prompt = f"""Generate a blog post outline based on the relevant headings from the search results for the topic "{topic}" and this data: {post}. Ensure that the outline covers the topic comprehensively, using no more than 10 main headings.

Headings:
{serp_headings}

Use the following json format: {{
  "headings" : [ {{ "title": "", // Add headings in the form of questions
    "keywords": ["...", "...", "...", "..."], // Add a list of keywords here to help to generate the final content of this title
    "headings": [ // Add sub-headings in the form of questions
      {{ "title": "", "keywords": ["...", "..."] }},
      {{ "title": "", "keywords": ["...", "..."] }}, 
    ... ] 
  }} ... ],
}}
    """

	outline = openai_response(prompt=prompt, is_json=True)
	print(outline)
	print('Expanding outline...')
	previous_section_content = ""
	for heading in outline['headings']:
		section_title = heading['title']
		section_keywords = heading['keywords']
	
		content_prompt = f"""
		**{section_title}**

		Keywords: {", ".join(section_keywords)}

		Previous section (for context): {previous_section_content}

		Write engaging content for the section "{section_title}" related to the topic {topic}. Focus on the keywords {section_keywords} and provide valuable insights based on your expertise and experiences. Ensure the content is detailed, informative, and helpful to the readers. Incorporate relevant examples, statistics, and credible sources to support your points.

		Use a combination of paragraphs, lists, and tables to enhance the reader's experience. Implement proper SEO formatting by using elements like lists, bold text, italics, quotes, and external links. Remember to maintain a formal and optimistic tone throughout the article. Ask thought-provoking questions and provide concise answers to enhance the chances of achieving a featured snippet on search engines.

		Feel free to use contractions, idioms, transitional phrases, and colloquialisms to make the content more engaging. Avoid repetitive phrases and unnatural sentence structures. 

		Begin the section with ##"{section_title}". Sub-headings begin with ###.

		Include  at the start of the section.

		Include at least one paragraph specifically focusing on {section_keywords}.

		Do not say 'Introduction' or 'Conclusion'.
		Use markdown formatting.
		"""
		heading['section_content'] = openai_response(prompt=content_prompt)
		previous_section_content = heading['section_content']
		print('Content generated...')
		print(heading)

	article_sections = []
	for i in outline['headings']:
		article_sections.append(f"""{i['section_content']}
<!--keywords:{", ".join(i['keywords'])}-->
""")
	content = '\n\n'.join(article_sections)
	
	# prompt = f"""
	# Using markdown formatting, act as an Expert Article Writer and write a fully detailed, long-form, 100% unique, creative, and human-like article of a minimum of 5000 words using headings and sub-headings. The article should be written in a formal, informative, and optimistic tone
	# Must Develop a comprehensive "Outline" for a long-form article for the Keyword {keyword}, featuring at least 25 engaging headings and subheadings that are detailed, mutually exclusive, collectively exhaustive, and cover the entire topic. Must use LSI Keywords in these outlines. Must show these "Outlines" in a table.
	# Use English for the keyword "{keyword}" and write at least 400–500 words of engaging content under every Heading. This article should show the experience, expertise, authority and trust for the Topic {keyword}. Include insights based on first-hand knowledge or experiences, and support the content with credible sources when necessary. Focus on providing accurate, relevant, and helpful information to readers, showcasing both subject matter expertise and personal experience in the topic {keyword}.
	# Try to use contractions, idioms, transitional phrases, interjections, dangling modifiers, and colloquialisms, and avoid repetitive phrases and unnatural sentence structures.
	# When you write, you must correctly format the blog post according to proper SEO standards, with as much rich and detailed HTML as possible, for example, lists, bold, italics, quotes from the internet, tables, and external links to high-quality websites such as Wikipedia. Try to ask questions and then immediately give a good and concise answer, to try to achieve the featured snippet on Google.
	# Also, use the seed keyword as the first H2. Always use a combination of paragraphs, lists, and tables for a better reader experience. Use fully detailed paragraphs that engage the reader. Write at least one paragraph with the heading {keyword}. Write down at least six FAQs with answers and a conclusion.
	# Note: Don't assign Numbers to Headings. Don't assign numbers to Questions. Don't write Q: before the question (faqs)
	# Make sure the article is plagiarism free. Don't forget to use a question mark (?) at the end of questions. Try not to change the original {keyword} while writing the title. Try to use "{keyword}" 2-3 times in the article. Try to include {keyword} in the headings as well. Write content that can easily pass the AI detection tools test. Bold all the headings and sub-headings using Markdown formatting. Use **double asterisks** to create bold text to highlight important phrases and entities.
	# """
	# content = openai_response(prompt=prompt, model="gpt-3.5-turbo-16k", is_json=False)
	# print("Post content generated", content)

	categories = subject
	date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
	filename = f"{post['slug']}-{date.replace(' ', '-').replace(':', '')}.md"

	fileString = f"""---
	title: "{post['title']}"
	date: "{date}"
	description: "{post['seoDescription']}"
	categories: {categories}
	draft: false
	slug: "{post['slug']}"
	---
	{content}
	"""
	article_filepath = os.path.join(post_destination, filename)
	with open(article_filepath, 'w') as file:
		file.write(content)

	add_images_to_articles(topic, image_directory, article_filepath)

	return article_filepath


def generate_legacy(topic, subject, post_destination, serp_results_dir, image_directory):
	if not os.path.exists(serp_results_dir):
		print('Making directory to store serp results')
		os.makedirs(serp_results_dir)
	serp_results_filepath = os.path.join(serp_results_dir, toSnakeCase(topic) + '.json')

	if not os.path.exists(serp_results_filepath):
		print(f'Getting serp results for {topic}')
		serp_results = get_serps(topic)

		with open(serp_results_filepath, 'w') as fp:
			json.dump(serp_results, fp)
	else:
		print('Serp results already exist...')
		with open(serp_results_filepath) as fp:
			serp_results = json.load(fp)

	vector_store = json_to_vectorstore(collection_name=topic, filepath=serp_results_filepath)
	serp_headings = []
	for result in serp_results:
		for heading in result.get('header_outline',''):
			if 70 > len(heading) > 15 and heading not in serp_headings:
				serp_headings.append(heading)
	serp_headings = '\n'.join(random.sample(get_unique_strings(serp_headings, threshold=0.7), 100))

	print('Serp outlines:', serp_headings)
	categories = subject
	print('Running generate.mjs')

	command = ['/usr/local/bin/node', 
		os.path.join(settings.BASE_DIR, 'generate', 'generate.mjs'), 
		post_destination, 
		subject, 
		categories, 
		topic, 
		serp_headings, 
		vector_store,
		settings.OPENAI_API_KEY,
	]
	try:
		with Popen(command, stdout=PIPE, bufsize=1, universal_newlines=True) as p:
			for line in p.stdout:
				if 'Markdown file has been written.' in line:
					article_filepath = line.split('Markdown file has been written.')[1].strip()
				print(line, end='') # process line here
	except CalledProcessError as e:
		raise RuntimeError("command '{}' return with error (code {}): {}".format(e.cmd, e.returncode, e.output))

	print('Adding images to article')
	add_images_to_articles(topic, image_directory, article_filepath)

	return article_filepath

if __name__ == '__main__':
	subject = sys.argv[1]
	topic = sys.argv[2]
	categories = subject

	post_destination = sys.argv[3] # '../sites/permaculture/site/content/posts/image_test/'
	serp_results_dir = sys.argv[4] # '../sites/permaculture/data/serp_results'
	image_directory = sys.argv[5] # '../permaculture/site/static/images'

	generate(topic, subject, post_destination, serp_results_dir, image_directory)

