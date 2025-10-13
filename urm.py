import subprocess, bs4

def download_10_images(twitter_media_url):
    gallery_dl_command = ["gallery-dl", "--range", "21-30", "-d", "./gallery-dl/", "--cookies-from-browser", "vivaldi"]
    gallery_dl_command.append(twitter_media_url)
    subprocess.run(gallery_dl_command)

def extract_result(html_source):
    b = bs4.BeautifulSoup(html_source, "html.parser")
    results = b.find_all("div", {"class": "result"})
    i = None
    for result in results:
        try:
            if result.attrs["id"] == "result-hidden-notification":
                i = results.index(result)
        except KeyError:
            continue
    
    try:
        while results[i]:
            results.pop(i)
    except IndexError:
        pass

    if results == []:
        return results

    for result in results:
            pass
    
def search_saucenao(image):
    
class SauceNaoResult():
    def __init__(self, raw: bs4.Tag):
        self.raw:        dict = raw
        self.similarity: float = float(self._get_similarity(raw))
        self.urls:       list[str] = self._get_urls(raw)

    def _get_similarity(self, raw: bs4.Tag) -> float:
        s = raw.find("div", {"class": "resultsimilarityinfo"})
        return s.text
    
    def _get_urls(self, raw: bs4.Tag) -> list:
        urls = []
        r = raw.find("div", {"class": "resultmiscinfo"})
        for u in r.find_all("a"):
            urls.append(u.attrs["href"])
        return urls