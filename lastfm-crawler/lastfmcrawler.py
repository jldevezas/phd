#!/usr/bin/env python3
# -*- coding: utf8 -*-
#
# lastfm-crawler.py
# José Devezas (joseluisdevezas@gmail.com)
# 2013-06-03

import os
import sys
import time
import pylast
import sqlite3
import logging


LIMIT = 1000
MAX_RETRIES = 10


logging.basicConfig(format='%(levelname)s %(asctime)s %(message)s',
		datefmt="%Y-%m-%d %H:%M:%S", level=logging.INFO)
requests = 0
users_expanded = set([])
seed_users = set([])


def inc_requests():
	global requests
	requests += 1
	if requests % 5 == 0:
		logging.debug("Respecting the API rules, waiting 1 second between every 5 requests.")
		time.sleep(1)


def create_schema(db):
	c = db.cursor()

	c.execute("CREATE TABLE IF NOT EXISTS tracks " +
			"(lastfm_id INTEGER, mbid TEXT, title TEXT, album TEXT, artist TEXT, timestamp INTEGER, " +
			"duration INTEGER, plays INTEGER, listeners INTEGER, user_id INTEGER, " +
			"UNIQUE (lastfm_id, user_id, timestamp))")

	c.execute("CREATE TABLE IF NOT EXISTS tags (name TEXT UNIQUE)")

	c.execute("CREATE TABLE IF NOT EXISTS tracks_tags " +
		"(track_id INTEGER, tag_id INTEGER, weight INTEGER, UNIQUE (track_id, tag_id))")

	c.execute("CREATE TABLE IF NOT EXISTS users " +
			"(name TEXT UNIQUE, age INTEGER, gender CHARACTER(1), country TEXT, " +
			"plays INTEGER)")

	c.execute("CREATE TABLE IF NOT EXISTS friends " +
		"(first_user_id INTEGER, second_user_id INTEGER, " +
		"UNIQUE (first_user_id, second_user_id))")

	c.close()
	db.commit()


def create_friendship(db, first_uid, second_uid):
	c = db.cursor()

	c.execute("SELECT first_user_id, second_user_id FROM friends " +
			"WHERE (first_user_id = ? OR first_user_id = ?) AND " +
			"(second_user_id = ? OR second_user_id = ?)", (first_uid, second_uid, first_uid, second_uid))

	res = c.fetchone()
	if res != None: return

	c.execute("INSERT OR IGNORE INTO friends (first_user_id, second_user_id) VALUES(?,?)",
			(first_uid, second_uid))

	c.close()
	db.commit()
	
	logging.info("Created new friendship between users %d and %d" % (first_uid, second_uid))


def create_user(db, user_data):
	c = db.cursor()

	c.execute("SELECT ROWID FROM users where name = ?", (user_data["name"], ))
	res = c.fetchone()
	
	if res != None:
		c.close()
		return res[0]

	c.execute("INSERT OR IGNORE INTO users (name, age, gender, country, plays) VALUES(?,?,?,?,?)",
			(user_data["name"], user_data["age"], user_data["gender"], user_data["country"], user_data["plays"]))

	db.commit()

	c.execute("SELECT last_insert_rowid()")
	user_id = c.fetchone()[0]
	c.close()

	logging.info("Created new user with ID %d" % user_id)

	return user_id


def create_track(db, track_data, user_id):
	c = db.cursor()

	track_id = None
	try:
		c.execute("INSERT INTO tracks (lastfm_id, mbid, title, album, artist, timestamp, duration, plays, " +
				"listeners, user_id)" + "VALUES(?,?,?,?,?,?,?,?,?,?)",
				(track_data["id"], track_data["mbid"], track_data["title"], track_data["album"],
					track_data["artist"], track_data["timestamp"], track_data["duration"], track_data["plays"],
					track_data["listeners"], user_id))
		c.execute("SELECT last_insert_rowid()")
		track_id = c.fetchone()[0]
	except sqlite3.IntegrityError:
		return

	for tag_data in track_data["tags"]:
		(tag, weight) = tag_data
		tag = tag.lower()

		c.execute("SELECT ROWID FROM tags WHERE name = ?", (tag,))
		res = c.fetchone()
		if res is None:
			c.execute("INSERT INTO tags (name) VALUES(?)", (tag,))
			c.execute("SELECT last_insert_rowid()")
			res = c.fetchone()
		
		tag_id = res[0]
		c.execute("INSERT OR REPLACE INTO tracks_tags (track_id, tag_id, weight) VALUES (?,?,?)",
				(track_id, tag_id, weight))

	db.commit()
	c.close()


def build_user_data(user):
	retries = MAX_RETRIES
	while retries > 0:
		try:
			user_data = {}
			user_data["name"] = user.get_name()
			user_data["age"] = int(user.get_age())

			gender = user.get_gender()
			if gender == "Male":
				user_data["gender"] = "m"
			elif gender == "Female":
				user_data["gender"] = "f"
			else:
				user_data["gender"] = None

			country = user.get_country()
			if country is None or country.get_name() is None:
				user_data["country"] = None
			else:
				user_data["country"] = country.get_name().lower()

			user_data["plays"] = int(user.get_playcount())
			inc_requests()
			return user_data
		except Exception as ex:
			logging.error("%s (build_user_data retry %d)" % (str(ex), MAX_RETRIES - retries + 1))
			retries -= 1
	return None


def build_track_data(played_track):
	retries = MAX_RETRIES
	while retries > 0:
		try:
			track = played_track.track

			track_data = {}

			# track.getInfo
			track_data["title"] = track.get_title()

			album = track.get_album()
			if album is None:
				track_data["album"] = None
			else:
				track_data["album"] = album.get_title()

			artist = track.get_artist()
			if artist is None:
				track_data["artist"] = None
			else:
				track_data["artist"] = artist.get_name()

			track_data["id"] = track.get_id()
			track_data["mbid"] = track.get_mbid()
			track_data["duration"] = track.get_duration()
			track_data["plays"] = track.get_playcount()
			track_data["listeners"] = track.get_listener_count()
			track_data["timestamp"] = int(played_track.timestamp)
			inc_requests()

			# track.getTopTags
			track_data["tags"] = [(t.item.get_name().lower(), int(t.weight))
					for t in track.get_top_tags() if t.weight != "0"]
			inc_requests()
			return track_data
		except Exception as ex:
			logging.error("%s (build_track_data retry %d)" % (str(ex), MAX_RETRIES - retries + 1))
			retries -= 1
	return None


def crawl_user_neighborhood(db, seed_username):
	neighbors_visited = set([])

	seed = network.get_user(seed_username)
	user_data = build_user_data(seed)
	
	if user_data is None:
		logging.warning("Failed to retrieve user %s data, skipping." % seed_username)
		return neighbors_visited

	seed_user_id = create_user(db, user_data)

	logging.info("Getting %s's recent tracks." % seed_username)
	recent_tracks = seed.get_recent_tracks()
	inc_requests()
	for played_track in recent_tracks:
		track_data = build_track_data(played_track)
		if track_data is None:
			logging.warning("Failed to retrieve track data, skipping.")
			continue
		create_track(db, track_data, seed_user_id)
		sys.stdout.write('.')
		sys.stdout.flush()
	sys.stdout.write('\n')
	
	neighbors_visited.add(seed_username)

	logging.info("Getting %s's friends." % seed_username)
	friends = seed.get_friends()
	inc_requests()

	for friend in friends:
		retries = MAX_RETRIES
		while retries > 0:
			try:
				user_data = build_user_data(friend)
				friend_user_id = create_user(db, user_data)
				
				create_friendship(db, seed_user_id, friend_user_id)

				try:
					logging.info("Getting %s's recent tracks." % user_data["name"])
					recent_tracks = friend.get_recent_tracks()
					inc_requests()
					for played_track in recent_tracks:
						track_data = build_track_data(played_track)
						create_track(db, track_data, friend_user_id)
						sys.stdout.write('.')
						sys.stdout.flush()
					sys.stdout.write('\n')
					neighbors_visited.add(user_data["name"])
				except pylast.WSError:
					logging.warning("Skipping recent tracks for user %s" % user_data["name"])
				retries = 0
			except Exception as ex:
				logging.error("%s (retry %d)" % (str(ex), MAX_RETRIES - retries + 1))
				retries -= 1
	
	return neighbors_visited


#
# =x= MAIN =x=
#

if len(sys.argv) < 2:
	print("Usage: %s lastfm-crawler.config" % os.path.basename(sys.argv[0]))
	sys.exit(0)

config = {}

for line in open(sys.argv[1], 'r'):
	line = line.strip()
	(key, value) = line.split('=')
	config[key] = value

logging.info("Connecting to Last.fm network.")
network = pylast.LastFMNetwork(
		api_key = config["API_KEY"],
		api_secret = config["API_SECRET"],
		username = config["USERNAME"],
		password_hash = config["PASSWORD_MD5"])

logging.info("Creating SQLite database schema.")
db = sqlite3.connect(config["SQLITE_DB"])
create_schema(db)

seed_users.add(config["SEED_USERNAME"])

while len(users_expanded) < LIMIT and len(seed_users) > 0:
	start_user = seed_users.pop()
	if start_user in users_expanded: continue
	seed_users = seed_users.union(crawl_user_neighborhood(db, start_user))
	users_expanded.add(start_user)

db.close()
