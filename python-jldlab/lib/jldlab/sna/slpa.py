#!/usr/bin/python
# -*- coding: utf8 -*-
#
# slpa.py
# José Devezas (joseluisdevezas@gmail.com)
# 2013-08-28

import logging
import random
import pymongo
from pymongo import MongoClient

class SLPA:
	def __init__(self, host=None, db='jldlabgraph', nodes_collection='nodes', edges_collection='edges',
			labels_property='labels', communities_property='communities', order_property='order'):
		logging.basicConfig(format='%(levelname)s %(asctime)s %(message)s',
				datefmt='%Y-%m-%d %H:%M:%S', level=logging.INFO)

		con = MongoClient(host)
		self.nodes = con[db][nodes_collection]
		self.edges = con[db][edges_collection]

		self.labels_property = labels_property
		self.communities_property = communities_property
		self.order_property = order_property

	def _initialization(self):
		logging.info("Initialization: setting node labels to their own ID")
		for node in self.nodes.find():
			node[self.labels_property] = [node['_id']]
			self.nodes.save(node)
		logging.info("Initialization: done")

	def _speaker_rule(self, node):
		"""
		Returns a random label with probability proportional to the occurrence frequency
		of this label in the node's memory (label_property). Note that a repeated label
		is more probably of being returned, which is exactly what we want.
		"""
		return random.choice(node[self.labels_property])

	def _listener_rule(self, label_list):
		"""
		Returns the most frequent label from the label_list. This label_list must have been
		created using the _speaker_rule and thus should contain speaker labels.
		"""
		return max(set(label_list), key=label_list.count)

	def _evolution(self, T):
		self.nodes.ensure_index([(self.order_property, pymongo.ASCENDING)])

		logging.info("Evolution: doing {0} iterations".format(T))
		for t in range(T):
			logging.info("Evolution: iteration {0}".format(t+1))

			logging.info("Evolution: generating a random number attribute to shuffle order")
			for node in self.nodes.find():
				node[self.order_property] = random.random()
				self.nodes.save(node)
			logging.info("Evolution: node order has been shuffled")

			logging.info("Evolution: randomly iterating through listeners and propagating labels " +
					"from their speakers")
			for listener in self.nodes.find().sort(self.order_property, pymongo.ASCENDING):
				label_list = []
				for speaker in self.nodes.find({ '_id': { '$in': listener['neighbors'] } }):
					label_list.append(self._speaker_rule(speaker))
				w = self._listener_rule(label_list)
				listener[self.labels_property].append(w)
				self.nodes.save(listener)
			logging.info("Evolution: Speaker-listener Label Propagation done")

	def _post_processing(self, r):
		logging.info("Post-processing: getting communities by removing labels with probability < r={0}".format(r))
		for node in self.nodes.find():
			node[self.communities_property] = [label for label in set(node[self.labels_property])
					if node[self.labels_property].count(label) / float(len(node[self.labels_property])) >= r]
			self.nodes.save(node)
		logging.info("Post-processing: communities obtained")

	def run(self, T=20, r=0.05):
		self._initialization()
		self._evolution(T)
		self._post_processing(r)

