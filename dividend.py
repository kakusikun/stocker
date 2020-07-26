from util import *

# etf 股利
class EtfDiv:
    def __init__(self, year, start='0101', end='1231'):
        year = year if year > 1000 else year+1911
        self.year = year #yyyy
        self.start = start
        self.end = end
        self.url = f"https://www.twse.com.tw/exchangeReport/TWT49U?response=json&strDate={year}{start}&endDate={year}{end}"
        self.headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36'}
        
    def add_raw(self):
        r = requests.get(self.url, headers=self.headers)  
        d = json.loads(r.text)
        data = pd.DataFrame(data=d['data'], columns=d['fields'])
        data = data[data.股票代號.str.startswith('0')]
        self.raw_data = data

    def unify(self):
        self.raw_data['詳細資料'] = self.raw_data['詳細資料'].apply(lambda x:x.split("'")[1][9:])
        self.raw_data.drop(['漲停價格','跌停價格','開盤競價基準','最近一次申報資料 季別/日期',\
                   '最近一次申報每股 (單位)淨值','最近一次申報每股 (單位)盈餘'], axis=1, inplace=True)
        self.raw_data['資料日期'] = self.raw_data['詳細資料'].apply(lambda x:x[-8:])
        self.raw_data = self.raw_data[self.raw_data['除權息前收盤價']!=self.raw_data['減除股利參考價']]
        
        def stockDividend(dtl):
            headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36'}
            basic_url = 'https://www.twse.com.tw/zh/'
            url = basic_url+dtl
            r = requests.get(url, headers=headers)
            d = pd.read_html(StringIO(r.text))[0]
            tgt = d.iloc[4][1].split(' ')[0]
            time.sleep(3)
            return tgt

        def cashDividend(dtl):
            headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36'}
            basic_url = 'https://www.twse.com.tw/zh/'
            url = basic_url+dtl
            r = requests.get(url, headers=headers)
            d = pd.read_html(StringIO(r.text))[0]
            tgt = d.iloc[2][1].split(' ')[0]
            time.sleep(3)
            return tgt
        
        x1 = self.raw_data[self.raw_data['權/息']=='息']
        x1['現金股利'] = x1['權值+息值']
        x1['股票股利'] = 0
        x2 = self.raw_data[self.raw_data['權/息']=='權']
        x2['現金股利'] = 0
        x2['股票股利'] = x2['詳細資料'].apply(stockDividend)
        x12 = self.raw_data[self.raw_data['權/息']=='權息']
        x12['現金股利']=x12['詳細資料'].apply(cashDividend)
        x12['股票股利']=x12['詳細資料'].apply(stockDividend)

        d_all = pd.concat([x1,x2,x12],ignore_index=True)
        d_all = d_all[['資料日期', '股票代號', '股票名稱', '現金股利', '股票股利', '詳細資料']]
        self.data = d_all
        
# 公司股利
class Dividend:
    m_mapping = {'上市':'sii','上櫃':'otc'}
    def __init__(self, mkt_type, year, m_mapping=m_mapping):
        year = year if year <= 1000 else year-1911
        self.mkt_type = m_mapping[mkt_type]
        self.year = str(year) #yyy
        self.url = f"https://mops.twse.com.tw/mops/web/ajax_t108sb27"
        self.headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36'}
        
    def add_raw(self):
        form = {
            "step": "1",
            "firstin": "1",
            "TYPEK": self.mkt_type,
            "year": self.year,
            "type": "2"
        }
        r = requests.post(self.url, data=form, headers=self.headers)  
        self.raw_data = pd.read_html(StringIO(r.text))[0]

    def unify(self):
        d = self.raw_data
        d.columns = d.columns.get_level_values(-1)
        d = d[d['公司代號']!='公司代號']
        d['資料日期'] = d[['除權交易日' , '除息交易日']].apply(lambda x:x[0] if x[0] is not np.nan else x[1], axis=1)
        for i in ['盈餘分配之股東現金股利(元/股)' , '法定盈餘公積、資本公積發放之現金(元/股)', \
                 '盈餘轉增資配股(元/股)' , '法定盈餘公積、資本公積轉增資配股(元/股)']:
            d[i] = d[i].replace(to_replace='-', value=np.nan)
        d['現金股利'] = d[['盈餘分配之股東現金股利(元/股)' , '法定盈餘公積、資本公積發放之現金(元/股)']].apply\
            (lambda x:float(x[0])+float(x[1]) if x[0] is not np.nan and x[1] is not np.nan else np.nan, axis=1)
        d['股票股利'] = d[['盈餘轉增資配股(元/股)' , '法定盈餘公積、資本公積轉增資配股(元/股)']].apply\
            (lambda x:(float(x[0])+float(x[1]))*100 if x[0] is not np.nan and x[1] is not np.nan else np.nan, axis=1)
        d = d[['資料日期', '公司代號', '公司名稱', '現金股利', '股票股利']]
        d = d.fillna(0)
        d = d[(d['現金股利']!=0) | (d['股票股利']!=0)]
        d = d.drop_duplicates()
        def f(x):
            x = x.split('/')
            return str(int(x[0])+1911)+x[1]+x[2]
        d['資料日期'] = d['資料日期'].apply(f)
        d['MKT'] = '上市' if self.mkt_type=='sii' else '上櫃'
        cols = list(d.columns)
        d = d[cols[:1]+cols[-1:]+cols[1:-1]]
        self.data = d

# 減資換發新股
class CptlReduct:
    m_mapping = {'上市':'sii','上櫃':'otc'}
    def __init__(self, mkt_type, year, start='0101', end='1231', m_mapping=m_mapping):
        eg_year = year if year > 1000 else year+1911 #yyyy
        cn_year = year if year < 1000 else year-1911
        self.mkt_type = m_mapping[mkt_type]
        if self.mkt_type=='sii':
            self.year = eg_year 
            self.full_start = f'{eg_year}{start}'
            self.full_end = f'{eg_year}{end}'
            self.url = f'https://www.twse.com.tw/exchangeReport/TWTAUU?response=json&strDate={self.full_start}&endDate={self.full_end}'
        elif self.mkt_type=='otc':
            self.year = cn_year 
            self.full_start = f'{cn_year}/{start[:2]}/{start[2:]}'
            self.full_end = f'{cn_year}/{end[:2]}/{end[2:]}'
            self.url = f'https://www.tpex.org.tw/web/stock/exright/revivt/revivt_result.php?l=zh-tw&d={self.full_start}&ed={self.full_end}&s=0,asc,0&o=csv'
        self.headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36'}
        
    def add_raw(self):
        if self.mkt_type=='sii':
            r = requests.get(self.url, headers=self.headers)  
            d = json.loads(r.text)
            data = pd.DataFrame(data=d['data'], columns=d['fields'])
            data = data.rename(columns={'停止買賣前收盤價格':'停止買賣前價格'})
            self.raw_data = data
        elif self.mkt_type=='otc':
            r = requests.get(self.url, headers=self.headers)  
            d = pd.read_csv(StringIO(r.text), header = ["股票代號" in l for l in r.text.split("\n")].index(True))
            d = d[~d.股票代號.isnull()]
            d.股票代號 = d.股票代號.astype(int)
            d.股票代號 = d.股票代號.astype(str)
            data = d.rename(columns={'恢復買賣日期 ':'恢復買賣日期'
                                    ,'最後交易日之收盤價格':'停止買賣前價格'
                                    ,'減資恢復買賣開始日參考價格':'恢復買賣參考價'
                                    ,'開始交易基準價':'開盤競價基準'})
            data['恢復買賣日期'] = data['恢復買賣日期'].apply(lambda x:f'{x[:3]}/{x[3:5]}/{x[5:]}')
            self.raw_data = data

    def unify(self):
        data = self.raw_data
        data = data[data['停止買賣前價格']!=data['恢復買賣參考價']]
        data.drop(['漲停價格','跌停價格','開盤競價基準','除權參考價'], axis=1, inplace=True)
        
        # 102 年前上櫃無減資資料
        if self.mkt_type=='otc' and self.year<102:
            self.data = self.raw_data
            
        elif self.mkt_type=='sii':
            data['詳細資料'] = data['詳細資料'].apply(lambda x:x.split("'")[1][9:])
            def rdc(x):
                p1, p2, reason, dtl = x[0], x[1], x[2], x[3]
                if reason=='彌補虧損':
                    exchange_ratio,refund = float(p1)/float(p2)*1000,0
                else:
                    stockId = dtl.split('STK_NO=')[1].rstrip()
                    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36'}
                    basic_url = 'https://www.twse.com.tw/zh/'
                    url = basic_url+dtl
                    r = requests.get(url, headers=headers)
                    d = pd.read_html(StringIO(r.text))[0]
                    exchange_ratio = float(d.iloc[3][1].split(' ')[0])
                    refund = float(d.iloc[4][1].split(' ')[0])
                    time.sleep(4)
                return exchange_ratio,refund
            tmpDtl = data[['停止買賣前價格','恢復買賣參考價','減資原因','詳細資料']].apply(rdc, axis=1)                    
            data['每千股換發股數'] = tmpDtl.apply(lambda x:x[0])
            data['每股退還金額'] = tmpDtl.apply(lambda x:x[1])
            cols = ['恢復買賣日期', '股票代號', '名稱', '停止買賣前價格', '恢復買賣參考價', '減資原因', '每千股換發股數', '每股退還金額']
            data = data[cols]
            data = data.rename(columns={'恢復買賣日期':'資料日期'})
            for i in ['每千股換發股數', '每股退還金額']:
                data[i] = data[i].apply(lambda x:round(x,2))
            for i in ['停止買賣前價格', '恢復買賣參考價', '每千股換發股數', '每股退還金額']:
                data[i] = data[i].astype(float)

            def f(x):
                x = x.split('/')
                return str(int(x[0])+1911)+x[1]+x[2]
            data['資料日期'] = data['資料日期'].apply(f)
            data['MKT'] = '上市' if self.mkt_type=='sii' else '上櫃'
            cols = list(data.columns)
            data = data[cols[:1]+cols[-1:]+cols[1:-1]]
            self.data = data
            
        elif self.mkt_type=='otc' and self.year>=102:
            # 簡化計算
            def rdc(x):
                p1, p2 = x[0], x[1]
                exchange_ratio,refund = float(p1)/float(p2)*1000,0
                return exchange_ratio,refund
            tmpDtl = data[['停止買賣前價格','恢復買賣參考價']].apply(rdc, axis=1)                  
            data['每千股換發股數'] = tmpDtl.apply(lambda x:x[0])
            data['每股退還金額'] = tmpDtl.apply(lambda x:x[1])
            cols = ['恢復買賣日期', '股票代號', '名稱', '停止買賣前價格', '恢復買賣參考價', '減資原因', '每千股換發股數', '每股退還金額']
            data = data[cols]
            data = data.rename(columns={'恢復買賣日期':'資料日期'})
            for i in ['每千股換發股數', '每股退還金額']:
                data[i] = data[i].apply(lambda x:round(x,2))
            for i in ['停止買賣前價格', '恢復買賣參考價', '每千股換發股數', '每股退還金額']:
                data[i] = data[i].astype(float)

            def f(x):
                x = x.split('/')
                return str(int(x[0])+1911)+x[1]+x[2]
            data['資料日期'] = data['資料日期'].apply(f)
            data['MKT'] = '上市' if self.mkt_type=='sii' else '上櫃'
            cols = list(data.columns)
            data = data[cols[:1]+cols[-1:]+cols[1:-1]]
            self.data = data