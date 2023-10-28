import re
import math
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

def replace_punctuations(text):
    text = text.replace("\n", " ").replace("\xa0", " ").replace("-", " ").lower()
    #text = re.sub(r'\s[\s]+', '', text)
    text = re.sub(r'[^\w\s]+', '', text)
    return re.sub(r'\s[\s]+', '', text).strip()


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
    
'''
class Crawler(object):
  """crawl webpage for content and hrefs to other sites"""

  def __init__(self, visited_list):
    """Initialize the class with 'global' variables"""
    #self.url = 
    #self.rel_ab_path = rel_ab_path
    self.visited_list = visited_list

  def __call__(self, search_url, rel_ab_path):
    """look through page content and retrieve information"""
    #print(search_url)
    # get page content
    if search_url in self.visited_list:
        return [], []
    
    response = requests.get(search_url)
    host_url = get_host_url(search_url, rel_ab_path)
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
    
    self.visited_list.append(search_url)
    return list_of_lists, self.visited_list
'''


class Crawler(object):
  """crawl webpage for content and hrefs to other sites"""

  def __init__(self, index, visited_list, rel_ab_path):
    """Initialize the class with 'global' variables"""
    #self.url = 
    #self.rel_ab_path = rel_ab_path
    self.index = index
    self.visited_list = visited_list
    self.rel_ab_path = rel_ab_path

  
  def get_all_hrefs(self, soup, host_url):
    list_of_hrefs = []

    # find hrefs in page content
    for url in soup.find_all('a'):
        try:
            found_url = url['href']
        except:
            return []
        if host_url in found_url:
            list_of_hrefs.append(found_url)

        elif not re.search(r'(https?://)', found_url) and not found_url[0] == '#':
            list_of_hrefs.append(host_url + add_slash(found_url))

    return list_of_hrefs
  
  def scrape_all_text(self, soup):
    '''
    text_concat = ""
    for texts in soup.find_all('p'):
        text_concat += " " + texts.text
    '''
    return soup.get_text(' ', strip=True)
  
  def replace_punctuations(self, text):
    text = text.replace("\n", " ").replace("\xa0", " ").replace("-", " ").lower()
    #text = re.sub(r'\s[\s]+', '', text)
    text = re.sub(r'[^\w\s]+', '', text)
    return re.sub(r'\s[\s]+', '', text).strip()
  
  def tf_into_index(self, text, url):
    
    # split text into list
    list_of_terms = text.split()
    # get length of list --> sum_f_td
    sum_f_td = len(list_of_terms)  
    # create new list.copy as set then back to list --> get uniques
    unique_terms = list(set(list_of_terms))
    # go through set_list and calculate frequency / sum_f_td while updating index
    for term in unique_terms:
        if term in self.index:
            #list_of_existing_values = index[term]
            self.index[term] = self.index[term] + [(url, list_of_terms.count(term) / sum_f_td)]
        else:
            self.index[term] = [(url, list_of_terms.count(term) / sum_f_td)]
    #return self.index

  def __call__(self, search_url):
    """look through page content and retrieve information"""
    #print(search_url)
    # get page content
    if search_url in self.visited_list:
        return [], self.index, [], search_url
    
    response = requests.get(search_url)
    host_url = get_host_url(search_url, self.rel_ab_path)
    soup = BeautifulSoup(response.content, "html.parser")

    text = self.scrape_all_text(soup)
    text = self.replace_punctuations(text)
    self.tf_into_index(text, search_url)

    list_of_hrefs = self.get_all_hrefs(soup, host_url)

    self.visited_list.append(search_url)

    return list_of_hrefs, self.index, self.visited_list, search_url
  
def calculate_tf_idf(term, index, scores):
    
    # dic["term"] --> get list of urls with tf
    if term not in index:
        return scores
    urls_and_tfs = index[term]
    
    #print(term)
    #print(urls_and_tfs)
    
    # calculate log (number_of_all_urls / ( len(dic["term"]))) as idf
    l = len(list(index.values()))
    number_all_urls = len(set([list(index.values())[i][j][0] for i in range(l) for j in range(len(list(index.values())[i]))]))
    idf = math.log(number_all_urls / len(urls_and_tfs), 10)
    #print(idf)
    # then calculate tf_idf for each dic["term"] tf 
    list_of_url_idfs = [(tf[0], tf[1]*idf) for tf in urls_and_tfs]
    
    # update scores for urls
    #print(term)
    #print(list_of_url_idfs)
    
    for url, score in list_of_url_idfs:
        if url not in scores:
            scores[url] = score
        else:
            scores[url] = scores[url] + score
    
    return scores


def merge_dics(dic_1, dic_2):
    #print(dic_1)
    print("\n")
    #print(dic_2)
    for key, value in dic_2.items():
    
        if key in dic_1:
            dic_1[key] = list(set(dic_1[key] + value))
        else:
            dic_1[key] = value
    return dic_1

if __name__ == '__main__':
    # if not limited by libraries, we would be using nltk in the Crawler class to filter words out
    # unacceptable = ["the", "in", "or", "and", "to"]

    #start_url = "https://vm009.rz.uos.de/crawl"
    #relative_absolute_path = '/crawl'
    start_url = "https://www.uni-osnabrueck.de/startseite/"
    relative_absolute_path = False
    search_list = [start_url]

    index = {}
    already_visisted = []

    itere = 1
    while len(search_list) != 0:
        
        print(itere)
        
        #print(search_list)
        for url in search_list:
            #print(search_list)

            # if not visited recently:
            #search_list, already_visisted += crawl(url, relative_absolute_path)
            print(len(index))
            print(len(search_list))
            crawly = Crawler(index, already_visisted, relative_absolute_path)
            aggregator = crawly(url)
            
            search_list = list((set(search_list) and set(aggregator[0])) - set(already_visisted))
            
            index = merge_dics(index, aggregator[1])
            already_visisted += aggregator[2]
            
            #print(index)

            #exit()

            search_list = list(set(search_list))
            print(len(search_list))
            already_visisted = list(set(already_visisted))

            search_list.remove(url) if url in search_list else search_list

        itere += 1
    print(already_visisted)
    
    while 1:
        scores = {}
        print("\n \n")
        print("please query me :")
        user = input()

        clean_query = replace_punctuations(user).split()

        for term in clean_query:
            scores = calculate_tf_idf(term, index, scores)
    
        print(scores)

    """
        with Pool(5) as p:
            aggregator = p.map(Crawler(index, already_visisted, relative_absolute_path), search_list)[0]
            print(aggregator[0])
            print(search_list)
            search_list += aggregator[0]
            index = merge_dics(index, aggregator[1])
            already_visisted += aggregator[2]
            url = aggregator[3]

            search_list = list(set(search_list))
            already_visisted = list(set(already_visisted))

            search_list.remove(url) if url in search_list else search_list

        itere += 1
    
    print(already_visisted)
     8.45s user 1.54s system 204% cpu 4.892 total
    while 1:
        scores = {}
        print("\n \n")
        print("please query me :")
        user = input()

        clean_query = replace_punctuations(user).split()

        for term in clean_query:
            scores = calculate_tf_idf(term, index, scores)
    
        print(scores)
    """