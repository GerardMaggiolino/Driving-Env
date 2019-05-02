'''
Attempted A2C, Advantage Actor Critic. 

Advantage Q(s, a) - V(s) calculated using TD Error, (R + Gamma * V(s') - V(s)).
State value function approximator trained with n step TD.

IN PROGRESS. 
'''

import torch 
import gym 
import gym_driving
import numpy as np
import torch.nn as nn
from util import *


def load_checkpoint(checkpoint_path, config): 
    '''
    Loads a checkpoint if it exists. Otherwise, initializes.
    '''
    # Policy
    policy = Network(config['ob_dim'], config['policy_hidden_units'] + 
        [config['action_dim']])
    optim = torch.optim.Adam(policy.parameters(), config['policy_lr'])
    # Critic 
    critic = Network(config['ob_dim'], config['critic_hidden_units'] + [1], 
        critic=True)
    critic_optim = torch.optim.Adam(critic.parameters(), config['critic_lr'])
    # Std 
    std = (torch.ones(config['action_dim'], requires_grad=True) if
        config['std_init'] is None else torch.tensor(config['std_init'],
        requires_grad=True))
    # Recording 
    ep_reward = []
    
    # Try to load from checkpoint
    try: 
        checkpoint = torch.load(checkpoint_path)

        # Reset policy
        policy_param = checkpoint['policy_param']
        policy = Network(*policy_param)
        optim = torch.optim.Adam(policy.parameters(), config['policy_lr'])
        # Reset critic
        critic_param = checkpoint['critic_param']
        critic = Network(*critic_param, critic=True)
        critic_optim = torch.optim.Adam(critic.parameters(), 
            config['critic_lr'])
        # Load state dicts
        policy.load_state_dict(checkpoint['policy'])
        critic.load_state_dict(checkpoint['critic'])
        std = checkpoint['std']
        optim.add_param_group({'params': std, 'lr': config['std_lr']})
        optim.load_state_dict(checkpoint['optim'])
        critic_optim.load_state_dict(checkpoint['critic_optim'])
        ep_reward = checkpoint['ep_reward']
        print(f'Resuming training from episode {len(ep_reward)}')
    except FileNotFoundError:
        optim.add_param_group({'params': std, 'lr': config['std_lr']})
        print('NOTE: Training from scratch.')
            
    return (policy, optim, critic, critic_optim, std, ep_reward)


def save_checkpoint(checkpoint_path, policy, optim, critic, critic_optim, 
    std, ep_reward, config):
    '''
    Saves checkpoint.
    '''
    torch.save({
        'policy': policy.state_dict(), 
        'policy_param': (config['ob_dim'], config['policy_hidden_units'] + 
            [config['action_dim']]),
        'critic': critic.state_dict(), 
        'critic_param': (config['ob_dim'], config['critic_hidden_units'] + [1]),
        'optim': optim.state_dict(), 
        'critic_optim': critic_optim.state_dict(),
        'std': std, 
        'ep_reward': ep_reward
    }, checkpoint_path)


def main(): 
    '''
    Calls training procedure.
    '''

    # Hyperparameters
    config = { 
    'action_dim': None,
    'ob_dim': None,
    'policy_hidden_units': [32, 32],
    'critic_hidden_units': [32, 32],
    'std_init': None,
    'policy_lr': 1e-3,
    'critic_lr': 5e-3,
    'std_lr': 1e-2,
    'max_steps': 500,
    'batch_size': 2000,
    'max_episodes': 4, 
    'critic_max_batch': 128,
    'n_step_return': 20
    'discount': 0.99,
    'epochs': 100
    }

    env = gym.make('Driving-v0')
    config['action_dim'] = env.action_space.low.size
    config['ob_dim'] = env.observation_space.low.size
    
    # Set std according to dimension bounds 
    config['std_init'] = (env.action_space.high - env.action_space.low) 

    # Load checkpoint
    checkp_path = 'checkpoint_ac.tar'
    policy, optim, critic, critic_optim, std, episode_reward = \
        load_checkpoint(checkp_path, config)
    device = (torch.device('cuda') if torch.cuda.is_available() else 
        torch.device('cpu'))
    policy.to(device)
    critic.to(device)
    std.to(device)

    critic_loss = nn.MSELoss(reduction='mean')

    # Train over epochs (batches of normalized steps)
    for ep in range(1, config['epochs'] + 1):
        # Recording for batch
        log_probs = []
        observations = []
        td_targets = []
        critic_pred = []
        # Recording for episodes within a batch
        episode_start_step = 0
        episodes = 0
        rewards = []

        # Run fixed number of steps with multiple episodes
        step = 0
        ob = torch.from_numpy(env.reset()).float().to(device)
        while step < config['batch_size']:
            # Record critic reward based off observation
            critic_pred.append(critic(ob))
            observations.append(ob)
            # Perform action on env, recover new ob, reward, done
            action, prob = classify_continuous(policy(ob), std)
            ob, reward, done, _ = env.step(action)
            ob = torch.from_numpy(ob).float().to(device)
            
            # Append true reward from step and log prob 
            rewards.append(reward)
            log_probs.append(prob)
            step += 1

            # If done with episode
            if done or (step - episode_start_step >= config['max_steps']):
                episodes += 1
                episode_reward.append(sum(rewards[episode_start_step:]))

                # Calculate n step td targets 

                # Exit if can't run another episode in batch size
                if step + config['max_steps'] > config['batch_size']:
                    break
                # Exit if over number of episodes desired
                if episodes >= config['max_episodes']:
                    break
                # Continue otherwise
                episode_start_step = step 
                ob = torch.from_numpy(env.reset()).float().to(device)
                rewards = []

        # Compute actor loss
        loss = 0
        for prob, adv in zip(log_probs, advantage): 
            loss -= prob * adv
        loss /= step
        optim.zero_grad() 
        loss.mean().backward()
        optim.step()

        # Save checkpoint 
        if ep % 5 == 0: 
            print([round(i.item(), 3) for i in std])
            print(f'Episode {len(episode_reward)}\t'
                  'Reward:\t', round(sum(episode_reward[-30:])
                  / 30, 2))
            save_checkpoint(checkp_path, policy, optim, critic, critic_optim, 
                std,  episode_reward, config)

    # Graph info 
    graph_reward(episode_reward)

    # Render 
    for _ in range(5):
        ob = torch.from_numpy(env.reset()).float().to(device)
        for step in range(config['max_steps']): 
            with torch.no_grad():
                env.render()
                action, prob = classify_continuous(policy(ob), std)
                ob, reward, done, _ = env.step(action)
                ob = torch.from_numpy(ob).float().to(device)
                if done: 
                    break
    env.close()

if __name__ == '__main__': 
    main()
