from selenium import webdriver
import time


def scroll_to_end(wd):
    wd.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(5)


def view_webpage(link_file):
    scroll_to_end(wd)
    try:
        elem1 = wd.find_elements_by_tag_name("a")
    except:
        print("some error occured")
    try:
        for elem in elem1:
            if elem.get_attribute("title") == "Download photo":
                print(elem.get_attribute("href"), file=link_file)
    except:
        print("No data in Element")


wd = webdriver.Firefox(executable_path="resources/geckodriver.exe")
url = "https://unsplash.com/t/fashion"
wd.get(url)
# we will open the file in apend mode
link_file = open("links.txt", mode="a+")
while True:
    view_webpage(link_file)


# Closing the file to save in drive
link_file.close()
