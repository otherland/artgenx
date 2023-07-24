import random
import os
import sys
import re
import asyncio
import subprocess
import json
from subprocess import Popen, PIPE, CalledProcessError
import Levenshtein
from serps import get_serps
from embed import json_to_vectorstore
from add_images import add_images_to_articles

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

    vector_store = json_to_vectorstore(serp_results_filepath)
    serp_headings = []
    for result in serp_results:
        for heading in result.get('header_outline',''):
            if 70 > len(heading) > 15 and heading not in serp_headings:
                serp_headings.append(heading)
    serp_headings = '\n'.join(random.sample(get_unique_strings(serp_headings, threshold=0.7), 100))

    print('Serp outlines:', serp_headings)

    print('Running generate.mjs')
    command = ['/usr/local/bin/node', 
        './generate.mjs', 
        post_destination, 
        subject, 
        categories, 
        topic, 
        serp_headings, 
        vector_store,
    ]
    try:
        with Popen(command, stdout=PIPE, bufsize=1, universal_newlines=True) as p:
            for line in p.stdout:
                print(line, end='') # process line here
    except CalledProcessError as e:
        raise RuntimeError("command '{}' return with error (code {}): {}".format(e.cmd, e.returncode, e.output))

    print('Adding images to articles')
    # Call the function to edit the markdown files
    add_images_to_articles(topic, image_directory, post_destination)

if __name__ == '__main__':
    subject = sys.argv[1]
    topic = sys.argv[2]
    categories = subject

    post_destination = sys.argv[3] # '../sites/permaculture/site/content/posts/image_test/'
    serp_results_dir = sys.argv[4] # '../sites/permaculture/data/serp_results'
    image_directory = sys.argv[5] # '../permaculture/site/static/images'

    generate(topic, subject, post_destination, serp_results_dir, image_directory)

