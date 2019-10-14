# -*- coding: utf-8 -*-
"""
Created on Sat Sep 28 18:50:40 2019

@author: Zhouyang Jiang
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

RPS_action_enum= util.enum('aRock', 'aPaper', 'aScissor')
RPS_observation_enum= util.enum('oRock', 'oPaper', 'oScissor')
RPS_reward_enum = util.enum('rLose','rDraw', 'rWin')



aRock=RPS_action_enum.aRock
aPaper=RPS_action_enum.aPaper
aScissor=RPS_action_enum.aScissor


oRock=RPS_observation_enum.oRock
oPaper=RPS_observation_enum.oPaper
oScissor=RPS_observation_enum.oScissor

#translate the rewards to the -1 0 1
'''
RPS_reward_enum.rLose=-1
RPS_reward_enum.rDraw=0
RPS_reward_enum.rWin=1
'''
rLose=RPS_reward_enum.rLose
rDraw=RPS_reward_enum.rDraw
rWin=RPS_reward_enum.rWin


class RPS(environment.Environment):
    """
        The agent repeatedly plays Rock-Paper-Scissor against an opponent that has a slight,
        predictable bias in its strategy. If the opponent has won a round by playing rock on
        the previous cycle, it will always play rock at the next time step; otherwise it will
        pick an action uniformly at random. The agent’s observation is the most recently
        chosen action of the opponent. It receives a reward of 1 for a win, 0 for a draw and
        -1 for a loss.
        
        Domain characteristics:

        - environment: "coin_flip"
        - maximum action: 3 (2 bit)
        - maximum observation: 3 (2 bit)
        - maximum reward: 3 (2 bit)
        
        Configuration options: None
    """
    
    
    
    def __init__(self, options = {}):
        # Set up the base environment.
        environment.Environment.__init__(self, options = options)
        # Define the acceptable action values.
        self.valid_actions = list(RPS_action_enum.keys())
        # Define the acceptable observation values.
        self.valid_observations = list(RPS_observation_enum.keys())
        # Define the acceptable reward values.
        self.valid_rewards = list(RPS_reward_enum.keys())
        self.observation = random.choice([oRock,oPaper,oScissor])
        self.reward = 0
        # end def
 
 
    def perform_action(self, action):
    
        """
        Receives the agent's action and calculates the new environment percept.
        """
         
        assert self.is_valid_action(action)
         
        # Save the action.
        self.action = action
        
        #the slight strategy of the opponent
        if self.reward==rLose :
            observation = self.observation
        else:
            observation = random.choice([oRock,oPaper,oScissor])
        
        #determine the result of the game and get the reward
        if action == aRock:
            if observation == oRock:
                reward= rDraw
            elif observation == oPaper:
                reward= rLose
            elif observation == oScissor:
                reward= rWin
        elif action == aPaper:
            if observation == oRock:
                reward= rWin
            elif observation == oPaper:
                reward= rDraw
            elif observation == oScissor:
                reward= rLose
        elif action == aScissor:
            if observation == oRock:
                reward= rLose
            elif observation == oPaper:
                reward= rWin
            elif observation == oScissor:
                reward= rDraw
         
         
        #Store the observation and reward in the environment.
        self.observation = observation
        
        self.reward = reward
        
        
        return (observation, reward)
        # end def
        
    def print(self):
        actionstring=''#translate the action
        if self.action==aRock:
            actionstring='Rock'
        elif self.action==aPaper:
            actionstring='Paper'
        elif self.action==aScissor:
            actionstring='Scissor'
        observationstring=''#translate the observation 
        if self.observation==oRock:
            observationstring='Rock'
        elif self.observation==oPaper:
            observationstring='Paper'
        elif self.observation==oScissor:
            observationstring='Scissor'
        massage="action: "+actionstring+", observation: "+observationstring+", reward: "+self.reward
        
        return massage
         


             
            
    































