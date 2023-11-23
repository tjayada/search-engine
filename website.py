from flask import Flask, render_template, request, redirect, url_for
from whoosh import index
from whoosh.qparser import QueryParser, OrGroup
from crawler import replace_punctuations
import subprocess
import sys

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

    return render_template("results.html", result_list=result_list)

@app.route('/reset_and_crawl', methods = ['POST', 'GET'])
def recrawl():
    '''recrawls given website and redirects to homeage'''
    try:
        # For Unix-like systems:
        venv_python = sys.prefix + '/bin/python'  # Assumes 'bin' for Unix-like systems, adjust for Windows
        # For Windows
        venv_python = sys.prefix + '\\Scripts\\python.exe'
        start_url = request.form['start_url']
        result = subprocess.run([venv_python, 'crawler.py', 'run', start_url], check=True, capture_output=True)
        print(result.stdout.decode('utf-8'))  # Print the standard output
    except subprocess.CalledProcessError as e:
        print(e.stderr.decode('utf-8'))  # Print the error output
        print("current venv: ", sys.prefix + '\\Scripts\\python.exe')
    return redirect(url_for('homepage'))
   
if __name__ == '__main__':
    app.run(debug = True)