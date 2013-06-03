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

requests = 0


def incRequests():
	global requests
	requests += 1
	if requests % 5 == 0:
		print("Respecting the API rules, waiting 1 second between every 5 requests...")
		time.sleep(1)


if len(sys.argv) < 2:
	print("Usage: %s lastfm-crawler.config" % os.path.basename(sys.argv[0]))
	sys.exit(0)

config = {}

for line in open(sys.argv[1], 'r'):
	line = line.strip()
	(key, value) = line.split('=')
	config[key] = value

network = pylast.LastFMNetwork(
		api_key = config["API_KEY"],
		api_secret = config["API_SECRET"],
		username = config["USERNAME"],
		password_hash = config["PASSWORD_MD5"])

# XXX Check whether this fails in following attempts (if not new data is returned)
#network.enable_caching()

seed = network.get_user(config["SEED_USERNAME"])
friends = seed.get_friends()
incRequests()

for friend in friends:
	try:
		recentTracks = friend.get_recent_tracks()
		incRequests()

		for playedTrack in recentTracks:
			track = playedTrack.track
			trackData = {}
			trackData["title"] = track.get_title()
			trackData["album"] = track.get_album()
			trackData["artist"] = track.get_artist()
			trackData["timestamp"] = playedTrack.timestamp
			print(track)
			incRequests()
	except pylast.WSError as ex:
		print(ex)

	print(recentTracks)
