import argparse

"""
User options:
help, google/imdb, sample_size, manual/list search, generate list, 
run_headless, delay, timeout, list, manual_search, search term, maxwidth, maxheight
about, version, github link
"""
parser = argparse.ArgumentParser(description='Web Scraper for images on Google and IMDb.')

parser.add_argument('--google', dest='google',
                    help='user\'s choice of search platform: google')
parser.add_argument('--imdb', dest='imdb', action='store_const',
                    const=imdb, default=google,
                    help='user\'s choice of search platform: IMDb')
parser.add_argument('sample_size', metavar='S')

parser.add_argument('integers', metavar='N', type=int, nargs='+',
                   help='an integer for the accumulator')
parser.add_argument('--sum', dest='accumulate', action='store_const',
                   const=sum, default=max,
                   help='sum the integers (default: find the max)')

args = parser.parse_args()
print(args.accumulate(args.integers))

sample_size = 20
run_headless = 'on'
run_headless = 'off'
delay = 0.75 # seconds, 1 second is recommended
timeout = 30 # number of times script will try hitting again after error; script will save work and quit if unsuccesful
list = "dataset/imdbactors.txt"
manual_search = 'on'
manual_search = 'off'
manual_search_term = 'Al Pacino'