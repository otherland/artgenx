import sys
import spacy
import markdown
from bs4 import BeautifulSoup
from fuzzywuzzy.process import dedupe
from fuzzywuzzy import fuzz

import re
import string
# Create a regex pattern to match a string
# that starts with one or more special characters
pattern = r'^[' + string.punctuation + ']+'

nlp = spacy.load('en_core_web_sm')

def remove_nested_bold_tags(content):
    soup = BeautifulSoup(content, 'html.parser')
    for bold_tag in soup.find_all('b'):
        for nested_bold_tag in bold_tag.find_all('b'):
            nested_bold_tag.unwrap()
    for item in soup.find_all('b'):
        if item.findChild():
            item.unwrap()

    text = str(soup)
    text = text.replace('<b>','**')
    text = text.replace('</b>','**')
    return text

def embolden_entities(file_path):
    with open(file_path, 'r') as file:
        markdown_content = file.read()

    heading = markdown_content.split('---')[1]
    markdown_content = markdown_content.split('---')[-1]

    # Process the HTML content with Spacy
    doc = nlp(markdown_content)

    # Identify entities and n-grams
    entities = []
    for e in list(doc.ents):
        e = str(e)
        if len(e.split()) >= 2 and '\n' not in e and not re.search(pattern, e) and e not in entities:
            entities.append(e)

    for e in list(doc.noun_chunks):
        e = str(e)
        if len(e.split()) >= 3 and '\n' not in e and e not in entities and not re.search(pattern, e) and e not in entities:
            entities.append(e)

    entities = entities[::5]
    entities = list(dedupe(entities, threshold=97, scorer=fuzz.ratio))

    # Replace entities and n-grams with bold tags in the HTML content
    for entity_text in entities:
        entity_html = f'<b>{entity_text}</b>'
        markdown_content = markdown_content.replace(entity_text, entity_html, 1)

    emboldened_markdown = remove_nested_bold_tags(markdown_content)

    # Write the emboldened markdown back to the same file
    with open(file_path, 'w') as file:
        file.write(f"""---{heading}---\n{emboldened_markdown}""")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Please provide the path to the markdown file as an argument.")
        sys.exit(1)

    markdown_file_path = sys.argv[1]
    embolden_entities(markdown_file_path)

    print(f"Emboldened entities and n-grams written to: {markdown_file_path}")
