import sys
sys.path.append("..")

import pandas as pd
import numpy as np
import os
import random

from tqdm import tqdm

DATASET_PATH = 'C:\\Users\\Павел\\Documents\\visa-master\\data\\compressed_all_MSU_DATA_TO_SHARE.tsv'
SMALL_DATASET_PATH = 'C:\\Users\\Павел\\Documents\\visa-master\\data\\small_compressed_all_MSU_DATA_TO_SHARE.tsv'

#DATASET_PATH = '/Users/ilya/visa/dataset_compressed/compressed_MSU_DATA_TO_SHARE.tsv'
#SMALL_DATASET_PATH = '/Users/ilya/visa/small_compressed_MSU_DATA_TO_SHARE.tsv'
TOTAL_N_CARDS = 125141

def random_select_cards(n_cards):
    cards = set(np.random.randint(0, TOTAL_N_CARDS, n_cards))

    with open(DATASET_PATH, 'r') as dataset, open(SMALL_DATASET_PATH, 'w') as samll_dataset:
        samll_dataset.write(dataset.readline())
        for line in tqdm(dataset):
            cur_user = int(line.split('\t')[1])
            if cur_user in cards:
                samll_dataset.write(line)

if __name__ == '__main__':
    print(sys.argv[1])
    random_select_cards(int(sys.argv[1]))
