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

  def __init__(self,rel_ab_path, not_allow=False, print_search_url=False):
    """initialize with variables other than iterable through Pool"""
    self.index = {}
    self.rel_ab_path = rel_ab_path
    self.not_allow = not_allow
    self.print_search_url = print_search_url

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
    if self.not_allow:
        for f in self.not_allow:
            if re.search(f'({f})', found_url, re.IGNORECASE):
                return False
        
    return (not found_url[0] == '#' 
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

    response = self.safe_connection(search_url)
    if self.print_search_url:
        print(search_url)
    if not response:
        print("no response huh?")
        return [], self.index, search_url
    
    host_url = self.get_host_url(search_url, self.rel_ab_path)
    soup = BeautifulSoup(response.content, "html.parser")
    text = self.scrape_all_text(soup)
    text = self.replace_punctuations(text)
    self.tf_into_index(text, search_url)

    list_of_hrefs = self.get_all_hrefs(soup, host_url)

    return list_of_hrefs, self.index, search_url



def calculate_tf_idf(term, index, scores, number_of_all_urls=False):
    """when index queried calculate term-frequency inverse-document-frequency to determine best match"""
    if term not in index:
        return scores
    urls_and_tfs = index[term]
    
    l = len(list(index.values()))
    if not number_of_all_urls:
        number_of_all_urls = len(set([list(index.values())[i][j][0] for i in range(l) for j in range(len(list(index.values())[i]))]))
    idf = math.log(number_of_all_urls / len(urls_and_tfs), 10)

    list_of_url_idfs = [(tf[0], tf[1]*idf) for tf in urls_and_tfs]

    for url, score in list_of_url_idfs:
        if url not in scores:
            scores[url] = score
        else:
            scores[url] = scores[url] + score
    
    return scores


def merge_dics(dic_1, dic_2=False):
    """merge two different dictionaries without information loss"""
    if not dic_2:
        dic_1, dic_2 = dic_1

    for key, value in dic_2.items():
        if key in dic_1:
            dic_1[key] = list(set(dic_1[key] + value))
        else:
            dic_1[key] = value

    return dic_1


def get_url_ordered(urls_with_scores):
    """return list of urls by scores descending"""
    sorted_scores = sorted(urls_with_scores.values(), reverse=True)
    
    sorted_urls = []
    
    for score in sorted_scores:
        for k, v in urls_with_scores.items():
            if score == v and k not in sorted_urls:
                sorted_urls.append(k)
                break
    return sorted_urls, sorted_scores


def pair_iterable(iterable):
    """
    pair iterable into two's
    inpired by 
    https://stackoverflow.com/questions/312443/how-do-i-split-a-list-into-equally-sized-chunks/74120449#74120449
    """
    args = [iter(iterable)] * 2
    return zip(*args)


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
    # disallow # in url ? or for two urls for same key to have some tf ?
    # e.g
    #https://www.uni-luebeck.de/forschung/verbundforschung/bmbf-netzwerke.html#TNM5             0.0017153155656649559
    #https://www.uni-luebeck.de/forschung/verbundforschung/bmbf-netzwerke.html#TNM3             0.0017153155656649559
    #https://www.uni-luebeck.de/forschung/verbundforschung/bmbf-netzwerke.html#TNM6             0.0017153155656649559
    #https://www.uni-luebeck.de/forschung/verbundforschung/bmbf-netzwerke.html             0.0017153155656649559
    #https://www.uni-luebeck.de/forschung/verbundforschung/bmbf-netzwerke.html?draft=1             0.0017153155656649559
    #https://www.uni-luebeck.de/forschung/verbundforschung/bmbf-netzwerke.html#TNM2             0.0017153155656649559
    #https://www.uni-luebeck.de/forschung/verbundforschung/bmbf-netzwerke.html#TNM1             0.0017153155656649559
    # or disallow ?id= or ?draft=
    # e.g.
    # https://www.uni-luebeck.de/studium/studiengaenge/biophysik.html             0.000923188310320098
    # https://www.uni-luebeck.de/studium/studiengaenge/biophysik.html?draft=1             0.000923188310320098
    # https://www.uni-luebeck.de/studium/studiengaenge/molecular-life-science.html             0.000772675528876484
    # https://www.uni-luebeck.de/studium/studiengaenge/molecular-life-science.html?draft=1             0.000772675528876484
    # boolean to allow /en/ ?
    # if no result, try again later ? 
    # boolean to allow switched to other webpages
    # some index to remember connection, to draw graph of connections in the end (overkill but would be cool)
    # use 'auto-complete' by looking wheter term in query is in index (overkill but would be cool)

    start_url = "https://vm009.rz.uos.de/crawl"
    relative_absolute_path = '/crawl'
    
    #start_url = "https://www.uni-osnabrueck.de/startseite/"
    #start_url = "https://www.fh-kiel.de"
    #start_url = "https://www.cogscispace.de"
    #start_url = "https://www.uni-luebeck.de/universitaet/universitaet.html"
    #relative_absolute_path = False

    not_allow = ["/en/"] # doesnt work for some reason
    #not_allow = False
    stop_after_crawl = False
    print_search_url = True

    crawler_worker = 4
    merge_worker = 4

    search_list = [start_url]
    index = {}
    already_visisted = []

    itere = 1
    try:
        while len(search_list) != 0:
            
            print("iteration : ", itere)

            # using multiple threads for crawling the webpage
            with Pool(crawler_worker) as p:
                aggregator = p.map(Crawler(relative_absolute_path, not_allow, print_search_url), search_list)
            
            # need to accumulate all the information from crawling 
            list_of_hrefs = [agg[0] for agg in aggregator]
            all_hrefs = [url for url_list in list_of_hrefs for url in url_list]
            already_visisted = already_visisted + [agg[2] for agg in aggregator]
            search_list =  list( set(all_hrefs) - set(already_visisted))
            list_of_indeces = [agg[1] for agg in aggregator]

            # if odd number of indeces returned, we make even by removing last one
            if len(list_of_indeces) % 2 != 0 and len(list_of_indeces) > 1:
                odd_one_out = list_of_indeces[-1]
                list_of_indeces = list_of_indeces[:-1]
                index = merge_dics(index, odd_one_out)
            
            # merge all indices together using mix of multiple threads and divide-and-conquer
            while len(list_of_indeces) > 1:
                pairs_of_indeces = pair_iterable(list_of_indeces)

                with Pool(merge_worker) as p:
                    list_of_indeces = p.map(merge_dics, pairs_of_indeces)
            
            # circumvent special case when crawling resulted in no content being found
            if list_of_indeces[0] != {}:
                index = merge_dics(index, list_of_indeces[0])
            
            print('len(search_list) :' ,len(search_list))
            print('len(already_visisted)' ,len(already_visisted))
            print("\n")
            
            itere += 1
    
    # in case crawling takes to long ..
    except KeyboardInterrupt:
        pass
    
    print(already_visisted)
    print("\n")
    print(len(already_visisted))
    number_of_all_urls = len(already_visisted)
    
    # used mainly for benchmarks, usually you'd like to query as well
    if stop_after_crawl:
        exit()

    # kinda stupid method to allow for unlimited user queries
    while 1:
        scores = {}
        print("\n \n")
        print("please query me :")
        user = input()
        # clean up query (also makes it easier to match with index)
        clean_query = replace_punctuations(user).split()
        # calculate matches for each term
        for term in clean_query:
            scores = calculate_tf_idf(term, index, scores, number_of_all_urls)
        # find website with highest match (order dic desc)
        urls, scores = get_url_ordered(scores)

        for u, s in zip(urls, scores):      
            print(u, "           ", s)    