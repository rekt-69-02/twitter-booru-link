import json, os, subprocess, bs4, pathlib, requests, random, time
from selenium import webdriver
from selenium_stealth import stealth
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from saucenao import search_saucenao, extract_saucenao_result, SauceNaoResult
from iqdb import search_iqdb, extract_iqdb_result

options = Options()
options.add_argument("--window-size=2560,1440")
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
    try:
        artist_label = driver.find_element(By.XPATH, "/html/body/div[1]/div[2]/div/div/aside/section[2]/div/h3[1]")
        if artist_label.text == "Artist":
            e = driver.find_element(By.XPATH, "/html/body/div[1]/div[2]/div/div/aside/section[2]/div/ul[1]/li/span[2]/a")
            href = e.get_attribute("href")
            return href
        else:
            print(f"get danbooru url failed: {url}")
            return None
    except NoSuchElementException:
        print(f"get danbooru url failed: {url}")
    
def get_artist_url_gelbooru(url):
    driver.get(url=url)
    try:                                             #/html/body/div[1]/section/ul/span[1]/li/b
        artist_label = driver.find_element(By.XPATH, "/html/body/div[1]/section/ul/span[1]/li/b")
        if artist_label.text == "Artist":#    "/html/body/div[1]/section/ul/li[1]/a"
            e = driver.find_element(By.XPATH, "/html/body/div[1]/section/ul/li[1]/a")
            href = e.get_attribute("href")
            return href
        else:
            print(f"get gelbooru url failed: {url}")
            return None
    except NoSuchElementException:
        print(f"error: get gelbooru url failed: {url}")

def get_artist_url_yandere(url):
    driver.get(url=url)
    try:
        tag_artist = driver.find_element(By.XPATH, "/html/body/div[8]/div[1]/div[4]/div[2]/ul/li[1]")
        a_tag = tag_artist.find_elements(By.XPATH, ".//*")
        a = "https://yande.re" + a_tag[-2].get_attribute("href")
        return a
    except NoSuchElementException:
        print(f"error: get yande.re url failed: {url}")

def download_10_images(twitter_media_url):
    gallery_dl_command = ["gallery-dl", "--range", "11-20", "-d", "./gallery-dl/", "--cookies-from-browser", "firefox", "--config", "./config.json"]
    gallery_dl_command.append(twitter_media_url)
    subprocess.run(gallery_dl_command)

def main():
    twitter_followings_json_file = input("input json link:")
    twitter_followings = [x for x in json.load(open(twitter_followings_json_file, "r"))]
    
    for following in twitter_followings:
        url = following["url"] + "/media/"
        file_path = f"{pathlib.Path().resolve()}/gallery-dl/twitter/{following["screen_name"]}/"

        o = None

        with open("output.json", "r") as jfile:
            j: dict = json.load(jfile)
            if not j.get(following["screen_name"]):
                o = {
                    "twitter_url": f'{following["url"]}'
                }
            else:
                continue

        download_10_images(twitter_media_url=url)

        if not os.path.isdir(file_path):
            continue

        for img in os.listdir(file_path):

            if len(o) >= 3:
                break

            if not (img.split(".")[-1] in avaliable_image_extensions):
                continue

            saucenao_failed = False

            search_result_html = search_saucenao(file_path + img)
            if search_result_html == None:
                saucenao_failed = True
                print(f"saucenao search failed: {file_path + img}, using iqdb instead.")
                search_result_html = search_iqdb(file_path + img)

            urls = []

            if saucenao_failed:
                urls = extract_iqdb_result(search_result_html)
            else:
                urls = extract_saucenao_result(search_result_html)
            
            for url in urls:
                
                if "danbooru.donmai.us" in url and not o.get("danbooru_url"):
                    o["danbooru_url"] = get_artist_url_danbooru(url)
                
                if "gelbooru.com" in url and not o.get("gelbooru_url"):
                    o["gelbooru_url"] = get_artist_url_gelbooru(url)

                if "yande.re" in url and not o.get("yandere_url"):
                    print(url)
                    o["yandere_url"] = get_artist_url_yandere(url)

            with open("output.json", "r") as file:
                j = json.load(file)
            with open("output.json", "w+") as file2:
                j[following["screen_name"]] = o
                json.dump(j, file2, indent=4)
            time.sleep(3)

if __name__ == "__main__":
    main()