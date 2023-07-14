import os
import json
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException
from selenium.webdriver.support.ui import WebDriverWait
from bs4 import BeautifulSoup
from selenium.webdriver.chrome.service import Service
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import sys
import time
from datetime import datetime
import os.path
import csv

import os
import json
import asyncio
import aiohttp
from get_structure_for_webpage import get_outline

async def fetch_html(url):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                response.raise_for_status()
                html_content = await response.text()
                return html_content
    except aiohttp.ClientError as e:
        print(f"Error fetching HTML for URL: {url}")
        return None

async def process_row(row):
    url = row["url"]

    html_content = await fetch_html(url)
    if html_content is not None:
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

def returnChromeDriver():
    username = 'your_username'
    password = 'your_password'
    endpoint = 'gate.smartproxy.com'
    port = '7000'
    # proxies_extension = proxies(username, password, endpoint, port)

    if sys.platform == 'linux':
        from pyvirtualdisplay import Display
        display = Display(visible=0, size=(1920, 1480))
        display.start()
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument('--no-sandbox')
    options.add_argument('--enable-logging')
    options.add_argument("--start-maximized")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--remote-debugging-port=9222")
    
    # chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    # chrome_options.add_experimental_option('useAutomationExtension', False)
    # chrome_options.add_experimental_option('prefs', {
    #     'profile.default_content_settings': {"images": 2},
    #     'profile.default_content_setting_values.clipboard': 1,
    #     'credentials_enable_service': False,
    #     'profile': {
    #         'password_manager_enabled': False,
    #         'managed_default_content_settings.javascript': 1, 
    #         'managed_default_content_settings.images': 2, 
    #         'managed_default_content_settings.stylesheet': 2,
    #     }
    # })
    driver = webdriver.Chrome(options=options)
    return driver

    
def returnSearchUrl(question, start=0):
    baseGoogleQuery = f"https://www.google.com/search?q={question}&biw=1280&bih=698&gl=us&start={start}&sa=N"
    searchUrl = baseGoogleQuery + question.lower().replace(" ", "+").replace("?", "%3F").replace("'", "%27")
    searchUrl += "&gl=us"
    return searchUrl

def scroll_center(driver, element):
    desired_y = (element.size['height'] / 2) + element.location['y']
    window_h = driver.execute_script('return window.innerHeight')
    window_y = driver.execute_script('return window.pageYOffset')
    current_y = (window_h / 2) + window_y
    scroll_y_by = desired_y - current_y

    driver.execute_script("window.scrollBy(0, arguments[0]);", scroll_y_by)

def get_links(query, pages=1):
    driver=returnChromeDriver()
    question_data = []
    searchUrl = returnSearchUrl(query)
    driver.get(searchUrl)

    try:
        cookie = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[.='Accept all']")))
        scroll_center(driver, cookie)
        cookie.click()
    except Exception as e:
        logging.error('Cookie error')
        logging.error(e)

    start = 0
    links = []
    for _ in range(pages):
        html = driver.page_source

        soup = BeautifulSoup(html)
        newlinks = []
        for i in soup.findAll('h3',{"class": "DKV0Md"}):
            description = ''
            try:
                # el = i.parent.parent.parent.parent.findChildren()[-3]
                # if is_valid_date(el.text) or (el.has_attr('class') and "WZ8Tjf" in el["class"]):
                #     el = i.parent.parent.parent.parent.findChildren()[-2]
                # description = el.text                
                description = i.parent.parent.parent.parent.findChildren('div',{'style':"-webkit-line-clamp:2"})[-1].text
            except Exception as e:
                print(e)
            newlinks.append((
                i.text,
                i.parent['href'],
                description,
            ))
        if not newlinks:
            return links
        print(newlinks)
        links.extend(newlinks)
        driver.execute_script("window.scrollTo(0, 100000)")
        more_results = None
        next_button = None
        try:
            more_results = driver.find_element(By.XPATH,"//span[text()='More results']")
            next_button = driver.find_element(By.XPATH,"//span[text()='Next']")
        except Exception:
            pass
        try:
            if more_results:
                more_results.click()
                start += 10
            elif next_button:
                next_button.click()
                start += 10
            else:
                start += 10
                driver.get(returnSearchUrl(query, start))
        except Exception as e:
            print('No more results button')

        time.sleep(2)

    return links

async def save_serps(query):
    links = get_links(query)
    serp_results = [{"title": title, "url": url, "description": description} for title, url, description in links]

    tasks = []
    for row in serp_results:
        tasks.append(process_row(row))

    await asyncio.gather(*tasks)
    serp_results = [i for i in serp_results if i.get('sample_words')]
    return serp_results

def get_serps(query):
    return asyncio.run(save_serps(query))


