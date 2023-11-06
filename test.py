import whoosh
import os, os.path
from whoosh import index
from whoosh.fields import Schema, TEXT, KEYWORD, ID, STORED


def save_data():
    if not os.path.exists("indexdir"):
        os.mkdir("indexdir")
    
    schema = Schema(title=TEXT(stored=True), path=ID(stored=True), content=TEXT)
    ix = index.create_in("indexdir", schema)

    writer = ix.writer()
    writer.add_document(title=u"First document", path=u"/a",
                     content=u"This is the first document we've added!")
    
    writer.commit()


if __name__ == "__main__":
    save_data()