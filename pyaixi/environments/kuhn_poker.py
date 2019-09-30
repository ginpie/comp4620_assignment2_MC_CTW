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

# define actions: the agent passes or bets
kuhn_action_enum = util.enum('aPass', 'aBet')

# define observations: the opponent passes or bets, the pot, the card holded by the agent
# and the card hold by the opponent when showdown
kuhn_observation_enum = util.enum('oPass', 'oBet', 'pot', 'K', 'Q', 'J')

# define rewards: lose one chip when the game is initialized or the agent bets,
# when the agent wins or loses, the reward is positive or negative value of pot 
kuhn_reward_enum = util.enum('rChip', 'pot')

aPass = kuhn_action_enum.aPass
aBet = kuhn_action_enum.aBet

oPass = kuhn_observation_enum.oPass
oBet = kuhn_observation_enum.oBet
pot = kuhn_observation_enum.pot
K = kuhn_observation_enum.K
Q = kuhn_observation_enum.Q
J = kuhn_observation_enum.J

rChip = kuhn_reward_enum.rChip

class KuhnPoker(environment.Environment):
    default_probability = 0.5
    
    def __init__(self, options={}):
        environment.Environment.__init__(self.options = options)
        
        self.valid_actions = list(kuhn_action_enum.keys())
        self.valid_obeservations = list(kuhn_observation_enum.keys())
        self.valid_rewards = list(kuhn_reward_enum.keys())
        
        # initialize the observation and reward with blinds
        self.observation = [random.sample([oPass,oBet]), pot=2*rChip, random.sample([K,Q,J])]
        self.reward = -rChip
        
    def perform_action(self, action):
        """ Receives the agent's action and calculates the new environment percept.
        """

        assert self.is_valid_action(action)

        # Save the action.
        self.action = action

		# different situations
        if oPass in self.observation[0]:
            if self.action == aPass:
                if self.observation[2]==K:
                    self.reward += pot
                elif self.observation[2]==Q:
                    self.reward += default_probability*pot
                # else:
                    # self.reward += 0
            elif self.action == aBet:
                self.reward -= rChip
                if self.observation[2]==K:
                    self.reward += pot
                elif self.observation[2]==Q:
                    self.reward += default_probability*pot
                
        else:
            pot += rChip
             if self.action == aBet:
                self.reward = -rChip
                pot += rChip
                if self.observation[2]==K:
                    self.reward += pot
                elif self.observation[2]==Q:
                    self.reward += default_probability*pot
                # else:
                    # self.reward += 0
            # elif self.action == aPass:
                # self.reward += 0           

        # Store the observation and reward in the environment.
        self.observation = observation
        self.reward = reward

        return (observation, reward)
    # end def

    def print(self):
        """ Returns a string indicating the status of the environment.
        """

        message = "prediction: " + \
                  ("pass" if self.action == aPass else "bet") + \
                  ", observation: " + \
                  ("the opponent passes" if self.observation[0] == oPass else "the opponent bets") + \
                  ("the pot is {}"%(self.observation[1])) + \
                  ("I hold {}"%(self.observation[2])) + \
                  ", reward: %d" % self.reward

        return message
    # end def
# end class