#! /bin/python

import os
import errno
import hashlib
import sys
import random

from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import *
from interface import Ui_Dialog
from filter import run_filter, run_preprocesses

from selenium import webdriver
import geckodriver_autoinstaller
import time, os, requests, io
from bs4 import BeautifulSoup
from PIL import Image
from math import floor
import argparse
from namelist_generator import (
    generate_list,
    get_imdb_thumbnail_links,
    get_imdb_image_link,
)
from google_link_collector import fetch_image_urls_google
from zipfile import ZipFile

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
    default="5000",
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
    "-f", "--filter", action="store_false", help="Skip OpenCV face filter",
)
parser.add_argument(
    "-e", "--headless", action="store_false", help="Don't run in headless mode"
)
parser.add_argument(
    "-pp", "--preprocess", action="store_false", help="Skip preprocessing of images"
)
parser.add_argument(
    "-w", "--width", type=int, help="Set image preprocessing width", default="160"
)
parser.add_argument(
    "-ht", "--height", type=int, help="Set image preprocessing height", default="160"
)
parser.add_argument(
    "-gs",
    "--grayscale",
    action="store_true",
    help="Set preprocessing color to grayscale",
)
parser.add_argument(
    "-z", "--zip", action="store_false", help="Skip adding dataset folder into zipfile"
)
parser.add_argument("-i", "--gui", action="store_true", help="Start in GUI mode")
parser.add_argument(
    "-b",
    "--browser",
    help="Choose preferred browser: [chrome, firefox]",
    default="firefox",
)
parser.add_argument(
    "-no", "--nosearch", help="Don't run any search or download", action="store_true"
)
parser.add_argument(
    "-x",
    "--xml",
    help="Enter path to preferred xml face filter file for opencv",
)
parser.add_argument(
    "-pd", "--padding", type=int, help="Set maximum percentage of padding - will be chosen as a random between 0 and that", default="0"
)

args = parser.parse_args()
non_search = args.nosearch

delay = args.delay  # seconds, 1 second is recommended
timeout = (
    args.timeout
)  # number of times script will try hitting again after error; script will save work and quit if unsuccesful
manual_search = args.manual
run_headless = args.headless
filter_images = args.filter
preprocess_images = args.preprocess
list_len = int(args.list)
zip_mode = args.zip
gui_mode = args.gui
custom_list = args.custom
browser_pref = args.browser
target_path_dataset = "./dataset"

if browser_pref == "firefox":
    if os.name == "nt":
        web_driver = webdriver.Firefox(executable_path="resources/geckodriver.exe")
    elif os.name == "darwin":
        web_driver = webdriver.Firefox(executable_path="resources/geckodriver_macos")
    else:  # linux
        geckodriver_autoinstaller.install()
        web_driver = webdriver.Firefox()
    options = webdriver.FirefoxOptions()
elif browser_pref == "chrome":
    if os.name == "nt":
        web_driver = webdriver.Chrome(executable_path="resources/chromedriver_win.exe")
    else:  # linux
        web_driver = webdriver.Chrome()
    options = webdriver.ChromeOptions()

if run_headless:
    options.add_argument("--headless")


def run_zip():
    try:
        os.makedirs(target_path_dataset)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise
        pass

    if not os.listdir(target_path_dataset):
        # TODO error handling more than just a print?
        print(
            "no dataset folder found. Created dataset folder. Fill this folder and try again"
        )
        return

    try:
        with ZipFile("dataset_zipped.zip", "w") as zipObj:
            for folderName, subfolders, filenames in os.walk(target_path_dataset):
                for filename in filenames:
                    filePath = os.path.join(folderName, filename)
                    zipObj.write(filePath)
    except Exception as e:
        print(f"Could not zip dataset - {e}")


search_url_imdb = "https://www.imdb.com/find?q={q}&ref_=nv_sr_sm"
imdb_list = "dataset/imdbactors.txt"


def bs_get_page_imdb(name: str):
    response = requests.get(search_url_imdb.format(q=name).replace(" ", "+"))
    print(f"Searching on imdb for: {name}")
    try:
        html_soup = BeautifulSoup(response.text, "html.parser")
        link = html_soup.find("td", class_="result_text")
        page = link.a.get("href").strip()
        return "https://imdb.com" + page + "mediaindex"
    except Exception as e:
        print(f"ERROR: Could not find {name} on imdb: {e}")
        return "no_result"


def fetch_image_urls_imdb(
    query: str,
    max_links_to_fetch: int,
    # wd: webdriver,
    sleep_between_interactions: 1,
    search_url,
):
    image_urls = set()
    thumbnail_results = get_imdb_thumbnail_links(search_url)
    if thumbnail_results:
        max_images_page = len(thumbnail_results)
        pictures = random.sample(range(max_images_page), max_images_page)
        thumbnail_results = [
            thumbnail_results[i] for i in pictures
        ]  # shuffling list randomly

        if max_links_to_fetch > max_images_page and max_images_page < 48:
            print(
                f"imdb doesn't offer enough pictures for {query}: Only another {max_images_page} available."
            )
            if max_images_page == 0:
                print(f"Link for manual debugging: {search_url}")
            max_links_to_fetch = max_images_page
        for thumbnail_result in thumbnail_results:
            if max_links_to_fetch > len(image_urls):
                link = get_imdb_image_link(f"https://www.imdb.com/{thumbnail_result}")
                if "https://m.media-amazon.com" in link:
                    image_urls.add(link)
                    print(f"{query}: {str(len(image_urls))}/{max_links_to_fetch}")
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
    platform: str, search_term: str, number_images, headless_toggle_sd
):
    target_folder_dataset = os.path.join(
        target_path_dataset, "_".join(search_term.split(" "))
    )
    if not os.path.exists(target_folder_dataset):
        os.makedirs(target_folder_dataset)

    if platform == "imdb":
        # number_pages = floor(number_images / 48) + 1
        # page = 1
        if number_images > 480:
            number_images = 480
        saved_images = 0
        imdb_link = bs_get_page_imdb(search_term)
        pages = random.sample(range(11), 10)
        for page in pages:
            if number_images - saved_images > 47:
                num_img_to_get_this_step = 48
            else:
                num_img_to_get_this_step = number_images - saved_images
            if imdb_link != "no_result" and num_img_to_get_this_step != 0:
                res_imdb = fetch_image_urls_imdb(
                    search_term,
                    num_img_to_get_this_step,
                    sleep_between_interactions=delay,
                    search_url=(imdb_link + f"?page={page + 1}"),
                )
                for elem in res_imdb:
                    persist_image(target_folder_dataset, elem)
                    saved_images += 1
            else:
                break

    elif platform == "google":
        if headless_toggle_sd:
            print("Running headless")
            with web_driver as wd:
                res_google = fetch_image_urls_google(
                    search_term,
                    number_images,
                    wd=web_driver,
                    sleep_between_interactions=delay,
                )

            if res_google:
                for elem in res_google:
                    persist_image(target_folder_dataset, elem)
        elif not headless_toggle_sd:
            res_google = fetch_image_urls_google(
                search_term,
                number_images,
                wd=web_driver,
                sleep_between_interactions=delay,
            )
            if res_google:
                for elem in res_google:
                    persist_image(target_folder_dataset, elem)


# Running the search
def run_search(manual_search, platform, headless_toggle_orig, rs_sample_size):
    global list_len
    if not manual_search:
        if custom_list == "":
            list = imdb_list
            print("Search based on automatically generated names list")
        elif custom_list != "":
            list = custom_list
            if not os.path.exists(custom_list):
                print("No file found at given path")
            else:
                print(f"Search based on given custom list at {custom_list}")

        with open(list, "r") as input:
            search_terms = input.readlines()
        for item in search_terms:
            search_and_download(
                platform=platform,
                search_term=item.strip(),
                number_images=rs_sample_size,
                headless_toggle_sd=headless_toggle_orig,
            )
            list_len -= 1
            if list_len == 0:
                return

    elif manual_search:
        print(f"Manual search: {manual_search}")
        search_and_download(
            platform=platform,
            search_term=manual_search.strip(),
            number_images=rs_sample_size,
            headless_toggle_sd=headless_toggle_orig,
        )


def start_search(google, imdb, manual, headless_switch, ss_sameple_size):
    if list_len == 0:
        return
    if not manual and not os.path.exists(imdb_list) and custom_list == "":
        print(f"No actors names list found, generating one with {list_len} elements")
        generate_list(list_len)
        print("SUCCESS: List generated")

    if google:
        run_search(manual, "google", headless_switch, ss_sameple_size)
    if imdb:
        run_search(manual, "imdb", headless_switch, ss_sameple_size)


# GUI related stuff


def run_gui():
    app = QApplication([])
    Dialog = QDialog()
    ui = Ui_Dialog()
    ui.setupUi(Dialog)

    ui.run_manual_search.clicked.connect(
        lambda: start_search(
            ui.google_manual.isChecked(),
            ui.imdb_manual.isChecked(),
            ui.manual_search_term.toPlainText(),
            ui.headless_2.isChecked(),
            ui.sample_size_manual.value(),
        )
    )

    ui.run_list_search.clicked.connect(
        lambda: start_search(
            ui.google_auto.isChecked(),
            ui.imdb_auto.isChecked(),
            args.manual,
            ui.headless.isChecked(),
            ui.sample_size_list.value(),
        )
    )

    Dialog.show()
    sys.exit(app.exec_())


if gui_mode:
    run_gui()
else:
    if not non_search:
        if args.platform == "google":
            start_search(
                google=True,
                imdb=False,
                manual=args.manual,
                headless_switch=run_headless,
                ss_sameple_size=args.sample_size,
            )
        elif args.platform == "imdb":
            start_search(
                google=False,
                imdb=True,
                manual=args.manual,
                headless_switch=run_headless,
                ss_sameple_size=args.sample_size,
            )
        elif args.platform == "both":
            start_search(
                google=True,
                imdb=True,
                manual=args.manual,
                headless_switch=run_headless,
                ss_sameple_size=args.sample_size,
            )
        else:
            print("Choose one of the following as search platform: [google, imdb, both]")

    if filter_images:
        assertion_failed = False
        if args.xml:
            if not run_filter(args.xml):
                print("FILTER ERROR: Given  path is not correct or file doesn't have proper format")
                assertion_failed = True
        if assertion_failed or not args.xml:
            for filter_schema in os.listdir("./resources"):
                if filter_schema.endswith(".xml"):
                    run_filter(xml_file=f"./resources/{filter_schema}", padding=abs(args.padding))
    if preprocess_images:
        run_preprocesses(
            width=abs(args.width), height=abs(args.height), grayscale=args.grayscale
        )
    if zip_mode:
        run_zip()
