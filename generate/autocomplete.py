import requests
import json
import time
import string
import itertools
import tqdm
import concurrent.futures
import datetime
import re

def format_proxy(proxy):
    proxy_servers = proxy.split(":")
    proxy_ip = proxy_servers[0]
    proxy_port = proxy_servers[1]
    proxy_username = proxy_servers[2]
    proxy_password = proxy_servers[3]
    proxy = f"http://{proxy_username}:{proxy_password}@{proxy_ip}:{proxy_port}"
    return proxy
def validate_proxy(proxy):
    proxy = format_proxy(proxy)
    res = requests.get("https://api.ipify.org", proxies={"http": proxy, "https": proxy})
    if res.status_code == 200:
        assert res.text in proxy
        return True
    else:
        raise Exception("Proxy not valid")
def replace_year(query: str) -> str:
    current_year = datetime.datetime.now().year
    match = re.search(r"(?<=\b)\d{4}(?=\b)", query)
    if match:
        original_year = int(match.group(0))
        if original_year <= current_year and original_year > current_year - 5:
            if datetime.datetime.now().month >= 10:
                current_year += 1
            return re.sub(r"(?<=\b)\d{4}(?=\b)", str(current_year), query)
    return query
def makeGoogleRequest(query: str, proxy:str = None) -> list:
    time.sleep(0.2)
    # proxy must be in the format of ip:port:username:password or ip:port
    try:
        URL = "http://www.google.com/complete/search"
        PARAMS = {"q": query, "hl": "en-US", "client": "firefox"}
        headers = {"User-agent": "Mozilla/5.0"}
        if proxy:
            request_proxy = {
                "http": proxy,
                "https": proxy,
            }
        else:
            request_proxy = None
        response = requests.get(
            URL, params=PARAMS, headers=headers, proxies=request_proxy
        )
        if response.status_code == 200:
            suggestedSearches = json.loads(response.content.decode("utf-8"))[1]
            return suggestedSearches
        elif response.status_code == 500:
            return makeGoogleRequest(query, proxy)
        elif response.status_code == 403:
            time.sleep(3600)
            return makeGoogleRequest(query, proxy)
    except Exception as e:
        return f"ERR - {e}"
  
class autocomplete:
    def __init__(self, query: str, website = None, simple=None):
        self.query = query
        self.website = website
        self.simple = simple
      
        if self.website:
            if self.website.proxy:
                self.proxy = format_proxy(website.proxy)
        else:
            self.proxy = None
      
    def getGoogleSuggests(self) -> list:
        charList = string.ascii_lowercase
        separators = [" ", " * "]
        # use itertools to generate all possible combinations of the following lists
        # prefix + separator + keyword
        # prefix + separator + keyword + separator + char
        # keyword + separator + char
        prefixes = [
            "what",
            "how",
            "is",
            "can",
            "why",
            "does",
            "which",
            "who",
            "do",
            "are",
            "where",
            "should",
            "when",
            "whats",
            "will",
            "did",
            "best",
            "was",
        ]
        queries_1 = map(
            lambda x: x[0] + x[1] + x[2],
            itertools.product(prefixes, separators, [self.query]),
        )
        queries_2 = map(
            lambda x: x[0] + x[1] + x[2] + x[3] + x[4],
            itertools.product(prefixes, separators, [self.query], separators, charList),
        )
        queries_3 = map(
            lambda x: x[0] + x[1] + x[2],
            itertools.product([self.query], separators, charList),
        )
        # if variable simple is defined
        if self.simple:
            query_list_az = list(queries_1)
        else:
            query_list_az = list(itertools.chain(queries_1, queries_2, queries_3))
        # combine all the lists and remove duplicates
        query_list = list(set(itertools.chain(query_list_az)))
        print(f"Scraping autocomplete for '{self.query}'...")
        suggestions = []
        for query in tqdm.tqdm(query_list):
            suggestion = makeGoogleRequest(query, proxy=self.proxy)
            if suggestion and "ERR" not in suggestion:
                print(suggestion)
                suggestions.append(suggestion)
        # Remove empty suggestions using filter
        suggestions = set(itertools.chain(*suggestions))
        suggestions = list(filter(None, suggestions))
        return suggestions
    def generate(self) -> list:
        resultList = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futuresGoogle = {executor.submit(self.getGoogleSuggests)}
            resultList = [
                suggestion
                for future in concurrent.futures.as_completed(futuresGoogle)
                for suggestion in future.result()
            ]
        # remove duplicates
        resultList = list(set(resultList))
        # replace the year in the query with the current year
        resultList = [replace_year(suggestion) for suggestion in resultList]
        return resultList
    def autocomplete(self) -> list:
        all_results = []
        results = self.generate()
        all_results.append(results)
        # flatten list and remove duplicates
        all_results = list(set(itertools.chain(*all_results)))
        all_results.sort()
        # check if self.query is in each item in all_results
        # if it isn't, remove it
        all_results = [item for item in all_results if self.query.casefold() in item.casefold()]
        return all_results

if __name__ == "__main__":
  
    x = autocomplete("permaculture", simple=False).autocomplete()
    print(x)
    # save to a file
    with open("results.txt", "w", encoding='utf-8') as f:
        for item in x:
            f.write(item + "\n")