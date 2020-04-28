#! /bin/python

import os
import hashlib
import sys

from PyQt5.QtWidgets import *
from selenium import webdriver
import time, os, requests, io
from bs4 import BeautifulSoup
from PIL import Image
from math import floor
import argparse
from namelist_generator import generate_list
from google_link_collector import fetch_image_urls_google
from faces import check_folder, preprocess_image
from zipfile import ZipFile
from layout import Ui_Dialog

# Paths and options
if os.name == "nt":
    DRIVER_PATH = "resources/chromedriver_win.exe"  # Windows
else:  # linux
    DRIVER_PATH = (
        "resources/chromedriver"  # Linux; might need to change for your own system
    )

options = webdriver.ChromeOptions()
options.add_argument("headless")
options.add_argument("window-size=1920x1080")

"""
User options:
help, google/imdb, sample_size, manual/list search, generate list,
run_headless, delay, timeout, list, manual_search, search term,
about, version, github link
"""
parser = argparse.ArgumentParser(
    description="Web Scraper for images on Google and IMDb."
)

parser.add_argument(
    "-v",
    "--version",
    action="version",
    version=f"Web scrapper intentional double p version 1.2",
)
parser.add_argument(
    "-p",
    "--platform",
    help="Choose searching platform: [google, imdb, both]",
    default="both",
)
parser.add_argument(
    "-s",
    "--sample-size",
    type=int,
    help="Type in how many samples you want per actor, recommended maximum is 24 for imdb, 50 for google "
    "default is 20",
    default=20,
)
parser.add_argument(
    "-m",
    "--manual",
    action="store",
    type=str,
    help='Type in "manual search term" or leave empty for using list',
)
parser.add_argument(
    "-l",
    "--list",
    help="Generate list of actor names; type in how many you want as argument",
    default="100",
)
parser.add_argument(
    "-c",
    "--custom",
    help="Use custom names list for search, path to file as argument",
    default="",
)
parser.add_argument(
    "-t",
    "--timeout",
    type=int,
    help="Number of retries before script gives up after errors, default is 30",
    default="30",
)
parser.add_argument(
    "-d",
    "--delay",
    type=float,
    help="Number of seconds for delay between page interactions, default is 1",
    default="1",
)
parser.add_argument(
    "-f",
    "--filter",
    action="store_true",
    help="OpenCV face filter. To be used independent of search function, "
    "by default turned off. Type -f on to apply to dataset",
)
parser.add_argument(
    "-e",
    "--headless",
    action="store_true",
    help="Run in headless more"
)
parser.add_argument(
    "-pp",
    "--preprocess",
    action="store_true",
    help="Run preprocessing mode"
)
parser.add_argument(
    "-w",
    "--width",
    type=int,
    help="Set image preprocessing width",
    default="0"
)
parser.add_argument(
    "-ht",
    "--height",
    type=int,
    help="Set image preprocessing height",
    default="0"
)
parser.add_argument(
    "-gs",
    "--grayscale",
    action="store_true",
    help="Set preprocessing color to grayscale"
)
parser.add_argument(
    "-z",
    "--zip",
    action="store_true",
    help="Add dataset folder into zipfile"
)
parser.add_argument(
    "-i",
    "--gui",
    action="store_true",
    help="Start in GUI mode"
)

args = parser.parse_args()

sample_size = args.sample_size
run_headless = args.headless
delay = args.delay  # seconds, 1 second is recommended
timeout = (
    args.timeout
)  # number of times script will try hitting again after error; script will save work and quit if unsuccesful
manual_search = args.manual
filter_mode = args.filter
preprocess_mode = args.preprocess
zip_mode = args.zip
gui_mode = args.gui
search_mode = False
custom_list = args.custom
target_path_imdb = "./dataset/images_imdb"
target_path_google = "./dataset/images_google"
target_path_dataset = "./dataset"

if (not filter_mode) and (not preprocess_mode) and (not zip_mode):
    search_mode = True

if filter_mode:
    print("Entering filter mode: will delete all non-face images and add a cropped folder for each actor")
    if os.path.exists(target_path_google):
        check_folder(target_path_google)
    else:
        print("No google dataset folder found")
    if os.path.exists(target_path_imdb):
        check_folder(target_path_imdb)
    else:
        print("No imdb dataset folder found")
    if os.path.exists(target_path_dataset):
        check_folder(folder=target_path_dataset)
    else:
        os.makedirs(target_path_dataset)
        print("ERROR: To filter, add images to the dataset folder")
elif preprocess_mode:
    if args.width != 0 and args.height != 0:
        str = " "
        if args.grayscale:
            str = "and convert to grayscale"
        print(f"Entering pre-processing mode: will change image size {str}")
        if os.path.exists(target_path_imdb):
            preprocess_image(folder=target_path_imdb,
                             width=args.width,
                             height=args.height,
                             grayscale=args.grayscale);
        if os.path.exists(target_path_google):
            preprocess_image(folder=target_path_google,
                             width=args.width,
                             height=args.height,
                             grayscale=args.grayscale);
        if os.path.exists(target_path_dataset):
            preprocess_image(folder=target_path_dataset,
                             width=args.width,
                             height=args.height,
                             grayscale=args.grayscale);
        else:
            os.makedirs(target_path_dataset)
            print("Add the images you want to preprocess in the dataset folder")
    else:
        print("You have to set the width and height arguments first")
elif zip_mode:
    if os.path.exists(target_path_dataset):
        try:
            with ZipFile('dataset_zipped.zip', 'w') as zipObj:
                for folderName, subfolders, filenames in os.walk(target_path_dataset):
                    for filename in filenames:
                        filePath = os.path.join(folderName, filename)
                        zipObj.write(filePath)
        except Exception as e:
            print(f"Could not zip dataset - {e}")
    else:
        os.makedirs(target_path_dataset)
        print("no dataset folder found. Created dataset folder. Fill this folder and try again")


search_url_imdb = "https://www.imdb.com/find?q={q}&ref_=nv_sr_sm"
list = "dataset/imdbactors.txt"

def bs_get_page_imdb(name: str):
    response = requests.get(search_url_imdb.format(q=name).replace(" ", "+"))
    print(f"Searching for: {name}")
    html_soup = BeautifulSoup(response.text, "html.parser")
    link = html_soup.find(
        "td", class_="result_text"
    )  # div class where actor names listed
    page = link.a.get("href").strip()
    return "https://imdb.com" + page + "mediaindex"

def fetch_image_urls_imdb(
    query: str,
    max_links_to_fetch: int,
    wd: webdriver,
    sleep_between_interactions: 1,
    search_url,
):
    imdb_image_path = "/html/body/div[2]/div/div[2]/div/div[1]/div[1]/div/div[3]/a"
    timeout_counter = 0
    image_urls = set()
    wd.get(search_url)
    thumbnail_results = wd.find_elements_by_xpath(imdb_image_path)
    max_images_page = len(thumbnail_results)
    if max_links_to_fetch > max_images_page and max_images_page < 48:
        print(
            f"imdb doesn't offer enough pictures for {query}: Only another {max_images_page} available."
        )
        if max_images_page == 0:
            print(f"Link for manual debugging: {search_url}")
        max_links_to_fetch = max_images_page
    for thumbnail_result in thumbnail_results:
        if max_links_to_fetch > len(image_urls):
            try:
                click_target = wd.find_element_by_xpath(
                    imdb_image_path + f"[{str(len(image_urls) + 1)}]"
                )
                click_target.click()
                time.sleep(sleep_between_interactions)
                actual_image = wd.find_element_by_xpath("/html/head/meta[7]")
                if actual_image.get_attribute(
                    "content"
                ) and "http" in actual_image.get_attribute("content"):
                    image_urls.add(actual_image.get_attribute("content"))
                    print(
                        f"{query}: {str(len(image_urls))}/{max_links_to_fetch} at {thumbnail_result}."
                    )
                    timeout_counter = 0
            except Exception as e:
                print(f"Failed click for {query}. Waiting... - {e}")
                time.sleep(5)
                timeout_counter += 1
                if timeout_counter == timeout:
                    return image_urls
                else:
                    continue
            try:
                wd.execute_script("window.history.go(-1)")
                time.sleep(sleep_between_interactions)
            except Exception as e:
                print(f"Failed going back for {query}. Waiting... - {e}")
                time.sleep(5)
                continue
    return image_urls


def persist_image(folder_path: str, url: str):
    try:
        image_content = requests.get(url).content
    except Exception as e:
        print(f"ERROR - Could not download {url} - {e}")

    try:
        image_file = io.BytesIO(image_content)
        image = Image.open(image_file).convert("RGB")
        file_path = os.path.join(
            folder_path, hashlib.sha1(image_content).hexdigest()[:10] + ".jpg"
        )
        with open(file_path, "wb") as f:
            image.save(f, "JPEG", quality=85)
        print(f"SUCCESS - saved {url} - as {file_path}")
    except Exception as e:
        print(f"ERROR - Could not save {url} - {e}")


# standard download size is 5
def search_and_download(
    platform: str, search_term: str, driver_path: str, number_images=5
):
    target_path_imdb = "./dataset/images_imdb"
    target_path_google = "./dataset/images_google"
    target_folder_imdb = os.path.join(
        target_path_imdb, "_".join(search_term.split(" "))
    )
    target_folder_google = os.path.join(
        target_path_google, "_".join(search_term.split(" "))
    )
    if not os.path.exists(target_folder_imdb):
        os.makedirs(target_folder_imdb)
    if not os.path.exists(target_folder_google):
        os.makedirs(target_folder_google)

    if (platform == "imdb") or (platform == "both"):
        number_pages = floor(number_images / 48) + 1
        page = 1
        while page <= number_pages:
            if page < number_pages:
                num_img_to_get_this_step = 48
            elif page == number_pages:
                num_img_to_get_this_step = number_images % 48

            # Currently only running in headful mode (is that even a word)
            # Headless kinda unstable
            if run_headless:
                with webdriver.Chrome(
                    executable_path=driver_path, options=options
                ) as wd:
                    res_imdb = fetch_image_urls_imdb(
                        search_term,
                        num_img_to_get_this_step,
                        wd=wd,
                        sleep_between_interactions=delay,
                        search_url=(bs_get_page_imdb(search_term) + f"?page={page}"),
                    )
                    for elem in res_imdb:
                        persist_image(target_folder_imdb, elem)
            elif not run_headless:
                with webdriver.Chrome(executable_path=driver_path) as wd:
                    res_imdb = fetch_image_urls_imdb(
                        search_term,
                        num_img_to_get_this_step,
                        wd=wd,
                        sleep_between_interactions=delay,
                        search_url=(bs_get_page_imdb(search_term) + f"?page={page}"),
                    )
                for elem in res_imdb:
                    persist_image(target_folder_imdb, elem)
            page += 1
    if (platform == "google") or (platform == "both"):
        with webdriver.Chrome(executable_path=driver_path) as wd:
            res_google = fetch_image_urls_google(
                search_term, number_images, wd=wd, sleep_between_interactions=delay
            )
        for elem in res_google:
            persist_image(target_folder_google, elem)


# Running the search
def run_search(manual_search, platform):
    if not manual_search:
        if custom_list == "":
            print("Search based on automatically generated names list")
            with open(list, "r") as input:
                search_terms = input.readlines()
            for item in search_terms:
                search_and_download(
                    platform=platform,
                    search_term=item.strip(),
                    driver_path=DRIVER_PATH,
                    number_images=sample_size,
                )
        elif custom_list != "":
            if not os.path.exists(custom_list):
                print("No file found at given path")
            else:
                print(f"Search based on given custom list at {custom_list}")
                with open(custom_list, "r") as input:
                    search_terms = input.readlines()
                for item in search_terms:
                    search_and_download(
                        platform=platform,
                        search_term=item.strip(),
                        driver_path=DRIVER_PATH,
                        number_images=sample_size,
                    )
    elif manual_search:
        print(f"Manual search: {manual_search}")
        search_and_download(
            platform=platform,
            search_term=manual_search.strip(),
            driver_path=DRIVER_PATH,
            number_images=sample_size,
        )

# GUI related stuff
def run_gui():
    app = QApplication([])
    Dialog = QDialog()
    ui = Ui_Dialog()
    ui.setupUi(Dialog)
    Dialog.show()
    sys.exit(app.exec_())

if gui_mode:
    search_mode = False
    run_gui()

# Running search mode
if search_mode:
    if not manual_search and not os.path.exists(list) and custom_list == "":
        list_len = int(args.list)
        if list_len > 5000:
            list_len = 5000
            print("Maximum actors' names list length is 5000, set length to 5000")
        elif list_len == 0:
            list_len = 1
            print("Minimum actors' names list length is 1, set length to 1")
        print(f"No actors names list found, generating one with {list_len} elements")
        generate_list(list_len)
        print("SUCCESS: List generated")

    if str(args.platform) == "google":
        run_search(manual_search, "google")
    elif str(args.platform) == "imdb":
        run_search(manual_search, "imdb")
    elif str(args.platform) == "both":
        run_search(manual_search, "both")
    else:
        print("Choose one of the following as search platform: [google, imdb, both]")
