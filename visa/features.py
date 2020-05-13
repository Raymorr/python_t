import sys
sys.path.append("..")

import pandas as pd
import numpy as np
import datetime
import os
import itertools
import random

from compressor.compress import FeatureCompressor
from tqdm import tqdm
from multiprocessing import Pool, cpu_count

# DEFAULT_PATH = 'C:\\Users\\molot\\OneDrive\\Документы\\ML\\dataset_compressed'
# DEFAULT_DATASET = 'C:\\Users\\molot\\OneDrive\\Документы\\ML\\dataset_compressed\\compressed_MSU_DATA_TO_SHARE.tsv'

DEFAULT_PATH = '/Users/ilya/visa/dataset_compressed'
DEFAULT_DATASET = '/Users/ilya/visa/small_compressed_MSU_DATA_TO_SHARE.tsv'

def load_dataset():
    dtypes = {
        'sample_data': np.int8,
        'acct_num_share': np.int32,
        'issr_code_numb': np.int8,
        'product_nm': np.int8,
        'funding_source': str,
        'mrch_country_nm': np.int16,
        'f2f_ecomm_flg': np.int8,
        'pos_cash_flg': np.int8,
        'rub_amt': np.float64,
        'purchase_dt': str,
        'mrch_category_01': np.int16,
        'mrch_category_02': np.int8,
        'mrch_category_03': np.int8,
        'mrch_category_04': np.int8
    }

    print('Loading dataset')
    fc = FeatureCompressor(DEFAULT_PATH)

    df = pd.read_csv(DEFAULT_DATASET, sep='\t', dtype=dtypes)  
    df.purchase_dt = df.purchase_dt.apply(lambda x: datetime.datetime.strptime(x, '%Y-%m-%d'))
    return df, fc


def rub_amt_feature(df, fc, date, month_offset):
    start_date = date - pd.DateOffset(months=month_offset)
    return {'rub_amt_month={}'.format(month_offset): df[start_date <= df.purchase_dt].rub_amt.sum()}


def number_feature(df, fc, date, month_offset):
    start_date = date - pd.DateOffset(months=month_offset)
    return {'rub_amt_month={}'.format(month_offset): (start_date <= df.purchase_dt).sum()}


def number_category2_feature(df, fc, date, month_offset, category):
    start_date = date - pd.DateOffset(months=month_offset)
    mask = (df.purchase_dt >= start_date) & (df.mrch_category_02 == category)
    return {'number_category2={}_month={}'.format(fc.mrch_category_02[category], month_offset): mask.sum()}


def rub_amt_category1_feature(df, fc, date, month_offset):
    start_date = date - pd.DateOffset(months=month_offset)
    df = df[df.purchase_dt >= start_date]
    cat_rub_amt = df.groupby('mrch_category_01').rub_amt.sum()
    res = dict()
    for cat_name, cat_idx in fc.mrch_category_01_id.items():
        feature_name = 'rub_amt_category1={}_month={}'.format(cat_name, month_offset)
        res[feature_name] = cat_rub_amt[cat_idx] if cat_idx in cat_rub_amt.index else 0
    return res


def card_level_feature(df, fc, data):
    num_levels = len(fc.product_nm)
    card_level_num = df.iloc[-1].product_nm if df.shape[0] != 0 else -1
    return {'card_level={}'.format(fc.product_nm[level]): int(card_level_num == level) for level in range(num_levels)}


def bank_feature(df, fc, data):
    num_banks = len(fc.issr_code_numb)
    bank_num = df.iloc[-1].issr_code_numb if df.shape[0] != 0 else -1
    return {'card_level={}'.format(fc.issr_code_numb[bank]): int(bank_num == bank) for bank in range(num_banks)}

def rub_mean_feature(df, fc, date, month_offset):
    start_date = date - pd.DateOffset(months=month_offset)
    return {'rub_mean_month={}'.format(month_offset): df[start_date <= df.purchase_dt].rub_amt.sum()/df[start_date <= df.purchase_dt].rub_amt.shape[0]
        if(df[start_date <= df.purchase_dt].rub_amt.shape[0] != 0) else 0}


def rub_ratio_feature(df, fc, date, month_offset):
    start_date1 = date - pd.DateOffset(months=month_offset)
    end_date1 = date - pd.DateOffset(months=month_offset-1)
    start_date2 = date - pd.DateOffset(months=month_offset-1)
    end_date2 = date - pd.DateOffset(months=month_offset-2)

    mask1 = (start_date1 <= df.purchase_dt) & (df.purchase_dt <= end_date1)
    mask2 = (start_date2 <= df.purchase_dt) & (df.purchase_dt <= end_date2)
    return {'rub_ratio_feature_from={}_to={}'.format(month_offset, month_offset+1): (df[mask1].rub_amt.sum())/(df[mask2].rub_amt.sum())
         if(df[mask2].rub_amt.sum() != 0) else 0}

def trades_contr(df, fc, date,  month_offset):
    country_mask = df.mrch_country_nm != fc.mrch_country_nm_id['RUSSIAN FEDERATION']
    face_mask_1 = df.f2f_ecomm_flg == fc.f2f_ecomm_flg_id['FACE-TO-FACE']
    face_mask_2 = df.pos_cash_flg == fc.pos_cash_flg_id['CASH']
    foreign_mask = country_mask & (face_mask_1 | face_mask_2)

    start_date = date - pd.DateOffset(months=month_offset)
    mask = (df.purchase_dt >= start_date) & foreign_mask
    
    return {'trades_contr_month={}'.format(month_offset): df[mask].rub_amt.sum()}

def calculate_features_user(df, fc, date):
    features_description = {
        rub_amt_feature: {'month_offset': list(range(1, 12, 3))},
        rub_mean_feature: {'month_offset': list(range(1, 12, 2))},
        number_feature: {'month_offset': list(range(1, 12, 3))},
        rub_ratio_feature: {'month_offset': list(range(3, 12)) },
        rub_amt_category1_feature: {'month_offset': [1]},
        card_level_feature: {},
        bank_feature: {},
        trades_contr: {'month_offset': list(range(1, 12, 2))},
    }

    features = dict()
    for feature_function, args in features_description.items():
        arg_names = list(args.keys())
        arg_range = list(args.values())
        for arg_values in itertools.product(*arg_range):
            features.update(feature_function(df, fc, date, **dict(zip(arg_names, arg_values))))

    return features


def calculate_target_user(df, fc, date):
    watch_period_beg = date + pd.DateOffset(months=1)
    watch_period_end = date + pd.DateOffset(months=3)
    df = df[(watch_period_beg <= df.purchase_dt) & (df.purchase_dt < watch_period_end)]
    country_mask = df.mrch_country_nm != fc.mrch_country_nm_id['RUSSIAN FEDERATION']
    face_mask_1 = df.f2f_ecomm_flg == fc.f2f_ecomm_flg_id['FACE-TO-FACE']
    face_mask_2 = df.pos_cash_flg == fc.pos_cash_flg_id['CASH']
    foreign_mask = country_mask & (face_mask_1 | face_mask_2)
    return 1 if foreign_mask.any() else 0


def calculate_user_rows(user_id, user_data, fc, start_date, end_date):
    date = start_date
    features = []
    while date < end_date:
        previous_data = user_data[user_data.purchase_dt < date]
        cur_features = calculate_features_user(previous_data, fc, date)
        cur_features['target'] = calculate_target_user(user_data, fc, date)
        cur_features['user_id'] = user_id
        cur_features['date'] = date
        date += pd.DateOffset(months=1)
        features.append(cur_features)
    
    return features


def create_features(df, fc):
    start_date = df.purchase_dt.min() + pd.DateOffset(months=9)
    end_date = df.purchase_dt.max() - pd.DateOffset(months=3, days=-1)
    print(start_date, end_date)
    features = []
    print('Groupping by user')
    #for user_id, user_data in tqdm(df.groupby('acct_num_share')):
    with Pool(4) as p:
        features = p.starmap(calculate_user_rows, [(name, group, fc, start_date, end_date) for name, group in df.groupby('acct_num_share')])
    
        
    #print('Number of features is', len(features[0]))
    features = pd.DataFrame(itertools.chain(*features))
    print('Number of featrues is', len(features.columns))
    features.to_csv(os.path.join(DEFAULT_PATH, 'features.csv'), index=False)


if __name__ == '__main__':
    print(datetime.datetime.now())
    df, fc = load_dataset()
    print(df.issr_code_numb.max())
    fc.issr_code_numb = list(range(df.issr_code_numb.max()))
    create_features(df, fc)
    print(datetime.datetime.now()) 
