import requests
from bs4 import BeautifulSoup
import pandas as pd



class MeffScraper:
    def __init__(self, url):
        self.url = url
        self.response = None
        self.soup = None
        self.futuros = None
        self.options = None
        
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

    def run(self):
        self.fetch_data()
        self.extract_futures()
        self.extract_options()

