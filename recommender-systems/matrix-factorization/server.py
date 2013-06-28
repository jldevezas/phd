#!/usr/bin/python
# -*- coding: utf8 -*-
#
# server.py
# José Devezas (joseluisdevezas@gmail.com)
# 2013-06-28

import sys
from flask import Flask
from flask import jsonify
from flask import g
from nmfrecommender import NmfRecommender

app = Flask(__name__)
model_path = None

@app.route("/api/recommend/<user_id>")
def recommend(user_id):
	model = NmfRecommender(model_path)

	recs = []
	rank = 1
	for rec in model.recommend(user_id)[0:20]:
		recs.append({ 'rank': rank, 'score': rec[0], 'artist': rec[1] })
		rank += 1

	return jsonify(recommendations=recs)

if __name__ == '__main__':
	model_path = sys.argv[1]
	app.run(debug=True)
