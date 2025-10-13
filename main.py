import json, os, subprocess, bs4, pathlib
import selenium, urllib.parse, time
from selenium import webdriver
from selenium_stealth import stealth
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

options = Options()
options.add_argument("start-maximized")
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)
driver = webdriver.Chrome(service=Service(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install()), options=options)
valiable_image_extensions = ["jpg", "jpeg", "png", "webp"]
headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"}

stealth(driver=driver,
        languages=["en-US", "en"],
        vendor="Google Inc.",
        platform="Win32",
        webgl_vendor="Intel Inc.",
        renderer="Intel Iris OpenGL Engine",
        fix_hairline=True,)

def get_artist_url_danbooru(url):
    driver.get(url=url)
    # WebDriverWait(driver=driver, timeout=10).until(expected_conditions.visibility_of_element_located((By.XPATH, "/html/body/header/div/div/a[2]")))
    try:
        artist_label = driver.find_element(By.XPATH, "/html/body/div[1]/div[2]/div/div/aside/section[2]/div/h3[1]")
        if artist_label.text == "Artist":
            e = driver.find_element(By.XPATH, "/html/body/div[1]/div[2]/div/div/aside/section[2]/div/ul[1]/li/span[2]/a")
            href = e.get_attribute("href")
            return href
        else:
            return "None"
    except NoSuchElementException:
        pass
    
def get_artist_url_gelbooru(url):
    driver.get(url=url)
    try:
        artist_label = driver.find_element(By.XPATH, "/html/body/div[1]/section/ul/span[1]/li/b")
        if artist_label.text == "Artist":
            e = driver.find_element(By.XPATH, "/html/body/div[1]/section/ul/li[1]/a")
            href = e.get_attribute("href")
            return href
        else:
            return "None"
    except NoSuchElementException:
        print(url)

def get_artist_url_yandere(url):
    driver.get(url=url)
    tag = driver.find_element(By.XPATH, "/html/body/div[8]/div[1]/div[3]/div[2]/ul/li[1]/a[2]")
    tag_color = tag.value_of_css_property("color")
    if tag_color == "rgba(204, 204, 0, 1)":
        return tag.get_attribute("href")
    else:
        return "None"

def search_saucenao(username, image):
    driver.get("https://saucenao.com/")
    upload = driver.find_element(By.NAME, "file")
    upload.send_keys(f"{pathlib.Path().resolve()}/gallery-dl/twitter/{username}/{image}")
    driver.find_element(By.CSS_SELECTOR, "input[type='submit']").click()

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

def main():
    twitter_followings_json_file = input("please input file path:")
    twitter_followings = [x for x in json.load(open(twitter_followings_json_file, 'r', encoding="utf8"))]

    for following in twitter_followings:
        download_10_images(twitter_media_url=following["url"] + "/media/")
        file_path = f"{pathlib.Path().resolve()}/gallery-dl/twitter/{following["screen_name"]}/"

        o = {
                "twitter_url": following["url"]
            }
        
        for img in os.listdir(file_path):
            search_saucenao(username=following["screen_name"], image=img)
            raw_html = driver.page_source
            results = extract_result(raw_html)            
            sauces = []
            for result in results:
                sauces.append(SauceNaoResult(result))

            if o.get("danbooru_url") and o.get("gelbooru_url") and o.get("yandere_url"):
                break

            for sauce in sauces:
                for url in sauce.urls:
                    if "danbooru.donmai.us" in url and not o.get("danbooru_url"):
                        o["danbooru_url"] = get_artist_url_danbooru(url)
                    
                    if "gelbooru.com" in url and not o.get("gelbooru_url"):
                        o["gelbooru_url"] = get_artist_url_gelbooru(url)

                    if "yande.re" in url and not o.get("yandere_url"):
                        o["yandere_url"] = get_artist_url_yandere(url)

            with open("output.json", "w+") as file:
                j = json.load(file)
                j[following["screen_name"]] = o
                json.dump(j, file)

if __name__ == "__main__":
    main()