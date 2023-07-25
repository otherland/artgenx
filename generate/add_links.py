import time
import sys
import random
import spacy
from bs4 import BeautifulSoup
from .serps import get_links

try:
    nlp = spacy.load('en_core_web_sm')
except OSError:
    print('Downloading language model for the spaCy POS tagger\n'
        "(don't worry, this will only happen once)", file=stderr)
    from spacy.cli import download
    download('en_core_web_sm')
    nlp = spacy.load('en_core_web_sm')


def extract_last_four_words(text):
    doc = nlp(text)
    last_four_words_list = []

    for sentence in doc.sents:
        words = [token.text_with_ws for token in sentence if not token.is_space]
        last_four_words = ''.join(words[-7:]).replace('**.','').replace('**','').strip()
        lfw = nlp(last_four_words)
        if sum(1 for token in lfw if token.pos_ == 'NOUN') > 1:
            last_four_words_list.append(last_four_words)
    return last_four_words_list

def scrape_web_page(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    return soup.get_text()

def add_links_to_articles(markdown_content, base_query):

    keyphrases = extract_last_four_words(markdown_content)[::6][:5]
    print(keyphrases)

    link_bank = []
    for phrase in keyphrases:
        print(f'Searching {phrase}')
        time.sleep(2)
        links = [l[1] for l in get_links(f'{base_query} {phrase}')]
        links = [l for l in links if l not in link_bank]
        link = random.choice(links)
        link_bank.append(link)
        print(f'Adding link {link}')
        markdown_content = markdown_content.replace(phrase, f'[{phrase}]({link})')
    return markdown_content

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("arguments: markdown_file_path, base_query")
        sys.exit(1)

    markdown_file_path = sys.argv[1]
    base_query = sys.argv[2]

    with open(markdown_file_path, 'r') as file:
        markdown_content = file.read()
    
    keyphrases = extract_last_four_words(markdown_content)[::2]
    print(keyphrases)

    link_bank = []
    for phrase in keyphrases:
        time.sleep(2)
        links = [l[1] for l in get_links(f'{base_query} {phrase}')]
        links = [l for l in links if l not in link_bank]
        link = random.choice(links)
        link_bank.append(link)
        print(f'Adding link {link}')
        markdown_content = markdown_content.replace(phrase, f'[{phrase}]({link})')

    print('Writing links to markdown file...')
    with open(markdown_file_path, 'w') as file:
        file.write(markdown_content)
    print('SUCCESS!')
