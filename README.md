# Webscrapper

Basic webscapping with Selenium, beautiful soup, scrapy (more tools will be investigated) to be used for building ML training image datasets.

Also trying to have a nice working UI with PyQT.

## Installation
Depending on your setup, you might be missing some Python modules, just
```bash
pip install ...
```
your way through.

## Files/Scripts
scrapper_static.py leverages Beautiful Soup to grab imdb's list of 250 most famous actors and saves them to a list in a txt file.
scrapper_dynamic.py uses Selenium to download the top you choose how many google image search results of the people in above named txt file.
faces.py process those faces to crop out the people inside.

## Legality
Will be read into.

## Avoid getting banned
Scrapy suggests:
```
- rotate your user agent from a pool of well-known ones from browsers (google around to get a list of them)
- disable cookies (see COOKIES_ENABLED) as some sites may use cookies to spot bot behaviour
- use download delays (2 or higher). See DOWNLOAD_DELAY setting.
- if possible, use Google cache to fetch pages, instead of hitting the sites directly
- use a pool of rotating IPs. For example, the free Tor project or paid services like ProxyMesh. An open source alternative is scrapoxy, a super proxy that you can attach your own proxies to.
- use a highly distributed downloader that circumvents bans internally, so you can just focus on parsing clean pages. One example of such downloaders is Crawlera
```