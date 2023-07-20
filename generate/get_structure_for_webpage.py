import sys
import urllib3
from bs4 import BeautifulSoup, Tag
from pprint import pprint
import re
from urllib.parse import urlparse
import collections
import requests
from requests.exceptions import HTTPError

def html_body_shorthand(html):
    # Parse HTML data
    soup = BeautifulSoup(html, 'html.parser')
    if not soup.body:
        return ''
    # Replace <p> tags with the appropriate heading tags
    for i in range(1, 7):
        for p_tag in soup.find_all('p'):
            _replace_p_with_heading(p_tag, i)
    
    content_tree = {"_parent": {}, "_children": [], "_name": "body"}
    current_node = content_tree
    
    shorthand_tags = soup.body.find_all(lambda tag: tag.name != "script", recursive=False)
    
    for tag in shorthand_tags:
        _build_parse_tree(current_node, tag)
    
    template_string = _traverse_parse_tree_build_string(current_node)
    return template_string

def _replace_p_with_heading(tag, heading_level):
    p_class = tag.get('class')
    if p_class and any(h_class in p_class for h_class in [f'h{heading_level}', f'heading{heading_level}', f'header{heading_level}', f'header-{heading_level}', f'heading-{heading_level}']):
        tag.name = f'h{heading_level}'
        tag.attrs = {}

def _traverse_parse_tree_build_string(node):
    string = ""
    for child_node in node["_children"]:
        string += child_node["_name"]
        if len(child_node["_children"]) > 0:
            string += "("
            string += _traverse_parse_tree_build_string(child_node)
            string += "),"
        else:
            string += ","
    
    return string.rstrip(",")

def _build_parse_tree(node, tag):
    node["_children"].append({"_parent": node, "_children": [], "_name": tag.name})
    if tag.children:
        for child_tag in tag.children:
            if child_tag.name is None:
                continue
            else:
                _build_parse_tree(node["_children"][-1], child_tag)

def remove_empty_tags(soup):
    for tag in soup.find_all(True):
        if isinstance(tag, Tag) and not tag.contents and not tag.string:
            tag.extract()

def remove_attributes(tag):
    for attribute in list(tag.attrs):
        del tag[attribute]
    return tag

def one_line(tag):
    string = ''.join(tag.stripped_strings)
    return re.sub(r"\n", " ", string)

def replace_newline_except_last(string):
    result = re.sub(r"\n", " ", string)
    return result

def get_header_outline(html):
    soup = BeautifulSoup(html, 'html.parser')
    remove_empty_tags(soup)
    h_tags = soup.find_all(['title', 'h1', 'h2', 'h3'])
    content = []
    title_tag_done = 0
    for tag in h_tags:
        clean_tag = remove_attributes(tag)
        if clean_tag.name == "title" and title_tag_done == 1:
            continue
        tag_content = one_line(clean_tag)[:100]

#        content.append(f"<{clean_tag.name}>{tag_content}</{clean_tag.name}>")
        if clean_tag.name == "title":
            title_tag_done = 1
       

        content.append(f"{clean_tag.name}:{tag_content}")
    return content

def count_words_in_paragraphs(html, sample_word_count):
    # Parse HTML data
    soup = BeautifulSoup(html, 'html.parser')

    # Find all <p> tags
    paragraphs = soup.find_all('p')

    word_count = 0
    sample_words = ""

    for p in paragraphs:
        # Get text inside <p> tag
        text = p.get_text()

        # Split text into words based on white spaces and count the words
        words = text.split()
        if not words:
            continue
        words[-1] += " "

        # Update the word count
        word_count += len(words)

        if sample_word_count > 0:
            if sample_word_count < word_count:
                sample_words += " ".join(words)
                sample_word_count -= word_count
            else:
                sample_words += " ".join(words[0:sample_word_count])
                sample_word_count -= word_count


    sample_words = sample_words.strip()
    p_count = len(paragraphs)

    return { "word_count": word_count, "sample_words": sample_words, "p_count": p_count }

def list_info(html):
    # Parse HTML data
    soup = BeautifulSoup(html, 'html.parser')

    # Find all <ol> and <ul> tags
    ordered_lists = soup.find_all('ol')
    unordered_lists = soup.find_all('ul')

    # Count the number of each type of list
    ol_count = len(ordered_lists)
    ul_count = len(unordered_lists)

    # Return the counts as a dictionary
    lists = {'ol_count': ol_count, 'ul_count': ul_count}
    return lists

def link_info(html, url):
    # Parse HTML data
    soup = BeautifulSoup(html, 'html.parser')

    # Find all <a> tags
    a_tags = soup.find_all('a')

    internal_counts = collections.defaultdict(int)
    external_counts = collections.defaultdict(int)
    general_counts = collections.defaultdict(int)
    internal_links = []
    external_links = []
    link_info = {}

    # Parse the provided URL to get its domain
    parsed_provided_url = urlparse(url)
    provided_domain = parsed_provided_url.netloc

    for a in a_tags:
        # Get the href attribute
        href = a.get('href')
        # If href is None, continue to the next iteration
        if not href:
            continue

        # Parse the URL
        parsed_url = urlparse(href)

        if href.startswith("#"):
            internal_counts["bookmark_count"] += 1
            continue


        uri_scheme_match = re.match(r"[^:]+:", href)
        if uri_scheme_match:
            uri_scheme = uri_scheme_match.group().rstrip(":")
            if (uri_scheme != "https") and (uri_scheme != "http"):
                continue
        
        # Check if the href starts with the provided domain, or if the domain of the parsed URL matches the provided domain
        if href.startswith("https://" + provided_domain) or href.startswith("http://" + provided_domain) or (href.startswith(provided_domain) and not parsed_url.netloc):
            internal_counts["internal_link_count"] += 1
            internal_links.append(href)
        else:
            external_counts["external_link_count"] += 1
            external_links.append(href)

    link_info = { 
        "internal": internal_counts, 
        "external": external_counts, 
        "general": general_counts, 
        "internal_links": internal_links, 
        "external_links": external_links 
        }

    return link_info


def get_outline(url, html_data, num_sample_words ):
    header_outline = get_header_outline(html=html_data)
    p_counts = count_words_in_paragraphs(html=html_data,sample_word_count=num_sample_words)
    links = link_info(html=html_data, url=url)
    lists = list_info(html=html_data)

    outline = { "header_outline": header_outline }
    outline.update(links)
    outline.update(p_counts)
    outline.update(lists)
    outline.update({"url": url})
    outline.update({"shorthand": html_body_shorthand(html_data)})
    return outline


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python script.py <url> <html_data>")
        sys.exit(1)

    url = sys.argv[1]
    html_data = sys.argv[2]
    result = {}

    try:
        result = get_outline(url=url, html_data=html_data, num_sample_words=25)
    except Exception as err:
        raise
        print(f"Error getting outline: {err}")
        #traceback.print_stack()
    

    pprint(result)


