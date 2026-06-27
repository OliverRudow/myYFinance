# This is a sample Python script.
from myyfinance import myYFinance


# Press ⌃R to execute it or replace it with your code.
# Press Double ⇧ to search everywhere for classes, files, tool windows, actions, and settings.


def print_hi(name):
    # Use a breakpoint in the code line below to debug your script.
    print(f'Hi, {name}')  # Press ⌘F8 to toggle the breakpoint.


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    # print_hi('PyCharm')
    my_y_fiance = myYFinance.MyYFinance()
    str_isin = 'US0378331005'
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

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
