from flask import Flask, render_template, request
from whoosh import index
from whoosh.qparser import QueryParser, OrGroup
from crawler import replace_punctuations

app = Flask(__name__)

@app.route("/")
def hello_world():
    return render_template("start.html")


@app.route('/show_results', methods = ['POST', 'GET']) 
def setcookie(): 
    q = request.form['query']
    clean_q = replace_punctuations(q)

    
    ix = index.open_dir("indexdir")
    with ix.searcher() as searcher:
        query = QueryParser("content", ix.schema, group=OrGroup.factory(0.9)).parse(clean_q)
        results = searcher.search(query, limit=None)

        print("hits: ", len(results))


        final_string =  """
                        <form action = "/show_results" method = "POST"> 
                            <p><input type = 'text' name = 'query' placeholder="whatcha lookin for ?"/></p> 
                            <p><input type = 'submit' value = 'start crawlin'/></p> 
                        </form>
                        <br><br><br><br><br><br><br>
                        """
        
        #final_string = "<br><br><br><br><br><br><br>"
        for hit in results:
            print(hit["url"], hit.score)
            final_string += " " + f"{hit['url']}" + "<br>"
    
    return final_string

        
    
    

if __name__ == '__main__':
    app.run(debug = True)