from flask import Flask, render_template, request, redirect, url_for
from whoosh import index
from whoosh.qparser import QueryParser, OrGroup
from crawler import replace_punctuations
import requests
import math
import os
import subprocess
import random

def check_url(search_url):
    """check user input url"""

    headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36'} 
    try:
        response = requests.get(search_url, headers=headers)
        if response.status_code != 200:
            return False
    except:
        return False
    
    return True

app = Flask(__name__)

@app.route("/")
def homepage():
    """landing page taking user input"""
    return render_template("start.html")


@app.route('/show_results', methods = ['POST', 'GET']) 
def search():
    """display new searchbar and search results from previous search"""
    # number of results per page
    results_per_page = 5

    # show spider in different colors ?
    random_spider = False

    # get user input
    q = request.form['query']
    
    # get the requested page number
    p = int(request.form['page'])

    # clean up input for easier parsing
    clean_q = replace_punctuations(q)

    ix = index.open_dir("indexdir")
    with ix.searcher() as searcher:
        query = QueryParser("content", ix.schema, group=OrGroup.factory(0.9)).parse(clean_q)
        results = searcher.search(query, limit=None)

        result_list = []
        for hit in results:
            result_list.append([hit["url"], hit.score, hit.highlights("content")])

    if len(result_list) == 0:
        return redirect(url_for('homepage'))
    
    pages = math.ceil(len(result_list)/results_per_page)
 
    # check if the requested page number is between boundaries
    if p <= 0:
        p = 1
    elif p >= pages:
        p = pages
    else:
        p = p

    # get the results based on the page number and number of results displayed per page
    result_list = result_list[(p - 1) * results_per_page : (p) * results_per_page]

    # either choose 'logo' randomly or not
    spider = "/static/spooder.png"
    if random_spider:
        spider = f"/static/spooder_{random.randint(1, 3)}.png"
    
    return render_template("results.html", result_list=result_list, user_query=q, page_number=p, spider=spider)


@app.route('/reset_and_crawl', methods = ['POST', 'GET'])
def recrawl():
    '''recrawls given website and redirects to homepage'''
    # if True, then the webpage takes user input to crawl a given url, else kinda 404 it
    allow_crawl = False

    if not allow_crawl:
        return redirect(url_for('sorry'))
    
    # get url given by user
    url = request.form['start_url']
    
    # check user input 
    if url == "":
        url = "https://www.cogscispace.de"
    
    # check user input 
    if not check_url(url):
        print("bad url")
        return redirect(url_for('homepage'))
    
    # get python version in case crawling is allowed
    python_version = os.popen("which python").read().replace("\n", "")

    # call crawler with user given url
    subprocess.call([python_version, "crawler.py", "-url", url, "-path", "True"])

    return redirect(url_for('homepage'))
    
@app.route("/sorry")
def sorry():
    """in case the crawling function is not allowed"""
    return render_template("sorry.html")

if __name__ == '__main__':
    app.run()