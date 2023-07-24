import http.client
import json
import sys
import time
import os.path
import csv
import os
import json
import asyncio
import aiohttp
import os
import json
from bs4 import BeautifulSoup
from datetime import datetime
from .get_structure_for_webpage import get_outline


async def fetch_html(url):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                response.raise_for_status()
                # Check the Content-Type header for the encoding
                content_type = response.headers.get('Content-Type', '').lower()
                if 'charset=' in content_type:
                    encoding = content_type.split('charset=')[-1]
                else:
                    # If encoding is not specified, use 'utf-8' as a default
                    encoding = 'utf-8'
                # Read the response content with the specified encoding
                html_content = await response.read()
                try:
                    decoded_content = html_content.decode(encoding)
                except UnicodeDecodeError:
                    decoded_content = html_content.decode('ISO-8859-1')
                return decoded_content
    except aiohttp.ClientError as e:
        print(f"Error fetching HTML for URL: {url}")
        return None

async def process_row(row):
    url = row["url"]
    print('Processing url', url)
    html_content = await fetch_html(url)
    if html_content is not None:
        print('Getting outline...')
        json_object = get_outline(url, html_content, num_sample_words=25)

        metadata = {
            "header_outline": json_object["header_outline"],
            "internal": json_object["internal"],
            "external": json_object["external"],
            "general": json_object["general"],
            "internal_links": json_object["internal_links"],
            "external_links": json_object["external_links"],
            "word_count": json_object["word_count"],
            "sample_words": json_object["sample_words"],
            "p_count": json_object["p_count"],
            "ol_count": json_object["ol_count"],
            "ul_count": json_object["ul_count"],
            "url": url,
            "shorthand": json_object["shorthand"]
        }

        row.update(metadata)

def is_valid_date(date_string):
    try:
        datetime.strptime(date_string, '%b %d, %Y')
        return True
    except ValueError:
        return False


def get_links(query, pages=1):
    conn = http.client.HTTPSConnection("google.serper.dev")
    payload = json.dumps({
      "q": query,
      "num": 20
    })
    headers = {
      'X-API-KEY': '9d9825178297e2a64a6ed26f31287e7e26bb548e',
      'Content-Type': 'application/json'
    }
    conn.request("POST", "/search", payload, headers)
    res = conn.getresponse()
    data = res.read()
    data = json.loads(data.decode("utf-8"))
    links = [(i['title'], i['link'], i['snippet']) for i in data['organic']]
    return links

async def save_serps(query):
    # print('getting links for', query)
    links = get_links(query)
    serp_results = [{"title": title, "url": url, "description": description} for title, url, description in links]
    print('Serp Results:', serp_results)
    tasks = []
    for row in serp_results:
        tasks.append(process_row(row))

    await asyncio.gather(*tasks)
    serp_results = [i for i in serp_results if i.get('sample_words')]
    print('Expanded Serp Results', serp_results)
    return serp_results

def get_serps(query):
    return asyncio.run(save_serps(query))


