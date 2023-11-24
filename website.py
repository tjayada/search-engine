from flask import Flask, render_template, request, redirect, url_for
from whoosh import index
from whoosh.qparser import QueryParser, OrGroup
from crawler import replace_punctuations, crawl
import requests

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
    # get user input
    q = request.form['query']
    
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
    
    return render_template("results.html", result_list=result_list)

@app.route('/reset_and_crawl', methods = ['POST', 'GET'])
def recrawl():
    '''recrawls given website and redirects to homepage'''
    
    url = request.form['start_url']
    
    # check user input 
    print(url)

    if url == "":
        crawl("https://www.cogscispace.de")
        return redirect(url_for('homepage'))

    if not check_url(url):
        print("bad url")
        return redirect(url_for('homepage'))
    
    crawl(url)
    return redirect(url_for('homepage'))
   
if __name__ == '__main__':
    app.run(debug = True)