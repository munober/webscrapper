import hashlib
from selenium import webdriver
import time, os, requests, io
from bs4 import BeautifulSoup
from PIL import Image
from math import floor
from selenium.webdriver.common.keys import Keys
# Set before running
DRIVER_PATH = "chromedriver.exe"
options = webdriver.ChromeOptions()
options.add_argument('headless')
options.add_argument('window-size=1920x1080')
sample_size = 100
run_headless = 'on'
run_headless = 'off'
delay = 1 # seconds
search_url_imdb = "https://www.imdb.com/find?q={q}&ref_=nv_sr_sm"
list = "dataset/imdbactors.txt"
manual_search = 'on'
# manual_search = 'off'
manual_search_term = 'Leonardo diCaprio'
manual_search_term = manual_search_term.replace('_', ' ').split()
manual_search_term = [term.capitalize() for term in manual_search_term]
manual_search_term =  (' '.join(manual_search_term))
if manual_search is 'on':
    print(f'Manual search: {manual_search_term}')
elif manual_search is 'off':
    print('Automatic search based on given list')

def bs_get_page(name: str):
    response = requests.get(search_url_imdb.format(q=name).replace(" ", "+"))
    print(f'Searching for: {name}')
    html_soup = BeautifulSoup(response.text, 'html.parser')
    link = html_soup.find('td', class_='result_text')  # div class where actor names listed
    page = link.a.get('href').strip()
    return ('https://imdb.com'+ page + 'mediaindex')

def fetch_image_urls(query: str, max_links_to_fetch: int, wd: webdriver,
                     sleep_between_interactions: 1, search_url):
    imdb_image_path = "/html/body/div[2]/div/div[2]/div/div[1]/div[1]/div/div[3]/a"
    image_urls = set()
    wd.get(search_url)
    thumbnail_results = (wd.find_elements_by_xpath(imdb_image_path))
    max_images_page = len(thumbnail_results)
    if max_links_to_fetch > max_images_page and max_images_page < 48:
        print(f'imdb doesn\'t offer enough pictures for {query}: Only another {max_images_page} available.')
        if max_images_page == 0:
            print(f'Link for manual debugging: {search_url}')
        max_links_to_fetch = max_images_page
    for thumbnail_result in thumbnail_results:
        if(max_links_to_fetch > len(image_urls)):
            try:
                click_target = (wd.find_element_by_xpath(
                    imdb_image_path + f"[{str(len(image_urls) + 1)}]"))
                click_target.click()
                time.sleep(sleep_between_interactions)
                actual_image = wd.find_element_by_xpath('/html/head/meta[7]')
                if actual_image.get_attribute('content') and 'http' in actual_image.get_attribute('content'):
                    image_urls.add(actual_image.get_attribute('content'))
                    print(f'{query}: {str(len(image_urls))}/{max_links_to_fetch} at {thumbnail_result}.')
            except Exception as e:
                print(f'Failed click for {query}. Saving what we got this far. - {e}')
                return image_urls
            try:
                wd.execute_script("window.history.go(-1)")
                time.sleep(sleep_between_interactions)
            except Exception as e:
                print(f'Failed going back for {query}. Saving what we got this far. - {e}')
                continue
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
def search_and_download(search_term: str, driver_path: str, target_path='./dataset/images_imdb', number_images = 5):
    target_folder = os.path.join(target_path, '_'.join(search_term.split(' ')))
    if not os.path.exists(target_folder):
        os.makedirs(target_folder)

    number_pages = floor(number_images / 48) + 1
    page = 1
    while (page <= number_pages):
        if page < number_pages:
            num_img_to_get_this_step = 48
        elif page == number_pages:
            num_img_to_get_this_step = (number_images % 48)

        if run_headless is 'on':
            with webdriver.Chrome(executable_path=driver_path, options=options) as wd:
                res = fetch_image_urls(search_term, num_img_to_get_this_step, wd=wd, sleep_between_interactions = delay,
                                       search_url = (bs_get_page(search_term) + f'?page={page}'))
        elif run_headless is 'off':
            with webdriver.Chrome(executable_path=driver_path) as wd:
                res = fetch_image_urls(search_term, num_img_to_get_this_step, wd=wd, sleep_between_interactions = delay,
                                       search_url = (bs_get_page(search_term) + f'?page={page}'))
        page += 1

    for elem in res:
        persist_image(target_folder, elem)

# Running the search
if manual_search is 'off':
    with open(list,"r") as input:
        search_terms = input.readlines()
    for item in search_terms:
        search_and_download(search_term=item.strip(),
                            driver_path=DRIVER_PATH, number_images=sample_size)
elif manual_search is 'on':
    search_and_download(search_term=manual_search_term.strip(),
                        driver_path=DRIVER_PATH, number_images=sample_size)
