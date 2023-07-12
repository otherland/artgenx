import re
import asyncio
import aiohttp
import urllib.parse
from bs4 import BeautifulSoup

main_queue = asyncio.Queue()
parsed_links_queue = asyncio.Queue()
parsed_links = set()

session = None
f_out = None
visited_urls = 0
max_depth = 2  # Maximum depth of links to search

def check_email(html):
    email_regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'  # Regular expression for email address pattern

    # Find email address patterns in the HTML
    email_addresses = re.findall(email_regex, html)

    if email_addresses:
        print(f'Found email addresses: {", ".join(email_addresses)}', flush=True)


async def get_url(url):
    global visited_urls
    try:
        async with session.get(url) as resp:
            visited_urls += 1
            return await resp.text()
    except:
        print(f'Bad URL: {url}')

async def worker(domain, depth):
    while True:
        url, curr_depth = await main_queue.get()
        soup = BeautifulSoup(await get_url(url), 'html.parser')

        for a in soup.select('a[href]'):
            href = a['href']
            if href.startswith('/') and ':' not in href:
                parsed_links_queue.put_nowait((domain + href, curr_depth + 1))
            elif href.startswith('//'):
                parsed_links_queue.put_nowait(('http:' + href, curr_depth + 1))  # Assuming http protocol by default

        check_email(soup.prettify())

        main_queue.task_done()


async def consumer():
    while True:
        url, curr_depth = await parsed_links_queue.get()

        if url not in parsed_links and curr_depth <= max_depth:
            print(urllib.parse.unquote(url), file=f_out, flush=True)  # <-- print the url to file
            parsed_links.add(url)
            main_queue.put_nowait((url, curr_depth))

        parsed_links_queue.task_done()


async def scrape_emails(seed_url, domain):
    global session, f_out

    parsed_links.add(seed_url)

    with open('scraped_links.txt', 'w') as f_out:
        async with aiohttp.ClientSession() as session:
            workers = {asyncio.create_task(worker(domain, 0)) for _ in range(16)}
            c = asyncio.create_task(consumer())

            main_queue.put_nowait((seed_url, 0))
            print('Initializing...')
            await asyncio.sleep(5)

            while main_queue.qsize():
                print(f'Visited URLs: {visited_urls:>7}  Known URLs (saved in out.txt): {len(parsed_links):>7}', flush=True)
                await asyncio.sleep(0.1)

    await main_queue.join()
    await parsed_links_queue.join()

if __name__ == '__main__':
    domain = 'https://es.wikipedia.org'
    seed_url = 'https://es.wikipedia.org/wiki/Olula_del_R%C3%ADo'
    asyncio.run(scrape_emails(seed_url, domain))