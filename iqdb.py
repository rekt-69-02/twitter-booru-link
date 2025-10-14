import requests

headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"}

def search_iqdb(image_path):
    url = "https://iqdb.org/"
    files = {"file": open(image_path, "rb")}
    resp = requests.post(url, files=files, headers=headers)
    return resp.text

def extract_iqdb_result(html_source):
    pass