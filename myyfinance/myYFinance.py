"""myYFinance.py."""

import logging
import math
from datetime import date, datetime
from typing import Optional

import pandas as pd
import yfinance
from yfinance import utils as yf_utils

from mysharesdefinition import (
    myAnalystWatchListDefinitions,
    myCalendarWatchListDefinitions,
    myDerivateWatchListDefinitions,
    myFundamentalsWatchListDefinitions,
    myPerformanceWatchListDefinitions,
    myStaticWatchListDefinitions,
)
from mytuple import myTuple

__title__: str = "myYFinance"
__version__: str = "1.0.0"
__author__: str = "Oliver Rudow"
__email__: str = "oliver.rudow@googlemail.com"
__copyright__: str = "Copyright 2026, Brain Center Höfen"

logger: logging.Logger = logging.getLogger(__name__)

LIST_ALLOWED_QUOTE_TYPES: list[str] = ['EQUITY']

# Magic numbers as constants
MAX_DELTA_DAYS: int = 365
REVISION_WEIGHT_SHORT: int = 2
REVISION_WEIGHT_LONG: int = 1
REVISION_WEIGHT_DIVISOR: int = 3
REVISION_THRESHOLD_NEGATIVE_HIGH: float = -0.5
REVISION_THRESHOLD_NEGATIVE_LOW: float = 0.0
REVISION_THRESHOLD_POSITIVE_LOW: float = 0.0
REVISION_THRESHOLD_POSITIVE_HIGH: float = 0.5
FLOAT_PRECISION: int = 2

def calc_weighted_revisions_index(pd_revision_data: pd.DataFrame) -> list[float]:
    """Calculate weighted revision index from EPS revision data."""
    if pd_revision_data.empty:
        return []

    list_revision_index: list[float] = []

    for _, row in pd_revision_data.iterrows():
        dict_rev_data = row.to_dict()

        # 7-day revision index
        up_7 = dict_rev_data.get('upLast7days')
        down_7 = dict_rev_data.get('downLast7Days')
        if isinstance(up_7, (int, float)) and isinstance(down_7, (int, float)):
            denom_7 = up_7 + down_7
            index_7 = (up_7 - down_7) / denom_7 if denom_7 != 0 else 0
        else:
            index_7 = 0

        # 30-day revision index
        up_30 = dict_rev_data.get('upLast30days')
        down_30 = dict_rev_data.get('downLast30days')
        if isinstance(up_30, (int, float)) and isinstance(down_30, (int, float)):
            denom_30 = up_30 + down_30
            index_30 = (up_30 - down_30) / denom_30 if denom_30 != 0 else 0
        else:
            index_30 = 0

        revision_body = REVISION_WEIGHT_SHORT * index_7 + index_30
        revision_weighted = round(revision_body / REVISION_WEIGHT_DIVISOR, FLOAT_PRECISION)
        list_revision_index.append(revision_weighted)

    return list_revision_index


def process_float_list(input_list: list[float]) -> list[float]:
    """Round all floats in a list to 2 decimal places if all elements are floats."""
    if all(isinstance(x, float) for x in input_list):
        return [round(x, FLOAT_PRECISION) for x in input_list]
    return input_list


def calc_delta_days(int_date_1: int, int_date_2: Optional[int] = None) -> int:
    """Calculate the number of days between two timestamps."""
    dt_1 = datetime.fromtimestamp(int_date_1)

    if int_date_2 is None:
        _today = date.today()
        int_date_2 = int(datetime.combine(_today, datetime.min.time()).timestamp())

    dt_2 = datetime.fromtimestamp(int_date_2)
    return (dt_2 - dt_1).days


def safe_get_float(info: dict[str, object], key: str) -> float | str:
    """Safely get a float value from a dict, rounding to 2 decimals."""
    value = info.get(key)
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return round(float(value), FLOAT_PRECISION)
    return ''


def safe_get_int(info: dict[str, object], key: str) -> int | str:
    """Safely get an int value from a dict, converting float if needed."""
    value = info.get(key)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    return ''


def safe_get_str(info: dict[str, object], key: str) -> str:
    """Safely get a string value from a dict."""
    value = info.get(key)
    if isinstance(value, str):
        return value
    return ''

class MyYFinance:
    """Fetch and process stock data from yfinance into dedicated watch-list dicts."""

    def __init__(self) -> None:
        # Tuple index
        self._index_tuple: myTuple.MyTuple = myTuple.MyTuple

        # Output dicts (will be initialized from definitions at end of __init__)
        self._dict_static_watch_list_data: dict[str, str | bool | None]
        self._dict_performance_watch_list_data: dict[str, str | int | float | None]
        self._dict_analyst_watch_list_data: dict[str, str | int | float | None]
        self._dict_fundamentals_watch_list_data: dict[str, str | int | float | None]
        self._dict_derivate_watch_list_data: dict[str, str | int | float | None]
        self._dict_calendar_watch_list_data: dict[str, str | int | None]

        # Caching flags per watch list category
        self._cache_static: bool = False
        self._cache_performance: bool = False
        self._cache_analyst: bool = False
        self._cache_fundamentals: bool = False
        self._cache_derivate: bool = False
        self._cache_calendar: bool = False

        # yfinance parameters
        self._ticker_y_finance: Optional[yfinance.Ticker] = None
        self._ticker_info: dict = {}
        self._ticker_eps_revisions: pd.DataFrame = pd.DataFrame()
        self._ticker_history: pd.DataFrame = pd.DataFrame()
        self._ticker_earning_estimate: pd.DataFrame = pd.DataFrame()
        self._ticker_calendar: dict = {}
        self._bool_ticker_info: bool = False

        # Static watch list
        self._str_actual_quote_isin: str = ''
        self._str_quote_name: str = ''
        self._str_quote_type: str = ''
        self._str_quote_symbol: str = ''
        self._str_quote_sector: str = ''
        self._str_quote_industry: str = ''
        self._str_quote_currency: str = ''

        # Performance watch list
        self._float_quote_ask: float | str = 0.0
        self._int_quote_ask_size: int | str = 0
        self._float_quote_bid: float | str = 0.0
        self._int_quote_bid_size: int | str = 0
        self._float_quote_current_price: float | str = 0.0
        self._float_quote_day_high: float | str = 0.0
        self._float_quote_day_low: float | str = 0.0
        self._float_quote_relative_daily_span: float | str = 0.0
        self._float_quote_interday_momentum: float | str = 0.0
        self._float_quote_open: float | str = 0.0
        self._float_quote_previous_close: float | str = 0.0
        self._float_regular_market_change_percent: float | str = 0.0
        self._float_quote_intraday_momentum: float | str = 0.0
        self._int_quote_volume: int | str = 0
        self._int_quote_average_volume: int | str = 0
        self._float_quote_relative_volume: float | str = 0.0
        self._int_quote_average_volume_10_days: int | str = 0
        self._float_quote_relative_volume_10_days: float | str = 0.0
        self._float_quote_beta: float | str = 0.0
        self._float_quote_fifty_two_weeks_low: float | str = 0.0
        self._float_quote_fifty_two_weeks_high: float | str = 0.0
        self._float_quote_fifty_two_weeks_low_momentum: float | str = 0.0
        self._float_quote_fifty_two_weeks_high_momentum: float | str = 0.0
        self._float_quote_fifty_day_average: float | str = 0.0
        self._float_quote_fifty_day_momentum: float | str = 0.0
        self._float_two_hundred_day_average: float | str = 0.0
        self._float_two_hundred_day_momentum: float | str = 0.0

        # Analyst watch list
        self._current_price: str | float = 0.0
        self._target_high_price: str | float = 0.0
        self._target_low_price: str | float = 0.0
        self._target_mean_price: str | float = 0.0
        self._target_median_price: str | float = 0.0
        self._upside_potential: str | float = 0.0
        self._risk_reward_ratio: str | float = 0.0
        self._analyst_dispersion: str | float = 0.0
        self._recommendation_mean: str | float = 0.0
        self._recommendation_key: str = ''
        self._number_of_analyst_opinions: int | str = 0
        self._weighted_reversion_index: str | float = 0.0
        self._list_revision_index: list = []
        self._int_revision_trend_credit: int | str = ''

        # Fundamentals
        self._trailing_eps: str | float = 0.0
        self._forward_eps: str | float = 0.0
        self._trailing_pe: str | float = 0.0
        self._forward_pe: str | float = 0.0
        self._price_to_earning_to_growth: str | float = 0.0
        self._book_value: str | float = 0.0
        self._price_to_book: str | float = 0.0
        self._earnings_quarterly_growth: str | float = 0.0
        self._profit_margins: str | float = 0.0
        self._total_cash_per_share: str | float = 0.0
        self._quick_ratio: str | float = 0.0
        self._dividend_yield: str | float = 0.0
        self._payout_ratio: str | float = 0.0
        self._five_year_ave_dividend_yield: str | float = 0.0
        self._ratio_dividend_yield: str | float = 0.0
        self._ex_dividend_date: str | int = ''
        self._ex_dividend_delta_date: str | int = ''
        self._enterprise_to_revenue: str | float = 0.0

        # Derivate
        self._shares_short: str | int = 0
        self._float_shares: str | int = 0
        self._short_percent_of_float: str | float = 0.0
        self._shares_outstanding: str | int = 0
        self._short_ratio: str | float = 0.0
        self._shares_short_prior_month: str | int = 0
        self._short_percent_change: str | float = 0.0
        self._shares_short_previous_month_date: str | int = 0
        self._date_short_interest: str | int = 0
        self._short_date_delta_last_month: str | int = 0
        self._short_date_delta_this_month: str | int = 0
        self._held_percent_insiders: str | float = 0.0
        self._held_percent_institutions: str | float = 0.0

        # Calendar
        self._str_dividend_date: str = ''
        self._int_dividend_delta_date: int = 0
        self._str_ex_dividend_date: str = ''
        self._int_ex_dividend_delta_date: int = 0
        self._str_earnings_date: str = ''
        self._int_earnings_delta_date: int = 0

        # Date
        self._today: date = date.today()

        # Initialize watch list dicts from definitions
        self._dict_static_watch_list_data = myStaticWatchListDefinitions.init_dict_static_watch_list_data()
        self._dict_performance_watch_list_data = myPerformanceWatchListDefinitions.init_dict_performance_watch_list_data()
        self._dict_analyst_watch_list_data = myAnalystWatchListDefinitions.init_dict_analyst_watch_list_data()
        self._dict_fundamentals_watch_list_data = myFundamentalsWatchListDefinitions.init_dict_fundamentals_watch_list_data()
        self._dict_derivate_watch_list_data = myDerivateWatchListDefinitions.init_dict_derivate_watch_list_data()
        self._dict_calendar_watch_list_data = myCalendarWatchListDefinitions.init_dict_calendar_watch_list_data()

    def set_actual_quote_isin(self, str_actual_quote_isin: str) -> None:
        """Set the ISIN and reset all caches."""
        self._str_actual_quote_isin = str_actual_quote_isin
        self._bool_ticker_info = False
        self._cache_static = False
        self._cache_performance = False
        self._cache_analyst = False
        self._cache_fundamentals = False
        self._cache_derivate = False
        self._cache_calendar = False

    def get_actual_quote_ticker_data_from_y_finance(self) -> None:
        """Public method to fetch ticker data from yfinance."""
        self._get_quote_ticker_data_from_yfinance()

    @property
    def get_actual_quote_isin(self) -> str:
        return self._str_actual_quote_isin

    @property
    def get_actual_quote_ticker_info(self) -> dict[str, str | int | float | None]:
        return self._ticker_info

    @property
    def get_actual_quote_dict_static_watch_list_data(self) -> dict[str, str | bool | None]:
        if not self._cache_static:
            self._get_quote_static_watch_list_data_from_yfinance()
            self._cache_static = True
        return self._dict_static_watch_list_data

    @property
    def get_actual_quote_dict_performance_watch_list_data(self) -> dict[str, str | int | float | None]:
        if not self._cache_performance:
            self._get_quote_performance_watch_list_data_from_yfinance()
            self._cache_performance = True
        return self._dict_performance_watch_list_data

    @property
    def get_actual_quote_dict_analyst_watch_list_data(self) -> dict[str, str | int | float | None]:
        if not self._cache_analyst:
            self._get_quote_analyst_watch_list_data_from_yfinance()
            self._cache_analyst = True
        return self._dict_analyst_watch_list_data

    @property
    def get_actual_quote_dict_fundamentals_watch_list_data(self) -> dict[str, str | int | float | None]:
        if not self._cache_fundamentals:
            self._get_quote_fundamentals_watch_list_data_from_yfinance()
            self._cache_fundamentals = True
        return self._dict_fundamentals_watch_list_data

    @property
    def get_actual_quote_dict_derivate_watch_list_data(self) -> dict[str, str | int | float | None]:
        if not self._cache_derivate:
            self._get_quote_derivate_watch_list_data_from_yfinance()
            self._cache_derivate = True
        return self._dict_derivate_watch_list_data

    @property
    def get_actual_quote_dict_calendar_watch_list_data(self) -> dict[str, str | int | None]:
        if not self._cache_calendar:
            self._get_quote_calendar_watch_list_data_from_yfinance()
            self._cache_calendar = True
        return self._dict_calendar_watch_list_data

    def _reset_ticker_data(self) -> None:
        """Reset all ticker-related data to empty defaults."""
        self._bool_ticker_info = False
        self._ticker_info = {}
        self._ticker_eps_revisions = pd.DataFrame()
        self._ticker_history = pd.DataFrame()
        self._ticker_earning_estimate = pd.DataFrame()
        self._ticker_calendar = {}

    def _get_quote_ticker_data_from_yfinance(self) -> None:
        """Fetch ticker data from yfinance by ISIN."""
        if not self._str_actual_quote_isin:
            self._reset_ticker_data()
            return

        if not yf_utils.is_isin(self._str_actual_quote_isin):
            self._reset_ticker_data()
            logger.warning('Invalid ISIN format: %s', self._str_actual_quote_isin)
            return

        ticker_symbol = yf_utils.get_ticker_by_isin(self._str_actual_quote_isin)
        if not ticker_symbol:
            self._reset_ticker_data()
            logger.warning('No ticker symbol found for ISIN: %s', self._str_actual_quote_isin)
            return

        try:
            self._ticker_y_finance = yfinance.Ticker(self._str_actual_quote_isin)
            self._ticker_info = self._ticker_y_finance.get_info()

            if len(self._ticker_info) <= 1:
                raise ValueError('Empty or insufficient ticker info')

        except ValueError as exc:
            self._reset_ticker_data()
            logger.warning('Y-Finance does not provide data for ISIN %s: %s',
                           self._str_actual_quote_isin, exc)
            return

        # Check quote type
        self._str_quote_type = self._ticker_info.get('quoteType', '')
        if self._str_quote_type not in LIST_ALLOWED_QUOTE_TYPES:
            self._reset_ticker_data()
            logger.info('Quote type %s not supported for ISIN %s',
                        self._str_quote_type, self._str_actual_quote_isin)
            return

        # Fetch additional data for EQUITY
        self._ticker_eps_revisions = self._ticker_y_finance.get_eps_revisions()
        self._ticker_history = self._ticker_y_finance.earnings_history
        self._ticker_earning_estimate = self._ticker_y_finance.earnings_estimate
        self._ticker_calendar = self._ticker_y_finance.get_calendar()
        self._bool_ticker_info = True

    def _get_quote_static_watch_list_data_from_yfinance(self) -> None:
        """Populate the static watch list dict from ticker info."""
        if not self._bool_ticker_info:
            self._get_quote_ticker_data_from_yfinance()

        info = self._ticker_info
        idx = self._index_tuple.OPTION_NAME

        # Set quote ISIN
        self._dict_static_watch_list_data[myStaticWatchListDefinitions.TUPLE_STATIC_WATCH_LIST_QUOTE_ISIN[idx]] = (
            self._str_actual_quote_isin)

        if not info:
            return

        # Quote name: prefer longName, fallback to shortName
        self._str_quote_name = safe_get_str(info, 'longName') or safe_get_str(info, 'shortName')
        self._dict_static_watch_list_data[myStaticWatchListDefinitions.TUPLE_STATIC_WATCH_LIST_QUOTE_NAME[idx]] = (
            self._str_quote_name)

        # Quote type
        self._str_quote_type = safe_get_str(info, 'quoteType')
        self._dict_static_watch_list_data[myStaticWatchListDefinitions.TUPLE_STATIC_WATCH_LIST_QUOTE_TYPE[idx]] = (
            self._str_quote_type)

        # Symbol
        self._str_quote_symbol = safe_get_str(info, 'symbol')
        self._dict_static_watch_list_data[myStaticWatchListDefinitions.TUPLE_STATIC_WATCH_LIST_QUOTE_TICKER_SYMBOL[idx]] = (
            self._str_quote_symbol)

        # Sector
        self._str_quote_sector = safe_get_str(info, 'sector')
        self._dict_static_watch_list_data[myStaticWatchListDefinitions.TUPLE_STATIC_WATCH_LIST_QUOTE_SECTOR[idx]] = (
            self._str_quote_sector)

        # Industry
        self._str_quote_industry = safe_get_str(info, 'industry')
        self._dict_static_watch_list_data[myStaticWatchListDefinitions.TUPLE_STATIC_WATCH_LIST_QUOTE_INDUSTRY[idx]] = (
            self._str_quote_industry)

        # Currency
        self._str_quote_currency = safe_get_str(info, 'currency')
        self._dict_static_watch_list_data[myStaticWatchListDefinitions.TUPLE_STATIC_WATCH_LIST_QUOTE_CURRENCY[idx]] = (
            self._str_quote_currency)

    @staticmethod
    def _calc_momentum(diff: float | str, base: float | str) -> float | str:
        """Calculate momentum percentage: (diff / base) * 100."""
        if isinstance(diff, float) and isinstance(base, float) and base > 0:
            return round((diff / base) * 100, FLOAT_PRECISION)
        return ''

    def _get_quote_performance_watch_list_data_from_yfinance(self) -> None:
        """Populate the performance watch list dict from ticker info."""
        if not self._bool_ticker_info:
            self._get_quote_ticker_data_from_yfinance()

        info = self._ticker_info
        idx = self._index_tuple.OPTION_NAME
        perf = self._dict_performance_watch_list_data
        pwl = myPerformanceWatchListDefinitions

        # ISIN
        perf[pwl.TUPLE_PERFORMANCE_WATCH_LIST_QUOTE_ISIN[idx]] = self._str_actual_quote_isin

        if not info:
            return

        # Direct float fields
        self._float_quote_ask = safe_get_float(info, 'ask')
        perf[pwl.TUPLE_PERFORMANCE_WATCH_LIST_ASK[idx]] = self._float_quote_ask

        self._int_quote_ask_size = safe_get_int(info, 'askSize')
        perf[pwl.TUPLE_PERFORMANCE_WATCH_LIST_ASK_SIZE[idx]] = self._int_quote_ask_size

        self._float_quote_bid = safe_get_float(info, 'bid')
        perf[pwl.TUPLE_PERFORMANCE_WATCH_LIST_BID[idx]] = self._float_quote_bid

        self._int_quote_bid_size = safe_get_int(info, 'bidSize')
        perf[pwl.TUPLE_PERFORMANCE_WATCH_LIST_BID_SIZE[idx]] = self._int_quote_bid_size

        self._float_quote_current_price = safe_get_float(info, 'currentPrice')
        perf[pwl.TUPLE_PERFORMANCE_WATCH_LIST_CURRENT_PRICE[idx]] = self._float_quote_current_price

        self._float_quote_day_high = safe_get_float(info, 'dayHigh')
        perf[pwl.TUPLE_PERFORMANCE_WATCH_LIST_DAY_HIGH[idx]] = self._float_quote_day_high

        # Interday momentum: (dayHigh - currentPrice) / currentPrice * 100
        self._float_quote_interday_momentum = self._calc_momentum(
            self._float_quote_day_high - self._float_quote_current_price, self._float_quote_current_price)
        perf[pwl.TUPLE_PERFORMANCE_WATCH_LIST_INTERDAY_MOMENTUM[idx]] = self._float_quote_interday_momentum

        self._float_quote_day_low = safe_get_float(info, 'dayLow')
        perf[pwl.TUPLE_PERFORMANCE_WATCH_LIST_DAY_LOW[idx]] = self._float_quote_day_low

        # Relative daily span: (dayHigh - dayLow) / dayLow * 100
        if isinstance(self._float_quote_day_low, float) and isinstance(self._float_quote_day_high, float):
            self._float_quote_relative_daily_span = self._calc_momentum(
                self._float_quote_day_high - self._float_quote_day_low, self._float_quote_day_low)
        else:
            self._float_quote_relative_daily_span = ''
        perf[pwl.TUPLE_PERFORMANCE_WATCH_LIST_RELATIVE_DAILY_SPAN[idx]] = self._float_quote_relative_daily_span

        self._float_quote_open = safe_get_float(info, 'open')
        perf[pwl.TUPLE_PERFORMANCE_WATCH_LIST_OPEN[idx]] = self._float_quote_open

        self._float_quote_previous_close = safe_get_float(info, 'previousClose')
        perf[pwl.TUPLE_PERFORMANCE_WATCH_LIST_PREVIOUS_CLOSE[idx]] = self._float_quote_previous_close

        # Intraday momentum: (dayLow - previousClose) / previousClose * 100
        if isinstance(self._float_quote_previous_close, float) and isinstance(self._float_quote_day_low, float):
            self._float_quote_intraday_momentum = self._calc_momentum(
                self._float_quote_day_low - self._float_quote_previous_close, self._float_quote_previous_close)
        else:
            self._float_quote_intraday_momentum = ''
        perf[pwl.TUPLE_PERFORMANCE_WATCH_LIST_INTRADAY_MOMENTUM[idx]] = self._float_quote_intraday_momentum

        self._float_regular_market_change_percent = safe_get_float(info, 'regularMarketChangePercent')
        perf[pwl.TUPLE_PERFORMANCE_WATCH_LIST_REGULAR_MARKET_CHANGE_PERCENT[idx]] = (
            self._float_regular_market_change_percent)

        self._int_quote_volume = safe_get_int(info, 'volume')
        perf[pwl.TUPLE_PERFORMANCE_WATCH_LIST_VOLUME[idx]] = self._int_quote_volume

        self._int_quote_average_volume = safe_get_int(info, 'averageVolume')
        perf[pwl.TUPLE_PERFORMANCE_WATCH_LIST_AVERAGE_VOLUME[idx]] = self._int_quote_average_volume

        # Relative volume
        if isinstance(self._int_quote_average_volume, int) and isinstance(self._int_quote_volume, int):
            if self._int_quote_average_volume > 0:
                self._float_quote_relative_volume = round(
                    float(self._int_quote_volume) / self._int_quote_average_volume, FLOAT_PRECISION)
            else:
                self._float_quote_relative_volume = ''
        else:
            self._float_quote_relative_volume = ''
        perf[pwl.TUPLE_PERFORMANCE_WATCH_LIST_RELATIVE_VOLUME[idx]] = self._float_quote_relative_volume

        self._int_quote_average_volume_10_days = safe_get_int(info, 'averageDailyVolume10Day')
        perf[pwl.TUPLE_PERFORMANCE_WATCH_LIST_AVERAGE_DAILY_VOLUME_10_DAY[idx]] = (
            self._int_quote_average_volume_10_days)

        # Relative volume 10-day
        if isinstance(self._int_quote_average_volume_10_days, int) and isinstance(self._int_quote_volume, int):
            if self._int_quote_average_volume_10_days > 0:
                self._float_quote_relative_volume_10_days = round(
                    float(self._int_quote_volume) / self._int_quote_average_volume_10_days, FLOAT_PRECISION)
            else:
                self._float_quote_relative_volume_10_days = ''
        else:
            self._float_quote_relative_volume_10_days = ''
        perf[pwl.TUPLE_PERFORMANCE_WATCH_LIST_RELATIVE_VOLUME_10_DAY[idx]] = (
            self._float_quote_relative_volume_10_days)

        self._float_quote_beta = safe_get_float(info, 'beta')
        perf[pwl.TUPLE_PERFORMANCE_WATCH_LIST_BETA[idx]] = self._float_quote_beta

        # 52-week low and momentum
        self._float_quote_fifty_two_weeks_low = safe_get_float(info, 'fiftyTwoWeekLow')
        perf[pwl.TUPLE_PERFORMANCE_WATCH_LIST_FIFTY_TWO_WEEK_LOW[idx]] = (
            self._float_quote_fifty_two_weeks_low)

        if isinstance(self._float_quote_fifty_two_weeks_low, float) and isinstance(self._float_quote_current_price, float):
            self._float_quote_fifty_two_weeks_low_momentum = self._calc_momentum(
                self._float_quote_current_price - self._float_quote_fifty_two_weeks_low,
                self._float_quote_fifty_two_weeks_low)
        else:
            self._float_quote_fifty_two_weeks_low_momentum = ''
        perf[pwl.TUPLE_PERFORMANCE_WATCH_LIST_FIFTY_TWO_WEEK_LOW_MOMENTUM[idx]] = (
            self._float_quote_fifty_two_weeks_low_momentum)

        # 52-week high and momentum
        self._float_quote_fifty_two_weeks_high = safe_get_float(info, 'fiftyTwoWeekHigh')
        perf[pwl.TUPLE_PERFORMANCE_WATCH_LIST_FIFTY_TWO_WEEK_HIGH[idx]] = (
            self._float_quote_fifty_two_weeks_high)

        if isinstance(self._float_quote_fifty_two_weeks_high, float) and isinstance(self._float_quote_current_price, float):
            self._float_quote_fifty_two_weeks_high_momentum = self._calc_momentum(
                self._float_quote_current_price - self._float_quote_fifty_two_weeks_high,
                self._float_quote_fifty_two_weeks_high)
        else:
            self._float_quote_fifty_two_weeks_high_momentum = ''
        perf[pwl.TUPLE_PERFORMANCE_WATCH_LIST_FIFTY_TWO_WEEK_HIGH_MOMENTUM[idx]] = (
            self._float_quote_fifty_two_weeks_high_momentum)

        # 50-day average and momentum
        self._float_quote_fifty_day_average = safe_get_float(info, 'fiftyDayAverage')
        perf[pwl.TUPLE_PERFORMANCE_WATCH_LIST_FIFTY_DAY_AVERAGE[idx]] = self._float_quote_fifty_day_average

        if isinstance(self._float_quote_fifty_day_average, float) and isinstance(self._float_quote_current_price, float):
            self._float_quote_fifty_day_momentum = self._calc_momentum(
                self._float_quote_current_price - self._float_quote_fifty_day_average,
                self._float_quote_fifty_day_average)
        else:
            self._float_quote_fifty_day_momentum = ''
        perf[pwl.TUPLE_PERFORMANCE_WATCH_LIST_FIFTY_DAY_MOMENTUM[idx]] = self._float_quote_fifty_day_momentum

        # 200-day average and momentum (BUGFIX: was using _float_quote_fifty_day_momentum)
        self._float_two_hundred_day_average = safe_get_float(info, 'twoHundredDayAverage')
        perf[pwl.TUPLE_PERFORMANCE_WATCH_LIST_TWO_HUNDRED_DAY_AVERAGE[idx]] = (
            self._float_two_hundred_day_average)

        if isinstance(self._float_two_hundred_day_average, float) and isinstance(self._float_quote_current_price, float):
            self._float_two_hundred_day_momentum = self._calc_momentum(
                self._float_quote_current_price - self._float_two_hundred_day_average,
                self._float_two_hundred_day_average)
        else:
            self._float_two_hundred_day_momentum = ''
        perf[pwl.TUPLE_PERFORMANCE_WATCH_LIST_TWO_HUNDRED_DAY_MOMENTUM[idx]] = (
            self._float_two_hundred_day_momentum)

    def _get_quote_analyst_watch_list_data_from_yfinance(self) -> None:
        """Populate the analyst watch list dict from ticker info."""
        if not self._bool_ticker_info:
            self._get_quote_ticker_data_from_yfinance()

        info = self._ticker_info
        idx = self._index_tuple.OPTION_NAME
        analyst = self._dict_analyst_watch_list_data
        awl = myAnalystWatchListDefinitions

        # ISIN
        analyst[awl.TUPLE_ANALYST_WATCH_LIST_QUOTE_ISIN[idx]] = self._str_actual_quote_isin

        if not info:
            return

        # Direct fields
        self._current_price = safe_get_float(info, 'currentPrice')
        analyst[awl.TUPLE_ANALYST_WATCH_LIST_CURRENT_PRICE[idx]] = self._current_price

        self._target_high_price = safe_get_float(info, 'targetHighPrice')
        analyst[awl.TUPLE_ANALYST_WATCH_LIST_TARGET_HIGH_PRICE[idx]] = self._target_high_price

        self._target_low_price = safe_get_float(info, 'targetLowPrice')
        analyst[awl.TUPLE_ANALYST_WATCH_LIST_TARGET_LOW_PRICE[idx]] = self._target_low_price

        self._target_mean_price = safe_get_float(info, 'targetMeanPrice')
        analyst[awl.TUPLE_ANALYST_WATCH_LIST_TARGET_MEAN_PRICE[idx]] = self._target_mean_price

        self._target_median_price = safe_get_float(info, 'targetMedianPrice')
        analyst[awl.TUPLE_ANALYST_WATCH_LIST_TARGET_MEDIAN_PRICE[idx]] = self._target_median_price

        self._recommendation_mean = safe_get_float(info, 'recommendationMean')
        analyst[awl.TUPLE_ANALYST_WATCH_LIST_RECOMMENDATION_MEAN[idx]] = self._recommendation_mean

        self._recommendation_key = safe_get_str(info, 'recommendationKey')
        analyst[awl.TUPLE_ANALYST_WATCH_LIST_RECOMMENDATION_KEY[idx]] = self._recommendation_key

        self._number_of_analyst_opinions = safe_get_int(info, 'numberOfAnalystOpinions')
        analyst[awl.TUPLE_ANALYST_WATCH_LIST_NUMBER_OF_ANALYST_OPINIONS[idx]] = (
            self._number_of_analyst_opinions)

        # Upside potential
        if (isinstance(self._current_price, float) and isinstance(self._target_mean_price, float)
                and self._current_price != 0):
            self._upside_potential = round(self._target_mean_price / self._current_price - 1, FLOAT_PRECISION)
        else:
            self._upside_potential = ''
        analyst[awl.TUPLE_ANALYST_WATCH_LIST_UPSIDE_POTENTIAL[idx]] = self._upside_potential

        # Risk/reward ratio
        if (isinstance(self._target_high_price, float) and isinstance(self._target_low_price, float)
                and isinstance(self._current_price, float) and self._current_price < self._target_high_price):
            self._risk_reward_ratio = round(
                (self._current_price - self._target_low_price) / (self._target_high_price - self._current_price), FLOAT_PRECISION)
        else:
            self._risk_reward_ratio = ''
        analyst[awl.TUPLE_ANALYST_WATCH_LIST_RISK_REWARD_RATIO[idx]] = self._risk_reward_ratio

        # Analyst dispersion
        if (isinstance(self._target_high_price, float) and isinstance(self._target_low_price, float)
                and isinstance(self._target_mean_price, float) and self._target_mean_price > 0):
            self._analyst_dispersion = round(
                (self._target_high_price - self._target_low_price) / self._target_mean_price, FLOAT_PRECISION)
        else:
            self._analyst_dispersion = ''
        analyst[awl.TUPLE_ANALYST_WATCH_LIST_ANALYST_DISPERSION[idx]] = self._analyst_dispersion

        # EPS revisions
        self._int_revision_trend_credit = ''
        self._list_revision_index = []

        if not self._ticker_eps_revisions.empty:
            self._list_revision_index = calc_weighted_revisions_index(self._ticker_eps_revisions)

            if isinstance(self._list_revision_index, list):
                # Filter NaN values
                self._list_revision_index = [
                    x for x in self._list_revision_index
                    if not (isinstance(x, float) and math.isnan(x))
                ]

                if self._list_revision_index:
                    # Classify revisions into -2, -1, 1, 2 buckets
                    classified = [
                        -2 if x < REVISION_THRESHOLD_NEGATIVE_HIGH
                        else (-1 if x < REVISION_THRESHOLD_NEGATIVE_LOW
                              else (1 if x < REVISION_THRESHOLD_POSITIVE_HIGH
                                    else 2))
                        for x in self._list_revision_index
                    ]
                    # Apply weighting
                    weighted = [a * b for a, b in zip(classified, [REVISION_WEIGHT_SHORT, REVISION_WEIGHT_SHORT, REVISION_WEIGHT_LONG, REVISION_WEIGHT_LONG])]
                    self._int_revision_trend_credit = sum(weighted)

        # Set revision index and trend
        if self._list_revision_index:
            analyst[awl.TUPLE_ANALYST_WATCH_LIST_WEIGHTED_REVISION_INDEX[idx]] = self._list_revision_index[0]
            analyst[awl.TUPLE_ANALYST_WATCH_LIST_WEIGHTED_REVISION_TREND[idx]] = str(self._list_revision_index)
        else:
            analyst[awl.TUPLE_ANALYST_WATCH_LIST_WEIGHTED_REVISION_INDEX[idx]] = ''
            analyst[awl.TUPLE_ANALYST_WATCH_LIST_WEIGHTED_REVISION_TREND[idx]] = ''

        analyst[awl.TUPLE_ANALYST_WATCH_LIST_WEIGHTED_REVISION_TREND_CREDIT[idx]] = (
            self._int_revision_trend_credit)

    def _get_quote_fundamentals_watch_list_data_from_yfinance(self) -> None:
        """Populate the fundamentals watch list dict from ticker info."""
        if not self._bool_ticker_info:
            self._get_quote_ticker_data_from_yfinance()

        info = self._ticker_info
        idx = self._index_tuple.OPTION_NAME
        fund = self._dict_fundamentals_watch_list_data
        fwl = myFundamentalsWatchListDefinitions

        # ISIN
        fund[fwl.TUPLE_FUNDAMENTALS_WATCH_LIST_QUOTE_ISIN[idx]] = self._str_actual_quote_isin

        if not info:
            return

        # Direct float fields
        self._trailing_eps = safe_get_float(info, 'trailingEps')
        fund[fwl.TUPLE_FUNDAMENTALS_WATCH_LIST_TRAILING_EPS[idx]] = self._trailing_eps

        # BUGFIX: was shadowing self._forward_eps with local _forward_eps
        self._forward_eps = safe_get_float(info, 'forwardEps')
        fund[fwl.TUPLE_FUNDAMENTALS_WATCH_LIST_FORWARD_EPS[idx]] = self._forward_eps

        self._trailing_pe = safe_get_float(info, 'trailingPE')
        fund[fwl.TUPLE_FUNDAMENTALS_WATCH_LIST_TRAILING_PE[idx]] = self._trailing_pe

        self._forward_pe = safe_get_float(info, 'forwardPE')
        fund[fwl.TUPLE_FUNDAMENTALS_WATCH_LIST_FORWARD_PE[idx]] = self._forward_pe

        # PEG ratio
        if (isinstance(self._trailing_pe, float) and isinstance(self._forward_pe, float)
                and self._forward_pe != 0.0):
            self._price_to_earning_to_growth = round(self._trailing_pe / self._forward_pe, FLOAT_PRECISION)
        else:
            self._price_to_earning_to_growth = ''
        fund[fwl.TUPLE_FUNDAMENTALS_WATCH_LIST_PRICE_TO_EARNING_TO_GROWTH[idx]] = (
            self._price_to_earning_to_growth)

        self._book_value = safe_get_float(info, 'bookValue')
        fund[fwl.TUPLE_FUNDAMENTALS_WATCH_LIST_BOOK_VALUE[idx]] = self._book_value

        self._price_to_book = safe_get_float(info, 'priceToBook')
        fund[fwl.TUPLE_FUNDAMENTALS_WATCH_LIST_PRICE_TO_BOOK[idx]] = self._price_to_book

        self._earnings_quarterly_growth = safe_get_float(info, 'earningsQuarterlyGrowth')
        fund[fwl.TUPLE_FUNDAMENTALS_WATCH_LIST_EARNINGS_QUARTERLY_GROWTH[idx]] = (
            self._earnings_quarterly_growth)

        # Growth trend from earnings estimate
        if 'growth' in self._ticker_earning_estimate.columns:
            _growth = list(self._ticker_earning_estimate['growth'].to_dict().values())
            fund[fwl.TUPLE_FUNDAMENTALS_WATCH_LIST_GROWTH_TREND[idx]] = str(process_float_list(_growth))
        else:
            fund[fwl.TUPLE_FUNDAMENTALS_WATCH_LIST_GROWTH_TREND[idx]] = ''

        # Surprise trend from earnings history
        if 'surprisePercent' in self._ticker_history.columns and not self._ticker_history.empty:
            _surprise_count_row = self._ticker_history['surprisePercent'].apply(
                lambda x: -1 if x < 0 else (1 if x < 0.1 else 2))
            _surprise_list = list(_surprise_count_row.to_dict().values())
            fund[fwl.TUPLE_FUNDAMENTALS_WATCH_LIST_SURPRISE_TREND[idx]] = str(_surprise_list)
            fund[fwl.TUPLE_FUNDAMENTALS_WATCH_LIST_SURPRISE_CREDIT[idx]] = sum(_surprise_list)
        else:
            fund[fwl.TUPLE_FUNDAMENTALS_WATCH_LIST_SURPRISE_TREND[idx]] = ''
            fund[fwl.TUPLE_FUNDAMENTALS_WATCH_LIST_SURPRISE_CREDIT[idx]] = ''

        self._profit_margins = safe_get_float(info, 'profitMargins')
        fund[fwl.TUPLE_FUNDAMENTALS_WATCH_LIST_PROFIT_MARGINS[idx]] = self._profit_margins

        self._total_cash_per_share = safe_get_float(info, 'totalCashPerShare')
        fund[fwl.TUPLE_FUNDAMENTALS_WATCH_LIST_TOTAL_CASH_PER_SHARE[idx]] = self._total_cash_per_share

        self._quick_ratio = safe_get_float(info, 'quickRatio')
        fund[fwl.TUPLE_FUNDAMENTALS_WATCH_LIST_QUICK_RATIO[idx]] = self._quick_ratio

        self._dividend_yield = safe_get_float(info, 'dividendYield')
        fund[fwl.TUPLE_FUNDAMENTALS_WATCH_LIST_DIVIDEND_YIELD[idx]] = self._dividend_yield

        self._payout_ratio = safe_get_float(info, 'payoutRatio')
        fund[fwl.TUPLE_FUNDAMENTALS_WATCH_LIST_PAYOUT_RATIO[idx]] = self._payout_ratio

        self._five_year_ave_dividend_yield = safe_get_float(info, 'fiveYearAvgDividendYield')
        fund[fwl.TUPLE_FUNDAMENTALS_WATCH_LIST_FIVE_YEAR_AVE_DIVIDEND_YIELD[idx]] = (
            self._five_year_ave_dividend_yield)

        # Dividend yield ratio
        if isinstance(self._five_year_ave_dividend_yield, float) and self._five_year_ave_dividend_yield > 0:
            if isinstance(self._dividend_yield, float):
                self._ratio_dividend_yield = round(self._dividend_yield / self._five_year_ave_dividend_yield, FLOAT_PRECISION)
            else:
                self._ratio_dividend_yield = ''
        else:
            self._ratio_dividend_yield = ''
        fund[fwl.TUPLE_FUNDAMENTALS_WATCH_LIST_RATIO_DIVIDEND_YIELD[idx]] = self._ratio_dividend_yield

        # Ex-dividend date (may be int timestamp or datetime object)
        ex_div_raw = info.get('exDividendDate', '')
        fund[fwl.TUPLE_FUNDAMENTALS_WATCH_LIST_EX_DIVIDED_DATE[idx]] = ex_div_raw

        if isinstance(ex_div_raw, int):
            self._ex_dividend_delta_date = min(calc_delta_days(ex_div_raw), MAX_DELTA_DAYS)
        else:
            self._ex_dividend_delta_date = ''
        fund[fwl.TUPLE_FUNDAMENTALS_WATCH_LIST_EX_DIVIDED_DELTA_DATE[idx]] = self._ex_dividend_delta_date

        self._enterprise_to_revenue = safe_get_float(info, 'enterpriseToRevenue')
        fund[fwl.TUPLE_FUNDAMENTALS_WATCH_LIST_ENTERPRISE_TO_REVENUE[idx]] = self._enterprise_to_revenue

    def _get_quote_derivate_watch_list_data_from_yfinance(self) -> None:
        """Populate the derivate watch list dict from ticker info."""
        if not self._bool_ticker_info:
            self._get_quote_ticker_data_from_yfinance()

        info = self._ticker_info
        idx = self._index_tuple.OPTION_NAME
        deriv = self._dict_derivate_watch_list_data
        dwl = myDerivateWatchListDefinitions

        # ISIN
        deriv[dwl.TUPLE_DERIVATE_WATCH_LIST_QUOTE_ISIN[idx]] = self._str_actual_quote_isin

        if not info:
            return

        # Direct int fields
        self._shares_short = safe_get_int(info, 'sharesShort')
        deriv[dwl.TUPLE_DERIVATE_WATCH_LIST_SHARES_SHORT[idx]] = self._shares_short

        self._float_shares = safe_get_int(info, 'floatShares')
        deriv[dwl.TUPLE_DERIVATE_WATCH_LIST_FLOAT_SHARES[idx]] = self._float_shares

        # Short percent of float
        if isinstance(self._float_shares, int) and isinstance(self._shares_short, int):
            if self._float_shares > 0:
                self._short_percent_of_float = round(self._shares_short * 100 / self._float_shares, FLOAT_PRECISION)
            else:
                self._short_percent_of_float = ''
        else:
            self._short_percent_of_float = ''
        deriv[dwl.TUPLE_DERIVATE_WATCH_LIST_SHORT_PERCENT_OF_FLOAT[idx]] = self._short_percent_of_float

        self._shares_outstanding = safe_get_int(info, 'sharesOutstanding')
        deriv[dwl.TUPLE_DERIVATE_WATCH_LIST_SHARES_OUTSTANDING[idx]] = self._shares_outstanding

        self._short_ratio = safe_get_float(info, 'shortRatio')
        deriv[dwl.TUPLE_DERIVATE_WATCH_LIST_SHORT_RATIO[idx]] = self._short_ratio

        self._shares_short_prior_month = safe_get_int(info, 'sharesShortPriorMonth')
        deriv[dwl.TUPLE_DERIVATE_WATCH_LIST_SHARES_SHORT_PRIOR_MONTH[idx]] = self._shares_short_prior_month

        # Short percent change
        if isinstance(self._shares_short_prior_month, int) and isinstance(self._shares_short, int):
            if self._shares_short_prior_month > 0:
                self._short_percent_change = round(
                    (self._shares_short / self._shares_short_prior_month - 1) * 100, FLOAT_PRECISION)
            else:
                self._short_percent_change = ''
        else:
            self._short_percent_change = ''
        deriv[dwl.TUPLE_DERIVATE_WATCH_LIST_SHORT_PERCENT_CHANGE[idx]] = self._short_percent_change

        self._shares_short_previous_month_date = safe_get_int(info, 'sharesShortPreviousMonthDate')
        deriv[dwl.TUPLE_DERIVATE_WATCH_LIST_SHARES_SHORT_PREVIOUS_MONTH_DATE[idx]] = (
            self._shares_short_previous_month_date)

        self._date_short_interest = safe_get_int(info, 'dateShortInterest')
        deriv[dwl.TUPLE_DERIVATE_WATCH_LIST_DATE_SHORT_INTEREST[idx]] = self._date_short_interest

        # Short date delta last month
        if (isinstance(self._shares_short_previous_month_date, int) and self._shares_short_previous_month_date > 0
                and isinstance(self._date_short_interest, int) and self._date_short_interest > 0):
            self._short_date_delta_last_month = abs(
                calc_delta_days(self._shares_short_previous_month_date, self._date_short_interest))
        else:
            self._short_date_delta_last_month = ''
        deriv[dwl.TUPLE_DERIVATE_WATCH_LIST_SHORT_DATE_DELTA_LAST_MONTH[idx]] = (
            self._short_date_delta_last_month)

        # Short date delta this month
        if isinstance(self._date_short_interest, int) and self._date_short_interest > 0:
            self._short_date_delta_this_month = abs(calc_delta_days(self._date_short_interest))
        else:
            self._short_date_delta_this_month = ''
        deriv[dwl.TUPLE_DERIVATE_WATCH_LIST_SHORT_DATE_DELTA_THIS_MONTH[idx]] = (
            self._short_date_delta_this_month)

        self._held_percent_insiders = safe_get_float(info, 'heldPercentInsiders')
        deriv[dwl.TUPLE_DERIVATE_WATCH_LIST_HELD_PERCENT_INSIDERS[idx]] = self._held_percent_insiders

        self._held_percent_institutions = safe_get_float(info, 'heldPercentInstitutions')
        deriv[dwl.TUPLE_DERIVATE_WATCH_LIST_HELD_PERCENT_INSTITUTIONS[idx]] = self._held_percent_institutions

    @staticmethod
    def _process_calendar_date(cal_date, today: date) -> tuple[str, int]:
        """Process a calendar date and return (formatted_date, delta_days)."""
        if isinstance(cal_date, date):
            return cal_date.strftime('%Y-%m-%d'), (cal_date - today).days
        return '', 0

    def _get_quote_calendar_watch_list_data_from_yfinance(self) -> None:
        """Populate the calendar watch list dict from ticker calendar."""
        if not self._bool_ticker_info:
            self._get_quote_ticker_data_from_yfinance()

        idx = self._index_tuple.OPTION_NAME
        cal = self._dict_calendar_watch_list_data
        cwl = myCalendarWatchListDefinitions

        # ISIN
        cal[cwl.TUPLE_CALENDAR_WATCH_LIST_QUOTE_ISIN[idx]] = self._str_actual_quote_isin

        calendar = self._ticker_calendar

        # Dividend date
        if 'Dividend Date' in calendar:
            self._str_dividend_date, self._int_dividend_delta_date = self._process_calendar_date(
                calendar['Dividend Date'], self._today)
        else:
            self._str_dividend_date = ''
            self._int_dividend_delta_date = 0
        cal[cwl.TUPLE_CALENDAR_WATCH_LIST_DIVIDEND_DATE[idx]] = self._str_dividend_date
        cal[cwl.TUPLE_CALENDAR_WATCH_LIST_DIVIDEND_DELTA_DATE[idx]] = self._int_dividend_delta_date

        # Ex-dividend date
        if 'Ex-Dividend Date' in calendar:
            self._str_ex_dividend_date, self._int_ex_dividend_delta_date = self._process_calendar_date(
                calendar['Ex-Dividend Date'], self._today)
        else:
            self._str_ex_dividend_date = ''
            self._int_ex_dividend_delta_date = 0
        cal[cwl.TUPLE_CALENDAR_WATCH_LIST_EX_DIVIDEND_DATE[idx]] = self._str_ex_dividend_date
        cal[cwl.TUPLE_CALENDAR_WATCH_LIST_EX_DIVIDEND_DELTA_DATE[idx]] = self._int_ex_dividend_delta_date

        # Earnings date (can be date, list of dates, or empty)
        self._str_earnings_date = ''
        self._int_earnings_delta_date = 0

        if 'Earnings Date' in calendar:
            earnings_date = calendar['Earnings Date']

            if isinstance(earnings_date, date):
                self._str_earnings_date, self._int_earnings_delta_date = self._process_calendar_date(
                    earnings_date, self._today)
            elif isinstance(earnings_date, list):
                if len(earnings_date) == 1:
                    self._str_earnings_date, self._int_earnings_delta_date = self._process_calendar_date(
                        earnings_date[0], self._today)
                elif len(earnings_date) > 1:
                    # Find the nearest earnings date
                    deltas = []
                    for elem in earnings_date:
                        if isinstance(elem, date):
                            deltas.append((elem - self._today).days)
                    if deltas:
                        min_idx = deltas.index(min(deltas))
                        valid_dates = [e for e in earnings_date if isinstance(e, date)]
                        if valid_dates:
                            nearest = valid_dates[min_idx]
                            self._str_earnings_date = nearest.strftime('%Y-%m-%d')
                            self._int_earnings_delta_date = min(deltas)

        cal[cwl.TUPLE_CALENDAR_WATCH_LIST_EARNINGS_DATE[idx]] = self._str_earnings_date
        cal[cwl.TUPLE_CALENDAR_WATCH_LIST_EARNINGS_DELTA_DATE[idx]] = self._int_earnings_delta_date


if __name__ == "__main__":
    my_y_finance = MyYFinance()
    my_y_finance.set_actual_quote_isin('US0378331005')
    print(my_y_finance.get_actual_quote_dict_static_watch_list_data)
    print(my_y_finance.get_actual_quote_dict_performance_watch_list_data)
    print(my_y_finance.get_actual_quote_dict_analyst_watch_list_data)
    print(my_y_finance.get_actual_quote_dict_fundamentals_watch_list_data)
    print(my_y_finance.get_actual_quote_dict_derivate_watch_list_data)
    print(my_y_finance.get_actual_quote_dict_calendar_watch_list_data)
