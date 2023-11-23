# simple search engine

## run crawler.py to fill index 
## (python crawler.py run optional_url_string)
you may change arguments in main, such as the url, printing results, amount of threads etc.

## run website.py to start server 
## (flask --app website.py run)
starts Flask with hompage taking user input to query index


# to-do
1. add css to make site fancy, e.g spider theme since we are *crawling* the *web* or something similarily stupid and fun, or make it look professional idk
2. add functions to site, eg. display (dump) all index entries, take user input url to crawl that etc. sky is the limit 
3. make scraping better: function scrape\_all\_text in crawler class currently takes ALL visible content, maybe reduce to only paragraphs or something like that
4. make index able to update: currently if same page gets crawled, 2 separate index entries would be created, current solution is to delete old index in main before crawling
5. fix crawlers KeyboadrInterrupt: does not work for pool of crawlers 
6. OS specifics: automatically recognice OS in recrawl() in website.py
