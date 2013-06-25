#!/usr/bin/python
# -*- coding: utf8 -*-
#
# nmfpredict.py
# José Devezas (joseluisdevezas@gmail.com)
# 2013-06-25


import os
import sys
from nmfrecommender import NmfRecommender

if __name__ == "__main__":
	if len(sys.argv) < 3:
		print("%s <user-id> <item-id>" % os.path.basename(sys.argv[0]))
		sys.exit(0)

	model = NmfRecommender("/Users/jldevezas/Desktop/nmfmodel.h5")
	print model.predict(sys.argv[1], sys.argv[2])
