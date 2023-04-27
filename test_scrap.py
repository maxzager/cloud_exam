import os
import pandas as pd
from scrap import MeffScraper

url = 'https://www.meff.es/esp/Derivados-Financieros/Ficha/FIEM_MiniIbex_35'

def test_extract_futures():
    scraper = MeffScraper(url)
    scraper.fetch_data()
    scraper.extract_futures()
    assert isinstance(scraper.futuros, float)
    assert scraper.futuros > 0


def test_extract_options():
    scraper = MeffScraper(url)
    scraper.fetch_data()
    scraper.extract_options()
    assert isinstance(scraper.options, pd.DataFrame)
    assert not scraper.options.empty
    assert "ANT" in scraper.options.columns

