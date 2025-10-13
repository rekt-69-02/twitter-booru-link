import json, os, subprocess, bs4
from saucenao_api import SauceNao
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
from . import urm
from .urm import SauceNaoResult

options = Options()
options.add_argument("start-maximized")
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)
driver = webdriver.Chrome(executable_path=ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install(), options=options)
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
    upload.send_keys(f"/home/user/git repo/x-booru-linker/gallery-dl/twitter/{username}/{image}")
    driver.find_element(By.CSS_SELECTOR, "input[type='submit']").click()

def main():
    twitter_followings_json_file = input("please input file path:")
    twitter_followings = [x for x in json.load(open(twitter_followings_json_file, 'r', encoding="utf8"))]

    for following in twitter_followings:
        urm.download_10_images(twitter_media_url=following["url"] + "/media/")
        file_path = f"/home/user/git repo/x-booru-linker/gallery-dl/{following["screen_name"]}/"
            
        for img in os.listdir(file_path):
            search_saucenao(username=following["screen_name"], image=img)
            raw_html = driver.page_source
            results = urm.extract_result(raw_html)            
            sauces = []
            for result in results:
                sauces.append(SauceNaoResult(result))

            o = {
                "twitter_url": following["url"]
            }

            for sauce in sauces:
                for url in sauce.urls:
                    if "danbooru.donmai.us" in url:
                        o["danbooru_url"] = get_artist_url_danbooru(url)
                    
                    if "gelbooru.com" in url:
                        o["gelbooru_url"] = get_artist_url_gelbooru(url)

                    if "yande.re" in url:
                        o["yandere_url"] = get_artist_url_yandere(url)

            