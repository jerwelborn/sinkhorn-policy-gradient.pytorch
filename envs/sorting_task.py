# Generate sorting data and store in .txt
# Define the reward function 
import torch
import math
from torch.utils.data import Dataset
from torch.autograd import Variable
from tqdm import trange, tqdm
import os
import sys

import scipy.sparse as sp
import numpy as np
from scipy import stats
#from pygcn import utils


def reward_nco(sample_solution, use_KT, use_cuda=False):
    """
    Reward is Kendall-Tau

    Input sequences must all be the same length.

    Example: 

    input       | output
    ====================
    [1 4 3 5 2] | [5 1 2 3 4]
    
    The output gets a reward of 4/5, or 0.8

    The range is [1/sourceL, 1]

    Args:
        sample_solution: list of len sourceL of [batch_size]
        Tensors
    Returns:
        [batch_size] containing rewards
    """
    solutions = torch.stack(sample_solution)
    # now solution is tensor of size [sourceL, batch_size]
    if use_KT:
        return -reward_ddpg_D(solutions.permute(1, 2, 0), use_cuda)
    else:
        return -reward_ddpg_C(solutions.permute(1, 2, 0), use_cuda, True)

def reward_ddpg_A(solution, use_cuda):
    """
    Count number of consecutively correctly sorted for each sample in minibatch
    starting from beginning
    
    Very hard to randomly find enough non-zero samples - reward is very sparse!

    solution is FloatTensor of dim [batch,n]
    """
    (batch_size, n, m) = solution.size()
    n_correctly_sorted = Variable(torch.zeros(batch_size, 1), requires_grad=False)
    mask = Variable(torch.ones(batch_size, 1).byte(), requires_grad=False)
    if use_cuda:
        n_correctly_sorted = n_correctly_sorted.cuda()
        mask = mask.cuda()

    for i in range(1, m):
        res = torch.lt(solution[:,:,i-1], solution[:,:,i])
        mask.data &= res.data
        n_correctly_sorted[mask] += 1

    return torch.div(n_correctly_sorted, m - 1)

def reward_ddpg_B(solution, use_cuda):
    """
    Count number of (nonconsecutively) correctly sorted starting from beginning
    
    Tends to converge to [0,2,4,6,8,1,3,5,7,9]

    solution is FloatTensor of dim [batch,n]
    """
    (batch_size, n, m) = solution.size()
    n_correctly_sorted = Variable(torch.zeros(batch_size, 1), requires_grad=False)
    
    if use_cuda:
        n_correctly_sorted = n_correctly_sorted.cuda()

    for i in range(1, m):
        res = torch.lt(solution[:,:,i-1], solution[:,:,i])
        n_correctly_sorted += res.float()

    return torch.div(n_correctly_sorted, m - 1)

def reward_ddpg_C(solution, use_cuda, nco=False):
    """
    Max size substring of correctly sorted numbers

    Exploration gets very tricky near global optimum..
    e.g., [0, 1, 2, 4, 5, 6, 7, 9, 8, 3] ??
    --> swap(9,3)
    --> swap(7,3)
    --> swap(6,3)
    --> swap(5,3)
    --> swap(4,3)
    solution is FloatTensor of dim [1,n]
    """
    (batch_size, n, m) = solution.size()
    
    if not nco:
        longest = Variable(torch.ones(batch_size, 1), requires_grad=False)
        current = Variable(torch.ones(batch_size, 1), requires_grad=False)
    else:
        longest = Variable(torch.ones(batch_size), requires_grad=False)
        current = Variable(torch.ones(batch_size), requires_grad=False)
        
    if use_cuda:
        longest = longest.cuda()
        current = current.cuda()
    for i in range(1, m):
        res = torch.lt(solution[:,:, i-1], solution[:,:,i])
        current += res.float()
        current[torch.eq(res, 0)] = 1
        mask = torch.gt(current, longest)
        longest[mask] = current[mask]

    return torch.div(longest, m)

def reward_ddpg_D(solution, use_cuda):
    """
    Kendall-Tau correlation coefficient
    """
    (batch_size, n, m) = solution.size()
    if use_cuda:
        solution = solution.data.cpu().numpy()
    else:
        solution = solution.data.numpy()

    target = np.array(list(range(m)))
    R = []
    for i in range(batch_size):
        R.append(torch.FloatTensor([stats.kendalltau(solution[i], target).correlation]))
    R = torch.stack(R)
    if use_cuda:
        R = R.cuda()
    return Variable(R, requires_grad=False)

def create_dataset(
        train_size,
        test_size,
        data_dir,
        epoch,
        low=1, 
        high=10,
        train_only=False,
        random_seed=None):    
    data_len = high - low + 1

    if random_seed is not None:
        torch.manual_seed(random_seed)
    
    train_task = 'epoch-{}-sorting-size-{}-low-{}-high-{}-train.txt'.format(epoch, train_size, low, high)
    test_task = 'sorting-size-{}-low-{}-high-{}-test.txt'.format(test_size, low, high)
    
    train_fname = os.path.join(data_dir, train_task)
    test_fname = os.path.join(data_dir, test_task)

    if not os.path.isdir(data_dir):
        os.makedirs(data_dir)
    elif os.path.exists(train_fname) and os.path.exists(test_fname):
            return train_fname, test_fname
    
    train_set = open(os.path.join(data_dir, train_task), 'w')
    if not train_only:
        test_set = open(os.path.join(data_dir, test_task), 'w') 
    
    def to_string(tensor):
        """
        Convert a a torch.LongTensor 
        of size data_len to a string 
        of integers separated by whitespace
        and ending in a newline character
        """
        line = ''
        for j in range(data_len-1):
            line += '{} '.format(tensor[j])
        #line += str(tensor[-1]) + '\n'
        # ValueError: invalid literal for int() with base 10: 'tensor(19)'
        line += '{}'.format(tensor[-1]) + '\n'
        return line
    
    print('Creating training data set for {}...'.format(train_task))
    
    # Generate a training set of size train_size
    for i in trange(train_size):
        x = torch.randperm(data_len) + low
        train_set.write(to_string(x))

    if not train_only:
        print('Creating test data set for {}...'.format(test_task))
        
        for i in trange(test_size):
            x = torch.randperm(data_len) + low
            test_set.write(to_string(x))
        test_set.close()

    train_set.close()

    return train_fname, test_fname

class SortingDataset(Dataset):

    def __init__(self, dataset_fname, use_graph=False):
        super(SortingDataset, self).__init__()
        self.is_bipartite = False

        print('Loading {} into memory'.format(dataset_fname))
        self.data_set = []
        with open(dataset_fname, 'r') as dset:
            lines = dset.readlines()
            for next_line in tqdm(lines):
                toks = next_line.split()
                sample = torch.zeros(len(toks), 1)
                for idx, tok in enumerate(toks):
                    sample[idx, 0] = int(tok)
                if use_graph:
                    features, adj = self.make_graph(sample)
                    self.data_set.append((features, adj))
                else:
                    self.data_set.append(sample)
        
        self.size = len(self.data_set)

    def make_graph(self, perm): 
        """
        Example: 
            perm is [[24 23 21 22 20]]

            Features: [[24],  Solution: [[0 0 0 0 1],
                      [23],             [0 0 0 1 0],
                      [21],             [0 1 0 0 0],
                      [22],             [0 0 1 0 0],
                      [20]] ^T          [1 0 0 0 0]]
            
            Adj:      [[0 0 0 0 1],
                       [0 0 1 0 0],
                       [1 0 0 0 0],
                       [0 1 0 0 0],
                       [0 0 0 1 0]]
        """
        # features is [n, 1] FloatTensor
        features = torch.t(perm).float()

        # create normalized adjacency matrix
        n = perm.size(1)
        smallest = torch.min(perm)
        idxs = (perm - smallest).long()
        adj = torch.eye(n, n)
        for i in range(n):
            adj[i][idxs[:,i]] = 1.
        adj = torch.div(adj, math.sqrt((n - 1) * (n - 1)))
        # row normalize
        adj = torch.div(adj, torch.mm(torch.mm(adj, torch.ones(n,1)), torch.ones(1,n)))
        return features, adj

    def __len__(self):
        return self.size

    def __getitem__(self, idx):
        return self.data_set[idx]
