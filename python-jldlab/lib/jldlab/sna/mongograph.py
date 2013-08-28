#!/usr/bin/python
# -*- coding: utf8 -*-
#
# mongograph.py
# José Devezas (joseluisdevezas@gmail.com)
# 2013-08-28

import csv
from pymongo import MongoClient

class MongoGraph():
	def __init__(self, host=None, db="jldlabgraph", nodes_collection="nodes", edges_collection="edges"):
		con = MongoClient(host)
		self.nodes = con[db][nodes_collection]
		self.edges = con[db][edges_collection]

	def node(self, node_id):
		node = self.nodes.find_one({ 'id': node_id })
		if node is None:
			_id = self.nodes.insert({ 'id': node_id })
			node = self.nodes.find_one({ '_id': _id })
		return node

	def edge(self, source_node, target_node):
		edge = self.edges.find_one({ 'source': source_node['_id'], 'target': target_node['_id'] })
		if edge is None:
			_id = self.edges.insert({ 'source': source_node['_id'], 'target': target_node['_id'] })
			edge = self.edges.find_one({ '_id': _id })
		return edge

	def load_from_csv(self, path, delimiter=',', header=True):
		with open(path, 'rb') as f:
			reader = csv.reader(f, delimiter=delimiter)
			if header: next(reader)
			for row in reader:
				if len(row) < 2:
					raise Exception("Row has less than two columns")
				source_node = self.node(row[0])
				target_node = self.node(row[1])
				self.edge(source_node, target_node)
