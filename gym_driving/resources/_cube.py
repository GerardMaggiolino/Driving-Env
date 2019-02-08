''' 
Contains basic cube class as URDF wrapper. 
'''
import pybullet as p 
from gym_driving.resources import getResourcePath

class Cube: 
    '''
    Basic cube class. 

    Parameters
    ----------
    position : list, optional
        Three floats of position in x, y, z coordinates for cube. 
        Default [0, 0, 0].
    size : int, optional
        Size of 1, 2, 3, 4, or 5, larger being a larger cube. Default 1.
    client : int, optional 
        Physics client, default of 0. 
    '''
    # Supported sizes
    sizes = {1, 2, 3, 4, 5}

    def __init__(self, position=[0, 0, 0], size=1, client=0, color="1 1 1 1"): 
        assert size in Cube.sizes, 'Unsupported size {size} for Cube.'

        self.client = client
        self.cube = p.loadURDF(
            fileName=getResourcePath('cube/cube1.urdf'), 
            basePosition=position, 
            physicsClientId=self.client)

    def get_ids(self): 
        ''' 
        Returns tuple of (bodyid, clientid) of underlying cube. 

        Returns 
        -------
        int, int 
            Body id, client id for underlying URDF. 
        '''
        return self.cube, self.client
   
