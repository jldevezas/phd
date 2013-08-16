#!/usr/bin/python
# -*- coding: utf8 -*-
#
# wikipedia_scraper.py
# José Devezas (joseluisdevezas@gmail.com)
# 2013-07-03

import sys
import argparse
import json
import pymongo
import urllib
import urllib2
import logging
import sparql
import musicbrainzngs as mb
from bs4 import BeautifulSoup
from pymongo import MongoClient
from pymongo.errors import *
from gridfs import GridFS
from gridfs.errors import *

def bigrams(words):
	wprev = None
	for w in words:
		if wprev is not None:
			yield (wprev, w)
		wprev = w

def sentence_similarity(str1, str2):
	count = 0.0

	tokens1 = str1.lower().split(' ')
	tokens2 = str2.lower().split(' ')
	for token1 in tokens1:
		for token2 in tokens2:
			if token1 == token2:
				count += 1.0

	bigrams1 = list(bigrams(tokens1))
	bigrams2 = list(bigrams(tokens2))
	for bigram1 in bigrams1:
		for bigram2 in bigrams2:
			if bigram1 == bigram2:
				count += 1.0

	return count / max(len(tokens1) + len(bigrams1), len(tokens2) + len(bigrams2))

def resolve_title_as_artist_musicbrainz(artist_name, sim_threshold=0.5):
	try:
		logging.info("Resolving %s as artist using MusicBrainz" % artist_name)
		mb.set_useragent("Juggle Mobile", "0.1", "http://juggle.fe.up.pt")
		
		res = mb.search_artists(artist=artist_name)['artist-list']
		res = sorted(res, key=lambda artist: int(artist['ext:score']), reverse=True)
		
		if len(res) > 0 and sentence_similarity(artist_name, res[0]['name']) > sim_threshold:
			html = urllib2.urlopen('http://musicbrainz.org/artist/%s' % res[0]['id']).read()
			soup = BeautifulSoup(html, 'lxml')
			wikipedia = soup.select('li.wikipedia a[href]')
			if len(wikipedia) > 0:
				return (artist_name, wikipedia[0]['href'][wikipedia[0]['href'].rfind('/')+1:].replace('_', ' '))
	except:
		logging.warning("Request to MusicBrainz failed for %s, skipping resolution" % artist_name)
		pass 

	return (artist_name, None)

def resolve_title_as_artist_dbpedia(artist_name, sim_threshold=0.5):
	try:
		logging.info("Resolving %s as artist using DBpedia" % artist_name)
		query = sparql.query('http://dbpedia.org/sparql', '''
			select ?artist where {
				?artist rdf:type ?type . 
				?type rdf:subClassOf* <http://schema.org/MusicGroup> . 
				?artist foaf:name "''' + artist_name.decode('utf-8') + '''"@en . 
			} LIMIT 10''')

		results = query.fetchall()

		if len(results) < 1:
			logging.warning("Request to DBpedia returned no results for %s, skipping resolution" % artist_name)
			return (artist_name, None)

		title = None
		maxSimilarity = 0.0
		for result in results:
			resolved_name = (sparql.unpack_row(result)[0].encode('utf-8')
					.replace('http://dbpedia.org/resource/', '')
					.replace('_', ' '))
			similarity = sentence_similarity(artist_name, urllib.unquote(resolved_name))
			if similarity > maxSimilarity:
				title = resolved_name
				maxSimilarity = similarity
	except urllib2.HTTPError, sparql.SparqlException:
		logging.warning("Request to DBpedia failed for %s, skipping resolution" % artist_name)
		return (artist_name, None)
	
	return (artist_name, title)

def wikipedia_call(query_title, resolver=None, fallback_resolver=None):
	title = query_title
	if resolver is not None:
		resolved_title = resolver(title)[1]
		if resolved_title is not None:
			title = resolved_title
		elif fallback_resolver is not None:
			resolved_title = fallback_resolver(title)[1]
			if resolved_title is not None:
				title = resolved_title

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
	if 'may refer to:' in html or 'can refer to' in html or 'may stand for' in html:
		logging.warning("Skipping ambiguous title %s" % title)
		return None

	# Heuristic to detect irrelevant pages.
	if 'is a word meaning' in html or 'is a redirect' in html:
		logging.warning("Skipping irrelevant title %s" % title)
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
	for strong in soup.select('strong[class~=error]'):
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

def fetch_and_store_artist(col, fs, title, resolver=None, fallback_resolver=None):
	artist_data = col.find_one({ '_id': title })
	if artist_data is None:
		artist = wikipedia_call(title, resolver, fallback_resolver)
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
		artist = wikipedia_call(title, resolver, fallback_resolver)
		if artist is None:
			logging.warning("Couldn't find information for %s, skipping" % title)
			return False

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
	resolver_choices = ["artists:musicbrainz", "artists:dbpedia"]
	parser.add_argument('--resolver', type=str, choices=resolver_choices,
			help="Select a resolver to disambiguate the title for a given context")
	parser.add_argument('--fallback-resolver', type=str, choices=resolver_choices,
			help="Select a fallback resolver to disambiguate the title for a given context")
	args = parser.parse_args()

	mongo = MongoClient('localhost')
	db = mongo[args.db_name]
	col = db[args.collection_name]
	fs = GridFS(db, args.collection_name)
	
	resolver = None
	if args.resolver is not None:
		if args.resolver == "artists:musicbrainz":
			resolver = resolve_title_as_artist_musicbrainz
		elif args.resolver == "artists:dbpedia":
			resolver = resolve_title_as_artist_dbpedia

	fallback_resolver = None
	if args.fallback_resolver is not None:
		if args.fallback_resolver == "artists:musicbrainz":
			fallback_resolver = resolve_title_as_artist_musicbrainz
		elif args.fallback_resolver == "artists:dbpedia":
			fallback_resolver = resolve_title_as_artist_dbpedia

	for line in open(args.titles_path, 'r'):
		title = line.strip()
		fetch_and_store_artist(col, fs, title, resolver=resolver, fallback_resolver=fallback_resolver)
