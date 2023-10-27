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


def crawl(url, relative_absolute_path):
    print(url)
    # get page content
    response = requests.get(url)
    host_url = get_host_url(url, relative_absolute_path)
    soup = BeautifulSoup(response.content, "html.parser")

    list_of_lists = []

    # find hrefs in page content
    for url in soup.find_all('a'):
        found_url = url['href']
        if host_url in found_url:
            list_of_lists.append(found_url)

        elif not re.search(r'(https?://)', found_url) and not found_url[0] == '#':
            #print(host_url + add_slash(found_url))
            list_of_lists.append(host_url + add_slash(found_url))
    
    return list_of_lists
    


if __name__ == '__main__':
    start_url = "https://vm009.rz.uos.de/crawl"
    relative_absolute_path = '/crawl'
    search_list = [start_url]


    itere = 1
    while len(search_list) != 0:
        print(itere)
        print(search_list)
        for url in search_list:
            print(search_list)

            # if not visited recently:
            search_list += crawl(url, relative_absolute_path)
            search_list = list(set(search_list))
            search_list.remove(url)

        itere += 1

        """
        with Pool(5) as p:
            search_list += p.map(crawl, search_list)
            print(len(search_list)) 
        """