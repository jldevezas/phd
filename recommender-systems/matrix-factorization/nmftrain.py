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
	if len(sys.argv) < 2:
		print("%s <user-preferences.csv>" % os.path.basename(sys.argv[0]))
		sys.exit(0)

	if not os.access(sys.argv[1], os.R_OK):
		print("'%s' is not readable." % sys.argv[1])
		sys.exit(0)

	model = NmfRecommender("/Users/jldevezas/Desktop/nmfmodel.h5")
	model.train(sys.argv[1], 1000)
