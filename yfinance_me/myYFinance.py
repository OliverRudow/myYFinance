"""myYFinance.py."""

__title__: str = "myYFinance"
__version__: str = "0.1.2"
__author__: str = "Oliver Rudow"
__email__: str = "oliver.rudow@googlemail.com"
__copyright__: str = "Copyright 2026, Brain Center Höfen"

# Press ⌃R to execute it or replace it with your code.
# Press Double ⇧ to search everywhere for classes, files, tool windows, actions, and settings.

import dataclasses
import operator
from datetime import datetime, date
from typing import Optional
import yfinance
import yfinance as yf
import pandas as pd
import math
from yfinance import utils as yf_utils
from tuple_me import myTuple
from watchlist_definition_me import (myStaticWatchListDefinitions,
                                     myPerformanceWatchListDefinitions,
                                     myAnalystWatchListDefinitions,
                                     myFundamentalsWatchListDefinitions,
                                     myDerivateWatchListDefinitions,
                                     myCalendarWatchListDefinitions)

LIST_ALLOWED_QUOTE_TYPES: list[str] = ['EQUITY']

def calc_weighted_revisions_index(pd_revision_data: pd.DataFrame) -> str | list:

    list_revision_index: list = []

    if not pd_revision_data.empty:

        _revision_index_7_days: str | float = ''

        _revision_index_30_days: str | float = ''

        _numerator_7_days: float = 0

        _numerator_30_days: float = 0

        _denominator_7_days: float = 0

        _denominator_30_days: float = 0

        for index, row in pd_revision_data.iterrows():

            dict_rev_data = row.to_dict()

            up_last_7_days = dict_rev_data['upLast7days']

            down_last_7_days = dict_rev_data['downLast7Days']

            if isinstance(up_last_7_days, int | float) and isinstance(down_last_7_days, int | float):

                _numerator_7_days = up_last_7_days - down_last_7_days

                _denominator_7_days = up_last_7_days + down_last_7_days

            else:

                _numerator_7_days = 0

                _denominator_7_days = 0

            up_last_30_days = dict_rev_data['upLast30days']

            down_last_30_days = dict_rev_data['downLast30days']

            if isinstance(up_last_30_days, int | float) and isinstance(down_last_30_days, int | float):

                _numerator_30_days = up_last_30_days - down_last_30_days

                _denominator_30_days = up_last_30_days + down_last_30_days

            else:

                _numerator_30_days = 0

                _denominator_30_days = 0

            if _denominator_7_days != 0:

                _revision_index_7_days: float = _numerator_7_days / _denominator_7_days

            else:

                _revision_index_7_days: float = 0

            if _denominator_30_days != 0:

                _revision_index_30_days: float = _numerator_30_days / _denominator_30_days

            else:

                _revision_index_30_days: float = 0

            _revision_body: float = 2 * _revision_index_7_days + _revision_index_30_days

            _revision_weighted: float = round((_revision_body / 3), 2)

            list_revision_index.append(_revision_weighted)

        return list_revision_index

    else:

        return ''

def process_float_list(input_list: list) -> list:

    if all(isinstance(x, float) for x in input_list):

        rounded_list = [round(x, 2) for x in input_list]

        return rounded_list

    else:

        return input_list

def calc_delta_days(int_date_1: int, int_date_2: Optional[int] = None) -> int:

    dt_1 = datetime.fromtimestamp(int_date_1)

    if int_date_2 is None:

        _today = date.today()

        int_date_2: int = int(datetime.combine(_today, datetime.min.time()).timestamp())

    dt_2 = datetime.fromtimestamp(int_date_2)

    delta = dt_2 - dt_1

    return delta.days

@dataclasses.dataclass(init=False)
class MyYFinance:
    """

    """
    _index_tuple: myTuple.MyTuple = dataclasses.field(repr=False, default=type(myTuple.MyTuple))

    # output dicts
    _dict_static_watch_list_data: dict[str, str | bool | None] = dataclasses.field(default_factory=dict)

    _dict_performance_watch_list_data: dict[str, str | int | float | None] = dataclasses.field(default_factory=dict)

    _dict_analyst_watch_list_data: dict[str, str | int | float | None] = dataclasses.field(default_factory=dict)

    _dict_fundamentals_watch_list_data: dict[str, str | int | float | None] = dataclasses.field(default_factory=dict)

    _dict_derivate_watch_list_data: dict[str, str | int | float | None] = dataclasses.field(default_factory=dict)

    _dict_calendar_watch_list_data: dict[str, str | int | None] = dataclasses.field(default_factory=dict)

    # yfinance parameter
    _ticker_y_finance: yfinance.Ticker = dataclasses.field(repr=False, default=yfinance.Ticker)

    _ticker_info: dict = dataclasses.field(default_factory=dict)

    _ticker_eps_revisions: pd.DataFrame = dataclasses.field(default_factory=pd.DataFrame)

    _ticker_history: pd.DataFrame = dataclasses.field(default_factory=pd.DataFrame)

    _ticker_earning_estimate: pd.DataFrame = dataclasses.field(default_factory=pd.DataFrame)

    _ticker_calendar: dict = dataclasses.field(default_factory=dict)

    _bool_ticker_info: bool = dataclasses.field(repr=False, default=False)

    # static watch list
    _str_actual_quote_isin: str = dataclasses.field(repr=False, default='')

    _str_quote_name: str = dataclasses.field(repr=False, default='')

    _str_quote_type: str = dataclasses.field(repr=False, default='')

    _str_quote_symbol: str = dataclasses.field(repr=False, default='')

    _str_quote_sector: str = dataclasses.field(repr=False, default='')

    _str_quote_industry: str = dataclasses.field(repr=False, default='')

    _str_quote_currency: str = dataclasses.field(repr=False, default='')

    _bool_actual_quote_invest_status: bool = dataclasses.field(repr=False, default=False)

    # performance watch list
    _float_quote_ask: float | str = dataclasses.field(repr=False, default=0.0)

    _int_quote_ask_size: int | str = dataclasses.field(repr=False, default=0)

    _float_quote_bid: float | str = dataclasses.field(repr=False, default=0.0)

    _int_quote_bid_size: int | str = dataclasses.field(repr=False, default=0)

    _float_quote_current_price: float | str = dataclasses.field(repr=False, default=0.0)

    _float_quote_day_high: float | str = dataclasses.field(repr=False, default=0.0)

    _float_quote_day_low: float | str = dataclasses.field(repr=False, default=0.0)

    _float_quote_relative_daily_span: float | str = dataclasses.field(repr=False, default=0.0)

    _float_quote_interday_momentum: float | str = dataclasses.field(repr=False, default=0.0)

    _float_quote_open: float | str = dataclasses.field(repr=False, default=0.0)

    _float_quote_previous_close: float | str = dataclasses.field(repr=False, default=0.0)

    _float_regular_market_change_percent: float | str = dataclasses.field(repr=False, default=0.0)

    _float_quote_intraday_momentum: float | str = dataclasses.field(repr=False, default=0.0)

    _int_quote_volume: int | str = dataclasses.field(repr=False, default=0)

    _int_quote_average_volume: int | str = dataclasses.field(repr=False, default=0)

    _float_quote_relative_volume: float | str = dataclasses.field(repr=False, default=0.0)

    _int_quote_average_volume_10_days: int | str = dataclasses.field(repr=False, default=0)

    _float_quote_relative_volume_10_days: float | str = dataclasses.field(repr=False, default=0.0)

    _float_quote_beta: float | str = dataclasses.field(repr=False, default=0.0)

    _float_quote_fifty_two_weeks_low: float | str = dataclasses.field(repr=False, default=0.0)

    _float_quote_fifty_two_weeks_high: float | str = dataclasses.field(repr=False, default=0.0)

    _float_quote_fifty_two_weeks_low_momentum: float | str = dataclasses.field(repr=False, default=0.0)

    _float_quote_fifty_two_weeks_high_momentum: float | str = dataclasses.field(repr=False, default=0.0)

    _float_quote_fifty_day_average: float | str = dataclasses.field(repr=False, default=0.0)

    _float_quote_fifty_day_momentum: float | str = dataclasses.field(repr=False, default=0.0)

    _float_two_hundred_day_average: float | str = dataclasses.field(repr=False, default=0.0)

    _float_two_hundred_day_momentum: float | str = dataclasses.field(repr=False, default=0.0)

    # analyst watch list
    _current_price: str | float = dataclasses.field(repr=False, default=0.0)

    _target_high_price: str | float = dataclasses.field(repr=False, default=0.0)

    _target_low_price: str | float = dataclasses.field(repr=False, default=0.0)

    _target_mean_price: str | float = dataclasses.field(repr=False, default=0.0)

    _upside_potential: str | float = dataclasses.field(repr=False, default=0.0)

    _risk_reward_ratio: str | float = dataclasses.field(repr=False, default=0.0)

    _analyst_dispersion: str | float = dataclasses.field(repr=False, default=0.0)

    _recommendation_mean: str | float = dataclasses.field(repr=False, default=0.0)

    _recommendation_key: str = dataclasses.field(repr=False, default='')

    _number_of_analyst_opinions: int | str = dataclasses.field(repr=False, default=0)

    _weighted_reversion_index: str | float = dataclasses.field(repr=False, default=0.0)

    _list_revision_index: str | list = dataclasses.field(repr=False, default=list)

    # fundamentals
    _trailing_eps: str | float = dataclasses.field(repr=False, default=0.0)

    _forward_eps: str | float =  dataclasses.field(repr=False, default=0.0)

    _trailing_pe: str | float =  dataclasses.field(repr=False, default=0.0)

    _forward_pe: str | float = dataclasses.field(repr=False, default=0.0)

    _price_to_earning_to_growth: str | float = dataclasses.field(repr=False, default=0.0)

    _book_value: str | float =  dataclasses.field(repr=False, default=0.0)

    _price_to_book: str | float = dataclasses.field(repr=False, default=0.0)

    _earnings_quarterly_growth: str | float =  dataclasses.field(repr=False, default=0.0)

    _profit_margins: str | float = dataclasses.field(repr=False, default=0.0)

    _total_cash_per_share: str | float =  dataclasses.field(repr=False, default=0.0)

    _quick_ratio: str | float =  dataclasses.field(repr=False, default=0.0)

    _dividend_yield: str | float =  dataclasses.field(repr=False, default=0.0)

    _payout_ratio: str | float =  dataclasses.field(repr=False, default=0.0)

    _five_year_ave_dividend_yield: str | float = dataclasses.field(repr=False, default=0.0)

    _ratio_dividend_yield: str | float = dataclasses.field(repr=False, default=0.0)

    _ex_dividend_date: str | int = dataclasses.field(repr=False, default='')

    _ex_dividend_delta_date: str | int = dataclasses.field(repr=False, default='')

    _enterprise_to_revenue: str | float = dataclasses.field(repr=False, default=0.0)

    # derivate
    _shares_short: str | int = dataclasses.field(repr=False, default=0)

    _float_shares: str | int = dataclasses.field(repr=False, default=0)

    _short_percent_of_float: str | float = dataclasses.field(repr=False, default=0.0)

    _shares_outstanding: str | int = dataclasses.field(repr=False, default=0)

    _short_ratio: str | float = dataclasses.field(repr=False, default=0.0)

    _shares_short_prior_month: str | int = dataclasses.field(repr=False, default=0)

    _short_percent_change: str | float =  dataclasses.field(repr=False, default=0.0)

    _shares_short_previous_month_date: str | int = dataclasses.field(repr=False, default=0)

    _date_short_interest: str | int = dataclasses.field(repr=False, default=0)

    _short_date_delta_last_month: str | int = dataclasses.field(repr=False, default=0)

    _short_date_delta_this_month: str | int = dataclasses.field(repr=False, default=0)

    _held_percent_insiders: str | float = dataclasses.field(repr=False, default=0.0)

    _held_percent_institutions: str | float = dataclasses.field(repr=False, default=0.0)

    # calendar
    _str_dividend_date: str = dataclasses.field(repr=False, default='')

    _int_dividend_delta_date: int = dataclasses.field(repr=False, default=0)

    _str_ex_dividend_date: str = dataclasses.field(repr=False, default='')

    _int_ex_dividend_delta_date: int = dataclasses.field(repr=False, default=0)

    _str_earnings_date: str = dataclasses.field(repr=False, default='')

    _int_earnings_delta_date: int = dataclasses.field(repr=False, default=0)

    _today: date = dataclasses.field(repr=False, default=date)

    def __init__(self) -> None:

        # init myTuple
        self._index_tuple = myTuple.MyTuple

        self._ticker_info = {}

        self._dict_static_watch_list_data = myStaticWatchListDefinitions.init_dict_static_watch_list_data()

        self._dict_performance_watch_list_data = (
            myPerformanceWatchListDefinitions.init_dict_performance_watch_list_data())

        self._dict_analyst_watch_list_data = myAnalystWatchListDefinitions.init_dict_analyst_watch_list_data()

        self._dict_fundamentals_watch_list_data = (
            myFundamentalsWatchListDefinitions.init_dict_fundamentals_watch_list_data())

        self._dict_derivate_watch_list_data = myDerivateWatchListDefinitions.init_dict_derivate_watch_list_data()

        self._dict_calendar_watch_list_data = myCalendarWatchListDefinitions.init_dict_calendar_watch_list_data()

        self._str_actual_quote_isin = ''

        self._today = date.today()

    def __repr__(self) -> str | dict:

        return self._dict_static_watch_list_data

    def set_actual_quote_isin(self, str_actual_quote_isin: str) -> None:
        self._str_actual_quote_isin = str_actual_quote_isin

    def set_actual_quote_invest_status(self, bool_actual_quote_invest_status: bool) -> None:
        self._bool_actual_quote_invest_status = bool_actual_quote_invest_status

    def get_actual_quote_ticker_data_from_y_finance(self) -> None:
        self._get_quote_ticker_data_from_yfinance()

    @property
    def get_actual_quote_isin(self) -> str:
        return self._str_actual_quote_isin

    @property
    def get_actual_quote_dict_static_watch_list_data(self) -> dict[str, str | bool | None]:

        self._get_quote_static_watch_list_data_from_yfinance()

        return self._dict_static_watch_list_data

    @property
    def get_actual_quote_dict_performance_watch_list_data(self) -> dict[str, str | int | float | None]:

        self._get_quote_performance_watch_list_data_from_yfinance()

        return self._dict_performance_watch_list_data

    @property
    def get_actual_quote_dict_analyst_watch_list_data(self) -> dict[str, str | int | float | None]:
        self._get_quote_analyst_watch_list_data_from_yfinance()

        return self._dict_analyst_watch_list_data

    @property
    def get_actual_quote_dict_fundamentals_watch_list_data(self) -> dict[str, str | int | float | None]:
        self._get_quote_fundamentals_watch_list_data_from_yfinance()

        return self._dict_fundamentals_watch_list_data

    @property
    def get_actual_quote_dict_derivate_watch_list_data(self) -> dict[str, str | int | float | None]:
        self._get_quote_derivate_watch_list_data_from_yfinance()

        return self._dict_derivate_watch_list_data

    @property
    def get_actual_quote_dict_calendar_watch_list_data(self) -> dict[str, str | int | None]:
        self._get_quote_calendar_watch_list_data_from_yfinance()

        return self._dict_calendar_watch_list_data

    def _get_quote_ticker_data_from_yfinance(self)-> None:

        if self._str_actual_quote_isin != '':

            if yf_utils.is_isin(self._str_actual_quote_isin):

                if yf_utils.get_ticker_by_isin(self._str_actual_quote_isin) != '':

                    self._ticker_y_finance = yf.Ticker(self._str_actual_quote_isin)

                    self._ticker_info = self._ticker_y_finance.get_info()

                    if 'quoteType' in self._ticker_info.keys():

                        self._str_quote_type = self._ticker_info['quoteType']

                    else:

                        self._str_quote_type = ''

                    if self._str_quote_type in LIST_ALLOWED_QUOTE_TYPES:

                        self._ticker_eps_revisions = self._ticker_y_finance.get_eps_revisions()

                        self._ticker_history = self._ticker_y_finance.earnings_history

                        self._ticker_earning_estimate = self._ticker_y_finance.earnings_estimate

                        self._ticker_calendar = self._ticker_y_finance.get_calendar()

                        self._bool_ticker_info = True

                    else:

                        self._ticker_eps_revisions = pd.DataFrame()

                        self._ticker_history = pd.DataFrame()

                        self._ticker_earning_estimate = pd.DataFrame()

                        self._ticker_calendar = {}

                else:

                    self._bool_ticker_info = False

                    self._ticker_eps_revisions = pd.DataFrame()

                    self._ticker_history = pd.DataFrame()

                    self._ticker_earning_estimate = pd.DataFrame()

                    self._ticker_calendar = {}

                    print('--- Value Error in ISIN, no data found !---')

            else:

                self._bool_ticker_info = False

                self._ticker_info = {}

                self._ticker_eps_revisions = pd.DataFrame()

                self._ticker_history = pd.DataFrame()

                self._ticker_earning_estimate = pd.DataFrame()

                self._ticker_calendar = {}

                print('--- Value Error: ISIN corrupt!---')

        else:

            self._bool_ticker_info = False

            self._ticker_info = {}

            self._ticker_eps_revisions = pd.DataFrame()

            self._ticker_history = pd.DataFrame()

            self._ticker_earning_estimate = pd.DataFrame()

            self._ticker_calendar = {}

    def _get_quote_static_watch_list_data_from_yfinance(self) -> None:

        if not self._bool_ticker_info:

            self._get_quote_ticker_data_from_yfinance()

        # set quote isin
        self._dict_static_watch_list_data[myStaticWatchListDefinitions.TUPLE_STATIC_WATCH_LIST_QUOTE_ISIN[
            self._index_tuple.OPTION_NAME]] = self._str_actual_quote_isin

        if self._ticker_info.__len__() > 0:

            # quote name
            if 'longName' in self._ticker_info.keys():

                self._str_quote_name = self._ticker_info['longName']

            elif 'shortName' in self._ticker_info.keys():

                self._str_quote_name = self._ticker_info['shortName']

            else:

                self._str_quote_name = ''

            self._dict_static_watch_list_data[myStaticWatchListDefinitions.TUPLE_STATIC_WATCH_LIST_QUOTE_NAME[
                self._index_tuple.OPTION_NAME]] = self._str_quote_name

            # quote type
            if 'quoteType' in self._ticker_info.keys():

                self._str_quote_type = self._ticker_info['quoteType']

            else:

                self._str_quote_type = ''

            self._dict_static_watch_list_data[myStaticWatchListDefinitions.TUPLE_STATIC_WATCH_LIST_QUOTE_TYPE[
                self._index_tuple.OPTION_NAME]] = self._str_quote_type

            if 'symbol' in self._ticker_info.keys():

                self._str_quote_symbol = self._ticker_info['symbol']

            else:

                self._str_quote_symbol = ''

            self._dict_static_watch_list_data[myStaticWatchListDefinitions.TUPLE_STATIC_WATCH_LIST_QUOTE_TICKER_SYMBOL[
                self._index_tuple.OPTION_NAME]] = self._str_quote_symbol

            if 'sector' in self._ticker_info.keys():

                self._str_quote_sector = self._ticker_info['sector']

            else:

                self._str_quote_sector = ''

            self._dict_static_watch_list_data[myStaticWatchListDefinitions.TUPLE_STATIC_WATCH_LIST_QUOTE_SECTOR[
                self._index_tuple.OPTION_NAME]] = self._str_quote_sector

            if 'industry' in self._ticker_info.keys():

                self._str_quote_industry = self._ticker_info['industry']

            else:

                self._str_quote_industry = ''

            self._dict_static_watch_list_data[myStaticWatchListDefinitions.TUPLE_STATIC_WATCH_LIST_QUOTE_INDUSTRY[
                self._index_tuple.OPTION_NAME]] = self._str_quote_industry

            if 'currency' in self._ticker_info.keys():

                self._str_quote_currency = self._ticker_info['currency']

            else:

                self._str_quote_currency = ''

            self._dict_static_watch_list_data[myStaticWatchListDefinitions.TUPLE_STATIC_WATCH_LIST_QUOTE_CURRENCY[
                self._index_tuple.OPTION_NAME]] = self._str_quote_currency

            self._dict_static_watch_list_data[myStaticWatchListDefinitions.TUPLE_STATIC_WATCH_LIST_QUOTE_INVEST_STATUS[
                    self._index_tuple.OPTION_NAME]] = self._bool_actual_quote_invest_status

    def _get_quote_performance_watch_list_data_from_yfinance(self) -> None:

        if not self._bool_ticker_info:

            self._get_quote_ticker_data_from_yfinance()

        self._dict_performance_watch_list_data[
            myPerformanceWatchListDefinitions.TUPLE_PERFORMANCE_WATCH_LIST_QUOTE_ISIN[
                self._index_tuple.OPTION_NAME]] = self._str_actual_quote_isin

        if self._ticker_info.__len__() > 0:

            if 'ask' in self._ticker_info.keys():

                self._float_quote_ask = self._ticker_info['ask']

                if isinstance(self._float_quote_ask, float):

                    self._float_quote_ask = round(self._float_quote_ask, 2)

                else:

                    self._float_quote_ask = ''

            else:

                self._float_quote_ask = ''

            self._dict_performance_watch_list_data[
                myPerformanceWatchListDefinitions.TUPLE_PERFORMANCE_WATCH_LIST_ASK[
                    self._index_tuple.OPTION_NAME]] = self._float_quote_ask

            if 'askSize' in self._ticker_info.keys():

                self._int_quote_ask_size = self._ticker_info['askSize']

                if not isinstance(self._int_quote_ask_size, int):

                    self._int_quote_ask_size = ''

            else:

                self._int_quote_ask_size = ''

            self._dict_performance_watch_list_data[
                myPerformanceWatchListDefinitions.TUPLE_PERFORMANCE_WATCH_LIST_ASK_SIZE[
                    self._index_tuple.OPTION_NAME]] = self._int_quote_ask_size

            if 'bid' in self._ticker_info.keys():

                self._float_quote_bid = self._ticker_info['bid']

                if isinstance(self._float_quote_bid, float):

                    self._float_quote_bid = round(self._float_quote_bid, 2)

                else:

                    self._float_quote_bid = ''

            else:

                self._float_quote_bid = ''

            self._dict_performance_watch_list_data[
                myPerformanceWatchListDefinitions.TUPLE_PERFORMANCE_WATCH_LIST_BID[
                    self._index_tuple.OPTION_NAME]] = self._float_quote_bid

            if 'bidSize' in self._ticker_info.keys():

                self._int_quote_bid_size = self._ticker_info['bidSize']

                if not isinstance(self._int_quote_bid_size, int):

                    self._int_quote_bid_size = ''

            else:

                self._int_quote_bid_size = ''

            self._dict_performance_watch_list_data[
                myPerformanceWatchListDefinitions.TUPLE_PERFORMANCE_WATCH_LIST_BID_SIZE[
                    self._index_tuple.OPTION_NAME]] = self._int_quote_bid_size

            if 'currentPrice' in self._ticker_info.keys():

                self._float_quote_current_price = self._ticker_info['currentPrice']

                if isinstance(self._float_quote_current_price, float):

                    self._float_quote_current_price = round(self._float_quote_current_price, 2)

                else:

                    self._float_quote_current_price = ''

            else:

                self._float_quote_current_price = ''

            self._dict_performance_watch_list_data[
                myPerformanceWatchListDefinitions.TUPLE_PERFORMANCE_WATCH_LIST_CURRENT_PRICE[
                    self._index_tuple.OPTION_NAME]] = self._float_quote_current_price

            if 'dayHigh' in self._ticker_info.keys():

                self._float_quote_day_high = self._ticker_info['dayHigh']

                if isinstance(self._float_quote_day_high, float):

                    self._float_quote_day_high = round(self._float_quote_day_high, 2)

                else:

                    self._float_quote_day_high = ''

            else:

                self._float_quote_day_high = ''

            self._dict_performance_watch_list_data[
                myPerformanceWatchListDefinitions.TUPLE_PERFORMANCE_WATCH_LIST_DAY_HIGH[
                    self._index_tuple.OPTION_NAME]] = self._float_quote_day_high

            if isinstance(self._float_quote_day_high, float) and isinstance(self._float_quote_current_price, float):

                if self._float_quote_current_price > 0:

                    _diff = self._float_quote_day_high - self._float_quote_current_price

                    self._float_quote_interday_momentum = round((_diff / self._float_quote_current_price) * 100, 2)

                else:

                    self._float_quote_interday_momentum = ''

            else:

                self._float_quote_interday_momentum = ''

            self._dict_performance_watch_list_data[
                myPerformanceWatchListDefinitions.TUPLE_PERFORMANCE_WATCH_LIST_INTERDAY_MOMENTUM[
                    self._index_tuple.OPTION_NAME]] = self._float_quote_interday_momentum

            if 'dayLow' in self._ticker_info.keys():

                self._float_quote_day_low = self._ticker_info['dayLow']

                if isinstance(self._float_quote_day_low, float):

                    self._float_quote_day_low = round(self._float_quote_day_low, 2)

                else:

                    self._float_quote_day_low = ''

            else:

                self._float_quote_day_low = ''

            self._dict_performance_watch_list_data[
                myPerformanceWatchListDefinitions.TUPLE_PERFORMANCE_WATCH_LIST_DAY_LOW[
                    self._index_tuple.OPTION_NAME]] = self._float_quote_day_low

            if isinstance(self._float_quote_day_low, float) and isinstance(self._float_quote_day_high, float):

                if self._float_quote_day_low > 0:

                    _diff = self._float_quote_day_high - self._float_quote_day_low

                    self._float_quote_relative_daily_span = round((_diff / self._float_quote_day_low) * 100, 2)

                else:

                    self._float_quote_relative_daily_span = ''

            else:

                self._float_quote_relative_daily_span = ''

            self._dict_performance_watch_list_data[
                myPerformanceWatchListDefinitions.TUPLE_PERFORMANCE_WATCH_LIST_RELATIVE_DAILY_SPAN[
                    self._index_tuple.OPTION_NAME]] = self._float_quote_relative_daily_span

            if 'open' in self._ticker_info.keys():

                self._float_quote_open = self._ticker_info['open']

                if isinstance(self._float_quote_open, float):

                    self._float_quote_open = round(self._float_quote_open, 2)

                else:

                    self._float_quote_open = ''

            else:

                self._float_quote_open = ''

            self._dict_performance_watch_list_data[
                myPerformanceWatchListDefinitions.TUPLE_PERFORMANCE_WATCH_LIST_OPEN[
                    self._index_tuple.OPTION_NAME]] = self._float_quote_open

            if 'previousClose' in self._ticker_info.keys():

                self._float_quote_previous_close = self._ticker_info['previousClose']

                if isinstance(self._float_quote_previous_close, float):

                    self._float_quote_previous_close = round(self._float_quote_previous_close, 2)

                else:

                    self._float_quote_previous_close = ''

            else:

                self._float_quote_previous_close = ''

            self._dict_performance_watch_list_data[
                myPerformanceWatchListDefinitions.TUPLE_PERFORMANCE_WATCH_LIST_PREVIOUS_CLOSE[
                    self._index_tuple.OPTION_NAME]] = self._float_quote_previous_close

            if isinstance(self._float_quote_previous_close, float) and isinstance(self._float_quote_day_low, float):

                if self._float_quote_previous_close > 0:

                    _diff =  self._float_quote_day_low - self._float_quote_previous_close

                    self._float_quote_intraday_momentum = round((_diff / self._float_quote_previous_close) * 100, 2)

                else:

                    self._float_quote_intraday_momentum = ''

            else:

                self._float_quote_intraday_momentum = ''

            self._dict_performance_watch_list_data[
                myPerformanceWatchListDefinitions.TUPLE_PERFORMANCE_WATCH_LIST_INTRADAY_MOMENTUM[
                    self._index_tuple.OPTION_NAME]] = self._float_quote_intraday_momentum


            if 'regularMarketChangePercent' in self._ticker_info.keys():

                self._float_regular_market_change_percent = round(self._ticker_info['regularMarketChangePercent'], 2)

                if not isinstance(self._float_regular_market_change_percent, float):

                    self._float_regular_market_change_percent = ''

            else:

                self._float_regular_market_change_percent = ''

            self._dict_performance_watch_list_data[
                myPerformanceWatchListDefinitions.TUPLE_PERFORMANCE_WATCH_LIST_REGULAR_MARKET_CHANGE_PERCENT[
                    self._index_tuple.OPTION_NAME]] = self._float_regular_market_change_percent

            if 'volume' in self._ticker_info.keys():

                self._int_quote_volume = self._ticker_info['volume']

                if not isinstance(self._int_quote_volume, int):

                    self._int_quote_volume = ''

            else:

                self._int_quote_volume = ''

            self._dict_performance_watch_list_data[
                myPerformanceWatchListDefinitions.TUPLE_PERFORMANCE_WATCH_LIST_VOLUME[
                    self._index_tuple.OPTION_NAME]] = self._int_quote_volume

            if 'averageVolume' in self._ticker_info.keys():

                self._int_quote_average_volume = self._ticker_info['averageVolume']

                if not isinstance(self._int_quote_average_volume, int):

                    self._int_quote_average_volume = ''

            else:

                self._int_quote_average_volume = ''

            self._dict_performance_watch_list_data[
                myPerformanceWatchListDefinitions.TUPLE_PERFORMANCE_WATCH_LIST_AVERAGE_VOLUME[
                    self._index_tuple.OPTION_NAME]] = self._int_quote_average_volume

            if isinstance(self._int_quote_average_volume, int) and isinstance(self._int_quote_volume, int):

                if self._int_quote_average_volume > 0:

                    _fraction = float(self._int_quote_volume) / self._int_quote_average_volume

                    self._float_quote_relative_volume = round(_fraction, 2)

                else:

                    self._float_quote_relative_volume = ''

            else:

                self._float_quote_relative_volume = ''

            self._dict_performance_watch_list_data[
                myPerformanceWatchListDefinitions.TUPLE_PERFORMANCE_WATCH_LIST_RELATIVE_VOLUME[
                    self._index_tuple.OPTION_NAME]] = self._float_quote_relative_volume

            if 'averageDailyVolume10Day' in self._ticker_info.keys():

                self._int_quote_average_volume_10_days = self._ticker_info['averageDailyVolume10Day']

                if not isinstance(self._int_quote_average_volume_10_days, int):

                    self._int_quote_average_volume_10_days = ''

            else:

                self._int_quote_average_volume_10_days = ''

            self._dict_performance_watch_list_data[
                myPerformanceWatchListDefinitions.TUPLE_PERFORMANCE_WATCH_LIST_AVERAGE_DAILY_VOLUME_10_DAY[
                    self._index_tuple.OPTION_NAME]] =  self._int_quote_average_volume_10_days

            if isinstance(self._int_quote_average_volume_10_days, int) and isinstance(self._int_quote_volume, int):

                if self._int_quote_average_volume_10_days > 0:

                    _fraction = float(self._int_quote_volume) / self._int_quote_average_volume_10_days

                    self._float_quote_relative_volume_10_days = round(_fraction, 2)

                else:

                    self._float_quote_relative_volume_10_days = ''

            else:

                self._float_quote_relative_volume_10_days = ''

            self._dict_performance_watch_list_data[
                myPerformanceWatchListDefinitions.TUPLE_PERFORMANCE_WATCH_LIST_RELATIVE_VOLUME_10_DAY[
                    self._index_tuple.OPTION_NAME]] = self._float_quote_relative_volume_10_days

            if 'beta' in self._ticker_info.keys():

                self._float_quote_beta = self._ticker_info['beta']

                if isinstance(self._float_quote_beta, float):

                    self._float_quote_beta = round(self._float_quote_beta, 2)

                else:

                    self._float_quote_beta = ''

            else:

                self._float_quote_beta = ''

            self._dict_performance_watch_list_data[
                myPerformanceWatchListDefinitions.TUPLE_PERFORMANCE_WATCH_LIST_BETA[
                    self._index_tuple.OPTION_NAME]] = self._float_quote_beta

            if 'fiftyTwoWeekLow' in self._ticker_info.keys():

                self._float_quote_fifty_two_weeks_low = self._ticker_info['fiftyTwoWeekLow']

                if isinstance(self._float_quote_fifty_two_weeks_low, float):

                    self._float_quote_fifty_two_weeks_low = round(self._float_quote_fifty_two_weeks_low, 2)

                else:

                    self._float_quote_fifty_two_weeks_low = ''

            else:

                self._float_quote_fifty_two_weeks_low = ''

            self._dict_performance_watch_list_data[
                myPerformanceWatchListDefinitions.TUPLE_PERFORMANCE_WATCH_LIST_FIFTY_TWO_WEEK_LOW[
                    self._index_tuple.OPTION_NAME]] = self._float_quote_fifty_two_weeks_low

            if isinstance(self._float_quote_fifty_two_weeks_low, float) and isinstance(self._float_quote_current_price, float):

                if self._float_quote_fifty_two_weeks_low > 0:

                    _diff = self._float_quote_current_price - self._float_quote_fifty_two_weeks_low

                    self._float_quote_fifty_two_weeks_low_momentum = (
                        round((_diff / self._float_quote_fifty_two_weeks_low) * 100, 2))

                else:

                    self._float_quote_fifty_two_weeks_low_momentum = ''

            else:

                self._float_quote_fifty_two_weeks_low_momentum = ''

            self._dict_performance_watch_list_data[
                myPerformanceWatchListDefinitions.TUPLE_PERFORMANCE_WATCH_LIST_FIFTY_TWO_WEEK_LOW_MOMENTUM[
                    self._index_tuple.OPTION_NAME]] = self._float_quote_fifty_two_weeks_low_momentum


            if 'fiftyTwoWeekHigh' in self._ticker_info.keys():

                self._float_quote_fifty_two_weeks_high = self._ticker_info['fiftyTwoWeekHigh']

                if isinstance(self._float_quote_fifty_two_weeks_high, float):

                    self._float_quote_fifty_two_weeks_high = round(self._float_quote_fifty_two_weeks_high, 2)

                else:

                    self._float_quote_fifty_two_weeks_high = ''

            else:

                self._float_quote_fifty_two_weeks_high = ''

            if isinstance(self._float_quote_fifty_two_weeks_high, float) and isinstance(self._float_quote_current_price, float):

                if self._float_quote_fifty_two_weeks_high > 0:

                    _diff = self._float_quote_current_price - self._float_quote_fifty_two_weeks_high

                    self._float_quote_fifty_two_weeks_high_momentum = (
                        round((_diff / self._float_quote_fifty_two_weeks_high) * 100, 2))

                else:

                    self._float_quote_fifty_two_weeks_high_momentum = ''

            else:

                self._float_quote_fifty_two_weeks_high_momentum = ''

            self._dict_performance_watch_list_data[
                myPerformanceWatchListDefinitions.TUPLE_PERFORMANCE_WATCH_LIST_FIFTY_TWO_WEEK_HIGH[
                    self._index_tuple.OPTION_NAME]] = self._float_quote_fifty_two_weeks_high

            self._dict_performance_watch_list_data[
                myPerformanceWatchListDefinitions.TUPLE_PERFORMANCE_WATCH_LIST_FIFTY_TWO_WEEK_HIGH_MOMENTUM[
                    self._index_tuple.OPTION_NAME]] = self._float_quote_fifty_two_weeks_high_momentum

            if 'fiftyDayAverage' in self._ticker_info.keys():

                self._float_quote_fifty_day_average = self._ticker_info['fiftyDayAverage']

                if isinstance(self._float_quote_fifty_day_average, float):

                    self._float_quote_fifty_day_average = round(self._float_quote_fifty_day_average, 2)

                else:

                    self._float_quote_fifty_day_average = ''

            else:

                self._float_quote_fifty_day_average = ''

            if isinstance(self._float_quote_fifty_day_average, float) and isinstance(self._float_quote_current_price, float):

                if self._float_quote_fifty_day_average > 0:

                    _diff = self._float_quote_current_price - self._float_quote_fifty_day_average

                    self._float_quote_fifty_day_momentum = round((_diff / self._float_quote_fifty_day_average) * 100, 2)

                else:

                    self._float_quote_fifty_day_momentum = ''

            else:

                self._float_quote_fifty_day_momentum = ''

            self._dict_performance_watch_list_data[
                myPerformanceWatchListDefinitions.TUPLE_PERFORMANCE_WATCH_LIST_FIFTY_DAY_AVERAGE[
                    self._index_tuple.OPTION_NAME]] = self._float_quote_fifty_day_average

            self._dict_performance_watch_list_data[
                myPerformanceWatchListDefinitions.TUPLE_PERFORMANCE_WATCH_LIST_FIFTY_DAY_MOMENTUM[
                    self._index_tuple.OPTION_NAME]] = self._float_quote_fifty_day_momentum

            if 'twoHundredDayAverage' in self._ticker_info.keys():

                self._float_two_hundred_day_average = self._ticker_info['twoHundredDayAverage']

                if isinstance(self._float_two_hundred_day_average, float):

                    self._float_two_hundred_day_average = round(self._float_two_hundred_day_average, 2)

                else:

                    self._float_two_hundred_day_average = ''

            else:

                self._float_two_hundred_day_average = ''

            if isinstance(self._float_two_hundred_day_average, float) and isinstance(self._float_quote_current_price,
                                                                                     float):

                if self._float_two_hundred_day_average > 0:

                    _diff = self._float_quote_current_price - self._float_two_hundred_day_average

                    self._float_quote_fifty_day_momentum = round((_diff / self._float_two_hundred_day_average) * 100, 2)

                else:

                    self._float_quote_fifty_day_momentum = ''

            else:

                self._float_quote_fifty_day_momentum = ''

            self._dict_performance_watch_list_data[
                myPerformanceWatchListDefinitions.TUPLE_PERFORMANCE_WATCH_LIST_TWO_HUNDRED_DAY_AVERAGE[
                    self._index_tuple.OPTION_NAME]] = self._float_two_hundred_day_average

            self._dict_performance_watch_list_data[
                myPerformanceWatchListDefinitions.TUPLE_PERFORMANCE_WATCH_LIST_TWO_HUNDRED_DAY_MOMENTUM[
                    self._index_tuple.OPTION_NAME]] = self._float_quote_fifty_day_momentum

    def _get_quote_analyst_watch_list_data_from_yfinance(self) -> None:

        if not self._bool_ticker_info:

            self._get_quote_ticker_data_from_yfinance()

        self._dict_analyst_watch_list_data[
            myAnalystWatchListDefinitions.TUPLE_ANALYST_WATCH_LIST_QUOTE_ISIN[
                self._index_tuple.OPTION_NAME]] = self._str_actual_quote_isin

        if self._ticker_info.__len__() > 0:

            if 'currentPrice' in self._ticker_info.keys():

                self._current_price = self._ticker_info['currentPrice']

                if isinstance(self._ticker_info['currentPrice'], float):

                    self._current_price = round(self._ticker_info['currentPrice'], 2)

                else:

                    self._current_price = ''

            else:

                self._current_price = ''

            self._dict_analyst_watch_list_data[
                myAnalystWatchListDefinitions.TUPLE_ANALYST_WATCH_LIST_CURRENT_PRICE[
                    self._index_tuple.OPTION_NAME]] = self._current_price

            if 'targetHighPrice' in self._ticker_info.keys():

                self._target_high_price = self._ticker_info['targetHighPrice']

                if isinstance(self._ticker_info['targetHighPrice'], float):

                    self._target_high_price = round(self._ticker_info['targetHighPrice'], 2)

                else:

                    self._target_high_price = ''

            else:

                self._target_high_price = ''

            self._dict_analyst_watch_list_data[
                myAnalystWatchListDefinitions.TUPLE_ANALYST_WATCH_LIST_TARGET_HIGH_PRICE[
                    self._index_tuple.OPTION_NAME]] = self._target_high_price

            if 'targetLowPrice' in self._ticker_info.keys():

                self._target_low_price = self._ticker_info['targetLowPrice']

                if isinstance(self._ticker_info['targetLowPrice'], float):

                    self._target_low_price = round(self._ticker_info['targetLowPrice'], 2)

                else:

                    self._target_low_price = ''

            else:

                self._target_low_price = ''

            self._dict_analyst_watch_list_data[
                myAnalystWatchListDefinitions.TUPLE_ANALYST_WATCH_LIST_TARGET_LOW_PRICE[
                    self._index_tuple.OPTION_NAME]] = self._target_low_price

            if 'targetMeanPrice' in self._ticker_info.keys():

                self._target_mean_price = self._ticker_info['targetMeanPrice']

                if isinstance(self._ticker_info['targetMeanPrice'], float):

                    self._target_mean_price = round(self._ticker_info['targetMeanPrice'], 2)

                else:

                    self._target_mean_price = ''

            else:

                self._target_mean_price = ''

            self._dict_analyst_watch_list_data[
                myAnalystWatchListDefinitions.TUPLE_ANALYST_WATCH_LIST_TARGET_MEAN_PRICE[
                    self._index_tuple.OPTION_NAME]] = self._target_mean_price

            if 'targetMedianPrice' in self._ticker_info.keys():

                self._target_median_price = self._ticker_info['targetMedianPrice']

                if isinstance(self._ticker_info['targetMedianPrice'], float):

                    self._target_median_price = round(self._ticker_info['targetMedianPrice'], 2)

                else:

                    self._target_median_price = ''

            else:

                self._target_median_price = ''

            self._dict_analyst_watch_list_data[
                myAnalystWatchListDefinitions.TUPLE_ANALYST_WATCH_LIST_TARGET_MEDIAN_PRICE[
                    self._index_tuple.OPTION_NAME]] = self._target_median_price

            if 'recommendationMean' in self._ticker_info.keys():

                self._recommendation_mean = self._ticker_info['recommendationMean']

                if isinstance(self._ticker_info['recommendationMean'], float):

                    self._recommendation_mean = round(self._ticker_info['recommendationMean'], 2)

                else:

                    self._recommendation_mean = ''

            else:

                self._recommendation_mean = ''

            self._dict_analyst_watch_list_data[
                myAnalystWatchListDefinitions.TUPLE_ANALYST_WATCH_LIST_RECOMMENDATION_MEAN[
                    self._index_tuple.OPTION_NAME]] = self._recommendation_mean

            if 'recommendationKey' in self._ticker_info.keys():

                self._recommendation_key = self._ticker_info['recommendationKey']

                if not isinstance(self._recommendation_key, str):

                    self._recommendation_key = ''

            else:

                self._recommendation_key = ''

            self._dict_analyst_watch_list_data[
                myAnalystWatchListDefinitions.TUPLE_ANALYST_WATCH_LIST_RECOMMENDATION_KEY[
                    self._index_tuple.OPTION_NAME]] = self._recommendation_key

            if 'numberOfAnalystOpinions' in self._ticker_info.keys():

                self._number_of_analyst_opinions = self._ticker_info['numberOfAnalystOpinions']

                if not isinstance(self._ticker_info['numberOfAnalystOpinions'], int):

                    self._number_of_analyst_opinions = ''

            else:

                self._number_of_analyst_opinions = ''

            self._dict_analyst_watch_list_data[
                myAnalystWatchListDefinitions.TUPLE_ANALYST_WATCH_LIST_NUMBER_OF_ANALYST_OPINIONS[
                    self._index_tuple.OPTION_NAME]] = self._number_of_analyst_opinions

            if isinstance(self._current_price, float) and isinstance(self._target_mean_price, float) and self._current_price != 0:

                self._upside_potential = round((self._target_mean_price/self._current_price - 1), 2)

            else:

                self._upside_potential = ''

            self._dict_analyst_watch_list_data[
                myAnalystWatchListDefinitions.TUPLE_ANALYST_WATCH_LIST_UPSIDE_POTENTIAL[
                    self._index_tuple.OPTION_NAME]] = self._upside_potential


            if isinstance(self._target_high_price, float) and isinstance(self._target_low_price, float) and isinstance(self._current_price, float):

                if self._current_price < self._target_high_price:

                    self._risk_reward_ratio = round(( (self._current_price - self._target_low_price) / (self._target_high_price - self._current_price) ),2)

                else:

                    self._risk_reward_ratio = ''

            else:

                self._risk_reward_ratio = ''

            self._dict_analyst_watch_list_data[
                myAnalystWatchListDefinitions.TUPLE_ANALYST_WATCH_LIST_RISK_REWARD_RATIO[
                    self._index_tuple.OPTION_NAME]] = self._risk_reward_ratio

            if isinstance(self._target_high_price, float) and isinstance(self._target_low_price, float) and isinstance(self._target_mean_price, float):

                if self._target_mean_price > 0:

                    self._analyst_dispersion = round(((self._target_high_price - self._target_low_price) / self._target_mean_price), 2)

                else:

                    self._analyst_dispersion = ''

            else:

                self._analyst_dispersion = ''

            self._dict_analyst_watch_list_data[
                myAnalystWatchListDefinitions.TUPLE_ANALYST_WATCH_LIST_ANALYST_DISPERSION[
                    self._index_tuple.OPTION_NAME]] = self._analyst_dispersion

            if not self._ticker_eps_revisions.empty:

                self._list_revision_index = calc_weighted_revisions_index(self._ticker_eps_revisions)

                if isinstance(self._list_revision_index, list):

                    # filter nan
                    self._list_revision_index = [x for x in self._list_revision_index if not (isinstance(x, float) and math.isnan(x))]

                    self._list_revision_index_filtered = (
                        list(map(lambda x: -2 if x < -0.5 else (-1 if x < 0 else (1 if x < 0.5 else 2)),
                             self._list_revision_index)))

                    _list_weighting = [2, 2, 1, 1]

                    self._list_revision_index_filtered = list(map(operator.mul, self._list_revision_index_filtered, _list_weighting))

                    self._int_revision_trend_credit = sum(self._list_revision_index_filtered)

                else:

                    self._int_revision_trend_credit = ''
                    self._list_revision_index_filtered = []

            else:

                self._int_revision_trend_credit = ''
                self._list_revision_index_filtered = []

            self._dict_analyst_watch_list_data[
                myAnalystWatchListDefinitions.TUPLE_ANALYST_WATCH_LIST_WEIGHTED_REVISION_TREND_CREDIT[
                    self._index_tuple.OPTION_NAME]] = self._int_revision_trend_credit

            if isinstance(self._list_revision_index, list) and len(self._list_revision_index) > 0:

                self._dict_analyst_watch_list_data[
                    myAnalystWatchListDefinitions.TUPLE_ANALYST_WATCH_LIST_WEIGHTED_REVISION_INDEX[
                        self._index_tuple.OPTION_NAME]] = self._list_revision_index[0]

                self._dict_analyst_watch_list_data[
                    myAnalystWatchListDefinitions.TUPLE_ANALYST_WATCH_LIST_WEIGHTED_REVISION_TREND[
                        self._index_tuple.OPTION_NAME]] = str(self._list_revision_index)

            else:

                self._dict_analyst_watch_list_data[
                    myAnalystWatchListDefinitions.TUPLE_ANALYST_WATCH_LIST_WEIGHTED_REVISION_INDEX[
                        self._index_tuple.OPTION_NAME]] = ''

                self._dict_analyst_watch_list_data[
                    myAnalystWatchListDefinitions.TUPLE_ANALYST_WATCH_LIST_WEIGHTED_REVISION_TREND[
                        self._index_tuple.OPTION_NAME]] = ''

    def _get_quote_fundamentals_watch_list_data_from_yfinance(self) -> None:

        if not self._bool_ticker_info:

            self._get_quote_ticker_data_from_yfinance()

        self._dict_fundamentals_watch_list_data[
            myFundamentalsWatchListDefinitions.TUPLE_FUNDAMENTALS_WATCH_LIST_QUOTE_ISIN[
                self._index_tuple.OPTION_NAME]] = self._str_actual_quote_isin

        if self._ticker_info.__len__() > 0:

            if 'trailingEps' in self._ticker_info.keys():

                self._trailing_eps =  self._ticker_info['trailingEps']

                if isinstance(self._trailing_eps, float):

                    self._trailing_eps = round(self._trailing_eps, 2)

                else:

                    self._trailing_eps = ''

            else:

                self._trailing_eps = ''

            self._dict_fundamentals_watch_list_data[
                myFundamentalsWatchListDefinitions.TUPLE_FUNDAMENTALS_WATCH_LIST_TRAILING_EPS[
                    self._index_tuple.OPTION_NAME]] = self._trailing_eps

            if 'forwardEps' in self._ticker_info.keys():

                self._forward_eps = self._ticker_info['forwardEps']

                if isinstance(self._forward_eps, float):

                    _forward_eps = round(self._forward_eps, 2)

                else:

                    self._forward_eps = ''

            else:

                self._forward_eps = ''

            self._dict_fundamentals_watch_list_data[
                myFundamentalsWatchListDefinitions.TUPLE_FUNDAMENTALS_WATCH_LIST_FORWARD_EPS[
                    self._index_tuple.OPTION_NAME]] = self._forward_eps

            if 'trailingPE' in self._ticker_info.keys():

                self._trailing_pe = self._ticker_info['trailingPE']

                if isinstance(self._trailing_pe, float):

                    self._trailing_pe = round(self._trailing_pe, 2)

                else:

                    self._trailing_pe = ''

            else:

                self._trailing_pe = ''

            self._dict_fundamentals_watch_list_data[
                myFundamentalsWatchListDefinitions.TUPLE_FUNDAMENTALS_WATCH_LIST_TRAILING_PE[
                    self._index_tuple.OPTION_NAME]] = self._trailing_pe

            if 'forwardPE' in self._ticker_info.keys():

                self._forward_pe = self._ticker_info['forwardPE']

                if isinstance(self._forward_pe, float):

                    self._forward_pe = round(self._forward_pe, 2)

                else:

                    self._forward_pe = ''

            else:

                self._forward_pe = ''

            self._dict_fundamentals_watch_list_data[
                myFundamentalsWatchListDefinitions.TUPLE_FUNDAMENTALS_WATCH_LIST_FORWARD_PE[
                    self._index_tuple.OPTION_NAME]] = self._forward_pe

            if isinstance(self._trailing_pe, float) and isinstance(self._forward_pe, float):

                if not self._forward_pe == 0.0:

                    self._price_to_earning_to_growth = round((self._trailing_pe / self._forward_pe), 2)

                else:

                    self._price_to_earning_to_growth = ''

            else:

                self._price_to_earning_to_growth = ''

            self._dict_fundamentals_watch_list_data[
                myFundamentalsWatchListDefinitions.TUPLE_FUNDAMENTALS_WATCH_LIST_PRICE_TO_EARNING_TO_GROWTH[
                    self._index_tuple.OPTION_NAME]] = self._price_to_earning_to_growth

            if 'bookValue' in self._ticker_info.keys():

                self._book_value = self._ticker_info['bookValue']

                if isinstance(self._book_value, float):

                    self._book_value = round(self._book_value, 2)

                else:

                    self._book_value = ''

            else:

                self._book_value = ''

            self._dict_fundamentals_watch_list_data[
                myFundamentalsWatchListDefinitions.TUPLE_FUNDAMENTALS_WATCH_LIST_BOOK_VALUE[
                    self._index_tuple.OPTION_NAME]] = self._book_value

            if 'priceToBook' in self._ticker_info.keys():

                self._price_to_book = self._ticker_info['priceToBook']

                if isinstance(self._price_to_book, float):

                    self._price_to_book = round(self._price_to_book, 2)

                else:

                    self._price_to_book = ''

            else:

                self._price_to_book = ''

            self._dict_fundamentals_watch_list_data[
                myFundamentalsWatchListDefinitions.TUPLE_FUNDAMENTALS_WATCH_LIST_PRICE_TO_BOOK[
                    self._index_tuple.OPTION_NAME]] = self._price_to_book

            if 'earningsQuarterlyGrowth' in self._ticker_info.keys():

                self._earnings_quarterly_growth = self._ticker_info['earningsQuarterlyGrowth']

                if isinstance(self._earnings_quarterly_growth, float):

                    self._earnings_quarterly_growth = round(self._earnings_quarterly_growth, 2)

                else:

                    self._earnings_quarterly_growth = ''

            else:

                self._earnings_quarterly_growth = ''

            self._dict_fundamentals_watch_list_data[
                myFundamentalsWatchListDefinitions.TUPLE_FUNDAMENTALS_WATCH_LIST_EARNINGS_QUARTERLY_GROWTH[
                    self._index_tuple.OPTION_NAME]] = self._earnings_quarterly_growth

            if 'growth' in self._ticker_earning_estimate.columns:

                _growth = list(self._ticker_earning_estimate['growth'].to_dict().values())

                # round list
                _growth = str(process_float_list(_growth))

                self._dict_fundamentals_watch_list_data[
                    myFundamentalsWatchListDefinitions.TUPLE_FUNDAMENTALS_WATCH_LIST_GROWTH_TREND[
                        self._index_tuple.OPTION_NAME]] = _growth

            else:

                self._dict_fundamentals_watch_list_data[
                    myFundamentalsWatchListDefinitions.TUPLE_FUNDAMENTALS_WATCH_LIST_GROWTH_TREND[
                        self._index_tuple.OPTION_NAME]] = ''


            if 'surprisePercent' in self._ticker_history.columns:

                if not self._ticker_history.empty:

                    _surprise_count_row = self._ticker_history['surprisePercent'].apply(
                        lambda x: -1 if x < 0 else (1 if x < 0.1 else 2))

                    _surprise_count_row = list(_surprise_count_row.to_dict().values())

                    _surprise_cross_sum = sum(_surprise_count_row)

                    _surprise_count_row = str(_surprise_count_row)

                else:

                    _surprise_count_row = ''

                    _surprise_cross_sum = ''

                self._dict_fundamentals_watch_list_data[
                    myFundamentalsWatchListDefinitions.TUPLE_FUNDAMENTALS_WATCH_LIST_SURPRISE_TREND[
                        self._index_tuple.OPTION_NAME]] = _surprise_count_row

                self._dict_fundamentals_watch_list_data[
                    myFundamentalsWatchListDefinitions.TUPLE_FUNDAMENTALS_WATCH_LIST_SURPRISE_CREDIT[
                        self._index_tuple.OPTION_NAME]] = _surprise_cross_sum

            else:

                self._dict_fundamentals_watch_list_data[
                    myFundamentalsWatchListDefinitions.TUPLE_FUNDAMENTALS_WATCH_LIST_SURPRISE_TREND[
                        self._index_tuple.OPTION_NAME]] = ''

                self._dict_fundamentals_watch_list_data[
                    myFundamentalsWatchListDefinitions.TUPLE_FUNDAMENTALS_WATCH_LIST_SURPRISE_CREDIT[
                        self._index_tuple.OPTION_NAME]] = ''

            if 'profitMargins' in self._ticker_info.keys():

                self._profit_margins = self._ticker_info['profitMargins']

                if isinstance(self._profit_margins, float):

                    self._profit_margins = round(self._profit_margins, 2)

                else:

                    self._profit_margins = ''

            else:

                self._profit_margins = ''

            self._dict_fundamentals_watch_list_data[
                myFundamentalsWatchListDefinitions.TUPLE_FUNDAMENTALS_WATCH_LIST_PROFIT_MARGINS[
                    self._index_tuple.OPTION_NAME]] = self._profit_margins

            if 'totalCashPerShare' in self._ticker_info.keys():

                self._total_cash_per_share = self._ticker_info['totalCashPerShare']

                if isinstance(self._total_cash_per_share, float):

                    self._total_cash_per_share = round(self._total_cash_per_share, 2)

                else:

                    self._total_cash_per_share = ''

            else:

                self._total_cash_per_share = ''

            self._dict_fundamentals_watch_list_data[
                myFundamentalsWatchListDefinitions.TUPLE_FUNDAMENTALS_WATCH_LIST_TOTAL_CASH_PER_SHARE[
                    self._index_tuple.OPTION_NAME]] = self._total_cash_per_share

            if 'quickRatio' in self._ticker_info.keys():

                self._quick_ratio = self._ticker_info['quickRatio']

                if isinstance(self._quick_ratio, float):

                    self._quick_ratio = round(self._quick_ratio, 2)

                else:

                    self._quick_ratio = ''

            else:

                self._quick_ratio = ''

            self._dict_fundamentals_watch_list_data[
                myFundamentalsWatchListDefinitions.TUPLE_FUNDAMENTALS_WATCH_LIST_QUICK_RATIO[
                    self._index_tuple.OPTION_NAME]] = self._quick_ratio

            if 'dividendYield' in self._ticker_info.keys():

                self._dividend_yield = self._ticker_info['dividendYield']

                if isinstance(self._dividend_yield, float):

                    self._dividend_yield = round(self._dividend_yield, 2)

                else:

                    self._dividend_yield = ''

            else:

                self._dividend_yield = ''

            self._dict_fundamentals_watch_list_data[
                myFundamentalsWatchListDefinitions.TUPLE_FUNDAMENTALS_WATCH_LIST_DIVIDEND_YIELD[
                    self._index_tuple.OPTION_NAME]] = self._dividend_yield

            if 'payoutRatio' in self._ticker_info.keys():

                self._payout_ratio = self._ticker_info['payoutRatio']

                if isinstance(self._payout_ratio, float):

                    self._payout_ratio = round(self._payout_ratio, 2)

                else:

                    self._payout_ratio = ''

            else:

                self._payout_ratio = ''

            self._dict_fundamentals_watch_list_data[
                myFundamentalsWatchListDefinitions.TUPLE_FUNDAMENTALS_WATCH_LIST_PAYOUT_RATIO[
                    self._index_tuple.OPTION_NAME]] = self._payout_ratio

            if 'fiveYearAvgDividendYield' in self._ticker_info.keys():

                self._five_year_ave_dividend_yield = self._ticker_info['fiveYearAvgDividendYield']

                if isinstance(self._five_year_ave_dividend_yield, float):

                    self._five_year_ave_dividend_yield = round(self._five_year_ave_dividend_yield, 2)

                else:

                    self._five_year_ave_dividend_yield = ''

            else:

                self._five_year_ave_dividend_yield = ''

            if isinstance(self._five_year_ave_dividend_yield, float) and self._five_year_ave_dividend_yield > 0:

                if isinstance(self._dividend_yield, float):

                    self._ratio_dividend_yield = round(self._dividend_yield / self._five_year_ave_dividend_yield, 2)

                else:

                    self._ratio_dividend_yield = ''

            else:

                self._ratio_dividend_yield = ''

            self._dict_fundamentals_watch_list_data[
                myFundamentalsWatchListDefinitions.TUPLE_FUNDAMENTALS_WATCH_LIST_FIVE_YEAR_AVE_DIVIDEND_YIELD[
                    self._index_tuple.OPTION_NAME]] = self._five_year_ave_dividend_yield

            self._dict_fundamentals_watch_list_data[
                myFundamentalsWatchListDefinitions.TUPLE_FUNDAMENTALS_WATCH_LIST_RATIO_DIVIDEND_YIELD[
                    self._index_tuple.OPTION_NAME]] = self._ratio_dividend_yield

            if 'exDividendDate' in self._ticker_info.keys():

                self._ex_dividend_date: str | int = self._ticker_info['exDividendDate']

                self._dict_fundamentals_watch_list_data[
                    myFundamentalsWatchListDefinitions.TUPLE_FUNDAMENTALS_WATCH_LIST_EX_DIVIDED_DATE[
                        self._index_tuple.OPTION_NAME]] = self._ex_dividend_date

            else:

                self._dict_fundamentals_watch_list_data[
                    myFundamentalsWatchListDefinitions.TUPLE_FUNDAMENTALS_WATCH_LIST_EX_DIVIDED_DATE[
                        self._index_tuple.OPTION_NAME]] = ''

            if isinstance(self._ex_dividend_date, int):

                self._ex_dividend_delta_date = calc_delta_days(self._ex_dividend_date)

                if self._ex_dividend_delta_date > 365:

                    self._ex_dividend_delta_date = 365

            else:

                self._ex_dividend_delta_date = ''

            self._dict_fundamentals_watch_list_data[
                myFundamentalsWatchListDefinitions.TUPLE_FUNDAMENTALS_WATCH_LIST_EX_DIVIDED_DELTA_DATE[
                    self._index_tuple.OPTION_NAME]] = self._ex_dividend_delta_date

            if 'enterpriseToRevenue' in self._ticker_info.keys():

                self._enterprise_to_revenue = self._ticker_info['enterpriseToRevenue']

                if isinstance(self._enterprise_to_revenue, float):

                    self._enterprise_to_revenue = round(self._enterprise_to_revenue, 2)

                else:

                    self._enterprise_to_revenue = ''

            else:

                self._enterprise_to_revenue = ''

            self._dict_fundamentals_watch_list_data[
                myFundamentalsWatchListDefinitions.TUPLE_FUNDAMENTALS_WATCH_LIST_ENTERPRISE_TO_REVENUE[
                    self._index_tuple.OPTION_NAME]] = self._enterprise_to_revenue

    def _get_quote_derivate_watch_list_data_from_yfinance(self) -> None:

        if not self._bool_ticker_info:

            self._get_quote_ticker_data_from_yfinance()

        self._dict_derivate_watch_list_data[
            myDerivateWatchListDefinitions.TUPLE_DERIVATE_WATCH_LIST_QUOTE_ISIN[
                self._index_tuple.OPTION_NAME]] = self._str_actual_quote_isin

        if self._ticker_info.__len__() > 0:

            if 'sharesShort' in self._ticker_info.keys():

                self._shares_short = self._ticker_info['sharesShort']

                if not isinstance(self._shares_short, int):

                    self._shares_short = ''

            else:

                self._shares_short = ''

            self._dict_derivate_watch_list_data[
                myDerivateWatchListDefinitions.TUPLE_DERIVATE_WATCH_LIST_SHARES_SHORT[
                    self._index_tuple.OPTION_NAME]] = self._shares_short

            if 'floatShares' in self._ticker_info.keys():

                self._float_shares = self._ticker_info['floatShares']

                if not isinstance(self._float_shares, int):

                    self._float_shares = ''

            else:

                self._float_shares = ''

            self._dict_derivate_watch_list_data[
                myDerivateWatchListDefinitions.TUPLE_DERIVATE_WATCH_LIST_FLOAT_SHARES[
                    self._index_tuple.OPTION_NAME]] = self._float_shares

            if isinstance(self._float_shares, int) and isinstance(self._shares_short, int):

                if self._float_shares > 0:

                    self._short_percent_of_float = round(self._shares_short * 100 /self._float_shares, 2)

                else:

                    self._short_percent_of_float = ''

            else:

                self._short_percent_of_float = ''

            self._dict_derivate_watch_list_data[
                myDerivateWatchListDefinitions.TUPLE_DERIVATE_WATCH_LIST_SHORT_PERCENT_OF_FLOAT[
                    self._index_tuple.OPTION_NAME]] = self._short_percent_of_float

            if 'sharesOutstanding' in self._ticker_info.keys():

                self._shares_outstanding = self._ticker_info['sharesOutstanding']

                if not isinstance(self._shares_outstanding, int):

                    self._shares_outstanding = ''

            else:

                self._shares_outstanding = ''

            self._dict_derivate_watch_list_data[
                myDerivateWatchListDefinitions.TUPLE_DERIVATE_WATCH_LIST_SHARES_OUTSTANDING[
                    self._index_tuple.OPTION_NAME]] = self._shares_outstanding

            if 'shortRatio' in self._ticker_info.keys():

                self._short_ratio = self._ticker_info['shortRatio']

                if isinstance(self._short_ratio, float):

                    self._short_ratio = round(self._short_ratio, 2)

                else:

                    self._short_ratio = ''

            else:

                self._short_ratio = ''

            self._dict_derivate_watch_list_data[
                myDerivateWatchListDefinitions.TUPLE_DERIVATE_WATCH_LIST_SHORT_RATIO[
                    self._index_tuple.OPTION_NAME]] = self._short_ratio

            if 'sharesShortPriorMonth' in self._ticker_info.keys():

                self._shares_short_prior_month = self._ticker_info['sharesShortPriorMonth']

                if not isinstance(self._shares_short_prior_month, int):

                    self._shares_short_prior_month = ''

            else:

                self._shares_short_prior_month = ''


            self._dict_derivate_watch_list_data[
                myDerivateWatchListDefinitions.TUPLE_DERIVATE_WATCH_LIST_SHARES_SHORT_PRIOR_MONTH[
                    self._index_tuple.OPTION_NAME]] = self._shares_short_prior_month

            if isinstance(self._shares_short_prior_month, int) and isinstance(self._shares_short, int):

                if self._shares_short_prior_month > 0:

                    self._short_percent_change = round(
                        (self._shares_short / self._shares_short_prior_month - 1) * 100, 2)

                else:

                    self._short_percent_change = ''

            else:

                self._short_percent_change = ''

            self._dict_derivate_watch_list_data[
                myDerivateWatchListDefinitions.TUPLE_DERIVATE_WATCH_LIST_SHORT_PERCENT_CHANGE[
                    self._index_tuple.OPTION_NAME]] = self._short_percent_change

            if 'sharesShortPreviousMonthDate' in self._ticker_info.keys():

                self._shares_short_previous_month_date = self._ticker_info['sharesShortPreviousMonthDate']

                if not isinstance(self._shares_short_previous_month_date, int):

                    self._shares_short_previous_month_date = ''

            else:

                self._shares_short_previous_month_date = ''

            self._dict_derivate_watch_list_data[
                myDerivateWatchListDefinitions.TUPLE_DERIVATE_WATCH_LIST_SHARES_SHORT_PREVIOUS_MONTH_DATE[
                    self._index_tuple.OPTION_NAME]] = self._shares_short_previous_month_date

            if 'dateShortInterest' in self._ticker_info.keys():

                self._date_short_interest: str | int = self._ticker_info['dateShortInterest']

                if not isinstance(self._date_short_interest, int):

                    self._date_short_interest = ''

            else:

                self._date_short_interest = ''

            self._dict_derivate_watch_list_data[
                myDerivateWatchListDefinitions.TUPLE_DERIVATE_WATCH_LIST_DATE_SHORT_INTEREST[
                    self._index_tuple.OPTION_NAME]] = self._date_short_interest

            if isinstance(self._shares_short_previous_month_date, int) and self._shares_short_previous_month_date > 0:

                if isinstance(self._date_short_interest, int) and self._date_short_interest > 0:

                    self._short_date_delta_last_month = abs(
                        calc_delta_days(self._shares_short_previous_month_date, self._date_short_interest))

                else:

                    self._short_date_delta_last_month = ''

            else:

                self._short_date_delta_last_month = ''

            self._dict_derivate_watch_list_data[
                myDerivateWatchListDefinitions.TUPLE_DERIVATE_WATCH_LIST_SHORT_DATE_DELTA_LAST_MONTH[
                    self._index_tuple.OPTION_NAME]] = self._short_date_delta_last_month

            if isinstance(self._date_short_interest, int) and self._date_short_interest > 0:

                self._short_date_delta_this_month = abs(calc_delta_days(self._date_short_interest))

            else:

                self._short_date_delta_this_month = ''

            self._dict_derivate_watch_list_data[
                myDerivateWatchListDefinitions.TUPLE_DERIVATE_WATCH_LIST_SHORT_DATE_DELTA_THIS_MONTH[
                    self._index_tuple.OPTION_NAME]] = self._short_date_delta_this_month

            if 'heldPercentInsiders' in self._ticker_info.keys():

                self._held_percent_insiders = self._ticker_info['heldPercentInsiders']

                if isinstance(self._held_percent_insiders, float):

                    self._held_percent_insiders = round(self._held_percent_insiders, 2)

                else:

                    self._held_percent_insiders = ''

            else:

                self._held_percent_insiders = ''

            self._dict_derivate_watch_list_data[
                myDerivateWatchListDefinitions.TUPLE_DERIVATE_WATCH_LIST_HELD_PERCENT_INSIDERS[
                    self._index_tuple.OPTION_NAME]] = self._held_percent_insiders

            if 'heldPercentInstitutions' in self._ticker_info.keys():

                self._held_percent_institutions = self._ticker_info['heldPercentInstitutions']

                if isinstance(self._held_percent_institutions, float):

                    self._held_percent_institutions = round(self._held_percent_institutions, 2)

                else:

                    self._held_percent_institutions = ''

            else:

                self._held_percent_institutions = ''

            self._dict_derivate_watch_list_data[
                myDerivateWatchListDefinitions.TUPLE_DERIVATE_WATCH_LIST_HELD_PERCENT_INSTITUTIONS[
                    self._index_tuple.OPTION_NAME]] = self._held_percent_institutions

    def _get_quote_calendar_watch_list_data_from_yfinance(self) -> None:

        if not self._bool_ticker_info:

            self._get_quote_ticker_data_from_yfinance()

        self._dict_calendar_watch_list_data[
            myCalendarWatchListDefinitions.TUPLE_CALENDAR_WATCH_LIST_QUOTE_ISIN[
                self._index_tuple.OPTION_NAME]] = self._str_actual_quote_isin

        if 'Dividend Date' in self._ticker_calendar.keys():

            _dividend_date = self._ticker_calendar['Dividend Date']

            if isinstance(_dividend_date, date):

                self._str_dividend_date = _dividend_date.strftime('%Y-%m-%d')

                _delta = _dividend_date - self._today

                self._int_dividend_date = _delta.days

            else:

                self._str_dividend_date = ''

                self._int_dividend_date = ''

            self._dict_calendar_watch_list_data[
                myCalendarWatchListDefinitions.TUPLE_CALENDAR_WATCH_LIST_DIVIDEND_DATE[
                    self._index_tuple.OPTION_NAME]] = self._str_dividend_date

            self._dict_calendar_watch_list_data[
                myCalendarWatchListDefinitions.TUPLE_CALENDAR_WATCH_LIST_DIVIDEND_DELTA_DATE[
                    self._index_tuple.OPTION_NAME]] = self._int_dividend_date

        if 'Ex-Dividend Date' in self._ticker_calendar.keys():

            _ex_dividend_date = self._ticker_calendar['Ex-Dividend Date']

            if isinstance(_ex_dividend_date, date):

                self._str_ex_dividend_date = _ex_dividend_date.strftime('%Y-%m-%d')

                _delta = _ex_dividend_date -  self._today

                self._int_ex_dividend_date = _delta.days

            else:

                self._str_ex_dividend_date = ''

                self._int_ex_dividend_date = ''

            self._dict_calendar_watch_list_data[
                myCalendarWatchListDefinitions.TUPLE_CALENDAR_WATCH_LIST_EX_DIVIDEND_DATE[
                    self._index_tuple.OPTION_NAME]] = self._str_ex_dividend_date

            self._dict_calendar_watch_list_data[
                myCalendarWatchListDefinitions.TUPLE_CALENDAR_WATCH_LIST_EX_DIVIDEND_DELTA_DATE[
                    self._index_tuple.OPTION_NAME]] = self._int_ex_dividend_date

        if 'Earnings Date' in self._ticker_calendar.keys():

            _earnings_date = self._ticker_calendar['Earnings Date']

            if isinstance(_earnings_date, date):

                self._str_earnings_date = _earnings_date.strftime('%Y-%m-%d')

                _delta =  _earnings_date - self._today

                self._int_earnings_date = _delta.days

            elif isinstance(_earnings_date, list):

                if _earnings_date.__len__() == 0:

                    self._str_earnings_date = ''

                    self._int_earnings_date = ''

                elif _earnings_date.__len__() == 1:

                    _earnings_date = _earnings_date[0]

                    if isinstance(_earnings_date, date):

                        self._str_earnings_date = _earnings_date.strftime('%Y-%m-%d')

                        _delta =  _earnings_date - self._today

                        self._int_earnings_date = _delta.days

                    else:

                        self._str_earnings_date = ''

                        self._int_earnings_date = ''

                else:

                    _list_delta_earnings_date = []

                    for elem in _earnings_date:

                        if isinstance(elem, date):

                            _delta = elem - self._today

                            _list_delta_earnings_date.append(_delta.days)

                    if _list_delta_earnings_date.__len__() > 0:

                        minimum = min(_list_delta_earnings_date)
                        index_minimums = _list_delta_earnings_date.index(minimum)

                        self._str_earnings_date = _earnings_date[index_minimums].strftime('%Y-%m-%d')

                        self._int_earnings_date = minimum

                    else:

                        self._str_earnings_date = ''

                        self._int_earnings_date = ''

            else:

                self._str_earnings_date = ''

                self._int_earnings_date = ''

            self._dict_calendar_watch_list_data[
                myCalendarWatchListDefinitions.TUPLE_CALENDAR_WATCH_LIST_EARNINGS_DATE[
                    self._index_tuple.OPTION_NAME]] = self._str_earnings_date

            self._dict_calendar_watch_list_data[
                myCalendarWatchListDefinitions.TUPLE_CALENDAR_WATCH_LIST_EARNINGS_DELTA_DATE[
                    self._index_tuple.OPTION_NAME]] = self._int_earnings_date


if __name__ == "__main__":
    my_y_fiance = MyYFinance()
    str_isin = 'US0378331005'
    # str_isin = 'NL0011683594'
    # str_isin = 'DE000A11QW68'
    my_y_fiance.set_actual_quote_invest_status(True)
    my_y_fiance.set_actual_quote_isin(str_isin)
    print(my_y_fiance.get_actual_quote_dict_static_watch_list_data)
    print('-------------------------------------------------')
    print(my_y_fiance.get_actual_quote_dict_performance_watch_list_data)
    print('-------------------------------------------------')
    print(my_y_fiance.get_actual_quote_dict_analyst_watch_list_data)
    print('-------------------------------------------------')
    print(my_y_fiance.get_actual_quote_dict_fundamentals_watch_list_data)
    print('-------------------------------------------------')
    print(my_y_fiance.get_actual_quote_dict_derivate_watch_list_data)
    print('-------------------------------------------------')
    print(my_y_fiance.get_actual_quote_dict_calendar_watch_list_data)
