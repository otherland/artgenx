import os
import sys
import re
import asyncio
import subprocess
from serps import get_serps
from embed import json_to_vectorstore
import json
from subprocess import Popen, PIPE, CalledProcessError
from add_images import add_images_to_articles

def toSnakeCase(string):
    string = re.sub(r'(?<=[a-z])(?=[A-Z])|[^a-zA-Z]', ' ', string).strip().replace(' ', '_')
    return ''.join(string.lower())

topic = sys.argv[1]

subject = 'permaculture'
destination = '../permaculture/site/content/posts/image_test/'
categories = subject

serp_results = get_serps(topic)

serp_results_dir = os.path.join('../permaculture/data/serp_results')
if not os.path.exists(serp_results_dir):
    os.makedirs(serp_results_dir)
serp_results_filepath = os.path.join(serp_results_dir, toSnakeCase(topic) + '.json')

with open(serp_results_filepath, 'w') as fp:
	json.dump(serp_results, fp)

vector_store = json_to_vectorstore(serp_results_filepath)
serp_outlines = '\n'.join(['\n'.join(i.get('header_outline','')) for i in serp_results])

print('Running generate.mjs')
command = ['/usr/local/bin/node', 
	'./generate.mjs', 
	destination, 
	subject, 
	categories, 
	topic, 
	serp_outlines, 
	vector_store,
]
try:
	with Popen(command, stdout=PIPE, bufsize=1, universal_newlines=True) as p:
	    for line in p.stdout:
	        print(line, end='') # process line here
except CalledProcessError as e:
    raise RuntimeError("command '{}' return with error (code {}): {}".format(e.cmd, e.returncode, e.output))


# Call the function to edit the markdown files
add_images_to_articles(topic, '../permaculture/site/static/images', '../permaculture/site/content/posts/image_test/')



