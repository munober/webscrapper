import hashlib
from selenium import webdriver
import time, os, requests, io
from bs4 import BeautifulSoup
from PIL import Image
from math import floor
import argparse
from namelist_generator import generate_list
from selenium_google import fetch_image_urls_google

# Paths and options
DRIVER_PATH = "chromedriver.exe"
options = webdriver.ChromeOptions()
options.add_argument('headless')
options.add_argument('window-size=1920x1080')

"""
User options:
help, google/imdb, sample_size, manual/list search, generate list, 
run_headless, delay, timeout, list, manual_search, search term,
about, version, github link
"""
parser = argparse.ArgumentParser(description='Web Scraper for images on Google and IMDb.')

parser.add_argument(
    "-v", "--version", action="version",
    version=f"{parser.prog} version 1.42.69"
)
parser.add_argument('-p', '--platform',
                    help='Choose searching platform: [google, imdb, both]',
                    default='both')
parser.add_argument('-s', '--samples',
                    help='Type in how many samples you want per actor, maximum is 24 for imdb, 50 for google; '
                         'default is 20', default=20)
parser.add_argument('-m', '--manual',
                    help='Type in "manual search term" or leave empty for using list',
                    default='list')
parser.add_argument('-l', '--list',
                    help='Generate list of actor names; type in how many you want as argument',
                    default='100')
parser.add_argument('-t', '--timeout',
                    help='Number of retries before script gives up after errors, default is 30',
                    default='30')
parser.add_argument('-d', '--delay',
                    help='Number of seconds for delay between page interactions, default is 1',
                    default='1')

args = parser.parse_args()

sample_size = int(args.samples)
run_headless = 'off'
delay = float(args.delay) # seconds, 1 second is recommended
timeout = int(args.timeout) # number of times script will try hitting again after error; script will save work and quit if unsuccesful

manual_search_term = args.manual
if manual_search_term is 'list':
    manual_search = 'off'
else:
    manual_search = 'on'

maxwidth = 1000
maxheight = 1000

manual_search_term = manual_search_term.replace('_', ' ').split()
manual_search_term = [term.capitalize() for term in manual_search_term]
manual_search_term =  (' '.join(manual_search_term))
search_url_imdb = "https://www.imdb.com/find?q={q}&ref_=nv_sr_sm"
list = "dataset/imdbactors.txt"

def bs_get_page_imdb(name: str):
    response = requests.get(search_url_imdb.format(q=name).replace(" ", "+"))
    print(f'Searching for: {name}')
    html_soup = BeautifulSoup(response.text, 'html.parser')
    link = html_soup.find('td', class_='result_text')  # div class where actor names listed
    page = link.a.get('href').strip()
    return ('https://imdb.com'+ page + 'mediaindex')

def fetch_image_urls_imdb(query: str, max_links_to_fetch: int, wd: webdriver,
                          sleep_between_interactions: 1, search_url):
    imdb_image_path = "/html/body/div[2]/div/div[2]/div/div[1]/div[1]/div/div[3]/a"
    timeout_counter = 0
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
                    timeout_counter = 0
            except Exception as e:
                print(f'Failed click for {query}. Waiting... - {e}')
                time.sleep(5)
                timeout_counter += 1
                if(timeout_counter == timeout):
                    return image_urls
                else:
                    continue
            try:
                wd.execute_script("window.history.go(-1)")
                time.sleep(sleep_between_interactions)
            except Exception as e:
                print(f'Failed going back for {query}. Waiting... - {e}')
                time.sleep(5)
                continue
    return image_urls

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
            image.save(f, "JPEG", quality=85)
        print(f"SUCCESS - saved {url} - as {file_path}")
    except Exception as e:
        print(f"ERROR - Could not save {url} - {e}")

# stadard download size is 5, can be overriden above
def search_and_download(platform: str, search_term: str, driver_path: str, number_images = 5):
    target_path_imdb = './dataset/images_imdb'
    target_path_google = './dataset/images_google'
    target_folder_imdb = os.path.join(target_path_imdb, '_'.join(search_term.split(' ')))
    target_folder_google = os.path.join(target_path_google, '_'.join(search_term.split(' ')))
    if not os.path.exists(target_folder_imdb):
        os.makedirs(target_folder_imdb)
    if not os.path.exists(target_path_google):
        os.makedirs(target_folder_google)

    if (platform is 'imdb') or (platform is 'both'):
        number_pages = floor(number_images / 48) + 1
        page = 1
        while (page <= number_pages):
            if page < number_pages:
                num_img_to_get_this_step = 48
            elif page == number_pages:
                num_img_to_get_this_step = (number_images % 48)

            # Currently only running in headful mode (is that even a word)
            # Headless kinda unstable
            if run_headless is 'on':
                with webdriver.Chrome(executable_path=driver_path, options=options) as wd:
                    res_imdb = fetch_image_urls_imdb(search_term, num_img_to_get_this_step, wd=wd, sleep_between_interactions = delay,
                                                search_url = (bs_get_page_imdb(search_term) + f'?page={page}'))
                    for elem in res_imdb:
                        persist_image(target_folder_imdb, elem)
            elif run_headless is 'off':
                with webdriver.Chrome(executable_path=driver_path) as wd:
                    res_imdb = fetch_image_urls_imdb(search_term, num_img_to_get_this_step, wd=wd, sleep_between_interactions = delay,
                                                search_url = (bs_get_page_imdb(search_term) + f'?page={page}'))
                for elem in res_imdb:
                    persist_image(target_folder_imdb, elem)
            page += 1
    if (platform is 'google') or (platform is 'both'):
        with webdriver.Chrome(executable_path=driver_path) as wd:
            res_google = fetch_image_urls_google(search_term, number_images, wd=wd, sleep_between_interactions=delay)
        for elem in res_google:
            persist_image(target_folder_google, elem)

# Running the search
def run_search(manual_search, platform):
    if manual_search is 'off':
        print('Automatic search based on given list')
        with open(list,"r") as input:
            search_terms = input.readlines()
        for item in search_terms:
            search_and_download(platform=platform, search_term=item.strip(),
                                driver_path=DRIVER_PATH, number_images=sample_size)
    elif manual_search is 'on':
        print(f'Manual search: {manual_search_term}')
        search_and_download(platform=platform, search_term=manual_search_term.strip(),
                            driver_path=DRIVER_PATH, number_images=sample_size)

# Running the whole thing
if manual_search is 'off' and not os.path.exists(list):
    list_len = int(args.list)
    if list_len > 5000:
        list_len = 5000
        print('Maximum actors\' names list length is 5000, set length to 5000')
    elif list_len == 0:
        list_len = 1
        print('Minimum actors\' names list length is 1, set length to 1')
    print(f'No actors names list found, generating one with {list_len} elements')
    generate_list(list_len)
    print('List generated. Run script again to search')

if str(args.platform) is 'google':
    run_search(manual_search, 'google')
if str(args.platform) is 'imdb':
    run_search(manual_search, 'imdb')
if str(args.platform) is 'both':
    run_search(manual_search, 'both')
else:
    print('Choose one of the following as -p: [google, imdb, both]')
