
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


class Price():
    def __init__(self, year, month, day):
        url = f'https://www.twse.com.tw/exchangeReport/MI_INDEX?response=csv&date={year}{month:02}{day:02}&type=ALL'

        self.year = year
        self.month = month
        self.day = day
        self.url = url
        
    def get(self):
        r = requests.get(url)
        if r.text=='':
            return False    

        df = pd.read_csv(StringIO(r.text.replace("=", "")), 
                    header=["證券代號" in l for l in r.text.split("\n")].index(True)-1)
        df.drop(['Unnamed: 16','最後揭示買價', '最後揭示買量', '最後揭示賣價', '最後揭示賣量','漲跌(+/-)'], axis=1, inplace=True)
        for i in ['成交股數', '成交筆數', '成交金額', '開盤價', '最高價', '最低價', '收盤價', '漲跌價差', '本益比']:
            df[i] = df[i].apply(lambda x: pd.to_numeric(x.replace(",", ""), errors='coerce') if type(x)!=float else x)
        df['股價日期'] = datetime(int(year),int(month),int(day),0,0,0)
        self.df = df
        return True
    
    def check_exist(self, dst):
        dst = os.path.join(dst, str(self.year))
        self.fname = os.path.join(dst, str(self.year), f'{self.year}_{self.month}_{self.day}.pkl')
        if not os.path.exists(self.fname):
            return False
        return True
    
    def save(self):
        self.df.to_pickle(self.fname)