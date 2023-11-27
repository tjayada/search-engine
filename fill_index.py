import subprocess
import os

if __name__ == '__main__':

    # get all urls specified in search_urls.txt
    with open("search_urls.txt", "r") as file:
        urls = file.readlines()
    
    # get python version currently in use to later spawn subprocess with
    python_version = os.popen("which python").read().replace("\n", "")

    # loop over all search urls and call crawler.py for them
    for data in urls:
        url, path = data.split(",")
        subprocess.run([python_version, "crawler.py", "-url", url, "-path", path])