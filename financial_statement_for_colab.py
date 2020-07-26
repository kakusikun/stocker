
import os
import sys
import pandas as pd
import requests
import numpy as np
from io import StringIO
import time
import html5lib
from datetime import datetime, timedelta, date
import calendar
import datetime as dt
from functools import reduce
import json
from collections import Counter
import logging
from urllib3.exceptions import NewConnectionError

def setup_logger(save_dir, log_name="log"):
    logger = logging.getLogger("logger")
    if not len(logger.handlers):
        logger.setLevel(logging.DEBUG)
        # don't log results for the non-master process
        ch = logging.StreamHandler(stream=sys.stdout)
        ch.setLevel(logging.DEBUG)
        formatter = logging.Formatter("%(asctime)s %(process)s %(filename)s %(levelname)s: %(message)s")
        ch.setFormatter(formatter)
        logger.addHandler(ch)

        if save_dir:
            fh = logging.FileHandler(os.path.join(save_dir, log_name + ".log"), mode='w')
            fh.setLevel(logging.DEBUG)
            fh.setFormatter(formatter)
            logger.addHandler(fh)
        logger.propagate = False

    return logger


class FS():
    def __init__(self, fs_type, co_id=1101, latest=True, year=109, season=1, market='sii', logger=None):
        if fs_type == 'asset':
            url = 'https://mops.twse.com.tw/mops/web/t164sb03'
        elif fs_type == 'income':
            url = 'https://mops.twse.com.tw/mops/web/t164sb04'
        elif fs_type == 'cashflow':
            url = 'https://mops.twse.com.tw/mops/web/t164sb05'
        elif fs_type == 'profit':
            url = 'https://mops.twse.com.tw/mops/web/t163sb06'
        else:
            raise TypeError

        self.year = year
        self.season = season
        self.fs_type = fs_type
        self.co_id = co_id
        self.market = market
        self.url = url
        
        self.month = [3,6,9,12]
        self.day = [31,30,30,31]
        self.from_month = [1,4,7,10]
        self.logger = logger

    def get(self, step=1):
        if self.fs_type in ['asset', 'income', 'cashflow']:
            form = {
                'encodeURIComponent': 1,
                'step': step,
                'firstin': 1,
                'off': 1,
                'queryName': 'co_id',
                'inpuType': 'co_id',
                'TYPEK': 'all',
                'isnew': 'false',
                'co_id': str(self.co_id),
                'year': str(self.year),
                'season': f"{self.season:02}",
            }
        
        if self.fs_type in ['profit']:
            form = {
                'encodeURIComponent':1,
                'step': step,
                'firstin': 1,
                'off': 1,
                'TYPEK': self.market,
                'year': str(self.year),
                'season': f"{self.season:02}"
            }
        
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) \
                    AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}    
        while True:
            try:
                r = requests.post(self.url, form, headers=headers)
                break
            except:
                if self.logger is not None:
                    self.logger.info('sleep')
                time.sleep(5*60)
                continue

        r.encoding = 'utf8'
        dfs = pd.read_html(StringIO(r.text))

        max_idx = 0
        for idx, df in enumerate(dfs):
            if len(df) > max_idx:
                max_idx = idx
        
        self.df = dfs[max_idx]

    
    def clean(self):
        self.get()
        if self.fs_type != 'profit':
            df = pd.DataFrame(columns=[self.fs_type, 'amount'])
            try:
                df[self.fs_type] = self.df[(f'民國{self.year}年第{self.season}季', '單位：新台幣仟元', '會計項目', 'Unnamed: 0_level_3')]
            except KeyError:
                try:
                    self.get(step=2)
                    df[self.fs_type] = self.df[(f'民國{self.year}年第{self.season}季', '單位：新台幣仟元', '會計項目', 'Unnamed: 0_level_3')]
                except KeyError:
                    return False
            try:
                df['amount'] = self.df[ (f'民國{self.year}年第{self.season}季', '單位：新台幣仟元', f'{self.year}年{self.month[self.season-1]:02}月{self.day[self.season-1]}日', '金額')]
            except KeyError:
                try:
                    df['amount'] = self.df[ (f'民國{self.year}年第{self.season}季', '單位：新台幣仟元', f'{self.year}年{self.from_month[0]:02}月01日至{self.year}年{self.month[self.season-1]:02}月{self.day[self.season-1]}日', '金額')]
                except KeyError:
                    try:
                        df['amount'] = self.df[ (f'民國{self.year}年第{self.season}季', '單位：新台幣仟元', f'{self.year}年第{self.season}季', '金額')]
                    except KeyError:
                        return False
            

            self.df = df
            self.df.amount.fillna(0.0, inplace=True)
            return True
           
        else:
            df = pd.DataFrame(columns=['index','name', '毛利率','營業利益率','稅前純益率','稅後純益率'])
            df['index'] = self.df[0][1:]
            df['name'] = self.df[1][1:]
            df['毛利率'] = self.df[3][1:].fillna(0.0)
            df['營業利益率'] = self.df[4][1:].fillna(0.0)
            df['稅前純益率'] = self.df[5][1:].fillna(0.0)
            df['稅後純益率'] = self.df[6][1:].fillna(0.0)
            df = df[df['index']!='公司代號']
            self.df = df
            return True

    def check_exist(self, dst):
        dst = os.path.join(dst, str(self.year), str(self.season), self.fs_type)
        if self.fs_type != 'profit':
            self.fname = os.path.join(dst, f'{self.fs_type}_{self.year}_{self.season}_{self.co_id}.pkl')
            if not os.path.exists(self.fname):
                return False
        else:
            self.fname = os.path.join(dst, f'{self.fs_type}_{self.year}_{self.season}.pkl')
            if not os.path.exists(self.fname):
                return False
        return True

    def save(self, dst):
        self.df.to_pickle(fname)

    def get_index(self):
        self.clean()
        return self.df['index'].to_numpy().tolist()