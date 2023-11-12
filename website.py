from flask import Flask, render_template, request
from whoosh import index
from whoosh.qparser import QueryParser, OrGroup
from crawler import replace_punctuations

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
   
if __name__ == '__main__':
    app.run(debug = True)