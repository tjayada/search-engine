import whoosh
import os, os.path
from whoosh import index
from whoosh.fields import Schema, TEXT, KEYWORD, ID, STORED
from whoosh.qparser import QueryParser
from whoosh.index import open_dir



def save_data(schema):
    
    if not os.path.exists("indexdir"):
        os.mkdir("indexdir")    
    
    ix = index.create_in("indexdir", schema)
    
    writer = ix.writer()
    writer.add_document(title=u"First document", 
                        path=u"/a",
                        content=u"This is the first added document we've added !")
    
    writer.add_document(title=u"second document", 
                        path=u"/b",
                        content=u"This is platypus sun moon water earth unicorn another one we added , yeah yippieh yeah !")
    
    '''
    writer.add_document(title=u"third document", 
                        path=u"/b",
                        content=u"hm yes this seems to be completely useless utterly dumb information")
    '''

    writer.commit()

    


if __name__ == "__main__":

    schema = Schema(title=TEXT(stored=True), 
                path=ID(stored=True), 
                #content=TEXT(phrase=False)
                #content=KEYWORD
                content=TEXT(stored=True)
                )
        
    save_data(schema)

    ix = open_dir("indexdir")
    
    from whoosh import scoring

    # weighting=scoring.TF_IDF()
    with ix.searcher(weighting=scoring.TF_IDF) as searcher:
        query = QueryParser("content", ix.schema).parse(u"added")
        results = searcher.search(query)
        
        scr = searcher.idf("content", u"added")
        print(scr)

        print(searcher.get_parent().doc_frequency("content", u"added platypus"))
        #s = searcher.avg_field_length("content")
        #print(s)

       # print(results[0])
        for i in results:
            print(i)
        #print(results)
        print(results[0].score)
        print(results[1].score)
        
        #s = searcher.document(path="/a")
        #print(s)
        #print(results[0].fields)
    
    
    #print(ix)