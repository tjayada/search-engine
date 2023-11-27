import subprocess
import os

if __name__ == '__main__':

    with open("search_urls.txt", "r") as file:
        urls = file.readlines()
    
    python_version = os.popen("which python").read().replace("\n", "")

    for data in urls:
        url, path = data.split(",")

        subprocess.run([python_version, "crawler.py", "-url", url, "-path", path])