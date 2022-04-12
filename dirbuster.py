import os
import csv
import sys
import base64
import socket
import random
import argparse
import colorama
import requests
import threading
import concurrent.futures

from datetime import datetime
from colorama import Fore, Style
from user_agent import generate_user_agent, generate_navigator

MAX_WORKERS = 13
DEF_TIMEOUT = 3
DEFAULT_DIR_LIST_FILE = 'dir_list.txt'
FOUND = []

def _print_err(message):
	sys.stderr.write(Fore.RED + "[X]"+Style.RESET_ALL+"\t%s\n" % message)

def _print_succ(message):
	sys.stdout.write(Fore.GREEN + "[+]"+Style.RESET_ALL+"\t%s\n" % message)

def _print_info(message):
	sys.stdout.write(Fore.BLUE + "[+]" + Style.RESET_ALL + "\t%s\n" % message)

def _fetch_url(url, headers, ssl_verify=True, write_response=False, timeout=DEF_TIMEOUT):
	global FOUND
	domain = url.split("//")[-1].split("/")[0].split('?')[0].split(':')[0]
	socket.setdefaulttimeout = timeout
	now = datetime.now()
	dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
	try:
		site_request = requests.get(url, headers=headers, verify=ssl_verify)
		FOUND.append([dt_string, url, site_request.status_code, len(site_request.content)])
		if write_response:
			file_name_string = "".join(x for x in url if x.isalnum())
			f = open(os.path.join(domain,file_name_string), 'wb')
			f.write(site_request.content)
			f.close()
	except Exception as e:
		FOUND.append([dt_string, url, "Error: %s" % e, 0])
	sys.stdout.write(".")
	sys.stdout.flush()

def parse_arguemnts():
	parser = argparse.ArgumentParser()
	parser.add_argument("domain", help="domain or host to buster")
	parser.add_argument("-t", "--threads", type=int, help="Concurrent threads to run [15]", default=MAX_WORKERS)
	parser.add_argument("-o", "--output", help="Output file to write to")
	parser.add_argument("-l", "--dlist", help="Directory list file")
	parser.add_argument("-w", "--writeresponse", help="Write response to file", action="store_true", default=False)
	parser.add_argument("-u", "--useragent", help="User agent to use.", default=generate_user_agent())
	parser.add_argument('--timeout', help="Socket timeout [3]", default=3, type=int)
	args = parser.parse_args()
	
	if args.dlist:
		if not os.path.exists(args.dlist):
			_print_err("Can't find file '%s'." % args.dlist)
			exit()
	if not args.output:
		args.output = "%s_output.csv" % args.domain

	if os.path.exists(args.output):
		i = input(Fore.RED + "[!]"+Style.RESET_ALL+"\tOutput file exists. Should i overwrite it?[no]:") or False
		if i == False:
			args.output = "%s_%s.csv" % (args.domain, random.randint(111,999))
			_print_info("Set output file to be '%s'." % args.output)
		else:
			_print_info("Original file will be overwritten.")
	return args

def main():
	args = parse_arguemnts()

	ports = [80]

	# Parse Directory file
	dirs = []
	if args.dlist:
		dirs_raw = open(args.dlist, 'r').readlines()
		for i in dirs_raw:
			thisDir = i.strip()
			if len(thisDir) == 0:
				continue
			dirs.append(thisDir)
	else:
		dirs_raw = open(DEFAULT_DIR_LIST_FILE, 'r').readlines()
		for i in dirs_raw:
			thisDir = i.strip()
			if len(thisDir) == 0:
				continue
			dirs.append(thisDir)

	# Make output directory incase of writing
	if args.writeresponse:
		try:
			os.mkdir(args.domain)
		except:
			# Directory exists
			pass

	# Start threading
	headers = {'User-Agent': args.useragent}
	thread_local = threading.local()
	URLs_to_check = []
	for port in ports:
		for dir in dirs:
			URLs_to_check.append("http://%s:%s/%s" % (args.domain, port, dir))

	_print_info("Starting execution on %s URLs of %s ports and %s directories." % (len(URLs_to_check), len(ports), len(dirs)))
	_print_info("Execution starting with %s threads..." % args.threads)

	thread_args = []
	for i in URLs_to_check:
		thread_args.append((i,headers,args.ignorecertificate,args.writeresponse, args.timeout))

	with concurrent.futures.ThreadPoolExecutor(max_workers=args.threads) as executor:
		executor.map(_fetch_url, *zip(*thread_args))

	_print_succ("Completed exection on %s items." % len(URLs_to_check))

	# Write output to file
	with open(args.output, 'w', newline='') as csvfile:
		fieldnames = ['Datetime', 'URL', 'StatusCode', 'ResponseSize']
		writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

		writer.writeheader()
		for item in FOUND:
			thisItem = {'Datetime': item[0], 'URL':item[1], 'StatusCode':item[2], 'ResponseSize': item[3]}
			writer.writerow(thisItem)

	_print_succ("Wrote all items to file '%s'." % args.output)

	exit()

if __name__ == "__main__":
	try:
		main()
	except KeyboardInterrupt:
		exit()
