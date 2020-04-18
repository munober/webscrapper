import hashlib
from selenium import webdriver
import time, os, requests, io
from bs4 import BeautifulSoup
from PIL import Image
from math import floor

# Macroparameters to set before running
from selenium.webdriver.common.keys import Keys

DRIVER_PATH = "chromedriver.exe"
sample_size = 80
search_url_imdb = "https://www.imdb.com/find?q={q}&ref_=nv_sr_sm"

def bs_get_page(name: str):
    response = requests.get(search_url_imdb.format(q=name).replace(" ", "+"))
    html_soup = BeautifulSoup(response.text, 'html.parser')
    link = html_soup.find('td', class_='result_text')  # div class where actor names listed
    if (link.a.text) == name:
        page = link.a.get('href').strip()
        return ('https://imdb.com'+ page + 'mediaindex') # could also add /?page=1...2...etc
    else:
        return

def fetch_image_urls(query: str, max_links_to_fetch: int, wd: webdriver,
                     sleep_between_interactions: 1, search_url: str = search_url_imdb):
    # load the page
    wd.get(query)

    image_urls = set()
    image_count = 0
    page_number = 1
    # get all image thumbnail results
    thumbnail_result = (wd.find_elements_by_xpath("/html/body/div[2]/div/div[2]/div/div[1]/div[1]/div/div[3]/a"))
    max_images_page = len(thumbnail_result)
    thumbnail_result[0].click()
    time.sleep(sleep_between_interactions)
    if max_links_to_fetch > max_images_page and max_images_page < 48:
        print(f'imdb doesn\'t offer enough pictures: Only {max_images_page} available.')
        max_links_to_fetch = max_images_page
    while len(image_urls) < max_links_to_fetch:
        actual_image = wd.find_element_by_xpath('/html/head/meta[7]')
        if actual_image.get_attribute('content') and 'http' in actual_image.get_attribute('content'):
            image_urls.add(actual_image.get_attribute('content'))
        image_count += 1
        if image_count == 48:
            page_number += 1
            wd.get(query + f'?page={page_number}')
            time.sleep(sleep_between_interactions)
            image_count = 0
            thumbnail_result = (
            wd.find_elements_by_xpath("/html/body/div[2]/div/div[2]/div/div[1]/div[1]/div/div[3]/a"))
            max_images_page = len(thumbnail_result)
            if max_links_to_fetch > max_images_page and max_images_page < 48:
                print(f'imdb doesn\'t offer enough pictures: Only other {max_images_page} available.')
                max_links_to_fetch = max_images_page
        else:
            wd.execute_script("window.history.go(-1)")
            time.sleep(sleep_between_interactions)

        if(len(image_urls) < max_links_to_fetch):
            thumbnail_result = (wd.find_element_by_xpath("/html/body/div[2]/div/div[2]/div/div[1]/div[1]/div/div[3]/a[" + str(image_count + 1) + "]"))
            thumbnail_result.click()
        time.sleep(sleep_between_interactions)
    return image_urls

maxwidth = 1000
maxheight = 1000
def persist_image(folder_path:str,url:str):
    try:
        image_content = requests.get(url).content

    except Exception as e:
        print(f"ERROR - Could not download {url} - {e}")

    try:
        image_file = io.BytesIO(image_content)
        image = Image.open(image_file).convert('RGB')
        file_path = os.path.join(folder_path,hashlib.sha1(image_content).hexdigest()[:10] + '.jpg')
        with open(file_path, 'wb') as f:
            width, height = image.size
            aspect_ratio = min(maxwidth / width, maxheight / height)
            new_width = floor(aspect_ratio * width)
            new_height = floor(aspect_ratio * height)
            if width > maxwidth or height > maxheight:
                image = image.resize((new_width, new_height), Image.ANTIALIAS)
            width, height = image.size
            if width < maxwidth and height < maxheight:
                image.save(f, "JPEG", quality=85)
        print(f"SUCCESS - saved {url} - as {file_path}")
    except Exception as e:
        print(f"ERROR - Could not save {url} - {e}")

# stadard download size is 5, can be overriden above
def search_and_download(search_term: str, driver_path: str, target_path='./dataset/images_imdb', number_images=5):
    target_folder = os.path.join(target_path, '_'.join(search_term.lower().split(' ')))

    if not os.path.exists(target_folder):
        os.makedirs(target_folder)

    with webdriver.Chrome(executable_path=driver_path) as wd:
        print(bs_get_page(search_term))
        res = fetch_image_urls(bs_get_page(search_term), number_images, wd=wd, sleep_between_interactions=1)

    for elem in res:
        persist_image(target_folder, elem)

# Running the search
with open("dataset/imdbactors.txt","r") as input:
    search_terms = input.readlines()
for item in search_terms:
    search_term = item.strip()
    search_and_download(search_term=search_term, driver_path=DRIVER_PATH, number_images= sample_size)

