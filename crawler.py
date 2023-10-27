import re
import requests
from bs4 import BeautifulSoup
from multiprocessing import Pool

def get_host_url(url, relative_path=False):

    if re.search(r'https?://(.*)/', url):
        return re.search(r'(https?://.*?)/', url).group(1) + (relative_path if relative_path else "")
    else:
        return re.search(r'(https?://.*)', url).group(1)+ (relative_path if relative_path else "")


def add_slash(url):
    if url[0] == '/':
        return url
    else:
        return '/' + url


def crawl(url):
    print(url)
    # get page content
    response = requests.get(url)
    host_url = get_host_url(url, '/crawl')
    soup = BeautifulSoup(response.content, "html.parser")

    list_of_lists = []

    # find hrefs in page content
    for url in soup.find_all('a'):
        found_url = url['href']
        if (not re.search(r'(https?://)', found_url) or host_url in found_url) and not found_url[0] == '#':
            print(host_url + add_slash(found_url))
            list_of_lists.append(host_url + add_slash(found_url))
    
    return list_of_lists
    


if __name__ == '__main__':
    start_url = "https://vm009.rz.uos.de/crawl/index.html"
    search_list = [start_url]

    while len(search_list) != 0:

        for url in search_list:
            search_list += crawl(url)
            search_list.remove(url)

        """
        with Pool(5) as p:
            search_list += p.map(crawl, search_list)
            print(len(search_list)) 
        """