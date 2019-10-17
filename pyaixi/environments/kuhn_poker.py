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
kuhn_observation_enum = util.enum('oPJ', 'oPQ', 'oPK', 'oBJ', 'oBQ', 'oBK')

# define cards
kuhn_card_enum = util.enum('J', 'Q', 'K')

# define rewards: there are fout rewards, and no draw
kuhn_reward_enum = util.enum(rLose2=0, rLose1=1, rWin1=3, rWin2=4)

aPass = kuhn_action_enum.aPass
aBet = kuhn_action_enum.aBet

oPJ = kuhn_observation_enum.oPJ
oPQ = kuhn_observation_enum.oPQ
oPK = kuhn_observation_enum.oPK
oBJ = kuhn_observation_enum.oBJ
oBQ = kuhn_observation_enum.oBQ
oBK = kuhn_observation_enum.oBK

J = kuhn_card_enum.J
Q = kuhn_card_enum.Q
K = kuhn_card_enum.K

rLose2 = kuhn_reward_enum.rLose2
rLose1 = kuhn_reward_enum.rLose1
rWin1 = kuhn_reward_enum.rWin1
rWin2 = kuhn_reward_enum.rWin2


class KuhnPoker(environment.Environment):
    # default_probability = 0.5

    def __init__(self, options={}):
        environment.Environment.__init__(self, options=options)

        self.valid_actions = list(kuhn_action_enum.keys())
        self.valid_observations = list(kuhn_observation_enum.keys())
        self.valid_rewards = list(kuhn_reward_enum.keys())
        self.agent_action = 0
        self.reward = 0
        self.opponent_init = 0

        self.game_reset()

    def perform_action(self, action):
        """ Receives the agent's action and calculates the new environment percept.
        """
        assert self.is_valid_action(action)

        # Save the action
        self.agent_action = action

        #                      /  Game start  \
        # Opponent:          pass            bet
        #                   /    \          /   \
        # Agent:        pass    bet       pass  bet
        #                 |    /   \        |    |
        # Opp/Res:      +-1  pass  bet     -1   +-2
        #                     |     |
        # Reward:            +1    +-2

        # opponent initially bets
        if self.opponent_action == aBet:
            # agent folds
            if self.agent_action == aPass:
                self.reward = rLose1
            # agent calls
            elif self.agent_action == aBet:
                self.reward = (rLose2 if self.smallerThan(self.agent_card, self.opponent_card) else rWin2)

        # opponent initially passes
        if self.opponent_action == aPass:
            # agent checks
            if self.agent_action == aPass:
                self.reward = (rLose1 if self.smallerThan(self.agent_card, self.opponent_card) else rWin1)
            # agent bets
            elif self.agent_action == aBet:
                # opponent calls or folds depending on his card
                # K must call
                if self.opponent_card == K:
                    self.opponent_action = aBet
                    self.reward = rLose2
                # J must fold
                elif self.opponent_card == J:
                    self.opponent_action = aPass
                    self.reward = rWin1
                # Q has a probability
                else:
                    if random.random() < self.pb:
                        self.opponent_action = aBet
                        self.reward = (rLose2 if self.smallerThan(self.agent_card, self.opponent_card) else rWin2)
                    else:
                        self.opponent_action = aPass
                        self.reward = rWin1

        # print("agent card: ", self.agent_card)
        # print("opponent card: ", self.opponent_card)
        # print("opponent initial: ", self.opponent_init)
        # print("agent action: ", self.agent_action)
        # print("opponent action: ", self.opponent_action)
        # print("reward: ", self.reward)

        obser = self.observation
        self.game_reset()

        return obser, self.reward
    # end def

    def smallerThan(self, card1, card2):
        if card1 == 0:
            return True
        elif card1 == 2:
            return False

        if card2 == 0:
            return False
        elif card2 == 2:
            return True
    # end def

    def print(self):
        """ Returns a string indicating the status of the environment.
        """
        message = "Prediction: " + \
                  "Agent has %s" % self.agent_card + ", opponent has %s" % self.opponent_card + "\n" + \
                  "Opponent decides to %s" % ("bet" if self.opponent_action == "aBet" else "pass") + \
                  ", agent decides to %s" % ("bet" if self.agent_action == "aBet" else "pass") + "\n" + \
                  "Result: " + \
                  "agent " + ("wins" if self.reward == rWin1 or self.reward == rWin2 else "loses") + \
                  ", reward: " + self.reward - 2

        return message
    # end def

    def game_reset(self):
        # shuffle
        self.dealer = random.sample([J, Q, K], 2)
        # deal
        self.agent_card = self.dealer[0]
        self.opponent_card = self.dealer[1]

        """
        Choose an initial action for the opponent:
        1. When having a Jack, opponent freely chooses the probability pj in [0,1/3]
           with which he will bet  (otherwise he checks; if the other player bets, he should always fold).
        2. When having a King, he should bet with the probability of 3 x pj  (otherwise he checks;
           if the other player bets, he should always call).
        3. When having a Queen he should always check, and if the other player bets after this check,
           he should call with the probability of pj + 1/3.
        """
        pj = 0.3
        pk = pj * 3
        pq = pj + 1.0/3.0
        self.pb = pj
        if self.opponent_card == Q:
            self.pb = pq
        elif self.opponent_card == K:
            self.pb = pk

        # initial action of opponent
        if self.opponent_card == Q:
            self.opponent_action = aPass
        elif random.random() > self.pb:
            self.opponent_action = aPass
        else:
            self.opponent_action = aBet

        self.opponent_init = self.opponent_action

        # observation of the agent is a concatenation of opponent_action and agent_card
        # self.observation = self.opponent_action + self.agent_card
        if self.agent_card == J:
            if self.opponent_action == aPass:
                self.observation = oPJ
            else:
                self.observation = oBJ
        elif self.agent_card == Q:
            if self.opponent_action == aPass:
                self.observation = oPQ
            else:
                self.observation = oBQ
        elif self.agent_card == K:
            if self.opponent_action == aPass:
                self.observation = oPK
            else:
                self.observation = oBK
        # self.observation = self.agent_card *10 + (oPass if (self.opponent_action == aPass) else oBet)

# end class
