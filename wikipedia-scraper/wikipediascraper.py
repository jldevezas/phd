#!/usr/bin/python
# -*- coding: utf8 -*-
#
# wikipediascraper.py
# José Devezas (joseluisdevezas@gmail.com)
# 2013-07-03

import argparse
import json
import pymongo
import urllib
import urllib2
import logging
from bs4 import BeautifulSoup
from pymongo import MongoClient
from pymongo.errors import *
from gridfs import GridFS

def wikipedia_call(title):
	base_url = 'http://en.wikipedia.org/w/api.php'
	values = {
		'action': 'query',
		'prop': 'revisions',
		'rvprop': 'content',
		'rvparse': 'true',
		'rvsection': '0',
		'format': 'json',
		'titles': title
	}
	
	data = urllib.urlencode(values)
	req = urllib2.Request(base_url, data)
	response = urllib2.urlopen(req)
	result = json.loads(response.read())

	revision_id = result['query']['pages'].keys()[0]
	html = result['query']['pages'][revision_id]['revisions'][0]['*']
	soup = BeautifulSoup(html, 'lxml')

	img = soup.select('img')[0]
	largest_image_url = 'http:' + img['srcset'].split(', ')[-1].split(' ')[0]

	# Heuristic to detect ambigious pages.
	if 'may refer to:' in html:
		logging.warning("Skipping ambiguous title %s" % title)
		return None
	
	for sup in soup.select('sup'):
		sup.extract()
	for strong in soup.select('strong[class=error]'):
		strong.extract()
	bio = ' '.join([p.text for p in soup.select('p')])

	artist = {
		'name': title,
		'bio': bio,
		'photo': largest_image_url
	}

	return artist

def store_artist(col, fs, artist):
	try:
		photo_bytes = urllib2.urlopen(artist['photo']).read()
		extension = artist['photo'][artist['photo'].rfind('.'):]
		photo_filename = artist['name'].lower().replace(' ', '_') + extension
		photo_id = fs.put(photo_bytes, content_type="image/jpeg", filename=photo_filename)
		
		#fs.get(photo_id).read() to get it back.
		
		col.insert({
			'_id': artist['name'],
			'bio': artist['bio'],
			'photo': photo_id
		})
		return True
	except DuplicateKeyError:
		logging.warning("%s already exists in the database, skipping" % artist['name'])
		return False

if __name__ == "__main__":
	logging.basicConfig(format='%(levelname)s %(asctime)s %(message)s',
			datefmt="%Y-%m-%d %H:%M:%S", level=logging.INFO)
	
	parser = argparse.ArgumentParser(
			description="""Based on a list of Wikipedia article titles,
							retrieve first paragraphs and a photo, if available.""")
	parser.add_argument('titles_path',
			help="text file containing one page title per line")
	parser.add_argument('db_name',
			help="MongoDB database name where scraped data will be stored")
	parser.add_argument('collection_name',
			help="MongoDB collection name where scraped data will be stored")
	args = parser.parse_args()

	mongo = MongoClient('localhost')
	db = mongo[args.db_name]
	col = db[args.collection_name]
	fs = GridFS(db)
	
	count = 0
	for line in open(args.titles_path, 'r'):
		title = line.strip()
		artist = wikipedia_call(title)
		store_artist(col, fs, artist)
		count += 1
		if count % 1 == 0: break
