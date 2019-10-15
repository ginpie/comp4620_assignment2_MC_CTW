from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from pyaixi import environment, util

import os
import random
import sys

# Insert the package's parent directory into the system search path, so that this package can be
# imported when the aixi.py script is run directly from a release archive.
PROJECT_ROOT = os.path.realpath(os.path.join(os.pardir, os.pardir))
sys.path.insert(0, PROJECT_ROOT)


tiger_action_enum = util.enum('aListen', 'aLeft', 'aRight')
tiger_observation_enum = util.enum('oLeft', 'oRight', 'oTiger', 'oGold', 'oNone')

# tiger normalised from -100 to 0, gold from 10 to 110, listen from -1 to 99
tiger_reward_enum = util.enum(rTiger=0, rGold=110, rListen=99)

aListen = tiger_action_enum.aListen
aLeft = tiger_action_enum.aLeft
aRight = tiger_action_enum.aRight

oLeft = tiger_observation_enum.oLeft
oRight = tiger_observation_enum.oRight
oTiger = tiger_observation_enum.oTiger
oGold = tiger_observation_enum.oGold
oNone = tiger_observation_enum.oNone

rTiger = tiger_reward_enum.rTiger
rGold = tiger_reward_enum.rGold
rListen = tiger_reward_enum.rListen

class Tiger(environment.Environment):


	listen_probability = 0.85

	def __init__(self, options={}):
		environment.Environment.__init__(self, options=options)
		# Define the acceptable action values.
		self.valid_actions = list(tiger_action_enum.keys())

		# Define the acceptable observation values.
		self.valid_observations = list(tiger_observation_enum.keys())

		# Define the acceptable reward values.
		self.valid_rewards = list(tiger_reward_enum.keys())

		# Define the winning action/losing action
		rand = random.random()

		self.winning_action = aLeft if rand < 0.5 else aRight
		self.losing_action = aRight if rand < 0.5 else aLeft

		self.listen_observation = [oLeft if self.winning_action == aLeft else oRight, oRight if self.winning_action == aLeft else oLeft]

		# Set an initial percept.
		self.observation = oNone
		self.reward = 0

	# end def

	def perform_action(self, action):
		""" Receives the agent's action and calculates the new environment percept.
		"""

		assert self.is_valid_action(action)

		# Save the action.
		self.action = action

		# handle listen action
		if action == tiger_action_enum.aListen:
			if random.random() < self.listen_probability:
				observation = self.listen_observation[0]
			else:
				observation = self.listen_observation[1]
			reward = rListen

		# handle open door actions
		elif action == self.winning_action:
			observation = oGold
			reward = rGold

		else:
			observation = oTiger
			reward = rTiger

		# Store the observation and reward in the environment.
		self.observation = observation
		self.reward = reward

		return observation, reward

	# end def

	def print(self):
		""" Returns a string indicating the status of the environment.
		"""

		message = "observation: {}, , reward: {}".format(self.observation, self.reward)

		return message
# end def
# end class