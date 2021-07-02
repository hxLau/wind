import pandas as pd
import numpy as np
import os
import math
import datetime
import WindPy
import warnings
import time
import easygui as eg
import re


# 判断字符串是否为数值
def is_number(num):
  pattern = re.compile(r'^[-+]?[-0-9]\d*\.\d*|[-+]?\.?[0-9]\d*$')
  result = pattern.match(num)
  if result:
    return True
  else:
    return False


def set_par():
    msg = "请设定参数"
    title = "设定参数"
    fieldNames = ["CCI值的范围上限值（例如101）:", "CCI值的范围下限值（例如80）:"]
    fieldValues = eg.multenterbox(msg, title, fieldNames)

    while True:
        # 点击取消按钮操作
        if fieldValues == None:
            break
        # 报错提示初始值
        errmsg = ""
        if fieldValues[0].strip() == "" or not is_number(fieldValues[0]):
            errmsg += ('CCI值的范围上限值，只能设置为数字且不能为空\n')

        if fieldValues[1].strip() == "" or not fieldValues[1].isdigit():
            errmsg += ('CCI值的范围下限值，只能设置为数字且不能为空\n')

        # 无报错提示，退出程序，否则，报错提示，重新进入输入界面
        if errmsg == "":
            break
        fieldValues = eg.multenterbox(errmsg, title, fieldNames, fieldValues)

    print("CCI值的范围上限值: " + str(float(fieldValues[0])))
    print("CCI值的范围下限值: " + str(float(fieldValues[1])))
    return float(fieldValues[0]), int(fieldValues[1])


def get_index_by_wsq(code):
    CCI = []
    KDJ_K = []
    KDJ_J = []
    KDJ_D = []
    RSI = []
    MACD = []
    DEA = []
    AMT = []
    divide_size = int(len(code)/500) + 1
    for i in range(divide_size):
        if i == divide_size - 1:
            index = WindPy.w.wsq(code[i*500:], "rt_cci_14,rt_kdj_k,rt_kdj_d,rt_kdj_j,rt_rsi_6d, rt_macd, rt_macd_diff, rt_amt"
                                 , usedf=True)[1]
        else:
            index = WindPy.w.wsq(code[i*500:(i+1)*500], "rt_cci_14,rt_kdj_k,rt_kdj_d,rt_kdj_j,rt_rsi_6d, rt_macd, rt_macd_diff, rt_amt"
                                 , usedf=True)[1]
        CCI = CCI + list(index['RT_CCI_14'].values)
        KDJ_K = KDJ_K + list(index['RT_KDJ_K'].values)
        KDJ_D = KDJ_D + list(index['RT_KDJ_D'].values)
        KDJ_J = KDJ_J + list(index['RT_KDJ_J'].values)
        RSI = RSI + list(index['RT_RSI_6D'].values)
        MACD = MACD + list(index['RT_MACD'].values)
        DEA = DEA + list(index['RT_MACD_DIFF'].values)
        AMT = AMT + list(index['RT_AMT'].values)
    return CCI, KDJ_K, KDJ_D, KDJ_J, RSI, MACD, DEA, AMT


def get_data_by_wss(code, variable, para):
    result = []
    divide_size = int(len(code)/2000) + 1
    for i in range(divide_size):
        if i == divide_size - 1:
            zfv = WindPy.w.wss(code[i*2000:], variable, para, usedf=True)[1]
        else:
            zfv = WindPy.w.wss(code[i*2000:(i+1)*2000], variable, para, usedf=True)[1]

        item_list = list(zfv[variable].values)
        result = result + item_list
    return result


def main():
    CCI_UL, CCI_DL = set_par()

    print('--------正在连接wind金融终端--------')
    WindPy.w.start()
    WindPy.w.isconnected()

    # 计算日期
    today = datetime.datetime.now()
    todaystr = today.strftime('%Y-%m-%d')
    yesterday = WindPy.w.tdaysoffset(-1, todaystr, "").Times[0]
    yesterdaystr = yesterday.strftime('%Y-%m-%d')

    # 获取全部股票数据
    stock_list = WindPy.w.wset("sectorconstituent", "date=" + todaystr + ";sectorid=a001010100000000", usedf=True)[1]
    stock_code = list(stock_list['wind_code'])
    stock_name = list(stock_list['sec_name'])

    # 获取指标
    print('--------正在获取数据--------')
    CCI, KDJ_K, KDJ_D, KDJ_J, RSI, MACD, DEA, AMT = get_index_by_wsq(stock_code)

    # 利用MACD值和DEA值计算DIF值
    DIF = []
    for i in range(len(MACD)):
        DIF.append(MACD[i] / 2 + DEA[i])

    # 获取上个交易日的指标
    last_RSI = get_data_by_wss(stock_code, "RSI", "tradeDate=" + yesterdaystr + ";RSI_N=6;priceAdj=U;cycle=D")
    last_CCI = get_data_by_wss(stock_code, "CCI", "tradeDate=" + yesterdaystr + ";CCI_N=14;priceAdj=U;cycle=D")
    last_AMT = get_data_by_wss(stock_code, "AMT", "tradeDate=" + yesterdaystr + ";cycle=D")

    choose_stock = []
    print('--------正在计算结果--------')
    for i in range(len(stock_code)):
        cci_raise_bool = CCI[i] > last_CCI[i]
        cci_range_bool = CCI[i] < CCI_UL and CCI[i] > CCI_DL
        # KDJ线向上是J>K>D
        kdj_raise_bool = KDJ_J[i] > KDJ_K[i] and KDJ_K[i] > KDJ_D[i]
        rsi_raise_bool = RSI[i] > last_RSI[i]
        macd_jincha_bool = MACD[i] > 0
        if cci_raise_bool and cci_range_bool and kdj_raise_bool and rsi_raise_bool and macd_jincha_bool:
            choose_stock.append(i)

    c_no = [i for i in range(1, len(choose_stock) + 1)]
    c_code = []
    c_name = []
    c_k_cci = []
    c_cci = []
    c_amt_ratio = []
    c_kdj_j = []
    c_rsi = []
    c_dif = []

    for i in range(len(choose_stock)):
        c_code.append(stock_code[choose_stock[i]])
        c_name.append(stock_name[choose_stock[i]])
        # 斜率公式要改
        c_k_cci.append(CCI[choose_stock[i]] - last_CCI[choose_stock[i]])
        c_cci.append(CCI[choose_stock[i]])
        c_amt_ratio.append(AMT[choose_stock[i]] - last_AMT[choose_stock[i]])
        c_kdj_j.append(KDJ_J[choose_stock[i]])
        c_rsi.append(RSI[choose_stock[i]])
        c_dif.append(DIF[choose_stock[i]])

    dic = {'序列号': c_no,
           '股票代码': c_code,
           '股票名称': c_name,
           'CCI曲线斜率': c_k_cci,
           'CCI值': c_cci,
           '成交额比': c_amt_ratio,
           'KDJ值（J值）': c_kdj_j,
           'RSI(R1值)': c_rsi,
           'MACD(DIF值)': c_dif}

    new_dataframe = pd.DataFrame(data=dic)
    excel_path = './data/' + todaystr + '.xlsx'
    new_dataframe.to_excel(excel_path, index=False)
    print('完成，结果保存为' + todaystr + '.xlsx')


if __name__ == '__main__':
    warnings.filterwarnings("ignore")
    main()
    time.sleep(5)
