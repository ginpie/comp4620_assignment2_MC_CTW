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
kuhn_observation_action_enum = util.enum('oPass', 'oBet', 'pot')
kuhn_observation_card_enum = util.enum('K', 'Q', 'J')

# define rewards: lose one chip when the game is initialized or the agent bets,
# when the agent wins or loses, the reward is positive or negative value of pot
kuhn_reward_enum = util.enum('rChip')
# kuhn_reward_enum = util.enum('rChip', 'pot')

aPass = kuhn_action_enum.aPass
aBet = kuhn_action_enum.aBet

oPass = kuhn_observation_action_enum.oPass
oBet = kuhn_observation_action_enum.oBet
pot = kuhn_observation_action_enum.pot
K = kuhn_observation_card_enum.K
Q = kuhn_observation_card_enum.Q
J = kuhn_observation_card_enum.J

rChip = kuhn_reward_enum.rChip


class KuhnPoker(environment.Environment):
    default_probability = 0.5

    def __init__(self, options={}):
        environment.Environment.__init__(self, options=options)

        self.valid_actions = list(kuhn_action_enum.keys())
        self.valid_obeservations_action = list(kuhn_observation_action_enum.keys())
        self.valid_obeservations_card = list(kuhn_observation_card_enum.keys())
        # dealing. the first card is for the agent, and the second card is for the opponent
        self.dealer = random.sample(self.valid_obeservations_card, 2)
        self.valid_rewards = list(kuhn_reward_enum.keys())
        self.action = random.sample([aPass, aBet])
        self.oppo_action = random.sample([oPass, oBet])
        # the agent gets the first card
        self.card = self.dealer[0]
        # now the agent can't see the card hold by the opponent. assigned when showtown
        self.oppo_card = self.dealer[1]
        self.showdown = False
        # the next action the opponent might take. if it adopts Nash strategy, the second action of the opponent is
        # always pass, but it will be assigned only in one condition: when the first action of the opponent is
        # pass and the action of the agent is bet
        self.next_step = None

        # initialize the observation and reward with blinds.
        # [0:the agent's action, 1:the agent's card, 2:the opponent's action, 3:the opponent's card, 4:the next action
        # of the opponent, 5:whether showdown]
        self.observation = [self.action, self.card, self.oppo_action, None, self.next_step, self.showdown]
        # self.observation = [self.action, self.pot, self.card, self.oppo_action, self.oppo_card, self.showdown]
        self.reward = -rChip
        # self.pot = 2 * rChip

    def perform_action(self, action):
        """ Receives the agent's action and calculates the new environment percept.
        """

        assert self.is_valid_action(action)
        # assert self.card != self.oppo_card
        # assert self.shownown == True and self.oppo_card != None and self.oppo_action !=None
        # assert self.shownown == False and self.oppo_card == None and self.oppo_action == None

        # define the strategy of the opponent
        def oppo_action(self, oppo_card):
            if oppo_card == K:
                return 'oBet'
            else:
                return 'oPass'

        # Save the action
        self.action = action

        # if the opponent pass
        if self.oppo_action == oPass:
            # if the agent pass
            if self.action == aPass:
                # showndown and assign value to opponent action & card
                self.showdown = True
                self.observation[3] = self.oppo_card
                # if hold K, win
                if self.card == K:
                    if self.oppo_card == Q:
                        self.reward = rChip
                    if self.oppo_card == J:
                        self.reward = rChip
                #  if hold Q
                if self.card == Q:
                    if self.oppo_card == K:
                        self.reward = rChip
                    if self.oppo_card == J:
                        self.reward = rChip
                #  if hold J
                if self.card == Q:
                    if self.oppo_card == K:
                        self.reward = -rChip
                    if self.oppo_card == Q:
                        self.reward = -rChip
            # if the agent bets
            else:
                # if the opponent pass, win
                if oppo_action(self.oppo_card) == oPass:
                    self.reward = rChip
                # if the opponent bet
                else:
                    self.showdown = True
                    self.observation[3] = self.oppo_card
                    # if hold K, win
                    if self.card == K:
                        if self.oppo_card == Q:
                            self.reward = 2*rChip
                        if self.oppo_card == J:
                            self.reward = 2*rChip
                    #  if hold Q
                    if self.card == Q:
                        if self.oppo_card == K:
                            self.reward = -2*rChip
                        if self.oppo_card == J:
                            self.reward = 2*rChip
                    #  if hold J
                    if self.card == Q:
                        if self.oppo_card == K:
                            self.reward = -2*rChip
                        if self.oppo_card == Q:
                            self.reward = -2*rChip

        # if the opponent bet
        else:
            # if the agent bet
            self.showdown = True
            self.observation[3] = self.oppo_card
            if self.action == aBet:
                # showndown and assign value to opponent action & card
                self.showdown = True
                self.observation[3] = self.oppo_card
                # if hold K, win
                if self.card == K:
                    if self.oppo_card == Q:
                        self.reward = 2*rChip
                    if self.oppo_card == J:
                        self.reward = 2*rChip
                #  if hold Q
                if self.card == Q:
                    if self.oppo_card == K:
                        self.reward = 2*rChip
                    if self.oppo_card == J:
                        self.reward = -2*rChip
                #  if hold J
                if self.card == Q:
                    if self.oppo_card == K:
                        self.reward = -2*rChip
                    if self.oppo_card == Q:
                        self.reward = -2*rChip
            # if the agent passes, lose
            else:
                self.reward = -rChip

        return (self.observation, self.reward)

    # end def

    def print(self):
        """ Returns a string indicating the status of the environment.
        """

        message = "prediction: " + \
                  ("pass" if self.action == aPass else "bet") + \
                  ", observation: " + \
                  ("the opponent passes" if self.observation[0] == oPass else "the opponent bets") + \
                  ("the pot is {}" % (self.observation[1])) + \
                  ("I hold {}" % (self.observation[2])) + \
                  ", reward: %d" % self.reward

        return message
    # end def
# end class