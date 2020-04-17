# imdb actors/actresses name generator
from numpy import size
from requests import get
from bs4 import BeautifulSoup
import math

url_topactors = 'https://www.imdb.com/search/name/?gender=male,female&start={page}&ref_=rlm' # top actors
url_movies_alltime = 'https://www.imdb.com/chart/top' # top 250 alltime great movies
url_movies_current = 'https://www.imdb.com/chart/moviemeter' # top 100 current popular movies
url_series_alltime = 'https://www.imdb.com/chart/toptv/?ref_=nv_tvv_250'
url_series_current = 'https://www.imdb.com/chart/tvmeter/?ref_=nv_tvv_mptv'

actors = []

# Scraping top current actors and directors
response = get(url_movies_current)
html_soup = BeautifulSoup(response.text, 'html.parser')
movie_containers = html_soup.find_all('td', class_ = 'titleColumn') #div class where actor names listed
print('Scraping currently popular movies')
for item in movie_containers:
    actors.append(item.a.attrs.get('title').strip()) # actual html container for name, .strip() removes spaces

# Scraping all time greatest actors and directors
response = get(url_movies_alltime)
html_soup = BeautifulSoup(response.text, 'html.parser')
movie_containers = html_soup.find_all('td', class_ = 'titleColumn') #div class where actor names listed
print('Scraping all time greatest movies')
for item in movie_containers:
    actors.append(item.a.attrs.get('title').strip()) # actual html container for name, .strip() removes spaces

# Scraping top current tv series
response = get(url_series_current)
html_soup = BeautifulSoup(response.text, 'html.parser')
movie_containers = html_soup.find_all('td', class_ = 'titleColumn') #div class where actor names listed
print('Scraping currently popular tv series')
for item in movie_containers:
    actors.append(item.a.attrs.get('title').strip()) # actual html container for name, .strip() removes spaces

# Scraping all time greatest tv series
response = get(url_series_alltime)
html_soup = BeautifulSoup(response.text, 'html.parser')
movie_containers = html_soup.find_all('td', class_ = 'titleColumn') #div class where actor names listed
print('Scraping all time greatest tv series')
for item in movie_containers:
    actors.append(item.a.attrs.get('title').strip()) # actual html container for name, .strip() removes spaces

actors_formatted = []
for actor in actors:
    split = []
    split = actor.split(",")
    for index in range (0, len(split)):
        actors_formatted.append(split[index].replace("(dir.)", "").strip())

# Scraping top 3k actors
index = 1
print('Scraping top 3k imdb actors')
while index < 2952:
    response = get(url_topactors.format(page=index))
    html_soup = BeautifulSoup(response.text, 'html.parser')
    movie_containers = html_soup.find_all('div', class_ = 'lister-item-content') #div class where actor names listed
    for item in movie_containers:
        actors_formatted.append(item.h3.a.text.strip()) # .strip() removes spaces
    print('Running on page ', math.floor(index / 50 + 1), '/ 60', end="\r")
    index = index + 50 # iterating on to the next pages

actors_formatted = list(dict.fromkeys(actors_formatted)) #removing duplicates
actors_formatted.sort() #alphabetical sorting

with open("dataset/imdbactors.txt","w+") as output:
    for actor in actors_formatted:
        output.write(actor + '\n')