import QuantLib as ql
import numpy as np

def calculate_iv(row, futuros):
    
    option_type = ql.Option.Call if row["DATA-TIPO"][1] == "C" else ql.Option.Put
    settlement_date = ql.Date.todaysDate()
    expiration_date = ql.Date(row["EXP_DATE"].day, row["EXP_DATE"].month, row["EXP_DATE"].year)
    calendar = ql.NullCalendar()
    day_count = ql.Actual365Fixed()
    interest_rate = ql.SimpleQuote(0.0)
    dividend_yield = ql.SimpleQuote(0.0)
    underlying_price = ql.SimpleQuote(futuros)

    interest_rate_ts = ql.FlatForward(settlement_date, ql.QuoteHandle(interest_rate), day_count)
    dividend_yield_ts = ql.FlatForward(settlement_date, ql.QuoteHandle(dividend_yield), day_count)
    underlying_ts = ql.SimpleQuote(futuros)
    underlying_price_ts = ql.FlatForward(settlement_date, ql.QuoteHandle(underlying_price), day_count)

    exercise = ql.EuropeanExercise(expiration_date)
    payoff = ql.PlainVanillaPayoff(option_type, row["STRIKE"])
    option = ql.VanillaOption(payoff, exercise)

    process = ql.BlackScholesMertonProcess(ql.QuoteHandle(underlying_price),
                                            ql.YieldTermStructureHandle(dividend_yield_ts),
                                            ql.YieldTermStructureHandle(interest_rate_ts),
                                            ql.BlackVolTermStructureHandle(ql.BlackConstantVol(settlement_date, calendar, 0.20, day_count)))

    option.setPricingEngine(ql.AnalyticEuropeanEngine(process))
    try:
        iv = option.impliedVolatility(row["ANT"], process)
        return iv * 100
    except RuntimeError:
        return np.nan
