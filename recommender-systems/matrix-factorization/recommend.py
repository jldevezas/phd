#!/usr/bin/python
# -*- coding: utf8 -*-
#
# recommend.py
# José Devezas (joseluisdevezas@gmail.com)
# 2013-06-28

import os
import sys
import argparse
from engine import Engine

if __name__ == "__main__":
	parser = argparse.ArgumentParser(
			description='Recommend new items to an existing user ordered by predicted rating.')
	parser.add_argument('user',
			help='user identification string, as defined in the training set')
	parser.add_argument('model_path',
			help='HDF5 file with the trained model containing the factorized matrices')
	args = parser.parse_args()
	
	model = Engine(args.model_path)

	rank = 1
	for item_id, rating in model.recommend(args.user, limit=20):
		print "%d\t%.10f\t%s" % (rank, rating, item_id)
		rank += 1
