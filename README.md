# Webscrapper

Basic webscraping with Selenium and Beautiful Soup to be used for building ML training face image datasets.
The double p is intentional.

## Installation
Depending on your setup, you might be missing some Python modules, just

```bash
sudo pip install -r requirements.txt
```
You might also need to change the browser driver executable, included in the repo are web drivers for chrome on Windows and Linux. Find yours at (https://chromedriver.storage.googleapis.com/index.html), download and unzip, then add to the project folder or add to system path. If you are using Firefox, the process is similar, just google for Selenium python Firefox.

## Use

Example usage:
```bash
python scrapper.py -p google -m "brad pitt"
```
The app has both a CLI parser, as well as a graphical user interface. Check out --help for details.

There are 3 modes of use: automated search (default), manual search (-m "search term") and filtering/cropping (-f on) of faces. Extra functionality built to enhance the results of these modes is available (e.g. automatic name list generation or fine parameter settings).

Manual search mode:
(https://github.com/munober/webscrapper/resources/Screenshot_1.png)

Data preprocessing mode:
(https://github.com/munober/webscrapper/resources/Screenshot_2.png)

## Legality
The app searches for, downloades and processes Google Image Search results and IMDb pictures of actors available freely online and is intented for academic use only.
