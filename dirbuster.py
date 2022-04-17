from multiprocessing.pool import Pool
from sys import argv
import requests

if len(argv) != 5
    print(f'Usage: {argv[0]} <URL> <brute force file> <num threads> <search string>')
    exit(1)

url = argv[1]
fname = argv[2]
numthreads = int(argv[3])
search_string = argv[4]

# Prints out the flag if it's in the content of this page
def check_page(name):
    name = name.strip()
    r = requests.get(f'{url}/{name}')
    if search_string in r.text:
        print(r.text)

# Uses a process pool to check all of the pages with names from the file
with open(fname, 'r') as f:
    with Pool(processes=numthreads) as pool:
        pool.map(check_page, f, 256)
