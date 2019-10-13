#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Defines a class for the MC-AIXI-CTW agent.
"""

from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import copy
import os
import random
import sys

# Insert the package's parent directory into the system search path, so that this package can be
# imported when the aixi.py script is run directly from a release archive.
PROJECT_ROOT = os.path.realpath(os.path.join(os.pardir, os.pardir))
sys.path.insert(0, PROJECT_ROOT)

# Ensure xrange is defined on Python 3.
from six.moves import xrange

from pyaixi import agent, prediction, search, util

from pyaixi.agent import update_enum, action_update, percept_update
from pyaixi.prediction import ctw_context_tree
from pyaixi.search import monte_carlo_search_tree
from pyaixi.search.monte_carlo_search_tree import nodetype_enum, chance_node, decision_node, MonteCarloSearchNode


class MC_AIXI_CTW_Undo:
    """ A class to save details from a MC-AIXI-CTW agent to restore state later.
    """

    # Instance methods.

    def __init__(self, agent):
        """ Store values from the given agent that can be used to revert that agent to a previous state.
        """

        # Copy the main attributes of the given agent into this class.
        self.age = agent.age
        self.total_reward = agent.total_reward
        self.history_size = agent.history_size()
        self.last_update = agent.last_update
    # end def


# end class


class MC_AIXI_CTW_Agent(agent.Agent):
    """ This class represents a MC-AIXI-CTW agent.

        It includes much of the high-level logic for choosing suitable actions.
        In particular, the agent maintains an internal model of the environment using
        a context tree.

        It uses this internal model to to predict the probability of future outcomes:

         - `get_predicted_action_probability()`
         - `percept_probability()`

        as well as to generate actions and precepts according to the model distribution:

         - `generate_action()`
         - `gen_percept()`
         - `generate_percept_and_update()`
         - `generate_random_action()`

        Actions are chosen via the UCT algorithm, which is orchestrated by a
        high-level search function and a playout policy:

         - `search()`
         - `playout()`
         - `horizon`
         - `mc_simulations`
         - `search_tree`

        Several functions decode/encode actions and percepts between the
        corresponding types (i.e. `action_enum`, `percept_enum`) and generic
        representation by symbol lists:

         - `decode_action()`
         - `decode_observation()`
         - `decode_percept()`
         - `decode_reward()`
         - `encode_action()`
         - `encode_percept()`

        There are various attributes which describe the agent and its
        interaction with the environment so far:

         - `age`
         - `average_reward`
         - `history_size()`
         - `horizon`
         - `last_update`
         - `maximum_action()`
         - `maximum_bits_needed()`
         - `maximum_reward()`
         - `total_reward`
    """

    # Instance methods.

    def __init__(self, environment=None, options={}):
        """ Construct a MC-AIXI-CTW learning agent from the given configuration values and the environment.

             - `environment` is an instance of the pyaixi.Environment class that the agent with interact with.
             - `options` is a dictionary of named options and their values.

            `options` must contain the following mandatory options:
             - `agent-horizon`: the agent's planning horizon.
             - `ct-depth`: the depth of the context tree for this agent, in symbols/bits.
             - `mc-simulations`: the number of simulations to run when choosing new actions.

            The following options are optional:
             - `learning-period`: the number of cycles the agent should learn for.
                                  Defaults to '0', which is indefinite learning.
        """

        # Set up the base agent options, which handles getting and setting the learning period, amongst other basic values.
        agent.Agent.__init__(self, environment=environment, options=options)

        # The agent's context tree depth.
        # Retrieved from the given options under 'ct-depth'. Mandatory.
        assert 'ct-depth' in options, \
            "The required 'ct-depth' context tree depth option is missing from the given options."
        self.depth = int(options['ct-depth'])

        # (CTW) Context tree representing the agent's model of the environment.
        # Created for this instance.
        self.context_tree = ctw_context_tree.CTWContextTree(self.depth)

        # The length of the agent's planning horizon.
        # Retrieved from the given options under 'agent-horizon'. Mandatory.
        assert 'agent-horizon' in options, \
            "The required 'agent-horizon' search horizon option is missing from the given options."
        self.horizon = int(options['agent-horizon'])

        # The number of simulations to conduct when choosing new actions via the UCT algorithm.
        # Retrieved from the given options under 'mc-simulations'. Mandatory.
        assert 'mc-simulations' in options, \
            "The required 'mc-simulations' Monte Carlo simulations count option is missing from the given options."
        self.mc_simulations = int(options['mc-simulations'])
        self.exploration_exploitation_rate = 0.01
        self.reset()

    # end def

    def decode_action(self, symbol_list):
        """ Returns the action decoded from the beginning of the given list of symbols.

            - `symbol_list`: the symbol list to decode the action from.
        """

        return util.decode(symbol_list, self.environment.action_bits())

    # end def

    def decode_observation(self, symbol_list):
        """ Returns the observation decoded from the given list of symbols.

            - `symbol_list`: the symbol list to decode the observation from.
        """

        return util.decode(symbol_list, self.environment.observation_bits())

    # end def

    def decode_reward(self, symbol_list):
        """ Returns the reward decoded from the beginning of the given list of symbols.

            - `symbol_list`: the symbol list to decode the reward from.
        """

        return util.decode(symbol_list, self.environment.reward_bits())

    # end def

    def decode_percept(self, symbol_list):
        """ Returns the percept (observation and reward) decoded from the beginning of
            the given list of symbols.

            - `symbol_list`: the symbol list to decode the percept from.
        """

        # Check if we've got exactly enough symbols.
        reward_bits = self.environment.reward_bits()
        observation_bits = self.environment.observation_bits()

        assert len(symbol_list) >= (reward_bits + observation_bits), \
            "The given symbol list isn't long enough to contain a percept."

        # Get the reward symbols from the given symbol list, starting with the
        # reward, then getting the observation from the list after that.
        reward_symbols = symbol_list[:reward_bits]
        observation_symbols = symbol_list[reward_bits:(reward_bits + observation_bits)]

        # Decode the obtained symbols.
        reward = self.decode_reward(reward_symbols)
        observation = self.decode_observation(observation_symbols)

        # Return the decoded percept as a tuple of observation and reward.
        return (observation, reward)

    # end def

    def encode_action(self, action):
        """ Returns the given action encoded as a list of symbols.

            - `action`: the action to encode.
        """

        return util.encode(action, self.environment.action_bits())

    # end def

    def encode_percept(self, observation, reward):
        """ Returns the given percept (an observation, reward part) as a list of symbols.

            - `observation`: the observation part of the percept to encode.
            - `reward`: the reward part of the percept to encode.
        """

        # Add first the encoded reward, then the encoded observation to the list of output symbols.
        symbol_list = util.encode(reward, self.environment.reward_bits())
        symbol_list += util.encode(observation, self.environment.observation_bits())

        # Return the generated list.
        return symbol_list

    # end def

    def generate_action(self):
        """ Returns an action generated according to the agent's history
            statistics by doing rejection sampling from the context tree.
        """

        # TODO: implement
        # sample from the context tree to get symbols of action
        samples = self.context_tree.generate_random_symbols(self.environment.action_bits())
        # decode the samples into actions
        action = self.decode_action((samples))
        return action

    # end def

    def generate_percept(self):
        """ Returns a percept (an observation, reward pair) distributed according to the agent's history
            statistics by sampling from the context tree.
        """

        # TODO: implement
        # sample from the context tree to get symbols of percept
        samples = self.context_tree.generate_random_symbols((self.environment.percept_bits()))
        # decode samples into percepts
        percept = self.decode_percept(samples)
        return percept

    # end def

    def generate_percept_and_update(self):
        """ Returns a percept (an observation, reward pair) distributed according to the agent's history
            statistics, after updating the context tree with it.
        """

        # TODO: implement
        # sample from the context tree to get the symbols of percept
        samples = self.context_tree.generate_random_symbols_and_update(self.environment.percept_bits())
        # get the observation and reward of the percept
        observation, reward = self.decode_percept(samples)
        # update observation and total reward
        self.last_update = percept_update
        self.total_reward += reward
        return (observation, reward)

    # end def

    def get_predicted_action_probability(self, action):
        """ Returns the probability of selecting a particular action according to the
            agent's internal model of its own behaviour.

            - `action`: the action we wish to find the likelihood of.
        """
        # TODO: implement
        # encode actions to get corresponding symbols
        action_symbols = self.encode_action(action)
        # get the probability of the action based on the context tree
        action_predicted = self.context_tree.predict(action_symbols)
        return action_predicted

    # end def

    def history_size(self):
        """ Returns the length of the stored history for an agent.
        """

        return len(self.context_tree.history)

    # end def

    def maximum_bits_needed(self):
        """ Returns the maximum number of bits needed to represent actions or percepts.
            NOTE: this is for binary alphabets.
        """

        return max(self.environment.action_bits(), self.environment.percept_bits())

    # end def

    def model_revert(self, undo_instance):
        """ Revert the agent's internal model of the world to that of a previous time cycle,
            using the given undo class instance.
        """

        # TODO: implement

        ''' context-tree branch implementation '''
        # revert CTW
        self.revert(self.history_size() - undo_instance.history_size, self.last_update)

        # revert other properties
        self.last_update = undo_instance.last_update
        self.age = undo_instance.age
        self.total_reward = undo_instance.total_reward

    def revert(self, number_of_reversion, update_type):
        # recursively revert CTW history
        if number_of_reversion != 0:
            self.context_tree.revert(self.environment.percept_bits() if update_type == percept_update
                                     else self.environment.action_bits())
            self.revert(number_of_reversion - 1, self.environment.action_bits() if update_type == percept_update
            else self.environment.percept_bits())

        ''' agent branch implementation '''
        # # deal with the new elements of history
        # while self.history_size() > undo_instance.history_size:
        #     # when the last update is action update
        #     if self.last_update == percept_update:
        #         self.context_tree.revert(self.environment.percept_bits())
        #         self.last_update = action_update
        #     # when the last update is percept update
        #     else:
        #         self.context_tree.revert_history(self.environment.action_bits())
        #         self.last_update = percept_update
        # # revert relevant attributes
        # self.age = undo_instance.age
        # self.total_reward = undo_instance.total_reward
        # self.last_update = undo_instance.last_update

    # end def

    def model_size(self):
        """ Returns the size of the agent's model.
        """
        return self.context_tree.size()

    # end def

    def model_update_action(self, action):
        """ Update the agent's model of the world with a percept from the
            environment.

            - `observation`: the observation that was received.
            - `reward`: the reward that was received.
        """

        # The last update must have been a percept, else this action update is invalid.
        assert self.environment.is_valid_action(action), "Invalid action given."
        assert self.last_update == percept_update, "Can only perform an action update after a percept update."

        # Update the agent's internal model of the world after performing an action.

        # Get the symbols that represent this action.
        action_symbols = self.encode_action(action)

        # Update the context tree.
        self.context_tree.update_history(action_symbols);

        # Update other properties.
        self.age += 1;
        self.last_update = action_update

    # end def

    def model_update_percept(self, observation, reward):
        """ Update the agent's model of the world with a percept from the
            environment.

            - `observation`: the observation that was received.
            - `reward`: the reward that was received.
        """

        # The last update must have been an action, else this percept update is invalid.
        assert self.last_update == action_update, "Can only perform a percept update after an action update."

        # Update the internal model after performing a percept.

        # Get the symbols that represent this percept from the given observation and reward.
        percept_symbols = self.encode_percept(observation, reward)

        # Are we still meant to be learning?
        if ((self.learning_period > 0) and (self.age > self.learning_period)):
            # No. Update, but don't learn.
            self.context_tree.update_history(percept_symbols)
        else:
            # Yes. Update and learn.
            self.context_tree.update(percept_symbols)
        # end if

        # Update other properties.
        self.total_reward += reward
        self.last_update = percept_update

    # end def

    def percept_probability(self, observation, reward):
        """ Returns the probability of receiving a particular percept
            (the given observation and reward) according to the agent's environment model.

            - `observation`: the observation part of the percept we wish to find the likelihood of.

            - `reward`: the reward part of the percept we wish to find the likelihood of.
        """

        # TODO: implement

        ''' context-tree branch implementation '''
        # symbols = self.encode_percept(observation, reward)
        # return self.context_tree.predict(symbols)

        ''' agent branch implementation '''
        # get the symbols of the (observation, reward) pair
        percept = self.encode_percept(observation, reward)
        # caculate the probability
        probability = self.context_tree.predict(percept)
        return probability

    # end def

    def playout(self, horizon):
        """ Simulate agent/enviroment interaction for a specified amount of steps
            (the given horizon value) where the agent actions are chosen uniformly
            at random and percepts are generated.

            Returns the total reward from the simulation.

            - `horizon`: the number of complete action/percept steps
                         (the search horizon) to simulate.
        """

        # TODO: implement

        # implemented as per Algorithm 4 from https://arxiv.org/pdf/0909.0801.pdf, Veness et al. 2009
        # initialize the total reward
        total_reward = 0.

        # caculate all reward in horizon
        for i in xrange(horizon):
            # genarate an antion randomly
            action = self.generate_random_action()
            # update the model
            self.model_update_action(action)
            # get the percept
            observation, reward = self.generate_percept_and_update()
            # update the total reward
            total_reward += reward

        return total_reward

    # end def

    def reset(self):
        """ Resets the agent and clears the context tree.
        """

        # Reset the context tree.
        self.context_tree.clear()

        # Reset the basic agent details.
        agent.Agent.reset(self)

    # end def

    def search(self):
        """ Returns the best action for this agent as determined using the Monte-Carlo Tree Search
            (predictive UCT).
        """
        # Use rhoUCT to search for the next action.

        # TODO: implement

        ''' context-tree branch implementation '''
        # construct an MCT
        mct = MonteCarloSearchNode(decision_node)

        # backup agent state in undo
        backup = MC_AIXI_CTW_Undo(self)

        # run simulations to train MCT
        for i in [0, self.mc_simulations]:
            mct.sample(self, self.horizon)
            # revert agent state after each trajectory is sampled so that MCT always start from the same root node
            self.model_revert(backup)

        # sample the best action from MCT
        return mct.select_action(self)

        ''' agent branch implementation '''
        # # store the state now
        # now = MC_AIXI_CTW_Undo(self)
        # # initialize a new tree and update
        # new = monte_carlo_search_tree.MonteCarloSearchNode(decision_node)
        # for i in xrange(self.mc_simulations):
        #     new.sample(self, self.horizon)
        #     self.model_revert(now)
        # # initialize the best action as a random chosen one and the best mean to be 0
        # best_action = self.generate_random_action()
        # best_mean = 0
        # # check all the possoble actions
        # for action in self.environment.valid_actions:
        #     # if action is available for the present node, update, or do nothing
        #     if action in new.children:
        #         # update mean with reward of exploration
        #         mean = new.children[action].mean + (random.random()*self.exploration_exploitation_rate)
        #         # update the best action and corresponding reward if updated mean is larger than the old best one
        #         if mean > best_mean:
        #             best_mean = mean
        #             best_action = action
        # return best_action

    # end def
# end class
