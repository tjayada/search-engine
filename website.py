from flask import Flask, render_template, request, redirect, url_for
from whoosh import index, highlight
from whoosh.qparser import QueryParser, OrGroup
from crawler import replace_punctuations, crawl
import requests
import math
import os
import subprocess

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


import traceback
@app.errorhandler(500)
def internal_error(exception):
   return "<pre>"+traceback.format_exc()+"</pre>"


@app.route('/show_results', methods = ['POST', 'GET']) 
def search():
    """display new searchbar and search results from previous search"""
    # number of results per page
    results_per_page = 5

    # get user input
    q = request.form['query']
    
    #choice = request.form['choice'] if request.form['choice'] == "" else int(request.form['choice'])

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

    '''
    if choice != "":
        if p + choice < 0:
            p = 0
        elif p + choice > pages:
            p = pages     
        else:
            p = p + choice
    '''

    if p <= 0:
        p = 1
    elif p >= pages:
        p = pages
    else:
        p = p

    result_list = result_list[(p - 1) * results_per_page : (p) * results_per_page]

    return render_template("results.html", result_list=result_list, user_query=q, page_number=p)



@app.route('/reset_and_crawl', methods = ['POST', 'GET'])
def recrawl():
    '''recrawls given website and redirects to homepage'''
    
    url = request.form['start_url']
    
    # check user input 
    print(url)

    if url == "":
        url = "https://www.cogscispace.de"
        
    if not check_url(url):
        print("bad url")
        return redirect(url_for('homepage'))
    

    python_version = os.popen("which python").read().replace("\n", "")

    
        #crawl("https://www.cogscispace.de", relative_absolute_path=False)
    
    #crawl(url, relative_absolute_path=True)
    print(os.path.abspath(os.getcwd()))
    subprocess.run([python_version, "crawler.py", "-url", url, "-path", "True"])
    return redirect(url_for('homepage'))
   
if __name__ == '__main__':
    app.run(debug = True)