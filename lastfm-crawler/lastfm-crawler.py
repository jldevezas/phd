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
usersExpanded = set([])
seedUsers = set([])


def incRequests():
	global requests
	requests += 1
	if requests % 5 == 0:
		logging.debug("Respecting the API rules, waiting 1 second between every 5 requests.")
		time.sleep(1)


def createSchema(db):
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


def createFriendship(db, firstUid, secondUid):
	c = db.cursor()

	c.execute("SELECT first_user_id, second_user_id FROM friends " +
			"WHERE (first_user_id = ? OR first_user_id = ?) AND " +
			"(second_user_id = ? OR second_user_id = ?)", (firstUid, secondUid, firstUid, secondUid))

	res = c.fetchone()
	if res != None: return

	c.execute("INSERT OR IGNORE INTO friends (first_user_id, second_user_id) VALUES(?,?)",
			(firstUid, secondUid))

	c.close()
	db.commit()
	
	logging.info("Created new friendship between users %d and %d" % (firstUid, secondUid))


def createUser(db, userData):
	c = db.cursor()

	c.execute("SELECT ROWID FROM users where name = ?", (userData["name"], ))
	res = c.fetchone()
	
	if res != None:
		c.close()
		return res[0]

	c.execute("INSERT OR IGNORE INTO users (name, age, gender, country, plays) VALUES(?,?,?,?,?)",
			(userData["name"], userData["age"], userData["gender"], userData["country"], userData["plays"]))

	db.commit()

	c.execute("SELECT last_insert_rowid()")
	userId = c.fetchone()[0]
	c.close()

	logging.info("Created new user with ID %d" % userId)

	return userId


def createTrack(db, trackData, userId):
	c = db.cursor()

	trackId = None
	try:
		c.execute("INSERT INTO tracks (lastfm_id, mbid, title, album, artist, timestamp, duration, plays, " +
				"listeners, user_id)" + "VALUES(?,?,?,?,?,?,?,?,?,?)",
				(trackData["id"], trackData["mbid"], trackData["title"], trackData["album"],
					trackData["artist"], trackData["timestamp"], trackData["duration"], trackData["plays"],
					trackData["listeners"], userId))
		c.execute("SELECT last_insert_rowid()")
		trackId = c.fetchone()[0]
	except sqlite3.IntegrityError:
		return

	for tagData in trackData["tags"]:
		(tag, weight) = tagData
		tag = tag.lower()

		c.execute("SELECT ROWID FROM tags WHERE name = ?", (tag,))
		res = c.fetchone()
		if res is None:
			c.execute("INSERT INTO tags (name) VALUES(?)", (tag,))
			c.execute("SELECT last_insert_rowid()")
			res = c.fetchone()
		
		tagId = res[0]
		c.execute("INSERT OR REPLACE INTO tracks_tags (track_id, tag_id, weight) VALUES (?,?,?)",
				(trackId, tagId, weight))

	db.commit()
	c.close()


def buildUserData(user):
	retries = MAX_RETRIES
	while retries > 0:
		try:
			userData = {}
			userData["name"] = user.get_name()
			userData["age"] = int(user.get_age())

			gender = user.get_gender()
			if gender == "Male":
				userData["gender"] = "m"
			elif gender == "Female":
				userData["gender"] = "f"
			else:
				userData["gender"] = None

			country = user.get_country()
			if country is None or country.get_name() is None:
				userData["country"] = None
			else:
				userData["country"] = country.get_name().lower()

			userData["plays"] = int(user.get_playcount())
			incRequests()
			return userData
		except Exception as ex:
			logging.error("%s (buildUserData retry %d)" % (str(ex), MAX_RETRIES - retries + 1))
			retries -= 1
	return None


def buildTrackData(playedTrack):
	retries = MAX_RETRIES
	while retries > 0:
		try:
			track = playedTrack.track

			trackData = {}

			# track.getInfo
			trackData["title"] = track.get_title()

			album = track.get_album()
			if album is None:
				trackData["album"] = None
			else:
				trackData["album"] = album.get_title()

			artist = track.get_artist()
			if artist is None:
				trackData["artist"] = None
			else:
				trackData["artist"] = artist.get_name()

			trackData["id"] = track.get_id()
			trackData["mbid"] = track.get_mbid()
			trackData["duration"] = track.get_duration()
			trackData["plays"] = track.get_playcount()
			trackData["listeners"] = track.get_listener_count()
			trackData["timestamp"] = int(playedTrack.timestamp)
			incRequests()

			# track.getTopTags
			trackData["tags"] = [(t.item.get_name().lower(), int(t.weight))
					for t in track.get_top_tags() if t.weight != "0"]
			incRequests()
			return trackData
		except Exception as ex:
			logging.error("%s (buildTrackData retry %d)" % (str(ex), MAX_RETRIES - retries + 1))
			retries -= 1
	return None


def crawlUserNeighborhood(db, seedUsername):
	neighborsVisited = set([])

	seed = network.get_user(seedUsername)
	userData = buildUserData(seed)
	
	if userData is None:
		logging.warning("Failed to retrieve user %s data, skipping." % seedUsername)
		return neighborsVisited

	seedUserId = createUser(db, userData)

	logging.info("Getting %s's recent tracks." % seedUsername)
	recentTracks = seed.get_recent_tracks()
	incRequests()
	for playedTrack in recentTracks:
		trackData = buildTrackData(playedTrack)
		if trackData is None:
			logging.warning("Failed to retrieve track data, skipping.")
			continue
		createTrack(db, trackData, seedUserId)
		sys.stdout.write('.')
		sys.stdout.flush()
	sys.stdout.write('\n')
	
	neighborsVisited.add(seedUsername)

	logging.info("Getting %s's friends." % seedUsername)
	friends = seed.get_friends()
	incRequests()

	for friend in friends:
		retries = MAX_RETRIES
		while retries > 0:
			try:
				userData = buildUserData(friend)
				friendUserId = createUser(db, userData)
				
				createFriendship(db, seedUserId, friendUserId)

				try:
					logging.info("Getting %s's recent tracks." % userData["name"])
					recentTracks = friend.get_recent_tracks()
					incRequests()
					for playedTrack in recentTracks:
						trackData = buildTrackData(playedTrack)
						createTrack(db, trackData, friendUserId)
						sys.stdout.write('.')
						sys.stdout.flush()
					sys.stdout.write('\n')
					neighborsVisited.add(userData["name"])
				except pylast.WSError:
					logging.warning("Skipping recent tracks for user %s" % userData["name"])
				retries = 0
			except Exception as ex:
				logging.error("%s (retry %d)" % (str(ex), MAX_RETRIES - retries + 1))
				retries -= 1
	
	return neighborsVisited


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
createSchema(db)

seedUsers.add(config["SEED_USERNAME"])

while len(usersExpanded) < LIMIT and len(seedUsers) > 0:
	startUser = seedUsers.pop()
	if startUser in usersExpanded: continue
	seedUsers = seedUsers.union(crawlUserNeighborhood(db, startUser))
	usersExpanded.add(startUser)

db.close()
