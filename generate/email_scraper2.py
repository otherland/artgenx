import re
import csv
import asyncio
import aiohttp
import urllib.parse
from bs4 import BeautifulSoup

main_queue = asyncio.Queue()
parsed_links_queue = asyncio.Queue()
parsed_links = set()
visited_urls = set()
max_depth = 2  # Maximum depth of links to search

async def get_url(url):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                return await resp.text()
    except:
        print(f'Bad URL: {url}')

async def worker(domain, depth):
    while True:
        url, curr_depth = await main_queue.get()

        if url not in visited_urls:
            visited_urls.add(url)
            html = await get_url(url)
            soup = BeautifulSoup(html, 'html.parser')

            for a in soup.select('a[href]'):
                href = a['href']
                if href.startswith('/') and ':' not in href:
                    parsed_links_queue.put_nowait((domain + href, curr_depth + 1))
                elif href.startswith('//'):
                    parsed_links_queue.put_nowait(('http:' + href, curr_depth + 1))  # Assuming http protocol by default

            check_email(domain, html)

            with open('scraped_links.txt', 'a') as f:
                f.write(url + '\n')

        main_queue.task_done()


async def consumer():
    while True:
        url, curr_depth = await parsed_links_queue.get()

        if url not in parsed_links and curr_depth <= max_depth:
            parsed_links.add(url)
            main_queue.put_nowait((url, curr_depth))

        parsed_links_queue.task_done()


def check_email(domain, html):
    email_regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'  # Regular expression for email address pattern

    # Find email address patterns in the HTML
    email_addresses = re.findall(email_regex, html)

    if email_addresses:
        print(f'Found email addresses for domain {domain}: {", ".join(email_addresses)}', flush=True)
        save_email_addresses(domain, email_addresses)


def save_email_addresses(domain, email_addresses):
    with open('domain_emails.csv', 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([domain, ', '.join(email_addresses)])


async def scrape_emails(seed_url, domain):
    parsed_links.add(seed_url)
    main_queue.put_nowait((seed_url, 0))

    while main_queue.qsize():
        print(f'Visited URLs: {len(visited_urls):>7}  Known URLs (saved in scraped_links.txt): {len(parsed_links):>7}', flush=True)
        await asyncio.sleep(0.1)

    await main_queue.join()
    await parsed_links_queue.join()


if __name__ == '__main__':
    domain = 'https://es.wikipedia.org'
    seed_url = 'https://es.wikipedia.org/wiki/Olula_del_R%C3%ADo'
    asyncio.run(scrape_emails(seed_url, domain))