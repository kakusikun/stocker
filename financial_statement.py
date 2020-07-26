from util import *
from logger import setup_logger
from urllib3.exceptions import NewConnectionError

logger = setup_logger('.')


# 
# 
'''

合併資產負債表
    流動資產 => 流動資產合計
        現金及約當現金 
        短期投資 => 透過損益按公允價值衡量之金融資產－流動
        應收帳款及票據 => 應收帳款淨額 + 應收帳款－關係人淨額
        存貨
        其餘流動資產 => 流動資產合計 - (以上)
    長期投資 => 採用權益法之投資
    固定資產 => 不動產、廠房及設備
    總資產 => 資產總計 => 期初、期末 => ROA
    每股淨值 => 每股參考淨值
    歸屬於母公司業主之權益合計 => 期初、期末 => ROA
    權益總額 => ROE杜邦

    流動負債 => 流動負債合計
    長期負債 => 長期借款
    總負債 => 負債總額
    淨值 => 權益總額

'''

# 資產
url = 'https://mops.twse.com.tw/mops/web/t164sb03'
form = {
    'encodeURIComponent':1,
    'step':1,
    'firstin':1,
    'off':1,
    'queryName': 'co_id',
    'inpuType': 'co_id',
    'TYPEK': 'all',
    'isnew': 'false',
    'co_id': '2353',
    'year': '108',
    'season': '04',
}
headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) \
            AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
r = requests.post(url, form, headers=headers)

'''
合併綜合損益表
    營收 => 營業收入合計
    毛利 => 營業毛利（毛損）淨額
    營業費用 => 營業費用合計
        銷售費用 => 推銷費用
        管理費用
        研發費用 => 研究發展費用
    營業利益 => 營業利益（損失）
    稅前淨利 => 稅前淨利（淨損）=> ROA
    稅後淨利 => 本期淨利（淨損）
    母公司業主淨利 => 母公司業主（淨利∕損）
    每股盈餘 => 基本每股盈餘
    ----------------------- ROA
    所得稅費用（利益）合計 
    繼續營業單位本期淨利（淨損）

業外收支佔稅前淨利比
    營業外收入及支出合計 / 稅前淨利（淨損）
'''
# 損益
url = 'https://mops.twse.com.tw/mops/web/t164sb04'

'''
現金流量
    折舊 => 折舊費用
    攤銷 => 攤銷費用	
    營業現金流 => 營業活動之淨現金流入（流出）
    投資現金流 => 投資活動之淨現金流入（流出）
    融資現金流 => 籌資活動之淨現金流入（流出）
    資本支出 => 取得不動產、廠房及設備
    自由現金流 => 營業現金流 - 資本支出
    淨現金流 => 本期現金及約當現金增加（減少）數 - 匯率變動對現金及約當現金之影響
    利息費用 => ROA

'''
# 現金
url = 'https://mops.twse.com.tw/mops/web/t164sb05'


'''
營益分析
    毛利率
    營業利益率
    稅前淨利率
    稅後淨利率

operating-expense-ratio
    X / 營業收入合計 
        營業費用率
        銷售費用率
        管理費用率
        研發費用率

'''

'''
ROA = ( 繼續營業單位本期淨利（淨損） + (利息費用 * ( 1 - 所得稅費用（利益）合計 / 稅前淨利（淨損）))) / (資產總計 => 期初、期末 => 平均)
ROE = ( 繼續營業單位本期淨利（淨損） + (利息費用 * ( 1 - 所得稅費用（利益）合計 / 稅前淨利（淨損）))) / (歸屬於母公司業主之權益合計 => 期初、期末 => 平均)

ROE 杜邦拆解：ROE = 淨利率 * 資產週轉率 * 權益乘數
    稅後淨利率 => 繼續營業單位本期淨利（淨損）/ 營業收入合計
    總資產週轉 => 營業收入合計 / 資產總計
    權益乘數 => 資產總計 / 權益總額
'''

class FS():
    def __init__(self, fs_type, co_id=1101, latest=True, year=109, season=1, market='sii'):
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
                logger.info('sleep')
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
            if len(self.df) >= 11:
                df = pd.DataFrame(columns=[self.fs_type, 'amount'])
                try:
                    df[self.fs_type] = self.df[(f'民國{self.year}年第{self.season}季', '單位：新台幣仟元', '會計項目', 'Unnamed: 0_level_3')]
                except KeyError:
                    self.get(step=2)
                    df[self.fs_type] = self.df[(f'民國{self.year}年第{self.season}季', '單位：新台幣仟元', '會計項目', 'Unnamed: 0_level_3')]

                try:
                    df['amount'] = self.df[ (f'民國{self.year}年第{self.season}季', '單位：新台幣仟元', f'{self.year}年{self.month[self.season-1]:02}月{self.day[self.season-1]}日', '金額')]
                except KeyError:
                    try:
                        df['amount'] = self.df[ (f'民國{self.year}年第{self.season}季', '單位：新台幣仟元', f'{self.year}年{self.from_month[0]:02}月01日至{self.year}年{self.month[self.season-1]:02}月{self.day[self.season-1]}日', '金額')]
                    except KeyError:
                        df['amount'] = self.df[ (f'民國{self.year}年第{self.season}季', '單位：新台幣仟元', f'{self.year}年第{self.season}季', '金額')]
                

                self.df = df
                self.df.amount.fillna(0.0, inplace=True)
                return True
            else:
                return False
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

    
    def save(self):
        if self.fs_type in ['asset', 'income', 'cashflow']:
            self.df.to_pickle(f'C:\\Users\\oo245\\Documents\\stocker\\data\\{self.fs_type}_{self.year}_{self.season}_{self.co_id}.pkl')
        if self.fs_type == 'profit':
            self.df.to_pickle(f'C:\\Users\\oo245\\Documents\\stocker\\data\\{self.fs_type}_{self.year}_{self.season}.pkl')

    def get_index(self):
        self.clean()
        return self.df['index'].to_numpy().tolist()

        

if __name__ == "__main__":
    for year in range(104, 110):
        fs = FS(fs_type='profit', year=year)
        index = fs.get_index()
        
        for season in range(1,5):
            fname = f'C:\\Users\\oo245\\Documents\\stocker\\data\\profit_{year}_{season}.pkl'
            logger.info(f'profit_{year}_{season}')
            if not os.path.exists(fname):
                fs = FS(fs_type='profit', year=year, season=season)
                if fs.clean():
                    fs.save()
                time.sleep(5)

            for co_id in index:
                for fs_type in ['asset', 'income', 'cashflow']:
                    fname = f'C:\\Users\\oo245\\Documents\\stocker\\data\\{fs_type}_{year}_{season}_{co_id}.pkl'
                    logger.info(f'{fs_type}_{year}_{season}_{co_id}')
                    if not os.path.exists(fname):
                        fs = FS(fs_type=fs_type, co_id=co_id, latest=False, year=year, season=season, market='sii')
                        if fs.clean():
                            fs.save()
                        time.sleep(5)