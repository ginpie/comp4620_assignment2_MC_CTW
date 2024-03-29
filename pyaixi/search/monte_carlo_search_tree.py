#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Define a class to implement a Monte Carlo search tree.
"""

from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os
import math
import random
import sys

# Insert the package's parent directory into the system search path, so that this package can be
# imported when the aixi.py script is run directly from a release archive.
PROJECT_ROOT = os.path.realpath(os.path.join(os.pardir, os.pardir))
sys.path.insert(0, PROJECT_ROOT)

from pyaixi import util

# An enumeration type used to specify the type of Monte Carlo search node.
# Chance nodes represent a set of possible observation
# (one child per observation) while decision nodes
# represent sets of possible actions (one child per action).
# Decision and chance nodes alternate.
nodetype_enum = util.enum('chance', 'decision')

# Define some short cuts for ease of reference.
chance_node = nodetype_enum.chance
decision_node = nodetype_enum.decision

class MonteCarloSearchNode:
    """ A class to represent a node in the Monte Carlo search tree.
        The nodes in the search tree represent simulated actions and percepts
        between an agent following an upper confidence bounds (UCB) policy and a generative
        model of the environment represented by a context tree.

        The purpose of the tree is to determine the expected reward of the
        available actions through sampling. Sampling proceeds several time steps
        into the future according to the size of the agent's horizon.
        (`MC_AIXI_CTW_Agent.horizon`)
 
        The nodes are one of two types (`nodetype_enum`), decision nodes are those
        whose children represent actions from the agent and chance nodes are those
        whose children represent percepts from the environment.

        Each MonteCarloSearchNode maintains several bits of information:

          - The current value of the sampled expected reward
            (`MonteCarloSearchNode.mean`, `MonteCarloSearchNode.expectation`).

          - The number of times the node has been visited during the sampling
            (`MonteCarloSearchNode.visits`).

          - The type of the node (MonteCarloSearchNode.type).

          - The children of the node (`MonteCarloSearchNode.children`).
            The children are stored in a dictionary indexed by action (if
            it is a decision node) or percept (if it is a chance node).

        The `MonteCarloSearchNode.sample` method is used to sample from the current node and
        the `MonteCarloSearchNode.selectAction` method is used to select an action according
        to the UCB policy.
    """

    # Class attributes.

    # Exploration constant for the UCB action policy.
    exploration_constant = 2.0

    # Unexplored action bias.
    unexplored_bias = 1000000000.0

    # Instance methods.

    def __init__(self, nodetype):
        """ Create a new search node of the given type.
        """

        # The children of this node.
        # The symbols used as keys at each level may be either action or observation,
        # depending on what type of node this is.
        self.children = {}

        # The sampled expected reward of this node.
        self.mean = 0.0

        # The type of this node indicates whether its children represent actions
        # (decision node) or percepts (chance node).
        assert nodetype in nodetype_enum, "The given value %s is a not a valid node type." % str(nodetype)
        self.type = nodetype

        # The number of times this node has been visited during sampling.
        self.visits = 0
    # end def

    def sample(self, agent, horizon):
        """ Returns the accumulated reward from performing a single sample on this node.

            - `agent`: the agent doing the sampling

            - `horizon`: how many cycles into the future to sample
        """

        # TODO: implement

        # Initialise reward value
        reward = 0.0
        
        if (horizon == 0):
            # Reach the horizon
            # Return 0
            return reward

        # Check if Psi(h) is a chance node
        elif(self.type == chance_node):
            # Reach a chance node

            # Update the context tree history and generate observation and reward
            # Generate (o, r) from rho(or|h)
            (o, r) = agent.generate_percept_and_update()

            # Check if T(hor) = 0
            if o not in self.children:
                # T(hor) = 0
                # Not explored, generate a decision child node
                # Create node Psi(hor)
                self.children[o] = MonteCarloSearchNode(decision_node)

            # Recursively search until the horizon to get the reward
            # reward <- r+sample(Psi, hor, m-1)
            reward = r + self.children[o].sample(agent, horizon-1)

        # Check if T(h) = 0
        elif(self.visits == 0):
            # T(h) = 0
            # Use rollout to estimate the reward
            # reward <- rollout(h, m)
            reward = agent.playout(horizon)

        else:
            # Select the action according to UCB policy
            # a <- selectaction(Psi, h)
            a = self.select_action(agent)

            # Update agent's model
            agent.model_update_action(a)

            # Check if T(ha) = 0
            if a not in self.children:
                # T(ha) = 0
                # Not explored, generate a chance child node
                # Create node Psi(ha)
                self.children[a] = MonteCarloSearchNode(chance_node)

            # Recursively search to get the reward
            # reward <- r+sample(Psi, ha, m)
            reward = self.children[a].sample(agent, horizon)

        # Calculate mean reward
        # V(h) <- (reward + T(h)V(h)) / (T(h) + 1)
        self.mean = (reward + (float(self.visits) * self.mean)) / (float(self.visits) + 1.0)
        
        # Update visits number
        # T(h) <- T(h) + 1
        self.visits += 1

        return reward
    # end def

    def select_action(self, agent):
        """ Returns an action selected according to UCB policy.

             - `agent`: the agent which is doing the sampling.
        """

        # TODO: implement
        best_action = None
        best_score = 0 # current the score of the best action
        
        nevertry=[] # unexplored nodes
        
        for action in agent.environment.valid_actions:
            score = 0
            if action not in self.children: # find all the unexplored nodes
                nevertry.append(action)
                best_score=self.unexplored_bias
            if len(nevertry)>0: # determine if U == {}
                continue
            else:
                minterval=agent.horizon*(agent.maximum_reward()-agent.minimum_reward()) #m(b-a)
                score = (self.children[action].mean)/(minterval)+self.unexplored_bias*math.sqrt(math.log(self.visits)/self.children[action].visits)
                #calculate the whole value of it 
                if score > best_score: # arg max
                    best_action = action
                    best_score = score
        if len(nevertry)>0:
            return random.choice(nevertry) # pick a uniformly at random 
        else:
            return best_action
        return best_action
    # end def
# end class