import WindPy
import warnings
import pandas as pd
from tool import *
import os


# 计算某一时段的底背离
def calculate_number(start_date, end_date):

    path = './data/price/' + end_date.strftime('%Y-%m-%d') + '.csv'

    price_data = pd.read_csv(path)

    path = './data/macd/' + end_date.strftime('%Y-%m-%d') + '.csv'
    MACD_data = pd.read_csv(path)

    date_list = list(price_data['DATE'].index)
    company_num = price_data.shape[1]-1
    stock_code = list(price_data.columns)[1:]

    # 数据记录
    price_lowest_3percent = []
    price_lowest_3day = []
    price_lowest_today = []
    lowest_3day_DBL = []
    lowest_today_DBL = []

    for i in range(len(stock_code)):
        price_series = list(price_data[stock_code[i]].values)
        MACD_series = list(MACD_data[stock_code[i]].values)

        min_price = min(price_series)
        now_price = price_series[-1]

        min_MACD = min(MACD_series)
        max_MACD = max(MACD_series)
        now_MACD = MACD_series[-1]

        # 计算底背离幅度
        if max_MACD - min_MACD == 0:
            DBL_value = 0
        else:
            DBL_value = abs((now_MACD - min_MACD) / (max_MACD - min_MACD))

        # 股价当日最低或不超过最低3%
        percent = abs(now_price - min_price) / min_price
        if percent <= 0.03:
            price_lowest_3percent.append(stock_code[i])
        # 若当日是最低价
        if min_price == now_price:
            price_lowest_today.append(stock_code[i])
            if DBL_value > 0.017:
                lowest_today_DBL.append(stock_code[i])

        # 若最低价在三日内
        if min_price in price_series[-3:]:
            price_lowest_3day.append(stock_code[i])
            if DBL_value > 0.017:
                lowest_3day_DBL.append(stock_code[i])

    return company_num, len(price_lowest_3percent), len(price_lowest_3day), len(price_lowest_today), \
           len(lowest_3day_DBL), len(lowest_today_DBL)


def runTask():
    # 加载股票数据信息
    a = np.load('monitor_time.npz', allow_pickle=True)
    start_date_list = a['start_date_list']
    end_date_list = a['end_date_list']
    company_num_list = []
    lowest_3percent_num_list = []
    lowest_3percent_percent_list = []
    lowest_3day_num_list = []
    lowest_3day_percent_list = []
    lowest_today_num_list = []
    lowest_today_percent_list = []
    lowest_3day_DBL_num_list = []
    lowest_3day_DBL_percent_list = []
    lowest_today_DBL_num_list = []
    lowest_today_DBL_percent_list = []

    for i in range(len(start_date_list)):
        print(end_date_list[i].strftime('%Y-%m-%d') + '---------------------------------------------------------------')
        company_num, lowest_3percent_num, lowest_3day_num, lowest_today_num, lowest_3day_DBL_num, lowest_today_DBL_num \
            = calculate_number(start_date_list[i], end_date_list[i])
        lowest_3percent_percent = round(lowest_3percent_num / company_num * 100, 2)
        lowest_3day_percent = round(lowest_3day_num / company_num * 100, 2)
        lowest_today_percent = round(lowest_today_num / company_num * 100, 2)
        lowest_3day_DBL_percent = round(lowest_3day_DBL_num / company_num * 100, 2)
        lowest_today_DBL_percent = round(lowest_today_DBL_num / company_num * 100, 2)
        print('日期：' + end_date_list[i].strftime('%Y-%m-%d'))
        print('上市公司数量：' + str(company_num))
        print('股价最低/不超3%: ' + str(lowest_3percent_num))
        print('股价最低/不超3%（率）%: ' + str(lowest_3percent_percent))
        print('股价最低价在三日内: ' + str(lowest_3day_num))
        print('股价最低价在三日内（率）%: ' + str(lowest_3day_percent))
        print('股价最低价为当日: ' + str(lowest_today_num))
        print('股价最低价为当日（率）%: ' + str(lowest_today_percent))
        print('三日内最低且底背离: ' + str(lowest_3day_DBL_num))
        print('三日内最低且底背离（率）%: ' + str(lowest_3day_DBL_percent))
        print('当日最低且底背离: ' + str(lowest_today_DBL_num))
        print('当日最低且底背离（率）%: ' + str(lowest_today_DBL_percent))

        company_num_list.append(company_num)
        lowest_3percent_num_list.append(lowest_3percent_num)
        lowest_3percent_percent_list.append(lowest_3percent_percent)
        lowest_3day_num_list.append(lowest_3day_num)
        lowest_3day_percent_list.append(lowest_3day_percent)
        lowest_today_num_list.append(lowest_today_num)
        lowest_today_percent_list.append(lowest_today_percent)
        lowest_3day_DBL_num_list.append(lowest_3day_DBL_num)
        lowest_3day_DBL_percent_list.append(lowest_3day_DBL_percent)
        lowest_today_DBL_num_list.append(lowest_today_DBL_num)
        lowest_today_DBL_percent_list.append(lowest_today_DBL_percent)

    for i in range(len(end_date_list)):
        end_date_list[i] = end_date_list[i].strftime('%Y-%m-%d')

    excel_dir = "./data/大盘.xlsx"
    df = {
        '日期': end_date_list,
        '上市公司数量': company_num_list,
        '股价最低/不超3%': lowest_3percent_num_list,
        '股价最低/不超3%（率）%': lowest_3percent_percent_list,
        '股价最低价在三日内': lowest_3day_num_list,
        '股价最低价在三日内（率）%': lowest_3day_percent_list,
        '股价最低价为当日': lowest_today_num_list,
        '股价最低价为当日（率） %': lowest_today_percent_list,
        '三日内最低且底背离': lowest_3day_DBL_num_list,
        '三日内最低且底背离（率）%': lowest_3day_DBL_percent_list,
        '当日最低且底背离': lowest_today_DBL_num_list,
        '当日最低且底背离（率）%': lowest_today_DBL_percent_list
    }
    new_data_frame = pd.DataFrame(data=df)
    new_data_frame.to_excel(excel_dir, index=False)


if __name__=='__main__':
    runTask()




