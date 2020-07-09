import pandas as pd
import requests
import numpy as np
from io import StringIO
import time
from datetime import datetime, timedelta
import calendar
import datetime as dt
from functools import reduce
import json
import os
from collections import Counter

class FinRatio():
    m_mapping = {'上市':'sii','上櫃':'otc'}
    base_url = 'https://mops.twse.com.tw/mops/web/'
    after_ifrs_mapping = {
        '營益分析':base_url+'t163sb06',
        '財務結構分析':base_url+'t51sb02'
    }
    before_ifrs_mapping = {
        '營益分析':base_url+'t51sb06',
        '財務結構分析':base_url+'ajax_t51sb02'
    }

    def __init__(self, market, year, season, table):
        self.year =  year if year < 1000 else year-1911
        self.season = '0'+str(season) if type(season)==int else season
        self.market = self.m_mapping[market] if market in self.m_mapping else None
        self.table = table
        table_mapping = self.after_ifrs_mapping if year>=102 else self.before_ifrs_mapping
        self.url = table_mapping[self.table] if self.table in table_mapping else None

    def get_raw(self):
        form = {
            'encodeURIComponent':1,
            'step':1,
            'firstin':1,
            'off':1,
            'TYPEK':self.market,
            'year':str(self.year),
            'season':self.season
        }
        form['ifrs'] = 'Y' if self.year >= 102 else 'N'            
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) \
                    AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
        r = requests.post(self.url, form, headers=headers)
        r.encoding = 'utf8'
        dfs = pd.read_html(StringIO(r.text))
        self.raw = dfs

    def parse(self):
        if self.table=='營益分析':
            dfs = [i for i in self.raw if i.shape[0]>5]
            dfs = [i for i in dfs if i.shape[1]>5]
            data = dfs[0]
            data.columns = ['公司代號','公司名稱','營業收入(百萬元)','毛利率(%)','營業利益率(%)','稅前純益率(%)','稅後純益率(%)']
            data = data[data['公司代號']!='公司代號']
            data = data.reset_index().drop('index', axis=1)
            data['財報年度'] = self.year+1911 #yyyy
            data['季'] = self.season
            self.data = data

        elif self.table=='財務結構分析':
            dfs = [i for i in self.raw if i.shape[0]>5]
            dfs = [i for i in dfs if i.shape[1]>5]
            data = dfs[0]
            data.columns = data.columns.get_level_values(1)
            data = data[data['公司代號']!='公司代號']
            data = data.reset_index().drop('index', axis=1)
            data.rename(columns={'股東權益報酬率(%)':'權益報酬率(%)'
                                 ,'不動產、廠房及設備週轉率(次)':'固定資產週轉率(次)'
                                 ,'負債佔資產比率(%)':'負債比率(%)'
                                 ,'公司簡稱':'公司名稱'}, inplace=True)
            data['財報年度'] = self.year+1911 #yyyy
            # if self.smp==True :
            #     clms = list(data.columns)
            #     clms = [i for i in clms if i not in \
            #            ['平均收現日數','平均售貨日數','平均銷貨日數'
            #             ,'長期資金佔不動產、廠房及設備比率(%)','純益率(%)','長期資金佔固定資產比率(%)'
            #             ,'應收款項收現日數','稅前純益佔實收資本比率(%)','營業利益佔實收資本比率(%)']]
            #     data = data[clms]
            self.data = data