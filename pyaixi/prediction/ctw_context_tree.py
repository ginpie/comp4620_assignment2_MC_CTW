#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Define classes to implement context trees according to the Context Tree Weighting algorithm.
"""

from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import math
import random

# Ensure xrange is defined on Python 3.
from six.moves import xrange

# The value ln(0.5).
# This value is used often in computations and so is made a constant for efficiency reasons.
log_half = math.log(0.5)

class CTWContextTreeNode:
	""" The CTWContextTreeNode class represents a node in an action-conditional context tree.


		The purpose of each node is to calculate the weighted probability of observing
		a particular bit sequence.

		In particular, denote by `n` the current node, by `n0` and `n1`  the child nodes,
		by `h_n` the subsequence of the history relevant to node `n`, and by `a`
		and `b` the number of zeros and ones in `h_n`.

		Then the weighted block probability of observing `h_n` at node `n` is given by

		  P_w^n(h_n) :=
  
			Pr_kt(h_n)                        (if n is a leaf node)
			1/2 Pr_kt(h_n) +
			1/2 P_w^n0(h_n0) P_w^n1(h_n1)     (otherwise)

		where `Pr_kt(h_n) = Pr_kt(a, b)` is the Krichevsky-Trofimov (KT) estimator defined by the relations

		  Pr_kt(a + 1, b) = (a + 1/2)/(a + b + 1) Pr_kt(a, b)

		  Pr_kt(a, b + 1) = (b + 1/2)/(a + b + 1) Pr_kt(a, b)

		and the base case

		  Pr_kt(0, 0) := 1


		In both relations, the fraction is referred to as the update multiplier and corresponds to the
		probability of observing a zero (first relation) or a one (second relation) given we have seen
		`a` zeros and `b` ones.

		Due to numerical issues, the implementation uses logarithmic probabilities
		`log(P_w^n(h_n))` and `log(Pr_kt(h_n)` rather than normal probabilities.

		These probabilities are recalculated during updates (`update()`)
		and reversions (`revert()`) to the context tree that involves the node.

		- The KT estimate is accessed and stored using `log_kt`.
		  It is updated from the previous estimate by multiplying with the update multiplier as
		  calculated by `log_kt_multiplier()`.

		- The weighted probability is access and stored using `log_probability`.
		  It is recalculated by `update_log_probability()`.

		In order to calculate these probabilities, `CTWContextTreeNode` also stores:

		- Links to child nodes: `children`

		- The number of symbols (zeros and ones) in the history subsequence relevant to the
		  node: `symbol_count`.


		The `CTWContextTreeNode` class is tightly coupled with the `ContextTree` class.

		Briefly, the `ContextTree` class:

		- Creates and deletes nodes.

		- Tells the appropriate nodes to update/revert their probability estimates.

		- Samples actions and percepts from the probability distribution specified
		  by the nodes.
	"""

	# Instance methods.

	def __init__(self, tree = None):
		""" Construct a node of the context tree.
		"""

		# The children of this node.
		self.children = {}

		# The tree object associated with this node.
		self.tree = tree

		# The cached KT estimate of the block log probability for this node.
		# This value is computed only when the node is changed by the update or revert methods.
		self.log_kt = 0.0

		# The cached weighted log probability for this node.
		# This value is computed only when the node is changed by the update or revert methods.
		self.log_probability = 0.0

		# The count of the symbols in the history subsequence relevant to this node.
		self.symbol_count = {0: 0, 1: 0}
	# end def

	def is_leaf_node(self):
		""" Return True if the node is a leaf node, False otherwise.
		"""

		# If this node has no children, it's a leaf node.
		return self.children == {}
	# end def

	def log_kt_multiplier(self, symbol):
		""" Returns the logarithm of the KT-estimator update multiplier.

		   The log KT estimate of the conditional probability of observing a zero given
		   we have observed `a` zeros and `b` ones at the current node is

			 log(Pr_kt(0 | 0^a 1^b)) = log((a + 1/2)/(a + b + 1))

		   Similarly, the estimate of the conditional probability of observing a one is

			 log(Pr_kt(1 |0^a 1^b)) = log((b + 1/2)/(a + b + 1))

		   - `symbol`: the symbol for which to calculate the log KT estimate of
			 conditional probability.
			 0 corresponds to calculating `log(Pr_kt(0 | 0^a 1^b)` and
			 1 corresponds to calculating `log(Pr_kt(1 | 0^a 1^b)`.
		"""

		# TODO(DONE): implement

		a = self.symbol_count[0]
		b = self.symbol_count[1]
		if symbol == 0:
			log_kt = math.log((a + 1 / 2) / (a + b + 1))
		else:
			log_kt = math.log((b + 1 / 2) / (a + b + 1))

		return log_kt
	# end def

	def revert(self, symbol):
		""" Reverts the node to its state immediately prior to the last update.
			This involves updating the symbol counts, recalculating the cached
			probabilities, and deleting unnecessary child nodes.

			- `symbol`: the symbol used in the previous update.
		"""

		# TODO(DONE): implement

		if self.symbol_count[symbol] >= 1:
			self.symbol_count[symbol] -= 1

		self.log_kt -= self.log_kt_multiplier(symbol)

		if symbol in self.children and self.children[symbol].visits() == 0:
			del self.children[symbol]
			self.tree.tree_size -= 1

		self.update_log_probability()
	# end def

	def size(self):
		""" The number of descendants of this node.
		"""

		# Iterate over the direct children of this node, collecting the size of each sub-tree.
		return 1 + sum([child.size() for child in self.children.values()])
	# end def

	def update(self, symbol):
		""" Updates the node after having observed a new symbol.
			This involves updating the symbol counts and recalculating the cached probabilities.

			- `symbol`: the symbol that was observed.
		"""

		# TODO(DONE): implement

		self.symbol_count[symbol] += 1
		# log[Pr_kt(a + 1, b)] = log[(a + 1 / 2) / (a + b + 1)] + log[Pr_kt(a, b)]
		# log[Pr_kt(a, b + 1)] = log[(b + 1 / 2) / (a + b + 1)] + log[Pr_kt(a, b)]
		self.log_kt = self.log_kt_multiplier(symbol)
		self.update_log_probability()


	# end def

	def update_log_probability(self):
		""" This method calculates the logarithm of the weighted probability for this node.

			Assumes that `log_kt` and `log_probability` is correct for each child node.

			  log(P^n_w) :=
				  log(Pr_kt(h_n)            (if n is a leaf node)
				  log(1/2 Pr_kt(h_n)) + 1/2 P^n0_w x P^n1_w)
											(otherwise)
			and stores the value in log_probability.

			Because of numerical issues, the implementation works directly with the
			log probabilities `log(Pr_kt(h_n)`, `log(P^n0_w)`,
			and `log(P^n1_w)` rather than the normal probabilities.

			To compute the second case of the weighted probability, we use the identity

				log(a + b) = log(a) + log(1 + exp(log(b) - log(a)))       a,b > 0

			to rearrange so that logarithms act directly on the probabilities:

				log(1/2 Pr_kt(h_n) + 1/2 P^n0_w P^n1_w) =

					log(1/2) + log(Pr_kt(h_n))
					  + log(1 + exp(log(P^n0_w) + log(P^n1_w)
									- log(Pr_kt(h_n)))

					log(1/2) + log(P^n0_w) + log(P^n1_w)
					  + log(1 + exp(log(Pr_kt(h_n)
										   - log(P^n0_w) + log(P^n1_w)))

			In order to avoid overflow problems, we choose the formulation for which
			the argument of the exponent `exp(log(b) - log(a))` is as small as possible.
		"""

		# TODO(DONE): implement

		pr = 0
		# log(P^n_w) := log(Pr_kt(h_n)            (if n is a leaf node)
		if self.is_leaf_node():
			pr = self.log_kt
		# log(P^n_w) := log(1/2 Pr_kt(h_n)) + 1/2 P^n0_w x P^n1_w)      (if n is NOT a leaf node)
		else:
			pn01 = 0
			for key, child in self.children.items():
				pn01 += child.log_probability

			# choose smaller b to avoid overflow
			a = max(pr, pn01)
			b = min(pr, pn01)

			pr = log_half + a + math.log(1 + math.exp(b-a))

		self.log_probability = pr
	# end def

	def visits(self):
		""" Returns the number of times this context has been visited.
			This is the sum of the visits of the (immediate) child nodes.
		"""

		return self.symbol_count[0] + self.symbol_count[1]
	# end def
# end class


class CTWContextTree:
	""" The high-level interface to an action-conditional context tree.
		Most of the mathematical details are implemented in the CTWContextTreeNode class, which is used to
		represent the nodes of the tree.
		CTWContextTree stores a reference to the root node of the tree (`root`), the history of
		updates to the tree (`history`), and the maximum depth of the tree (`depth`).

		It is primarily concerned with calling the appropriate functions in the appropriate nodes
		in order to deliver certain functionality:

		- `update(symbol_or_list_of_symbols)` updates the tree and the history
		  after the agent has observed new percepts.

		- `update_history(symbol_or_list_of_symbols)` updates just the history
		  after the agent has executed an action.

		- `revert()` reverts the last update to the tree.

		- `revert_history()` deletes the recent history.

		- `predict()` predicts the probability of future outcomes.

		- `generate_random_symbols_and_update()` samples a sequence from the
		   context tree, updating the tree with each symbol as it is sampled.

		- `generate_random_symbols()` samples a sequence of a specified length,
		   updating the tree with each symbol as it is sampled, then reverting all the
		   updates so that the tree is in the same state as it was before the
		   sampling.
	"""

	def __init__(self, depth):
		""" Create a context tree of specified maximum depth.
			Nodes are created as needed.

			- `depth`: the maximum depth of the context tree.
		"""

		# An list used to hold the nodes in the context tree that correspond to the current context.
		# It is important to ensure that `update_context()` is called before accessing the contents
		# of this list as they may otherwise be inaccurate.
		self.context = []

		# The maximum depth of the context tree.
		assert depth >= 0, "The given tree depth must be greater than zero."
		self.depth = depth

		# The history (a list) of symbols seen by the tree.
		self.history = []

		# The root node of the context tree.
		self.root = CTWContextTreeNode(tree = self)

		# The size of this tree.
		self.tree_size = 1
	# end def

	def clear(self):
		""" Clears the entire context tree including all nodes and history.
		"""

		# Reset the history.
		self.history = []

		# Set a new root object, and reset the tree size.
		self.root.tree = None
		del self.root
		self.root = CTWContextTreeNode(tree = self)
		self.tree_size = 1

		# Reset the context.
		self.context = []
	# end def

	def generate_random_symbols(self, symbol_count):
		""" Returns a symbol string of a specified length by sampling from the context tree.

			- `symbol_count`: the number of symbols to generate.
		"""
		symbol_list = self.generate_random_symbols_and_update(symbol_count)
		self.revert(symbol_count)

		return symbol_list
	# end def

	def generate_random_symbols_and_update(self, symbol_count):
		""" Returns a specified number of random symbols distributed according to
			the context tree statistics and update the context tree with the newly
			generated symbols.

			- `symbol_count`: the number of symbols to generate.
		"""

		# TODO: implement

		symbol_list = []
		for i in range(0, symbol_count):
			if random.randint(0, 1) >= self.predict([1]):
				next_symbol = 1
			else:
				next_symbol = 0
			symbol_list.append(next_symbol)
			self.update([next_symbol])

		return symbol_list
	# end def

	def predict(self, symbol_list):
		""" Returns the conditional probability of a symbol (or a list of symbols), considering the history.

			Given a history sequence `h` and a symbol `y`, the estimated probability is given by

			  rho(y | h) = rho(hy)/rho(h)

			where `rho(h) = P_w^epsilon(h)` is the weighted probability estimate of observing `h`
			evaluated at the root node `epsilon` of the context tree.

			- `symbol_list` The symbol (or list of symbols) to estimate the conditional probability of.
							0 corresponds to `rho(0 | h)` and 1 to `rho(1 | h)`.
		"""

		# TODO: implement

		# rho(h)
		pw_h = self.root.log_probability

		# add y to h to produce rho(hy)
		self.update(symbol_list)
		pw_hy = self.root.log_probability

		# revert y from h
		self.revert(len(symbol_list))

		# return rho(hy)/rho(h) => exp(pw_hy) / exp(pw_h)
		return math.exp(pw_hy - pw_h)
	# end def

	def revert(self, symbol_count = 1):
		""" Restores the context tree to its state prior to a specified number of updates.

			- `num_symbols`: the number of updates (symbols) to revert. (Default of 1.)
		"""

		# TODO: implement

		for i in range(0, symbol_count):

			# symbol count to revert should never exceeds length of history in practice, hence we shouldn't need to
			# particularly handle for boundary case
			symbol = self.history[len(self.history) - 1 - i]

			self.update_context()

			# nodes in self.context are in order of parent -> children, we need to revert children then parent
			for n in reversed(self.context):
				n.revert(symbol)

			# revert the symbol from history
			self.revert_history()

	# end def

	def revert_history(self, symbol_count = 1):
		""" Shrinks the history without affecting the context tree.
		"""

		assert symbol_count > 0, "The given symbol count should be greater than 0."
		history_length = len(self.history)
		assert history_length >= symbol_count, "The given symbol count must be greater than the history length."

		new_size = history_length - symbol_count
		self.history = self.history[:new_size]
	# end def

	def size(self):
		""" Returns the number of nodes in the context tree.
		"""

		# Return the value stored and updated by the children nodes.
		return self.tree_size
	# end def

	def update(self, symbol_list):
		""" Updates the context tree with a new (binary) symbol, or a list of symbols.
			Recalculates the log weighted probabilities and log KT estimates for each affected node.

			- `symbol_list`: the symbol (or list of symbols) with which to update the tree.
							  (The context tree is updated with symbols in the order they appear in the list.)
		"""

		# TODO: implement

		# iterate through symbol
		for symbol in symbol_list:
			# for each symbol, go through context tree -> the path from root to leaf based on history and increase a or b for each node in path
			# i.e. if history is 01101, symbol is 1
			# we'll go through each node corresponds to 0, 01, 011, 0110, 01101 and increase their b value
			# this could be easily done through self.update_context() which returns the list of nodes in context
			self.update_context()
			for i in range(0, len(self.context)):
				# update leaf first, as Pw of parents depends on children
				n = self.context[len(self.context) - 1 - i]
				n.update(symbol)
			# insert the symbol to history before next round of process - this is important as context changes
			self.update_history([symbol])
	# end def

	def update_context(self):
		""" Calculates which nodes in the context tree correspond to the current
			context, and adds them to `context` in order from root to leaf.

			In particular, `context[0]` will always correspond to the root node
			and `context[self.depth]` corresponds to the relevant leaf node.

			Creates the nodes if they do not exist.
		"""
		# TODO: implement

		v = self.root
		self.context = [v]
		for i in range(0, self.depth):
			# handle corner case
			if i >= len(self.history):
				break

			# find the ith suffix in history string
			symbol = self.history[len(self.history) - 1 - i]
			# if node not exists, create it
			if symbol not in v.children:
				u = CTWContextTreeNode(self)
				v.children[symbol] = u
				self.tree_size += 1
			# else creates new node and add the the list
			v = v.children[symbol]
			self.context.append(v)

	# end def

	def update_history(self, symbol_list):
		""" Appends a symbol (or a list of symbols) to the tree's history without updating the tree.

			- `symbol_list`: the symbol (or list of symbols) to add to the history.
		"""

		# Ensure that we have a list, by making this a list if it's a single symbol.
		if type(symbol_list) != list:
			symbol_list = [symbol_list]
		# end if

		self.history += symbol_list
	# end def
# end class