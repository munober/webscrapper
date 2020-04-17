# imdb top 10000 actors/actresses
# actually results in 9996 names when removing duplicates
from requests import get
from bs4 import BeautifulSoup
import math

url = 'https://www.imdb.com/search/name/?gender=male,female&start={page}&ref_=rlm'
index = 1
actors = []
while index < 9952:
    response = get(url.format(page=index))
    html_soup = BeautifulSoup(response.text, 'html.parser')
    movie_containers = html_soup.find_all('div', class_ = 'lister-item-content') #div class where actor names listed
    for item in movie_containers:
        actors.append(item.h3.a.text.strip()) # actual html container for name, .strip() removes spaces
    print('Running on page ', math.floor(index / 50 + 1), '/ 200', end="\r")
    index = index + 50 # iterating on to the next pages

actors = list(dict.fromkeys(actors)) #removing duplicates
actors.sort() #alphabetical sorting

with open("imdbtop10k.txt","w+") as output:
    for actor in actors:
        output.write(actor + '\n')