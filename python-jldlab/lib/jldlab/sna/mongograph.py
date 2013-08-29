#!/usr/bin/python
# -*- coding: utf8 -*-
#
# mongograph.py
# José Devezas (joseluisdevezas@gmail.com)
# 2013-08-28

import csv
import logging
import pymongo
from pymongo import MongoClient

class MongoGraph():
	def __init__(self, host=None, db='jldlabgraph', nodes_collection='nodes', edges_collection='edges'):
		logging.basicConfig(format='%(levelname)s %(asctime)s %(message)s',
				datefmt='%Y-%m-%d %H:%M:%S', level=logging.INFO)

		con = MongoClient(host)

		self.nodes = con[db][nodes_collection]
		self.nodes.ensure_index('id')

		self.edges = con[db][edges_collection]
		self.edges.ensure_index([('source', pymongo.ASCENDING), ('target', pymongo.ASCENDING)])

	def node(self, node_id):
		node = self.nodes.find_one({ 'id': node_id })
		if node is None:
			_id = self.nodes.insert({ 'id': node_id })
			node = self.nodes.find_one({ '_id': _id })
		return node

	def edge(self, source_node, target_node):
		edge = self.edges.find_one({ '$or': [
				{ 'source': source_node['_id'], 'target': target_node['_id'] },
				{ 'source': target_node['_id'], 'target': source_node['_id'] }
			]
		})

		if edge is None:
			_id = self.edges.insert({ 'source': source_node['_id'], 'target': target_node['_id'] })
			edge = self.edges.find_one({ '_id': _id })

		return edge

	def _add_edge_to_node(self, edge, node):
		if not 'edges' in node:
			node['edges'] = [edge['_id']]
		elif not edge['_id'] in node['edges']:
			node['edges'].append(edge['_id'])
		self.nodes.save(node)

	def _add_neighbor_to_node(self, neighbor, node):
		if not 'neighbors' in node:
			node['neighbors'] = [neighbor['_id']]
		elif not neighbor['_id'] in node['neighbors']:
			node['neighbors'].append(neighbor['_id'])
		self.nodes.save(node)

	def load_from_csv(self, path, delimiter=',', header=True):
		logging.info("Loading graph data as edge list from {0}".format(path))

		with open(path, 'rb') as f:
			reader = csv.reader(f, delimiter=delimiter)
			if header: next(reader)
			row_counter = 0
			for row in reader:
				if len(row) < 2: raise Exception("Row has less than two columns")
				source_node = self.node(row[0])
				target_node = self.node(row[1])
				
				edge = self.edge(source_node, target_node)

				# For index-free adjacency, which hopefuly replicates a graph database's behavior
				self._add_neighbor_to_node(source_node, target_node)
				self._add_neighbor_to_node(target_node, source_node)
				self._add_edge_to_node(edge, source_node)
				self._add_edge_to_node(edge, target_node)
				
				row_counter += 1
				if row_counter % 500 == 0:
					logging.info("{0} rows read".format(row_counter))

			logging.info("Graph loaded into MongoDB")

