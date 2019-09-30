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
kuhn_observation_enum = util.enum('oPass', 'oBet', 'pot2', 'pot3', 'pot4',
                                  'showdown', 'go_on',
                                  'K', 'Q', 'J', 'unknown')
                                  # 'oK', 'oQ', 'oJ', 'aK', 'aQ', 'aJ',)

# define rewards: lose one chip when the agent put one chip and lose(lose1),
# lose two chips when the agent bets and lose(lose2),
# win one(win1) or two(win2) chips when the opponent puts one or two chips and the agent wins
kuhn_reward_enum = util.enum('lose2', 'lose1', 'win1', 'win2')
# kuhn_reward_enum = util.enum(-2, -1, 2, 3, 4)

# similarly define the opponent
# kuhn_action_enum = util.enum('oPass', 'oBet')
# kuhn_op_observation_emum = util.enum('no','aPass', 'aBet', 'pot2', 'pot3', 'pot4',
#                                   'showdown', 'go_on',
#                                   'K', 'Q', 'J', 'unknown')
# kuhn_reward_enum = util.enum('lose2', 'lose1', 'win1', 'win2')


aPass = kuhn_action_enum.aPass
aBet = kuhn_action_enum.aBet

oPass = kuhn_observation_enum.oPass
oBet = kuhn_observation_enum.oBet

pot2 = kuhn_observation_enum.pot2
pot3 = kuhn_observation_enum.pot3
pot4 = kuhn_observation_enum.pot4

showdown = kuhn_observation_enum.showdown
go_on = kuhn_observation_enum.go_on

K = kuhn_observation_enum.K
Q = kuhn_observation_enum.Q
J = kuhn_observation_enum.J
unknown = kuhn_observation_enum.unknown

lose2 = kuhn_reward_enum.lose2
lose1 = kuhn_reward_enum.lose1
win1 = kuhn_reward_enum.win1
win2 = kuhn_reward_enum.win2


class KuhnPoker(environment.Environment):

    def __init__(self, options={}):
        environment.Environment.__init__(self.options = options)

        self.valid_actions = list(kuhn_action_enum.keys())
        self.valid_obeservations = list(kuhn_observation_enum.keys())
        self.valid_rewards = list(kuhn_reward_enum.keys())
        
        # initialize the observation and reward with blinds
        # the length of observation is five: the last action of the opponent , the value of the pot,
        # the card hold by the agent, the card hold by the opponent, whether the play showdown or go_on
        self.observation = [random.sample([oPass,oBet]), pot2, random.sample([K,Q,J]), unknown, go_on]
        self.reward = lose1

    def opponent_action(self, action):



    def perform_action(self, action):
        """ Receives the agent's action and calculates the new environment percept.
        """

        assert self.is_valid_action(action)
        assert (self.observation[3]==unknown and self.observation[4]==go_on) \
               or (self.observation[3] == K and self.observation[4] == showdown) \
               or (self.observation[3] == Q and self.observation[4] == showdown) \
               or (self.observation[3] == J and self.observation[4] == showdown)
        assert self.observation[2] != self.observation[3]

        # Save the action.
        self.action = action

		# different situations
        if oPass in self.observation[0]:
            if self.action == aPass:
                if self.observation[2]==K:
                    self.reward = win2
                elif self.observation[2]==Q:
                    self.reward = 0.5 * (win1 + lose1)
                else:
                    self.reward = lose1
            else:
                if self.observation[2]==K:
                    self.reward = win2
                elif self.observation[2]==Q:
                    self.reward = 0.5 * (win2 + lose2)
                
        else:
            # self.observation[1] = pot3
            if self.action == aBet:
                if self.observation[2]==K:
                    self.reward = win2
                elif self.observation[2]==Q:
                    self.reward = 0.5 * (win2 + lose2)
                else:
                    self.reward = lose2
            else:
                self.reward = lose1

        return (self.observation, self.reward)
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