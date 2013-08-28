#!/usr/bin/python
# -*- coding: utf8 -*-
#
# load_graph.py
# José Devezas (joseluisdevezas@gmail.com)
# 2013-08-28

from jldlab.sna import MongoGraph

g = MongoGraph()
g.load_from_csv("/Users/jldevezas/Desktop/lastfm-jld-dataset/lastfm-friends.csv")
