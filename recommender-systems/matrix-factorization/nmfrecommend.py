#!/usr/bin/python
# -*- coding: utf8 -*-
#
# nmfrecommend.py
# José Devezas (joseluisdevezas@gmail.com)
# 2013-06-28

import os
import sys
import argparse
from nmfrecommender import NmfRecommender

if __name__ == "__main__":
	parser = argparse.ArgumentParser(
			description='Recommend new items to an existing user ordered by predicted rating.')
	parser.add_argument('user',
			help='user identification string, as defined in the training set')
	parser.add_argument('model_path',
			help='HDF5 file with the trained model containing the factorized matrices')
	args = parser.parse_args()
	
	model = NmfRecommender(args.model_path)

	rank = 1
	for rec in model.recommend(args.user)[0:20]:
		print "%d\t%7.2f\t%s" % ((rank, ) + rec)
		rank += 1
