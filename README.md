# Webscrapper

Basic webscraping with Selenium and Beautiful Soup to be used for building ML training face image datasets.
The double p is intentional.

## Installation
Depending on your setup, you might be missing some Python modules, just
```bash
pip install ...
```
your way through. 
You might also need to change the browser driver executable. The one included is for Chrome version 80 on Windows.

## Use
```bash
python scrapper.py 
```
The app has a CLI argument parser, check out --help for details.

There are 3 modes of use: automated search (default), manual search (-m "term") and filtering/cropping of faces. Extra functionality built to enhance the results of these modes is available (e.g. automatic name list generation or fine parameter settings).

## Legality
The app searches for, downloades and processes Google Image Search results and IMDb pictures of actors available freely online and is intented for academic use only.