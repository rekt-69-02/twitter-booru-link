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

options = Options()
options.add_argument("start-maximized")
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)
driver = webdriver.Chrome(executable_path=ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install(), options=options)

stealth(driver=driver,
        languages=["en-US", "en"],
        vendor="Google Inc.",
        platform="Win32",
        webgl_vendor="Intel Inc.",
        renderer="Intel Iris OpenGL Engine",
        fix_hairline=True,)
sauce = SauceNao(api_key=json.load(open(file="token.json", mode='r'))["saucenao-api"])
avaliable_image_extensions = ["jpg", "jpeg", "png", "webp"]
headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"}

def get_saucenao_results(username, file):
    driver.get("https://saucenao.com/")
    upload = driver.find_element(By.NAME, "file")
    upload.send_keys(f"/home/user/git repo/x-booru-linker/gallery-dl/twitter/{username}/{file}")
    driver.find_element(By.CSS_SELECTOR, "input[type='submit']").click()
    
    WebDriverWait(driver, 10).until(
    expected_conditions.presence_of_element_located((By.CLASS_NAME, "result")))

    b = bs4.BeautifulSoup(driver.page_source, "html.parser")
    # results = driver.find_elements(By.CLASS_NAME, "result")
    results = b.find_all("div",{"class": "result"})

    r: list[SauceNaoResults] = []

    for res in results:
        similarity = results.
        links = [a.get_attribute("href") for a in res.find_elements(By.CSS_SELECTOR, ".resultcontent a")]
        r.append(SauceNaoResults(similarity=int(sim.text), links=links))

    return r

    return [SauceNaoResults(similarity=0, links=[])]

class SauceNaoResults():
    def __init__(self, similarity: float, links: list):
        self.similarity = similarity
        self.links = links

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

def main(following: dict):
    url = following["url"] + "/media"
    username = following["screen_name"]

    with open("output.json", 'r') as f:
        jj = json.load(f)
        try:
            if jj[username]:
                if jj[username]["danbooru_url"] and jj[username]["gelbooru_url"] and jj[username]["yandere_url"]:
                    print(f'"{username}" has finished, skipping.')
                    return
        except KeyError:
            pass

    gallery_dl_command = ["gallery-dl", "--range", "21-30", "-d", "./gallery-dl/", "--cookies-from-browser", "vivaldi"]
    gallery_dl_command.append(url)
    subprocess.run(gallery_dl_command)
    imgs = os.listdir(f"./gallery-dl/twitter/{username}/")
    
    # print(imgs)

    if imgs == []:
        return
    
    for file in imgs:
        if file.split(".")[-1] not in avaliable_image_extensions:
            continue
        
        # upload file
        
        s = get_saucenao_results(username=username, file=file)            

        if s[0].similarity < 80:
            print(f"{username}: {file} similarity < 80%, skipping")
            time.sleep(10)
            continue
        
        o = {
            "x_url": f"{url}",
        }

        for i in range(3):
            for booru_url in s[i].links:

                if s[i].similarity < 80:
                    continue

                if "danbooru.donmai.us" in booru_url:
                    o["danbooru_url"] = get_artist_url_danbooru(url=booru_url)

                if "gelbooru.com" in booru_url:
                    o["gelbooru_url"] = get_artist_url_gelbooru(url=booru_url)

                if "yande.re" in booru_url:
                    o["yandere_url"] = get_artist_url_yandere(url=booru_url)

            with open("output.json", "r", encoding="utf8") as file:
                j = json.load(file)

            print(o)
            j[f"{username}"] = o

            with open("output.json", "w", encoding="utf8") as file2:
                json.dump(j, file2)

            time.sleep(10)


if __name__ == "__main__":
    twitter_followings_json_file = input("please input file path:")
    twitter_followings = [x for x in json.load(open(twitter_followings_json_file, 'r', encoding="utf8"))]
    for following in twitter_followings:
        main(following=following)