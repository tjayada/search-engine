import re
import time
import requests
from bs4 import BeautifulSoup
from multiprocessing import Pool
import os, os.path
from whoosh import index
from whoosh.fields import Schema, TEXT, ID
from whoosh.writing import AsyncWriter
import sys


def replace_punctuations(text):
    """remove new lines, unbreakable spaces, multiple spaces or any non characters"""
    text = text.replace("\n", " ").replace("\xa0", " ").replace("-", " ").lower()
    text = re.sub(r'[^\w\s]+', '', text)
    return re.sub(r'\s[\s]+', '', text).strip()


def get_extra_path(url):
    """get path on top of 'host' url"""
    if re.search(r'https?://(.*)/', url):
        try:
            return re.search(r'(https?://.*?)/(.*)', url).group(2) if re.search(r'(https?://.*?)/(.*)', url).group(2)[-1] != "/" else re.search(r'(https?://.*?)/(.*)', url).group(2)[:-1]

        except:
            return False


class Crawler(object):
  """crawl webpage for content and hrefs to other sites"""
  def __init__(self, schema, rel_ab_path, not_allow=False, print_search_url=False, max_depth=5):
    """initialize with variables other than iterable through Pool"""
    self.rel_ab_path = rel_ab_path
    self.not_allow = not_allow
    self.print_search_url = print_search_url
    self.schema = schema
    self.max_depth = max_depth

  def get_all_hrefs(self, soup, host_url, rel_ab_path):
    """scrape url for hrefs that do not lead to other sites"""
    list_of_hrefs = []
    for url in soup.find_all('a'):
        try:
            found_url = url['href']
            if len(found_url) != 0 and self.sanity_check(found_url):
                if host_url in found_url:
                    list_of_hrefs.append(found_url)

                elif not re.search(r'(https?://)', found_url):
                    if re.search(r'(//)', found_url):
                        list_of_hrefs.append('https:' + self.add_slash(found_url))

                    elif rel_ab_path and (host_url + self.add_slash(rel_ab_path) in host_url + self.add_slash(found_url)):
                        list_of_hrefs.append(host_url + self.add_slash(rel_ab_path))
                    
                    elif rel_ab_path:
                        list_of_hrefs.append(host_url + self.add_slash(rel_ab_path) + self.add_slash(found_url))
                    
                    else:
                        list_of_hrefs.append(host_url + self.add_slash(found_url)) 
        except:
            pass
    return list_of_hrefs
  
  def get_host_url(self, url):
    """get 'host' of whole url"""
    if re.search(r'https?://(.*)/', url):
        return re.search(r'(https?://.*?)/', url).group(1)
    else:
        return re.search(r'(https?://.*)', url).group(1)
    
  def scrape_all_text(self, soup):
    """get all visible text from url"""
    return soup.get_text(' ', strip=True)
  
  def replace_punctuations(self, text):
    """remove new lines, unbreakable spaces, multiple spaces or any non characters"""
    text = text.replace("\n", " ").replace("\xa0", " ").replace("-", " ").lower()
    text = re.sub(r'[^\w\s]+', '', text)
    return re.sub(r'\s[\s]+', '', text).strip()
  
  def add_slash(self, url):
    """url is only the part after host, thus may add slash to front if needed"""
    if url[0] == '/':
        return url
    else:
        return '/' + url
    
  def sanity_check(self, found_url):
    """check whether the url contains files or other not usable content"""
    if self.not_allow:
        for f in self.not_allow:
            if re.search(f'({f})', found_url, re.IGNORECASE):
                return False
    return (
            '#' not in  found_url
            and '..' not in found_url
            and not re.search(r'(.pdf)', found_url, re.IGNORECASE)
            and not re.search(r'(.doc)', found_url, re.IGNORECASE) 
            and not re.search(r'(.xml)', found_url, re.IGNORECASE)
            and not re.search(r'(.php)', found_url, re.IGNORECASE)
            and not re.search(r'(.ics)', found_url, re.IGNORECASE) # calendar
            and not re.search(r'(.jpg)', found_url, re.IGNORECASE)
            and not re.search(r'(.png)', found_url, re.IGNORECASE)
            and not re.search(r'(.gif)', found_url, re.IGNORECASE)
            and not re.search(r'(.mp3)', found_url, re.IGNORECASE)
            and not re.search(r'(type=)', found_url, re.IGNORECASE) # RSS feed
            and not re.search(r'(tel:)', found_url, re.IGNORECASE)
            and not re.search(r'(mailto:)', found_url, re.IGNORECASE)
            and not re.search(r'(javascript:)', found_url, re.IGNORECASE)
            )
  
  def safe_connection(self, search_url):
    """in case the connection is broken, timed out or other things happen"""
    tries = 1
    headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36'}
    while tries < 3:
        try:
            response = requests.get(search_url, headers=headers, timeout=3)
            if response.status_code != 200:
                raise TypeError
            return True, response
        except:
            time.sleep(tries)
            tries += 1
    return False, False
  
  def content_to_index(self, text, url):
    """write scraped content into index"""
    ix = index.open_dir("indexdir")
    writer = AsyncWriter(ix)
    writer.update_document(
                    url=url,
                    content=text
                    )
    writer.commit()

  def __call__(self, args):
    """apply all other functions by requesting page, looking through content and retrieving information"""
    search_url, depth = args
    
    if depth >= self.max_depth:
        return [], search_url # provides no more links, if max search depth exceeded
    else:
        code, response = self.safe_connection(search_url)
        if self.print_search_url:
            print(search_url)
        if not code:
            if self.print_search_url:
                print("no response huh?")
            return [], search_url
        
        host_url = self.get_host_url(search_url)
        soup = BeautifulSoup(response.content, "html.parser")
        text = self.scrape_all_text(soup)
        text = self.replace_punctuations(text)
        
        self.content_to_index(text, search_url)
        list_of_hrefs = self.get_all_hrefs(soup, host_url, self.rel_ab_path)
        return list_of_hrefs, search_url



def crawl(start_url, relative_absolute_path=False):
    # create index shema
    schema = Schema( 
                url=ID(unique=True, stored=True), 
                content=TEXT(stored=True)
                )
    
    # create dir for index everytime crawler is run to avoid double entries
    # maybe there is an update function that we could use ?
    
    if not os.path.exists("indexdir"):
        os.mkdir("indexdir")    
        ix = index.create_in("indexdir", schema)
    '''
    else:
        os.system("rm -rf indexdir")
        os.mkdir("indexdir")    
        ix = index.create_in("indexdir", schema)
    '''


    if relative_absolute_path:
        relative_absolute_path = get_extra_path(start_url)
    

    #start_url = url #"https://vm009.rz.uos.de/crawl"
    #relative_absolute_path = relative_absolute_path #'/crawl'

    #start_url = "https://www.uni-osnabrueck.de/startseite/"
    #start_url = "https://www.fh-kiel.de"
    #start_url = "https://www.cogscispace.de"
    #start_url = "https://www.uni-luebeck.de/universitaet/universitaet.html"
    #start_url = "https://en.wikipedia.org/wiki/Knowledge_space"
    #relative_absolute_path = rel_ab_path
    

    #not_allow = ["/en/"] # doesnt work for some reason
    not_allow = False
    print_search_url = True

    crawler_worker = 10
    search_depth = 5

    search_list = [start_url]
    already_visited = []
    doc_count = 0
    max_docs = 500

    itere = 1
    try:
        depth = 0
        while len(search_list) != 0:
            
            # using multiple threads for crawling the webpage
            doc_count += len(search_list)
            with Pool(crawler_worker) as p:
                call_args = list(zip(search_list, [depth]*len(search_list)))
                if doc_count > max_docs:
                    index_capacity = max(0, max_docs - (doc_count - len(search_list)))
                    print("Limited index_capacity: Only processing ", index_capacity)
                    aggregator = p.map(Crawler(schema, relative_absolute_path, not_allow, print_search_url, max_depth=search_depth), call_args[:index_capacity])
                else: 
                    aggregator = p.map(Crawler(schema, relative_absolute_path, not_allow, print_search_url, max_depth=search_depth), call_args)
            
            depth += 1
            
            # need to accumulate all the information from crawling 
            list_of_hrefs = [agg[0] for agg in aggregator]
            all_hrefs = [url for url_list in list_of_hrefs for url in url_list]
            already_visited = already_visited + [agg[1] for agg in aggregator]
            search_list =  list( set(all_hrefs) - set(already_visited))
            
            if print_search_url:
                print("iteration : ", itere)
                print('len(search_list) :' ,len(search_list))
                print('len(already_visited)' ,len(already_visited))
                print("\n")
            
            itere += 1
    
    # in case crawling takes to long ..
    except KeyboardInterrupt:
        exit
    
    if print_search_url:
        print(already_visited)
        print("\n")
        print(len(already_visited))



if __name__ == '__main__':
    # in case arguments have been passed
    args = sys.argv[1:]

    # default starting url    
    #url = "https://vm009.rz.uos.de/crawl"
    #url = "https://whoosh.readthedocs.io/en/latest/"
    # in case if search url needs extra path
    #relative_absolute_path = '/crawl'
    #start_url = "https://www.uni-osnabrueck.de/False/"

    #start_url = "https://www.wikipedia.org"

    url = "https://www.cogscispace.de"
    #url = "https://www.fh-kiel.de"
    relative_absolute_path = True

    # if args passed, use these instead
    if len(args) == 2 and args[0] == '-url':
        url = args[1]
        relative_absolute_path = False
    
    if len(args) == 4 and args[0] == '-url' and args[2] == '-path':
        url = args[1]
        relative_absolute_path = args[3]
    

    crawl(start_url=url, relative_absolute_path=relative_absolute_path)