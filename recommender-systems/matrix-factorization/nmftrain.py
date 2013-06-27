#!/usr/bin/python
# -*- coding: utf8 -*-
#
# nmftrain.py
# José Devezas (joseluisdevezas@gmail.com)
# 2013-06-14

import os
import sys
from nmfrecommender import NmfRecommender

if __name__ == "__main__":
	if len(sys.argv) < 3:
		print("%s <user-item-rating.csv> <model.h5>" % os.path.basename(sys.argv[0]))
		sys.exit(0)

	if not os.access(sys.argv[1], os.R_OK):
		print("'%s' is not readable." % sys.argv[1])
		sys.exit(0)

	model = NmfRecommender(sys.argv[2])

	# TODO Make parameters available as command line arguments.
	#model.train(sys.argv[1], sample_size=1000)
	model.train(sys.argv[1], delimiter=',')
