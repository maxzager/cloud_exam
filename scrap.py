import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import datetime
import calculate_iv as iv


class MeffScraper:
    def __init__(self, url):
        self.url = url
        self.response = None
        self.soup = None
        self.futuros = None
        self.options = None
        self.options_new = None
        
    def fetch_data(self):
        self.response = requests.get(self.url)
        self.soup = BeautifulSoup(self.response.content, 'html.parser')

    def extract_futures(self):
        fut_table = self.soup.find('table', {'id': 'Contenido_Contenido_tblFuturos'})
        self.futuros = pd.read_html(str(fut_table))[0]
        self.futuros.columns = self.futuros.columns.droplevel(1)
        self.futuros = self.futuros.iloc[0,-1]
        self.futuros = float(self.futuros.replace('.', '').replace(',', '.'))

    def extract_options(self):
        trs_ope = self.soup.find_all('tr', attrs={'data-tipo': lambda x: x and x.startswith('OPE')})
        trs_oce = self.soup.find_all('tr', attrs={'data-tipo': lambda x: x and x.startswith('OCE')})
        trs = trs_ope + trs_oce
        rows = []

        for tr in trs:
            tds = tr.find_all('td')
            data_tipo = tr['data-tipo']
            row = {
                'DATA-TIPO': data_tipo,
                'STRIKE': tds[0].text,
                'ANT': tds[-1].text,
            }
            rows.append(row)

        self.options = pd.DataFrame(rows)

    def process_options(self):
        self.options_new = self.options.copy()
        self.options_new = self.options_new.loc[~self.options_new['ANT'].str.contains('–|-', regex=True)]
        self.options_new["EXP_DATE"] = self.options_new["DATA-TIPO"].str[3:11]
        self.options_new["EXP_DATE"] = pd.to_datetime(self.options_new["EXP_DATE"], format='%Y%m%d')
        self.options_new["DTE"] = (self.options_new["EXP_DATE"].dt.date - datetime.date.today()).dt.days
        self.options_new["ANT"] = self.options_new["ANT"].str.replace(".", "", regex=False).str.replace(",", ".", regex=False)
        self.options_new["STRIKE"] = self.options_new["STRIKE"].str.replace(".", "", regex=False).str.replace(",", ".", regex=False)
        self.options_new["ANT"] = pd.to_numeric(self.options_new["ANT"], errors='coerce')
        self.options_new["STRIKE"] = pd.to_numeric(self.options_new["STRIKE"], errors='coerce')
        self.options_new["IV"] = self.options_new.apply(lambda row: iv.calculate_iv(row, self.futuros), axis=1)
        self.options_new["EXP_DATE"] = self.options_new["EXP_DATE"].dt.strftime('%Y-%m-%d')
        #classify options as call or put
        self.options_new["CALL_PUT"] = np.where(self.options_new["DATA-TIPO"].str[1] == "C", "CALL", "PUT")

    def run(self):
        self.fetch_data()
        self.extract_futures()
        self.extract_options()
        self.process_options()

