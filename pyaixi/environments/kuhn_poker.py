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

# define actions
kuhn_action_enum = util.enum('aPass', 'aBet')

# define observations 
kuhn_observation_enum = util.enum('oPass', 'oBet', 'oK', 'oQ', 'oJ')

# define rewards: there are fout rewards, and no draw
kuhn_reward_enum = util.enum(rLose2=0, rLose1=1, rWin1=3, rWin2=4)

aPass = kuhn_action_enum.aPass
aBet = kuhn_action_enum.aBet

oPass = kuhn_observation_enum.oPass
oBet = kuhn_observation_enum.oBet
K = kuhn_observation_enum.oK
Q = kuhn_observation_enum.oQ
J = kuhn_observation_enum.oJ

rLose2 = kuhn_reward_enum.rLose2
rLose1 = kuhn_reward_enum.rLose1
rWin1 = kuhn_reward_enum.rWin1
rWin2 = kuhn_reward_enum.rWin2


class KuhnPoker(environment.Environment):
    # default_probability = 0.5

    def __init__(self, options={}):
        environment.Environment.__init__(self, options=options)

        self.valid_actions = list(kuhn_action_enum.keys())
        self.valid_obeservations = list(kuhn_observation_enum.keys())
        self.valid_rewards = list(kuhn_reward_enum.keys())
        self.reward = 0
        
        # dealing. the first card is for the agent, and the second card is for the opponent
        self.dealer = random.sample(self.valid_observations[2:4], 2)
        # the agent gets the first card
        self.card = self.dealer[0]
        # now the agent can't see the card hold by the opponent. assigned when showtown
        self.oppo_card = self.dealer[1]
        self.showdown = False
        # the second action the opponent might take. if it adopts Nash strategy, the second action of the opponent is
        # always pass, but it will be assigned only in one condition: when the first action of the opponent is
        # pass and the action of the agent is bet
        self.next_step = None

        # initialize the observation and reward with blinds.
        # [0:the agent's action,
        #  1:the agent's card,
        #  2:the opponent's action,
        #  3:the opponent's card,
        #  4:the next action of the opponent,
        #  5:whether showdown]
        self.observation = [self.action, self.card, None, None, self.next_step, self.showdown]
        # initialize gamma in Nash strategy
        self.gamma = 0.5
        self.reset()
    def perform_action(self, action):
        """ Receives the agent's action and calculates the new environment percept.
        """

        assert self.is_valid_action(action)
        # assert self.card != self.oppo_card
        # assert self.shownown == True and self.oppo_card != None and self.oppo_action !=None
        # assert self.shownown == False and self.oppo_card == None and self.oppo_action == None

        # define a function to choose one action with given probability
        def random_action(action_list, probability_list):
            index = random.uniform(0,1)
            assert len(action_list)==len(probability_list)
            assert sum(probability_list) == 1
            for i in range(len(action_list)):
                if index >= probability_list[i] and index < probability_list[i+1]:
                    return action_list[i]

        # define the strategy of the opponent
        def oppo_first_action(self, oppo_card):
            if oppo_card == K:
                return random_action([oBet, oPass], [self.gamma, 1-self.gamma])
            elif oppo_card == Q:
                return 'oPass'
            else:
                alpha = self.gamma/3
                return random_action([oBet, oPass], [alpha, 1-alpha])

        def oppo_second_action(self):
            beta = (1+self.gamma)/3
            return random_action([oBet, oPass], [beta, 1-beta])

        # Save the action
        self.action = action
        oppo_action = oppo_first_action(self, self.oppo_card)
        self.observation[2] = oppo_action

        # if the opponent pass
        if oppo_action == oPass:
            # if the agent pass
            if self.action == aPass:
                # showndown and assign value to opponent action & card
                self.showdown = True
                self.observation[3] = self.oppo_card
                # if hold K, win
                if self.card == K:
                    if self.oppo_card == Q:
                        self.reward = rWin1
                    if self.oppo_card == J:
                        self.reward = rWin1
                #  if hold Q
                if self.card == Q:
                    if self.oppo_card == K:
                        self.reward = rLose1
                    if self.oppo_card == J:
                        self.reward = rWin1
                #  if hold J
                if self.card == Q:
                    if self.oppo_card == K:
                        self.reward = -rLose1
                    if self.oppo_card == Q:
                        self.reward = -rLose1
            # if the agent bets
            else:
                second_action = oppo_second_action()
                # if the opponent pass, win
                if second_action == oPass:
                    self.reward = rWin1
                # if the opponent bet
                else:
                    self.showdown = True
                    self.observation[3] = self.oppo_card
                    # if hold K, win
                    if self.card == K:
                        if self.oppo_card == Q:
                            self.reward = rWin2
                        if self.oppo_card == J:
                            self.reward = rWin2
                    #  if hold Q
                    if self.card == Q:
                        if self.oppo_card == K:
                            self.reward = rLose2
                        if self.oppo_card == J:
                            self.reward = rWin2
                    #  if hold J
                    if self.card == Q:
                        if self.oppo_card == K:
                            self.reward = rLose2
                        if self.oppo_card == Q:
                            self.reward = rLose2

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
                        self.reward = rWin2
                    if self.oppo_card == J:
                        self.reward = rWin2
                #  if hold Q
                if self.card == Q:
                    if self.oppo_card == K:
                        self.reward = rLose2
                    if self.oppo_card == J:
                        self.reward = rWin2
                #  if hold J
                if self.card == Q:
                    if self.oppo_card == K:
                        self.reward = rLose2
                    if self.oppo_card == Q:
                        self.reward = rLose2
            # if the agent passes, lose
            else:
                self.reward = rLose1

        return (self.observation, self.reward)

    # end def

    def print(self):
        """ Returns a string indicating the status of the environment.
        """

        message = "prediction: " + \
                  ("pass" if self.action == aPass else "bet") + \
                  ", observation: " + \
                  ("the opponent passes" if self.observation[0] == oPass else "the opponent bets") + \
                  ("I hold %s" % (self.observation[2])) + \
                  ", reward: %d" % self.reward

        return message
    # end def

    def reset(self):
        self.observation = [None, None, None, None, None, False]
        self.reward = None
# end class