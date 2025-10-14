import requests, bs4

headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"}

def search_saucenao(image_path):
    url = "https://saucenao.com/search.php?hide=0"
    files = {"file": open(image_path, "rb")}
    resp = requests.post(url, files=files, headers=headers)
    return resp.text

def extract_saucenao_result(html_source):
    b = bs4.BeautifulSoup(html_source, "html.parser")
    results = b.find_all("div", {"class": "result"})
    results = [r for r in results if r.get("id") != "result-hidden-notification"]
    return results

class SauceNaoResult():
    def __init__(self, raw):
        self.raw = raw
        self.similarity = self._get_similarity()
        self.urls = self._get_urls()

    def _get_similarity(self) -> float:
        s = self.raw.find("div", {"class": "resultsimilarityinfo"})
        if not s:
            return 0.0
        s = s.text.replace("%", "").strip()
        try:
            return float(s)
        except ValueError:
            return 0.0

    def _get_urls(self) -> list[str]:
        urls = []
        miscinfo = self.raw.find("div", {"class": "resultmiscinfo"})
        if not miscinfo:
            return urls
        for a in miscinfo.find_all("a", href=True):
            urls.append(a["href"])
        return urls