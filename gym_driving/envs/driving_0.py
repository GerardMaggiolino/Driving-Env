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


class Driving0(DrivingEnv):
    '''
    action_space : spaces.Box
        np.ndarray of size 3. [0, 1], [0, 1], [-.6, .6] range. First
        feature is throttle, second is break, third is central steering
        angle. 
    '''
    metadata = {'render.modes': ['human']}
    
    def __init__(self, additional_observation=None):
        super().__init__()

        self.done = False

        # Reset observation space
        low = np.array([-float('inf'), -float('inf'), -1, -1, -5, -5, -15, -15])
        high = np.array([float('inf'), float('inf'), 1, 1, 5, 5, 15, 15])
        self.observation_space = gym.spaces.Box(low=low, high=high, 
            dtype=np.float32)
                                           
    def reset(self):
        ''' 
        Initialization to start simulation. Loads all proper objects. 
        '''
        # Default initialization of car, plane, and gravity 
        super().reset()

        # Generate new target every time
        self.target = np.array(
            (self.random.randint(-15,15), self.random.randint(-15,15)))

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
        Retrieves observation of car with no lidar. 

        Returns
        -------
        np.ndarray
        Car position (2), orientation (2), velocity (2), target(2)
        '''
        pos, ori = self.car.get_position_orientation()
        vel = self.car.get_velocity()
        return np.concatenate((pos, ori, vel, self.target))

    def _get_reward(self, obs):
        ''' 
        Retrieves reward of car.

        Returns
        -------
        float
        Euclidean distance between car and target. 
        '''
        currPos, _, angle = self.car.get_position_orientation(True)
        targetPos = self.target 
        diff = abs(currPos - targetPos).sum()
        if diff < 0.05: 
            self.done = True
            return 100
        distance = np.linalg.norm(currPos - targetPos) 
        return -distance
