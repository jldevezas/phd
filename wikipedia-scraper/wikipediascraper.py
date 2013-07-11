#!/usr/bin/python
# -*- coding: utf8 -*-
#
# wikipediascraper.py
# José Devezas (joseluisdevezas@gmail.com)
# 2013-07-03

import sys
import argparse
import json
import pymongo
import urllib
import urllib2
import logging
import musicbrainz2.webservice as mb
from bs4 import BeautifulSoup
from pymongo import MongoClient
from pymongo.errors import *
from gridfs import GridFS
from gridfs.errors import *

def resolve_title_as_artist(artist_name):
	logging.info("Resolving %s as artist using MusicBrainz" % artist_name)
	q = mb.Query()
	filter = mb.ArtistFilter(query=artist_name.decode('utf8', 'ignore'))
	res = q.getArtists(filter)
	if len(res) > 0:
		html = urllib2.urlopen(res[0].artist.id).read()
		soup = BeautifulSoup(html, 'lxml')
		wikipedia = soup.select('li.wikipedia a[href]')
		if len(wikipedia) > 0:
			return (artist_name, wikipedia[0]['href'][wikipedia[0]['href'].rfind('/')+1:].replace('_', ' '))
	return (artist_name, artist_name)

def wikipedia_call(query_title, resolver=None):
	title = query_title
	if resolver is not None:
		title = resolver(title)[1]

	logging.info("Getting summary data for %s" % query_title)

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
	if revision_id == "-1":
		return None
	html = result['query']['pages'][revision_id]['revisions'][0]['*']

	# Heuristic to detect ambigious pages.
	if 'may refer to:' in html:
		logging.warning("Skipping ambiguous title %s" % title)
		return None

	soup = BeautifulSoup(html, 'lxml')

	imgs = soup.select('table[class~=infobox] img')
	largest_image_url = None
	if len(imgs) > 0:
		img = imgs[0]
		if img.has_attr('srcset'):
			largest_image_url = 'http:' + img['srcset'].split(', ')[-1].split(' ')[0]
		elif img.has_attr('src'):
			logging.warning("Using small image for %s" % title)
			largest_image_url = 'http:' + img['src']

	for sup in soup.select('sup'):
		sup.extract()
	for strong in soup.select('strong[class=error]'):
		strong.extract()
	bio = ' '.join([p.text for p in soup.select('p')])

	artist = {
		'name': query_title,
		'bio': bio,
		'photo': largest_image_url
	}

	return artist

def fetch_and_store_photo(artist):
	photo_id = None

	if artist.get('photo') is not None:
		extension = artist['photo'][artist['photo'].rfind('.'):]
		photo_filename = artist['name'].lower().replace(' ', '_') + extension

		try:
			photo_file = fs.get_last_version(photo_filename)
			photo_id = photo_file._id
		except NoFile:
			photo_bytes = urllib2.urlopen(artist['photo']).read()
			#photo_id = fs.put(photo_bytes, content_type="image/jpeg", filename=photo_filename)
			photo_id = fs.put(photo_bytes, content_type="image", filename=photo_filename)

	return photo_id

def fetch_and_store_artist(col, fs, title, resolver=None):
	artist_data = col.find_one({ '_id': title })
	if artist_data is None:
		artist = wikipedia_call(title, resolver)
		if artist is None:
			logging.warning("Couldn't find information for %s, skipping" % title)
			return False

		artist_data = {
			'_id': artist['name'],
			'bio': artist['bio'],
		}
		
		if artist['bio'] == "":
			logging.warning("No summary found for %s, skipping" % artist['name'])
			return False
		
		photo_id = fetch_and_store_photo(artist)
		if photo_id is not None:
			artist_data['photo'] = photo_id
		col.insert(artist_data)
		return True
	elif not 'photo' in artist_data:
		artist = wikipedia_call(title, resolver)
		photo_id = fetch_and_store_photo(artist)
		if photo_id is not None:
			logging.info("%s updated with missing photo" % artist['name'])
			col.update({ '_id': artist['name'] }, { '$set': { 'photo': photo_id } })
			return True

	logging.warning("%s already exists in the database, skipping" % title)
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
	parser.add_argument('--resolver', type=str, choices=["artists"],
			help="Select a resolver to disambiguate the title for a given context")
	args = parser.parse_args()

	mongo = MongoClient('localhost')
	db = mongo[args.db_name]
	col = db[args.collection_name]
	fs = GridFS(db)
	
	for line in open(args.titles_path, 'r'):
		title = line.strip()
		resolver = None
		if args.resolver is not None:
			if args.resolver == "artists":
				resolver = resolve_title_as_artist
		fetch_and_store_artist(col, fs, title, resolver=resolver)
