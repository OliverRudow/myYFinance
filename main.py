"""Main entry point for myYFinance."""
from myyfinance.myYFinance import MyYFinance


if __name__ == '__main__':
    my_y_finance = MyYFinance()
    str_isin = 'US0378331005'
    my_y_finance.set_actual_quote_isin(str_isin)
    print(my_y_finance.get_actual_quote_dict_static_watch_list_data)
    print('-------------------------------------------------')
    print(my_y_finance.get_actual_quote_dict_performance_watch_list_data)
    print('-------------------------------------------------')
    print(my_y_finance.get_actual_quote_dict_analyst_watch_list_data)
    print('-------------------------------------------------')
    print(my_y_finance.get_actual_quote_dict_fundamentals_watch_list_data)
    print('-------------------------------------------------')
    print(my_y_finance.get_actual_quote_dict_derivate_watch_list_data)
    print('-------------------------------------------------')
    print(my_y_finance.get_actual_quote_dict_calendar_watch_list_data)
