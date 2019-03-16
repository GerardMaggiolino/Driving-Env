''' 
Contains basic challenge of getting to goal with no obstacles.
'''

# OpenAI gym library imports 
import gym 
# External libraries 
import pybullet as p
import numpy as np
# Local resources
from gym_driving.envs.driving_env import DrivingEnv
import gym_driving.resources._car as car
from gym_driving.resources._cube import Cube


class Driving1(DrivingEnv):
    '''
    action_space : spaces.Box
        np.ndarray of size 3. [0, 1], [0, 1], [-.6, .6] range. First
        feature is throttle, second is break, third is central steering
        angle. 
    '''
    metadata = {'render.modes': ['human']}
    
    def __init__(self, additional_observation=None):
        # Add target to observation space
        low = np.array([5, -13])
        high = np.array([13, 13])
        super().__init__((low, high))

        self.done = False
        self.prev_dist = None
                                           
    def reset(self):
        ''' 
        Initialization to start simulation. Loads all proper objects. 
        '''
        # Default initialization of car, plane, and gravity 
        super().reset()

        # Generate new target every time
        self.target = np.array((self.random.randint(5, 13), 
             self.random.choice([-1, 1]) * self.random.randint(5,13)))

        # Marker for target
        Cube(list(self.target) +  [0], client=self.client)

        # Obstacle 
        Cube(list(self.target / 2) + [0], 3, client=self.client)

        self.done = False
        self.prev_dist = np.linalg.norm(np.array(
            self.car.get_position_orientation()[0]) - self.target)

        return self._get_observation()

    def _get_done(self): 
        ''' 
        Returns true if car reaches goal.

        Returns 
        -------
        bool 
        True if reaches goal state.
        '''
        return self.done

    def _get_observation(self): 
        ''' 
        Retrieves observation of car with target.

        Returns
        -------
        np.ndarray
        '''
        return np.concatenate((self.car.get_observation(), self.target))

    def _get_reward(self, obs):
        ''' 
        Retrieves reward of car.

        Returns
        -------
        float
        Euclidean distance between car and target. 
        '''
        currPos, _= self.car.get_position_orientation()

        if (abs(currPos[0]) > 14.8 or abs(currPos[1]) > 14.8 or
            self.car.get_collision()): 
            self.done = True
            return -100

        distance = np.linalg.norm(currPos - self.target) 

        if distance < 0.5: 
            self.done = True
            return 100

        reward = (self.prev_dist - distance) 
        reward = reward * 10 if reward > 0 else reward

        self.prev_dist = distance

        return reward
