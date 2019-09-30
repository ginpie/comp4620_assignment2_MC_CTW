#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Defines an environment for a 1D maze.
This module is modified from coin_flip.py.
Author: Haotian Weng (u6254332)
"""

from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os
import random
import sys

# Insert the package's parent directory into the system search path, so that this package can be
# imported when the aixi.py script is run directly from a release archive.
PROJECT_ROOT = os.path.realpath(os.path.join(os.pardir, os.pardir))
sys.path.insert(0, PROJECT_ROOT)

from pyaixi import environment, util

# Define a enumeration to represent the agent's actions, which is a choice between left or right.
oned_maze_action_enum = util.enum('aLeft', 'aRight')

# As the agent's observations are uninformative, the observation is defined as goal or non-goal instead of location.
oned_maze_observation_enum = util.enum('oGoal', 'oNonGoal')

# Define a enumeration to represent the agent's rewards e.g. 1 or 0, for reaching the goal point.
oned_maze_reward_enum = util.enum('rOne', 'rZero')

# Define the locations of the cells in the 1D maze.
locs = [0, 1, 2, 3]

# Define some shorthand notation for ease of reference.
aLeft = oned_maze_action_enum.aLeft
aRight = oned_maze_action_enum.aRight

oGoal = oned_maze_observation_enum.oGoal
oNonGoal = oned_maze_observation_enum.oNonGoal

rOne = oned_maze_reward_enum.rOne
rZero = oned_maze_reward_enum.rZero

class OneDMaze(environment.Environment):
    """ The agent travels in the 1d-maze and receives a reward of 1 if it reaches the third cell from the left.
        
        Domain characteristics:

        - environment: "oned_maze"
        - maximum action: 1 (1 bit)
        - maximum observation: 1 (1 bit)
        - maximum reward: 1 (1 bit)

        Configuration options:
        - Not Applicable
    """

    # Instance methods.

    def __init__(self, options = {}):
        """ Construct the OneDMaze environment from the given options.

             - `options` is a dictionary of named options and their values.

            options are not applicable in this environment.
        """

        # Set up the base environment.
        environment.Environment.__init__(self, options = options)

        # Define the acceptable action values.
        self.valid_actions = list(oned_maze_action_enum.keys())

        # Define the acceptable observation values.
        self.valid_observations = list(oned_maze_observation_enum.keys())

        # Define the acceptable reward values.
        self.valid_rewards = list(oned_maze_reward_enum.keys())

        # Set an initial percept.
        self.loc = random.choice(locs)
        self.observation = oNonGoal
        self.reward = 0
    # end def

    def perform_action(self, action):
        """ Receives the agent's action and calculates the new environment percept.
        """

        assert self.is_valid_action(action)

        # Save the action.
        self.action = action

        if (action == aLeft and self.loc > 0):
            self.loc = self.loc-1
        elif (action == aRight and self.loc < 3):
            self.loc = self.loc+1

        if (self.loc == 2):
            observation = oGoal
            reward = rOne
        else:
            observation = oNonGoal
            reward = rZero

        # Store the observation and reward in the environment.
        self.observation = observation
        self.reward = reward

        return (observation, reward)
    # end def

    def print(self):
        """ Returns a string indicating the status of the environment.
        """

        message = "action: " + \
                  ("left" if self.action == aLeft else "right") + \
                  ("goal" if self.observation == oGoal else "non-goal") + \
                  ", reward: %d" % self.reward

        return message
    # end def
# end class
