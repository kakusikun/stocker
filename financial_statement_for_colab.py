
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

            fs_type1 = (f'民國{self.year}年第{self.season}季', '單位：新台幣仟元', '會計項目', 'Unnamed: 0_level_3')
            if fs_type1 in self.df:
                df[self.fs_type] = self.df[fs_type1]
            else:
                self.get(step=2)
                if fs_type1 in self.df: 
                    df[self.fs_type] = self.df[fs_type1]
                else:
                    return False

            amount1 = (f'民國{self.year}年第{self.season}季', '單位：新台幣仟元', f'{self.year}年{self.month[self.season-1]:02}月{self.day[self.season-1]}日', '金額')
            amount2 = (f'民國{self.year}年第{self.season}季', '單位：新台幣仟元', f'{self.year}年{self.from_month[0]:02}月01日至{self.year}年{self.month[self.season-1]:02}月{self.day[self.season-1]}日', '金額')
            amount3 = (f'民國{self.year}年第{self.season}季', '單位：新台幣仟元', f'{self.year}年第{self.season}季', '金額')
            amount4 = (f'民國{self.year}年第{self.season}季', '單位：新台幣仟元', f'{self.year}年上半年度', '金額')
            amount5 = (f'民國{self.year}年第{self.season}季', '單位：新台幣仟元', f'{self.year}年度', '金額')
            if amount1 in self.df:
                df['amount'] = self.df[amount1]
            elif amount2 in self.df:
                df['amount'] = self.df[amount2]
            elif amount3 in self.df:
                df['amount'] = self.df[amount3]
            elif amount4 in self.df:
                df['amount'] = self.df[amount4]
            elif amount5 in self.df:
                df['amount'] = self.df[amount5]
            else:
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

    def save(self):
        self.df.to_pickle(self.fname)

    def get_index(self):
        self.clean()
        return self.df['index'].to_numpy().tolist()

class MergeRawFS():
    def __init__(self, co_id, fs_type):
        self.logger = setup_logger("/content/drive/My Drive/financial_statements", log_name='merge_raw_fs')
        self.co_id = co_id
        self.fs_type = fs_type
        self.month = [3,6,9,12]
        self.dfs = {}
        self.src = "/content/drive/My Drive/financial_statements/raw"
        self.dst = "/content/drive/My Drive/financial_statements/merge"
        if not os.path.exists(self.dst):
            os.mkdir(self.dst)

        self.target_item = {
            'asset': ['資產總計', '資產總額', '歸屬於母公司業主之權益', '權益總額', '權益總計'],
            'income': ['營業收入合計', '營業毛利（毛損）淨額', 
                       '營業費用合計', '營業利益（損失）', '所得稅費用（利益）合計', '繼續營業單位本期淨利（淨損）',
                       '稅前淨利（淨損', '本期淨利（淨損', 
                       '母公司業主（淨利∕損）', '母公司業主（淨利／損）', '基本每股盈餘'],
            'cashflow': ['折舊費用', '攤銷費用', '利息費用',
                        '營業活動之淨現金流入（流出）', '投資活動之淨現金流入（流出）', '籌資活動之淨現金流入（流出）',
                        '取得不動產、廠房及設備',
                        '本期現金及約當現金增加（減少）數','匯率變動對現金及約當現金之影響',]
        }
        self.unified_target_item = {
            'asset': {'資產總額':'資產總計','權益總額':'權益總計'},
            'income': {'母公司業主（淨利／損）': '母公司業主（淨利∕損）'},
            'cashflow': {}
        }
    def get(self):
        for year in range(102,datetime.now().year-1911+1):
            for season in range(1,5):
                fname = os.path.join(self.src, str(year), str(season), self.fs_type, f'{self.fs_type}_{year}_{season}_{self.co_id}.pkl')
                if not os.path.exists(fname):
                    self.logger.info(f"{fname} does not exist")
                else:
                    self.logger.info(f"{fname}")
                    self.dfs[f'{year}_{season}'] = pd.read_pickle(fname)

    def merge(self):
        dfs = []
        for key in self.dfs:
            df = self.dfs[key]
            year, season = key.split("_")
            _df = df[df[self.fs_type].isin(self.target_item[self.fs_type])]
            _df = _df.transpose()
            _df.columns = _df.loc[[self.fs_type]].iloc[0]
            _df.drop(self.fs_type, inplace=True)
            _df.insert(0,'season', int(season))
            _df.insert(0,'year', int(year))
            _df.rename(columns=self.unified_target_item[self.fs_type], index={'amount': f'{int(year)+1911}{self.month[int(season)-1]:02}'}, inplace=True)
            _df = _df.loc[:,~_df.columns.duplicated(keep='last')]
            dfs.append(_df)
        self.df = pd.concat(dfs)

class AggregateFS():
    def __init__(self, co_id):
        self.co_id = co_id
        self.df = None

    def aggregate(self):
        fs_dfs = {} 
        for fs_type in ['asset', 'income', 'cashflow']:
            mfs = MergeRawFS(co_id=self.co_id, fs_type=fs_type)
            mfs.get()
            mfs.merge()
            fs_dfs[fs_type] = mfs.df
        ddf = pd.concat(fs_dfs.values(), axis=1)
        unit_cols = ddf.columns.difference(['year', 'season', '資產總計', '歸屬於母公司業主之權益', '權益總計'])
        ddf = ddf.loc[:, ~ddf.columns.duplicated()]
        diff_ddf = ddf[unit_cols].diff()
        diff_ddf[ddf['season']==1] = ddf[ddf['season']==1][unit_cols]
        self.df = pd.concat([fs_dfs['asset'], diff_ddf], axis=1)

    def check_exist(self, dst, read=False):
        self.fname = os.path.join(dst, f"merge_fs_{self.co_id}.csv")
        if os.path.exists(self.fname):
            if read:
                self.df = pd.read_csv(self.fname)
            return True
        return False

    def save(self):
        self.df.to_csv(self.fname)

def get_index(dst, year, season):
    fname = os.path.join(dst, "raw", str(year), str(season), "profit", f"profit_{year}_{season}.pkl")
    df = pd.read_pickle(fname)
    return df['index'].to_numpy().tolist()