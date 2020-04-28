#! /bin/python

import os
import hashlib
import sys

from PyQt5 import QtCore, QtGui
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
custom_list = args.custom
target_path_imdb = "./dataset/images_imdb"
target_path_google = "./dataset/images_google"
target_path_dataset = "./dataset"

def run_filter_mode():
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

def run_preprocesses(width, height, grayscale):
    if width != 0 and height != 0:
        str = " "
        if grayscale:
            str = "and convert to grayscale"
        print(f"Entering pre-processing mode: will change image size {str}")
        if os.path.exists(target_path_imdb):
            preprocess_image(folder=target_path_imdb,
                             width=width,
                             height=height,
                             grayscale=grayscale);
        if os.path.exists(target_path_google):
            preprocess_image(folder=target_path_google,
                             width=width,
                             height=height,
                             grayscale=grayscale);
        if os.path.exists(target_path_dataset):
            preprocess_image(folder=target_path_dataset,
                             width=width,
                             height=height,
                             grayscale=grayscale);
        else:
            os.makedirs(target_path_dataset)
            print("Add the images you want to preprocess in the dataset folder")
    else:
        print("You have to set the width and height arguments first")

def run_zip():
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

def start_search():
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

# GUI related stuff
class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(520, 400)
        self.bottom_buttons = QDialogButtonBox(Dialog)
        self.bottom_buttons.setGeometry(QtCore.QRect(20, 360, 481, 32))
        self.bottom_buttons.setOrientation(QtCore.Qt.Horizontal)
        self.bottom_buttons.setStandardButtons(QDialogButtonBox.Close)
        self.bottom_buttons.setCenterButtons(False)
        self.bottom_buttons.setObjectName("bottom_buttons")
        self.tabWidget = QTabWidget(Dialog)
        self.tabWidget.setGeometry(QtCore.QRect(20, 10, 481, 261))
        self.tabWidget.setObjectName("tabWidget")
        self.manual = QWidget()
        self.manual.setObjectName("manual")
        self.manual_search_term = QPlainTextEdit(self.manual)
        self.manual_search_term.setGeometry(QtCore.QRect(80, 10, 120, 30))
        self.manual_search_term.setObjectName("manual_search_term")
        self.label_7 = QLabel(self.manual)
        self.label_7.setGeometry(QtCore.QRect(10, 10, 71, 31))
        self.label_7.setObjectName("label_7")
        self.headless_2 = QCheckBox(self.manual)
        self.headless_2.setGeometry(QtCore.QRect(20, 160, 131, 17))
        self.headless_2.setObjectName("headless_2")
        self.label_9 = QLabel(self.manual)
        self.label_9.setGeometry(QtCore.QRect(20, 90, 91, 16))
        self.label_9.setObjectName("label_9")
        self.google_2 = QRadioButton(self.manual)
        self.google_2.setGeometry(QtCore.QRect(20, 110, 82, 17))
        self.google_2.setObjectName("google_2")
        self.imdb_2 = QRadioButton(self.manual)
        self.imdb_2.setGeometry(QtCore.QRect(20, 130, 82, 17))
        self.imdb_2.setObjectName("imdb_2")
        self.sample_size_manual = QSpinBox(self.manual)
        self.sample_size_manual.setGeometry(QtCore.QRect(160, 110, 80, 22))
        self.sample_size_manual.setObjectName("sample_size_manual")
        self.sample_size_manual.setMaximum(100)
        self.label_10 = QLabel(self.manual)
        self.label_10.setGeometry(QtCore.QRect(160, 90, 61, 16))
        self.label_10.setObjectName("label_10")
        self.label_11 = QLabel(self.manual)
        self.label_11.setGeometry(QtCore.QRect(260, 90, 61, 16))
        self.label_11.setObjectName("label_11")
        self.label_12 = QLabel(self.manual)
        self.label_12.setGeometry(QtCore.QRect(360, 90, 61, 16))
        self.label_12.setObjectName("label_12")
        self.delay_2 = QSpinBox(self.manual)
        self.delay_2.setGeometry(QtCore.QRect(360, 110, 42, 22))
        self.delay_2.setObjectName("delay_2")
        self.timeout_2 = QSpinBox(self.manual)
        self.timeout_2.setGeometry(QtCore.QRect(260, 110, 42, 22))
        self.timeout_2.setObjectName("timeout_2")
        self.run_manual_search = QPushButton(self.manual)
        self.run_manual_search.setGeometry(QtCore.QRect(390, 170, 75, 23))
        self.run_manual_search.setObjectName("run_manual_search")
        self.stop_manual_search = QPushButton(self.manual)
        self.stop_manual_search.setGeometry(QtCore.QRect(390, 200, 75, 23))
        self.stop_manual_search.setObjectName("stop_manual_search")
        self.tabWidget.addTab(self.manual, "")
        self.listsearch = QWidget()
        self.listsearch.setObjectName("listsearch")
        self.list_len = QSpinBox(self.listsearch)
        self.list_len.setGeometry(QtCore.QRect(80, 60, 80, 22))
        self.list_len.setMinimumSize(QtCore.QSize(0, 0))
        self.list_len.setAutoFillBackground(False)
        self.list_len.setObjectName("list_len")
        self.list_len.setMaximum(5000)
        self.label_8 = QLabel(self.listsearch)
        self.label_8.setGeometry(QtCore.QRect(20, 60, 61, 21))
        self.label_8.setObjectName("label_8")
        self.pushButton = QPushButton(self.listsearch)
        self.pushButton.setGeometry(QtCore.QRect(20, 20, 75, 23))
        self.pushButton.setObjectName("pushButton")
        self.pushButton_4 = QPushButton(self.listsearch)
        self.pushButton_4.setGeometry(QtCore.QRect(250, 20, 75, 23))
        self.pushButton_4.setObjectName("pushButton_4")
        self.headless = QCheckBox(self.listsearch)
        self.headless.setGeometry(QtCore.QRect(20, 160, 131, 17))
        self.headless.setObjectName("headless")
        self.label = QLabel(self.listsearch)
        self.label.setGeometry(QtCore.QRect(20, 90, 91, 16))
        self.label.setObjectName("label")
        self.google = QRadioButton(self.listsearch)
        self.google.setGeometry(QtCore.QRect(20, 110, 82, 17))
        self.google.setObjectName("google")
        self.imdb = QRadioButton(self.listsearch)
        self.imdb.setGeometry(QtCore.QRect(20, 130, 82, 17))
        self.imdb.setObjectName("imdb")
        self.label_2 = QLabel(self.listsearch)
        self.label_2.setGeometry(QtCore.QRect(160, 90, 61, 16))
        self.label_2.setObjectName("label_2")
        self.sample_size_list = QSpinBox(self.listsearch)
        self.sample_size_list.setGeometry(QtCore.QRect(160, 110, 80, 22))
        self.sample_size_list.setObjectName("sample_size_list")
        self.sample_size_list.setMaximum(100)
        self.timeout = QSpinBox(self.listsearch)
        self.timeout.setGeometry(QtCore.QRect(260, 110, 42, 22))
        self.timeout.setObjectName("timeout")
        self.label_3 = QLabel(self.listsearch)
        self.label_3.setGeometry(QtCore.QRect(260, 90, 61, 16))
        self.label_3.setObjectName("label_3")
        self.label_4 = QLabel(self.listsearch)
        self.label_4.setGeometry(QtCore.QRect(360, 90, 61, 16))
        self.label_4.setObjectName("label_4")
        self.delay = QSpinBox(self.listsearch)
        self.delay.setGeometry(QtCore.QRect(360, 110, 42, 22))
        self.delay.setObjectName("delay")
        self.run_list_search = QPushButton(self.listsearch)
        self.run_list_search.setGeometry(QtCore.QRect(390, 170, 75, 23))
        self.run_list_search.setObjectName("run_list_search")
        self.stop_list_search = QPushButton(self.listsearch)
        self.stop_list_search.setGeometry(QtCore.QRect(390, 200, 75, 23))
        self.stop_list_search.setObjectName("stop_list_search")
        self.tabWidget.addTab(self.listsearch, "")
        self.filter = QWidget()
        self.filter.setObjectName("filter")
        self.run_filter = QPushButton(self.filter)
        self.run_filter.setGeometry(QtCore.QRect(390, 170, 75, 23))
        self.run_filter.setObjectName("run_filter")
        self.run_filter.clicked.connect(run_filter_mode)
        self.tabWidget.addTab(self.filter, "")
        self.preprocesses = QWidget()
        self.preprocesses.setObjectName("preprocesses")
        self.height = QSpinBox(self.preprocesses)
        self.height.setGeometry(QtCore.QRect(110, 30, 80, 22))
        self.height.setObjectName("height")
        self.height.setMaximum(1000)
        # self.height.valueChanged.connect(update_height)
        self.width = QSpinBox(self.preprocesses)
        self.width.setGeometry(QtCore.QRect(10, 30, 80, 22))
        self.width.setObjectName("width")
        self.width.setMaximum(1000)
        # self.width.valueChanged.connect(update_width)
        self.label_5 = QLabel(self.preprocesses)
        self.label_5.setGeometry(QtCore.QRect(10, 10, 61, 16))
        self.label_5.setObjectName("label_5")
        self.label_6 = QLabel(self.preprocesses)
        self.label_6.setGeometry(QtCore.QRect(110, 10, 61, 16))
        self.label_6.setObjectName("label_6")
        self.grayscale = QCheckBox(self.preprocesses)
        self.grayscale.setGeometry(QtCore.QRect(10, 80, 131, 17))
        self.grayscale.setObjectName("grayscale")
        self.zip = QCheckBox(self.preprocesses)
        self.zip.setGeometry(QtCore.QRect(10, 100, 161, 17))
        self.zip.setObjectName("zip")
        self.run_prep = QPushButton(self.preprocesses)
        self.run_prep.setGeometry(QtCore.QRect(390, 170, 75, 23))
        self.run_prep.setObjectName("run_prep")
        self.run_prep.clicked.connect(lambda: run_preprocesses(self.width.value(), self.height.value(), self.grayscale.isChecked()))
        self.tabWidget.addTab(self.preprocesses, "")
        self.retranslateUi(Dialog)
        self.tabWidget.setCurrentIndex(0)
        self.bottom_buttons.accepted.connect(Dialog.accept)
        self.bottom_buttons.rejected.connect(Dialog.reject)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "WebScrapper 1.1"))
        self.manual_search_term.setPlainText(_translate("Dialog", "Leonardo DiCaprio"))
        self.label_7.setText(_translate("Dialog", "Search Term"))
        self.headless_2.setText(_translate("Dialog", "Run in headless mode"))
        self.label_9.setText(_translate("Dialog", "Search platform"))
        self.google_2.setText(_translate("Dialog", "Google"))
        self.imdb_2.setText(_translate("Dialog", "IMDb"))
        self.label_10.setText(_translate("Dialog", "Sample size"))
        self.label_11.setText(_translate("Dialog", "Timeout"))
        self.label_12.setText(_translate("Dialog", "Delay"))
        self.run_manual_search.setText(_translate("Dialog", "Run"))
        self.stop_manual_search.setText(_translate("Dialog", "Stop"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.manual), _translate("Dialog", "Manual"))
        self.label_8.setText(_translate("Dialog", "List length"))
        self.pushButton.setText(_translate("Dialog", "Generate list"))
        self.pushButton_4.setText(_translate("Dialog", "Custom list"))
        self.headless.setText(_translate("Dialog", "Run in headless mode"))
        self.label.setText(_translate("Dialog", "Search platform"))
        self.google.setText(_translate("Dialog", "Google"))
        self.imdb.setText(_translate("Dialog", "IMDb"))
        self.label_2.setText(_translate("Dialog", "Sample size"))
        self.label_3.setText(_translate("Dialog", "Timeout"))
        self.label_4.setText(_translate("Dialog", "Delay"))
        self.run_list_search.setText(_translate("Dialog", "Run"))
        self.stop_list_search.setText(_translate("Dialog", "Stop"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.listsearch), _translate("Dialog", "Search from list"))
        self.run_filter.setText(_translate("Dialog", "Run"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.filter), _translate("Dialog", "Filter"))
        self.label_5.setText(_translate("Dialog", "Width"))
        self.label_6.setText(_translate("Dialog", "Height"))
        self.grayscale.setText(_translate("Dialog", "Grayscale"))
        self.zip.setText(_translate("Dialog", "Generate zipfile when done"))
        self.run_prep.setText(_translate("Dialog", "Run"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.preprocesses), _translate("Dialog", "Preprocesses"))


def run_gui():
    app = QApplication([])
    Dialog = QDialog()
    ui = Ui_Dialog()
    ui.setupUi(Dialog)
    Dialog.show()
    sys.exit(app.exec_())

if gui_mode:
    run_gui()
else:
    if filter_mode:
        run_filter_mode()
    if preprocess_mode:
        run_preprocesses(width=args.width, height=args.height, grayscale=args.grayscale)
    if zip_mode:
        run_zip()
    if (not filter_mode) and (not preprocess_mode) and (not zip_mode):
        start_search()
