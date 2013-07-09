#!/usr/bin/python
# -*- coding: utf8 -*-
#
# nn.py
# José Devezas (joseluisdevezas@gmail.com)
# 2013-07-09


import os
import sys
import argparse
from jld import LatentFactorsModel

def csv(value):
	return value.split(',')

if __name__ == "__main__":
	parser = argparse.ArgumentParser(
			description="Discover nearest neighbor in trained model based on qualitative user input.")
	parser.add_argument('model_path',
			help="HDF5 file with the trained model containing the factorized matrices")
	parser.add_argument('--love', type=csv,
			help="Comma-separated item IDs for loved items.")
	parser.add_argument('--like', type=csv,
			help="Comma-separated item IDs for liked items.")
	parser.add_argument('--neutral', type=csv,
			help="Comma-separated item IDs for neutral items.")
	parser.add_argument('--dislike', type=csv,
			help="Comma-separated item IDs for disliked items.")
	parser.add_argument('--hate', type=csv,
			help="Comma-separated item IDs for hated items.")
	args = parser.parse_args()
	
	model = LatentFactorsModel(args.model_path)

	tastes = {}
	if args.love is not None:
		for item in args.love:
			tastes[item] = 1.0
	if args.like is not None:
		for item in args.like:
			tastes[item] = 0.75
	if args.neutral is not None:
		for item in args.neutral:
			tastes[item] = 0.5
	if args.dislike is not None:
		for item in args.dislike:
			tastes[item] = 0.25
	if args.hate is not None:
		for item in args.hate:
			tastes[item] = 0.0

	nn = model.nearest_neighbor(tastes)

	print "Recommendations for most similar user: %s" % nn[0]

	rank = 1
	for item_id, rating in model.recommend(nn[0], limit=20, all=True):
		print "%d\t%.10f\t%s" % (rank, rating, item_id)
		rank += 1
