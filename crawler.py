import re
import math
import requests
from bs4 import BeautifulSoup
from multiprocessing import Pool


def replace_punctuations(text):
    """remove new lines, unbreakable spaces, multiple spaces or any non characters"""
    text = text.replace("\n", " ").replace("\xa0", " ").replace("-", " ").lower()
    text = re.sub(r'[^\w\s]+', '', text)
    return re.sub(r'\s[\s]+', '', text).strip()


class Crawler(object):
  """crawl webpage for content and hrefs to other sites"""

  def __init__(self, index, visited_list, rel_ab_path):
    """initialize with variables other than iterable through Pool"""
    self.index = index
    self.visited_list = visited_list
    self.rel_ab_path = rel_ab_path

  def get_all_hrefs(self, soup, host_url):
    """scrape url for hrefs that do not lead to other sites"""
    list_of_hrefs = []
    for url in soup.find_all('a'):
        try:
            found_url = url['href']
            if len(found_url) != 0 and self.sanity_check(found_url):
                if host_url in found_url:
                    list_of_hrefs.append(found_url)

                elif not re.search(r'(https?://)', found_url):
                    list_of_hrefs.append(host_url + self.add_slash(found_url))   
        except:
            pass
    return list_of_hrefs
  
  def get_host_url(self, url, relative_path=False):
    """get 'host' of whole url"""
    if re.search(r'https?://(.*)/', url):
        return re.search(r'(https?://.*?)/', url).group(1) + (relative_path if relative_path else "")
    else:
        return re.search(r'(https?://.*)', url).group(1) + (relative_path if relative_path else "")
    
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
    return (not found_url[0] == '#' 
            and not re.search(r'(.pdf)', found_url, re.IGNORECASE)
            and not re.search(r'(.doc)', found_url, re.IGNORECASE) 
            and not re.search(r'(.xml)', found_url, re.IGNORECASE)
            and not re.search(r'(.ics)', found_url, re.IGNORECASE)
            and not re.search(r'(.jpg)', found_url, re.IGNORECASE)
            and not re.search(r'(.png)', found_url, re.IGNORECASE)
            and not re.search(r'(.mp3)', found_url, re.IGNORECASE)
            and not re.search(r'(tel:)', found_url, re.IGNORECASE)
            and not re.search(r'(mailto:)', found_url, re.IGNORECASE)
            )
  def safe_connection(self, search_url):
    """in case the connection is broken, timed out or other things happen"""
    tries = 1
    while tries < 3:
        try:
            response = requests.get(search_url)
            if response.status_code != 200:
                raise TypeError
            return response
        except:
            tries += 1
    return False
  
  def tf_into_index(self, text, url):
    """calculate term-frequency for each term in page content"""
    # split text into list
    list_of_terms = text.split()
    # get length of list --> sum_f_td
    sum_f_td = len(list_of_terms)  
    # create new list.copy as set then back to list --> get uniques
    unique_terms = list(set(list_of_terms))
    
    for term in unique_terms:
        if term in self.index:
            self.index[term] = self.index[term] + [(url, list_of_terms.count(term) / sum_f_td)]
        else:
            self.index[term] = [(url, list_of_terms.count(term) / sum_f_td)]

  def __call__(self, search_url):
    """apply all other functions by requesting page, looking through content and retrieving information"""

    # this function should never be called, eventually remove after enough testing
    if search_url in self.visited_list:
        print("why am i here ?")
        return [], self.index, self.visited_list, search_url

    response = self.safe_connection(search_url)
    if not response:
        print("no response huh?")
        self.visited_list.append(search_url)
        return [], self.index, self.visited_list, search_url
    
    host_url = self.get_host_url(search_url, self.rel_ab_path)
    soup = BeautifulSoup(response.content, "html.parser")
    print(search_url)
    text = self.scrape_all_text(soup)
    text = self.replace_punctuations(text)
    self.tf_into_index(text, search_url)

    list_of_hrefs = self.get_all_hrefs(soup, host_url)

    self.visited_list.append(search_url)

    return list_of_hrefs, self.index, self.visited_list, search_url



def calculate_tf_idf(term, index, scores):
    """when index queried calculate term-frequency inverse-document-frequency to determine best match"""
    if term not in index:
        return scores
    urls_and_tfs = index[term]
    
    l = len(list(index.values()))
    number_all_urls = len(set([list(index.values())[i][j][0] for i in range(l) for j in range(len(list(index.values())[i]))]))
    idf = math.log(number_all_urls / len(urls_and_tfs), 10)

    list_of_url_idfs = [(tf[0], tf[1]*idf) for tf in urls_and_tfs]

    for url, score in list_of_url_idfs:
        if url not in scores:
            scores[url] = score
        else:
            scores[url] = scores[url] + score
    
    return scores


def merge_dics(dic_1, dic_2):
    """merge two different dictionaries without information loss"""
    for key, value in dic_2.items():
        if key in dic_1:
            dic_1[key] = list(set(dic_1[key] + value))
        else:
            dic_1[key] = value
    return dic_1

if __name__ == '__main__':

    # benchmarks
    # without multi
    # 0.29s user 0.05s system 15% cpu 2.205 total
    # 1 pool --> 0.68s user 0.12s system 27% cpu 2.916 total
    # 1 pool --> 0.67s user 0.12s system 24% cpu 3.195 total
    # with multi, e.g > 4 pool
    # 2.27s user 0.46s system 164% cpu 1.659 total  
    # 2.29s user 0.43s system 155% cpu 1.752 total

    # to-do
    # make aggregation after multi faster (recursive, use multi to merge ?)
    # boolean to allow /en/ ?
    # boolean to allow switched to other webpages
    # some index to remember connection, to draw graph of connections in the end (overkill but would be cool)
    # use 'auto-complete' by looking wheter term in query is in index (overkill but would be cool)

    start_url = "https://vm009.rz.uos.de/crawl"
    relative_absolute_path = '/crawl'
    
    #start_url = "https://www.uni-osnabrueck.de/startseite/"
    #start_url = "https://www.fh-kiel.de"
    #relative_absolute_path = False

    search_list = [start_url]
    index = {}
    already_visisted = []

    itere = 1
    try:
        while len(search_list) != 0:
            
            print("iteration : ", itere)
            
            """ idea is to use smaller chunks of search_list to not spend too much time in aggregation loop aftwerwards or make aggregation faster
            if len(search_list) > 200:
                old_search_list = search_list.copy()
                search_list = old_search_list[:200]
            """
            with Pool(5) as p:
                aggregator = []
                aggregator = p.map(Crawler(index, already_visisted, relative_absolute_path), search_list)

            for agg in aggregator:

                x = (set(search_list) | set(agg[0]))
                y = (set(agg[2]) | set(already_visisted))
                    
                search_list = list(x - y)
                index = merge_dics(index, agg[1])
                already_visisted += agg[2]

            search_list = list(set(search_list))
            already_visisted = list(set(already_visisted))

            print('len(search_list) :' ,len(search_list))
            print('len(already_visisted)' ,len(already_visisted))
            print("\n")

            itere += 1
    
    except KeyboardInterrupt:
        pass
    
    print(already_visisted)
    print("\n")
    print(len(already_visisted))
    
    while 1:
        scores = {}
        print("\n \n")
        print("please query me :")
        user = input()

        clean_query = replace_punctuations(user).split()

        for term in clean_query:
            scores = calculate_tf_idf(term, index, scores)
    
        print(scores)
    