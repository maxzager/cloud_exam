import pandas as pd
import numpy as np
import datetime
import calculate_iv as iv


class adding_variables:

    def __init__(self, options: pd.DataFrame, futuros: float):
        self.futuros = futuros
        self.options = options


    def run(self):
        self.options = self.options.loc[~self.options['ANT'].str.contains('–|-', regex=True)].copy()
        self.options.loc[:, "EXP_DATE"] = self.options["DATA-TIPO"].str[3:11]
        self.options["EXP_DATE"] = pd.to_datetime(self.options["EXP_DATE"], format='%Y%m%d')
        self.options.loc[:, "DTE"] = (self.options["EXP_DATE"].dt.date - datetime.date.today()).dt.days
        self.options.loc[:, "ANT"] = self.options["ANT"].str.replace(".", "", regex=False).str.replace(",", ".", regex=False)
        self.options.loc[:, "STRIKE"] = self.options["STRIKE"].str.replace(".", "", regex=False).str.replace(",", ".", regex=False)
        self.options["ANT"] = pd.to_numeric(self.options["ANT"], errors='coerce')
        self.options["STRIKE"] = pd.to_numeric(self.options["STRIKE"], errors='coerce')
        self.options.loc[:, "IV"] = self.options.apply(lambda row: iv.calculate_iv(row, self.futuros), axis=1)
        self.options["EXP_DATE"] = self.options["EXP_DATE"].dt.strftime('%Y-%m-%d')
        self.options.loc[:, "CALL_PUT"] = np.where(self.options["DATA-TIPO"].str[1] == "C", "CALL", "PUT")
        self.options.loc[:, "TTM"] = self.options["DTE"] / 365
        self.options.loc[:, "MONEYNES"] = np.where(self.options["CALL_PUT"] == "CALL", self.options["STRIKE"] / self.futuros, self.futuros / self.options["STRIKE"])
