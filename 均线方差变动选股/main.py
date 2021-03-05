from WindPy import w
import numpy as np
import pandas as pd
from datetime import datetime
import os
import easygui as eg
import re

# 判断字符串是否为数字
def is_number(num):
  pattern = re.compile(r'^[-+]?[-0-9]\d*\.\d*|[-+]?\.?[0-9]\d*$')
  result = pattern.match(num)
  if result:
    return True
  else:
    return False


# 计算MA值
def calculateMA(df, MANUM, days):
    MA_list = []
    for i in range(days):
        item = np.mean(df[i:i+MANUM]['CLOSE'].values)
        MA_list.append(item)
    return MA_list


# 获取某个期货的完整数据，计算除方差
def get_qihuo_data(w, codes, beginTime):
    today = datetime.today().strftime("%Y%m%d")
    l_today = str(int(today) - 10000)
    year = l_today[:4]
    if l_today[-4:] == '0229':
        l_today = year + '0228'
    days = w.tdayscount(l_today, today, "").Data[0][0]
    print(days)

    history_data = w.wsd(codes=codes, fields="close", beginTime=beginTime, options="returnType=1;PriceAdj=F",
                         usedf=True)

    df = history_data[1].iloc[::-1]
    if df['CLOSE'][0]==None:
        print('it is None')
        return df, True
    # 抽取日期列表
    date_list = list(df[:days].index)
    for i in range(days):
        date_list[i] = date_list[i].strftime("%Y%m%d")

    # 计算均值和方差
    MA5 = calculateMA(df, 5, days)
    MA10 = calculateMA(df, 10, days)
    MA21 = calculateMA(df, 21, days)
    MA55 = calculateMA(df, 55, days)
    MA250 = calculateMA(df, 250, days)

    VAR = []
    for i in range(days):
        item = [MA5[i], MA10[i], MA21[i], MA55[i], MA250[i]]
        VAR.append(np.var(item))

    # 形成dataframe
    new_df = pd.DataFrame(columns=['Date'], data=date_list)
    new_df['MA5'] = MA5
    new_df['MA10'] = MA10
    new_df['MA21'] = MA21
    new_df['MA55'] = MA55
    new_df['MA250'] = MA250
    new_df['VAR'] = VAR
    return new_df, False


# 获取某个A股的完整数据，计算除方差
def get_Agu_data(w, codes, beginTime):
    today = datetime.today().strftime("%Y%m%d")
    l_today = str(int(today) - 10000)
    year = l_today[:4]
    if l_today[-4:] == '0229':
        l_today = year + '0228'
    days = w.tdayscount(l_today, today, "").Data[0][0]
    print(days)

    history_data = w.wsd(codes=codes, fields="close", beginTime=beginTime, options="returnType=1;PriceAdj=F",
                         usedf=True)

    df = history_data[1].iloc[::-1]
    if df['CLOSE'][0]==None:
        print('it is None')
        return df, True
    # 抽取日期列表
    date_list = list(df[:days].index)
    for i in range(days):
        date_list[i] = date_list[i].strftime("%Y%m%d")

    # 计算均值和方差
    MA5 = calculateMA(df, 5, days)
    MA10 = calculateMA(df, 10, days)
    MA20 = calculateMA(df, 20, days)
    MA60 = calculateMA(df, 60, days)
    MA250 = calculateMA(df, 250, days)

    VAR = []
    for i in range(days):
        item = [MA5[i], MA10[i], MA20[i], MA60[i], MA250[i]]
        VAR.append(np.var(item))

    # 形成dataframe
    new_df = pd.DataFrame(columns=['Date'], data=date_list)
    new_df['MA5'] = MA5
    new_df['MA10'] = MA10
    new_df['MA20'] = MA20
    new_df['MA60'] = MA60
    new_df['MA250'] = MA250
    new_df['VAR'] = VAR
    return new_df, False


# 获取期货列表
def get_qihuo(w, begin, end):
    qihuo = w.wset("sectorconstituent", "startdate=" + begin + ";enddate=" + end + ";sectorid=1000010084000000")
    qihuocode = list(pd.Series(qihuo.Data[1]))
    return qihuocode


# 获取A股列表
def get_Agu(w, begin, end):
    all_a = w.wset('SectorConstituent', "startdate=" + begin + ";enddate=" + end + ";sector=全部A股")
    all_Code = list(pd.Series(all_a.Data[1]))  # 获取的是列表数据
    return all_Code


# 获取全部期货文件
def get_qihuo_file():
    w.start()
    w.isconnected()
    today = datetime.today().strftime("%Y%m%d")
    begin = "20180101"

    qihuo_list = get_qihuo(w, begin, today)
    for i in range(len(qihuo_list)):
        print(qihuo_list[i])
        df, errorcode = get_qihuo_data(w, qihuo_list[i], begin)
        if errorcode:
            continue
        df.to_csv('./data/qihuo/' + qihuo_list[i] +'.csv', index=False)


# 获取A股全部文件
def get_Agu_file():
    w.start()
    w.isconnected()
    today = datetime.today().strftime("%Y%m%d")
    begin = "20180101"

    Agu_list = get_Agu(w, begin, today)
    for i in range(len(Agu_list)):
        print(Agu_list[i])
        df, errorcode = get_Agu_data(w, Agu_list[i], begin)
        if errorcode:
            continue
        df.to_csv('./data/Agu/' + Agu_list[i] +'.csv', index=False)


# 获取期货和A股数据
def get_data():
    get_qihuo_file()
    get_Agu_file()


# 选择符合条件的股票
def choose_data(mypath = './data/qihuo/', percent=0.05):
    choose_stock = []

    file_list = [f for f in os.listdir(mypath) if os.path.isfile(os.path.join(mypath, f))]
    # print(file_list)

    for i in range(len(file_list)):
        file_path = mypath + file_list[i]
        df = pd.read_csv(file_path)
        var_array = df['VAR'].values
        max_var = max(var_array)
        now_value = var_array[0]
        if now_value < percent*max_var:
            choose_stock.append(file_list[i])
    return choose_stock


# 设置阈值
def set_percent():
    msg = "请设定阈值（默认为0.05），设定范围在0到1（不包括0和1）"
    title = "设定阈值"
    fieldNames = ["阈值设定："]
    fieldValues = eg.multenterbox(msg, title, fieldNames)

    while True:
        # 点击取消按钮操作
        if fieldValues == None:
            break
        # 报错提示初始值
        errmsg = ""
        for i in range(len(fieldNames)):
            if fieldValues[i].strip() == "" or not is_number(fieldValues[i]):
                errmsg += ('只能设置为数字且不能为空，如0.05')
            if float(fieldValues[i])>=1 or fieldValues<=0:
                errmsg += ('设定范围在0到1（不包括0和1）')

        # 无报错提示，退出程序，否则，报错提示，重新进入输入界面
        if errmsg == "":
            break
        fieldValues = eg.multenterbox(errmsg, title, fieldNames, fieldValues)

    print("阈值设定为: " + str(float(fieldValues[0])))
    return float(fieldValues[0])


def main():
    # get_data()
    percent = set_percent()
    mypath = './data/qihuo/'
    choose_stock = choose_data(mypath, percent)
    msg = '选中的股票有：\n'
    for i in range(len(choose_stock)):
        msg += '代码: ' + choose_stock[i] + '\n'
    print(msg)


if __name__ == '__main__':
    main()


