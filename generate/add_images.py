import re
import os
import glob
from .google_image_scraper import download_images
from .add_links import add_links_to_articles

def replace_references(text):
    # Use regular expression to find and replace the references
    updated_text = re.sub(r'\[\^(\d)\^\]', r'[^\1]', text)
    updated_text = updated_text.replace('**References:**', '')
    return updated_text

def add_images_to_article(topic, image_directory, article_filepath):
    # Read the contents of the markdown file
    with open(article_filepath, 'r') as file:
        contents = file.read()

    # Perform your desired modifications to the contents
    # For example, let's convert all headings to uppercase
    keyword_pattern = r"<!--keywords:(.*?)-->"
    image_template = '![{}]({})'
    keywords = [i for i in re.findall(keyword_pattern, contents, flags=re.DOTALL) if i]

    print('Keywords to replace with images', keywords)
    if keywords:
        image_kw_mapping = download_images(image_directory, keywords)
        print(image_kw_mapping)
        for key, image_path in image_kw_mapping.items():
            replacement = image_template.format(key, image_path)
            contents = re.sub(keyword_pattern, replacement, contents, count=1, flags=re.DOTALL)
        print(contents)

    # Write the modified contents back to the markdown file
    with open(file_path, 'w') as file:
        file.write(contents)

    print('Adding links to article...')
    contents = add_links_to_articles(contents, topic)
    print('Reformatting references...')
    contents = replace_references(contents)

    # Write the modified contents back to the markdown file
    with open(file_path, 'w') as file:
        file.write(contents)

    print(f"Modified file: {file_path}")


