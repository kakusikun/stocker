from util import *

class Revenue:
    m_mapping = {'上市':'sii','上櫃':'otc'}
    base_url = 'https://mops.twse.com.tw/nas/t21/{}/t21sc03_{}_{}_0.html' 
    def __init__(self, mkt_type, year, month, url=base_url, m_mapping=m_mapping):
        self.mkt_type = m_mapping[mkt_type] if mkt_type in m_mapping else None
        year = year if year < 1000 else year-1911
        self.year = year #yyy
        self.month = month
        self.url = url.format(self.mkt_type, self.year, self.month)
        
    def add_raw(self):
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36'}    
        r = requests.get(self.url, headers=headers)
        r.encoding = 'big5'
        dfs = pd.read_html(StringIO(r.text))
        self.raw_data = dfs
        
    def unify(self, smp=True):
        data = pd.concat([data for data in self.raw_data if data.shape[1] <= 11 and data.shape[1] > 5]\
                       ,axis=0,ignore_index=True)
        if 'levels' in dir(data.columns):
            data.columns = data.columns.get_level_values(1)
        else:
            data = data[list(range(0,10))]
            column_index = data.index[(data[0] == '公司代號')][0]
            data.columns = data.iloc[column_index]
        data['當月營收'] = pd.to_numeric(data['當月營收'], 'coerce')
        data = data[~data['當月營收'].isnull()]
        data = data[~data['公司代號'].str.contains('合計')]
        if '備註' not in data.columns:
            data['備註'] = '-'
        data.drop_duplicates(subset='公司代號', keep='first', inplace=True)
        # 置換例外資料
        if (self.year,self.month)==(102,1):
            data.replace(to_replace='不適用', value=np.NaN, inplace=True)            
        data = data.drop('備註', axis=1)
        data['年'] = self.year
        data['月'] = self.month
        if smp==True:
            clms = ['年','月','公司代號','公司名稱','當月營收','去年當月營收','去年同月增減(%)']
        else:
            clms = ['年','月','公司代號','公司名稱','當月營收','去年當月營收','去年同月增減(%)'\
                    ,'上月營收','上月比較增減(%)','前期比較增減(%)','去年累計營收','當月累計營收']
        data = data[clms]
        data = data.rename(columns={'當月營收':f'{self.month}月營收'
                            ,'去年當月營收':f'去年{self.month}月營收'
                            ,'去年同月增減(%)':f'{self.month}月營收年成長(%)'})
        data = clean(data)        
        self.data = data