import re
import math
import requests
from bs4 import BeautifulSoup
from multiprocessing import Pool

def hy(iterable):
    print(iterable)
    return iterable + 1

if __name__ == '__main__':
    
    search_list = [1,2,3]
    with Pool(3) as p:
        search_list = p.map(hy, search_list)
