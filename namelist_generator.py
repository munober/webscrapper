# imdb actors/actresses/directors name generator
from numpy import size
from requests import get
from bs4 import BeautifulSoup
import math
import os

url_topactors = "https://www.imdb.com/search/name/?gender=male,female&start={page}&ref_=rlm"  # 10k items
url_movies_alltime = (
    "https://www.imdb.com/chart/top"  # top 250 alltime great movies times 3 people
)
url_movies_current = "https://www.imdb.com/chart/moviemeter"  # top 100 current popular movies times 3 people
url_series_alltime = (
    "https://www.imdb.com/chart/toptv/?ref_=nv_tvv_250"  # top 250 times one or two
)
url_series_current = (
    "https://www.imdb.com/chart/tvmeter/?ref_=nv_tvv_mptv"  # top 250 times one or two
)
url = "https://www.imdb.com/name/nm0000138/mediaviewer/rm1136570881"
def get_imdb_image_link(url):
    links = []
    response = get(url)
    content = BeautifulSoup(response.text, "html.parser")
    big_container = content.find(
        "meta", itemprop = "image"
    )
    link = big_container.get("content")
    return link

def get_imdb_thumbnail_links(url):
    links = []
    response = get(url)
    content = BeautifulSoup(response.text, "html.parser")
    big_container = content.find(
        "div", class_="media_index_thumb_list"
    )
    small_containers = big_container.find_all("a")
    for item in small_containers:
        link = item.get("href")
        links.append(f"{link}")
    return links

def generate_list(number):
    actors = []

    # Scraping top current actors and directors in movies
    response = get(url_movies_current)
    html_soup = BeautifulSoup(response.text, "html.parser")
    movie_containers = html_soup.find_all(
        "td", class_="titleColumn"
    )
    print("Scraping currently popular movies")
    for item in movie_containers:
        actors.append(
            item.a.attrs.get("title").strip()
        )

    # Scraping top current tv series
    response = get(url_series_current)
    html_soup = BeautifulSoup(response.text, "html.parser")
    movie_containers = html_soup.find_all(
        "td", class_="titleColumn"
    )  # div class where actor names listed
    print("Scraping currently popular tv series")
    for item in movie_containers:
        actors.append(
            item.a.attrs.get("title").strip()
        )  # actual html container for name, .strip() removes spaces

    # Scraping all time greatest actors and directors in movies
    response = get(url_movies_alltime)
    html_soup = BeautifulSoup(response.text, "html.parser")
    movie_containers = html_soup.find_all(
        "td", class_="titleColumn"
    )  # div class where actor names listed
    print("Scraping all time greatest movies")
    for item in movie_containers:
        actors.append(
            item.a.attrs.get("title").strip()
        )  # actual html container for name, .strip() removes spaces

    # Scraping all time greatest tv series
    response = get(url_series_alltime)
    html_soup = BeautifulSoup(response.text, "html.parser")
    movie_containers = html_soup.find_all(
        "td", class_="titleColumn"
    )  # div class where actor names listed
    print("Scraping all time greatest tv series")
    for item in movie_containers:
        actors.append(
            item.a.attrs.get("title").strip()
        )  # actual html container for name, .strip() removes spaces

    actors_formatted = []
    for actor in actors:
        split = []
        split = actor.split(",")
        for index in range(0, len(split)):
            actors_formatted.append(split[index].replace("(dir.)", "").strip())

    # Scraping top 3k actors
    if number > 500:
        index = 1
        print("Scraping top 5k imdb actors")
        while index < number:
            response = get(url_topactors.format(page=index))
            html_soup = BeautifulSoup(response.text, "html.parser")
            movie_containers = html_soup.find_all(
                "div", class_="lister-item-content"
            )  # div class where actor names listed
            for item in movie_containers:
                actors_formatted.append(
                    item.h3.a.text.strip()
                )  # .strip() removes spaces
            print(
                "Running on page ",
                math.floor(index / 50 + 1),
                f"/ {math.floor(number / 50 + 1)}",
                end="\r",
            )
            index = index + 50  # iterating on to the next pages

    actors_formatted = list(dict.fromkeys(actors_formatted))  # removing duplicates

    if number < len(actors_formatted):
        actors_formatted = actors_formatted[:number]  # trims list to desired size
    if not os.path.exists("dataset"):
        os.makedirs("dataset")
    with open("dataset/imdbactors.txt", "w+") as output:
        for actor in actors_formatted:
            output.write(actor + "\n")
