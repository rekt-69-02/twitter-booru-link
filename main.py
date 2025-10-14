import json, os, subprocess, bs4, pathlib, logging
import selenium, urllib.parse, time, datetime, requests
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
from selenium.common.exceptions import TimeoutException

options = Options()
options.add_argument("start-maximized")
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)
driver = webdriver.Chrome(service=Service(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install()), options=options)
avaliable_image_extensions = ["jpg", "jpeg", "png", "webp"]
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
            return None
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
            return None
    except NoSuchElementException:
        print(url)

def get_artist_url_yandere(url):
    driver.get(url=url)
    tag = driver.find_element(By.XPATH, "/html/body/div[8]/div[1]/div[3]/div[2]/ul/li[1]/a[2]")
    tag_color = tag.value_of_css_property("color")
    if tag_color == "rgba(204, 204, 0, 1)":
        return tag.get_attribute("href")
    else:
        return None

def search_saucenao_requests(image_path):
    url = "https://saucenao.com/search.php?hide=0"
    files = {"file": open(image_path, "rb")}
    resp = requests.post(url, files=files, headers=headers)
    return resp.text

def search_saucenao(image_path):
    try:
        driver.get("https://saucenao.com/")
        upload = driver.find_element(By.NAME, "file")
        driver.execute_script("arguments[0].style.display = 'block';", upload)
        upload.send_keys(image_path)
        driver.find_element(By.CSS_SELECTOR, "input[type='submit']").click()
        WebDriverWait(driver, 10).until(
            expected_conditions.presence_of_element_located((By.CLASS_NAME, "result"))
        )

        return driver.page_source
    except TimeoutException:
        with open(f"{datetime.datetime.now()}.html", "w+") as file:
            file.write(driver.page_source)

def download_10_images(twitter_media_url):
    gallery_dl_command = ["gallery-dl", "--range", "11-50", "-d", "./gallery-dl/", "--cookies-from-browser", "firefox", "--config", "./config.json"]
    gallery_dl_command.append(twitter_media_url)
    subprocess.run(gallery_dl_command)

def extract_result(html_source):
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
            
            if not (img.split(".")[-1] in avaliable_image_extensions):
                continue

            raw_html = search_saucenao_requests(file_path + img)
            results = extract_result(raw_html)            
            sauces = []
            for result in results:
                r = SauceNaoResult(result)
                if r.similarity < 70:
                    continue
                sauces.append(r)

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

            with open("output.json", "r") as file:
                j = json.load(file)
            with open("output.json", "a") as file2:
                j[following["screen_name"]] = o
                json.dump(j, file2)

if __name__ == "__main__":
    main()