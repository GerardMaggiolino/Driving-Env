import gym 
import gym_driving
import tensorflow as tf
from stable_baselines.common.policies import MlpPolicy
from stable_baselines.common.vec_env import DummyVecEnv
from stable_baselines import TRPO
import matplotlib.pyplot as plt
import pickle

def graph_reward(ep_reward):
    '''
    Graph info of ep_reward
    '''
    fig = plt.figure(figsize=(7, 5))
    ax = fig.add_subplot(111)
    ax.plot(ep_reward)
    ran = (max(ep_reward) - min(ep_reward)) * 0.1
    ax.set_ylim((min(ep_reward) - ran, max(ep_reward) + ran))
    ax.set_title('Reward per episode.')
    plt.show()

def main(): 
    ''' 
    Trains baselines TRPO.
    '''
    total_steps = 1200 * 800
    policy_kwargs = dict(act_fun=tf.nn.relu, net_arch=[64, 64])

    env = gym.make('Driving-v1')
    env.seed(1)
    env = DummyVecEnv([lambda: env])
    model = TRPO('MlpPolicy', env, verbose=0, policy_kwargs=policy_kwargs, 
        timesteps_per_batch=24000)

    logger = {'rewards': [], 'lengths': []}
    model.learn(total_timesteps=total_steps, gerard_logger=logger)
    model.save('saved_trpo_v1')

    with open('trpo_v1_rew', 'wb') as fp: 
        dic = {'trpo': logger}
        pickle.dump(dic, fp)

def render(): 
    env = gym.make('Driving-v1')
    env = DummyVecEnv([lambda: env])
    model = TRPO.load('saved_trpo_v1')

    with open('trpo_rew_per_episode', 'rb') as fp: 
        reward = pickle.load(fp)
    print(reward)
    ob = env.reset()
    while True: 
        action, _states = model.predict(ob)
        ob, rew, done, _ = env.step(action)
        if done: 
            break
        env.render()
    env.close()

if __name__ == '__main__': 
    main()
