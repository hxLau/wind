import WindPy
import numpy as np
import datetime
import warnings
import pandas as pd
from tool import *


# 获取某一类的当前全部期货商品代码
def get_all_now_code(f_code):
    future_code = []
    today = datetime.datetime.today().strftime("%Y-%m-%d")
    for i in range(len(f_code)):
        data = WindPy.w.wset("futurecc","startdate="+ today + ";enddate="+ today + ";wind_code=" + f_code[i] + ";field=wind_code,last_trade_date", usedf=True)
        future_code.append(data[1]['wind_code'].values)
    return future_code


# 获取某一类的全部期货商品代码
def get_all_code(f_code):
    future_code = []
    today = datetime.datetime.today().strftime("%Y-%m-%d")
    last_3year_date = WindPy.w.tdaysoffset(-3, today, "Period=Y").Times[0].strftime("%Y-%m-%d")
    for i in range(len(f_code)):
        data = WindPy.w.wset("futurecc","startdate="+ last_3year_date + ";enddate="+ today + ";wind_code=" + f_code[i] + ";field=wind_code,last_trade_date", usedf=True)
        future_code.append(data[1]['wind_code'].values)
    return future_code


# 获取所有期货商品3年的价格，返回df
def get_history_price(code, now):
    print('获取历史价格-------------------')
    size = int(len(code)/1000) + 1
    for i in range(size):
        if i == 0:
            df = WindPy.w.wsd(code[i*1000:(i+1)*1000], "close", "ED-3Y", now.strftime("%Y-%m-%d %H:%M:%S"), "", usedf=True)[1]
        elif i == size-1:
            item_df = WindPy.w.wsd(code[i*1000:], "close", "ED-3Y", now.strftime("%Y-%m-%d %H:%M:%S"), "", usedf=True)[1]
            df = pd.concat([df, item_df], axis=1)
        else:
            item_df = WindPy.w.wsd(code[i * 1000:(i+1)*1000], "close", "ED-3Y", now.strftime("%Y-%m-%d %H:%M:%S"), "",
                                   usedf=True)[1]
            df = pd.concat([df, item_df], axis=1)
    df = df.iloc[::-1]
    return df


# 计算所有期货商品的历史基差
def get_history_zc(df, history_cls_code, futures_info, zc_dic):
    print('计算历史基差-------------------')
    zc_history = zc_dic
    for i in range(len(history_cls_code)):
        # 同类别迭代
        for j in range(len(history_cls_code[i]) - 1):
            f_code = history_cls_code[i][j]
            a_code = history_cls_code[i][j + 1]
            f_dight = re.sub("\D", "", f_code)
            a_dight = re.sub("\D", "", a_code)
            if len(f_dight) != len(a_dight):
                continue
            else:
                f_month = int(f_dight[-2:])
                a_month = int(a_dight[-2:])
                f_year = int(f_dight[:-2])
                a_year = int(a_dight[:-2])
                judge = (f_month + 1 == a_month and f_year == a_year) \
                        or (f_month == 12 and a_month == 1 and f_year + 1 == a_year)
                if not judge:
                    continue
            keystr = futures_info[i] + f_dight[-2:] + a_dight[-2:]
            if keystr not in zc_history:
                continue
            zc_item_list = []

            item_df = df[[f_code, a_code]].dropna()
            time_size = item_df.shape[0]
            for k in range(time_size):
                f_price = item_df.values[k][0]
                a_price = item_df.values[k][1]

                if f_price > a_price:
                    min_price = a_price
                else:
                    min_price = f_price

                item_zc = abs(f_price - a_price) / min_price
                zc_item_list.append(item_zc)
            if len(zc_item_list) != 0:
                zc_history[keystr] = zc_history[keystr] + zc_item_list
    return zc_history


def get_zc_dic(now_cls_code, futures_info):
    dic = {}
    for i in range(len(now_cls_code)):
        # 同类别迭代
        for j in range(len(now_cls_code[i]) - 1):
            f_code = now_cls_code[i][j]
            a_code = now_cls_code[i][j + 1]
            f_dight = re.sub("\D", "", f_code)
            a_dight = re.sub("\D", "", a_code)
            if len(f_dight) != len(a_dight):
                continue
            else:
                f_month = int(f_dight[-2:])
                a_month = int(a_dight[-2:])
                f_year = int(f_dight[:-2])
                a_year = int(a_dight[:-2])
                judge = (f_month + 1 == a_month and f_year == a_year) \
                        or (f_month == 12 and a_month == 1 and f_year + 1 == a_year)
                if not judge:
                    continue
            keystr = futures_info[i] + f_dight[-2:] + a_dight[-2:]
            if keystr in list(dic.keys()):
                continue
            else:
                dic[keystr] = []
    return dic


def runTask(day=0, hour=0, min=1, second=0):
    position = set_par()
    with open('./para.txt', "w") as f:
        f.write(str(position))

    # 链接wind
    print("正在连接wind金融终端------------------------------------------")
    WindPy.w.start()
    WindPy.w.isconnected()

    # 获得开始运行的系统时间
    now = datetime.datetime.now()
    format_pattern = '%Y-%m-%d %H:%M:%S'
    yesterday = WindPy.w.tdaysoffset(-1, now, "").Times[0]

    weekday = now.weekday()
    if weekday == 5 or weekday == 6:
        print('---------------------------------------------------------')
        print('现在是' + now.strftime(format_pattern))
        print('周六日不在开市时间之中')
        while True:
            time.sleep(500)

    # 加载股票数据信息
    futures_info = np.load('futures_info.npz', allow_pickle=True)['futures_code']
    # 分了类别的期货商品代码
    now_cls_code = get_all_now_code(futures_info)
    # 没分类的期货商品代码和名字
    now_commodity_code = [b for a in now_cls_code for b in a]
    name_df = WindPy.w.wsd(now_commodity_code, "sec_name", "ED0D", now.strftime("%Y-%m-%d"), "Fill=Previous", usedf=True)
    now_commodity_name = list(name_df[1]['SEC_NAME'].values)
    history_cls_code = get_all_code(futures_info)
    history_commodity_code = [b for a in history_cls_code for b in a]
    zc_dic = get_zc_dic(now_cls_code, futures_info)

    # 创建代码到名字的字典
    C2N = list2dic(now_commodity_code, now_commodity_name)

    # 记录一天符合基差在历史数据前5%的期货
    zc_commodity = []

    # 获取所有期货的历史价格
    print("正在计算所有商品的当前相邻月基差比例历史数据-------------------------------")
    histroy_price = get_history_price(history_commodity_code, yesterday)
    histroy_zc = get_history_zc(histroy_price, history_cls_code, futures_info, zc_dic)

    # 计算下一次运行时间
    period = datetime.timedelta(days=day, hours=hour, minutes=min, seconds=second)
    next_time = now + period
    strnext_time = next_time.strftime('%Y-%m-%d %H:%M:%S')

    # 循环运行
    while True:
        # 获得当前的系统时间
        iter_now = datetime.datetime.now()
        iter_now_time = iter_now.strftime('%Y-%m-%d %H:%M:%S')
        # 用于判断是否已经越过了下一时间，若越过就要立刻执行工作
        cmp_time = (datetime.datetime.strptime(strnext_time, format_pattern) -
                    datetime.datetime.strptime(iter_now_time, format_pattern))

        # 判断当前时间是否符合下一运行时间
        if str(iter_now_time) == str(strnext_time) or cmp_time.days < 0:
            # 开始运行程序工作内容
            # 开始计时
            time_start = time.time()

            # 存储选中的期货的信息
            zc_choose_commodity = []
            zc_choose_diff = []

            # 创建存储期货最新价格的字典，初始化所有价格为-1，用于后面判断是否有期货没有价格
            C2P = list2dic(now_commodity_code, [-1] * len(now_commodity_code))

            # 读取参数
            with open('./para.txt', "r") as f:
                s = f.read()
                para = s.split()
                position = float(para[0])

            # 计算出今天是星期几，是否为交易日
            today = datetime.datetime.today()
            todaystr = today.strftime("%Y-%m-%d %H:%M:%S")

            print('---------------------------------------------------------')
            print('现在是' + todaystr)

            # 获取全部期货现在的分钟数据
            a = WindPy.w.wsq(now_commodity_code, "rt_last", usedf=True)

            if len(list(a[1].index)) == 0:
                print('返回数据错误')
                zc_commodity = []
            else:
                # 获取期货的代码和当前价格
                wind_code = list(a[1].index)

                wind_price = [a[1].values[i][0] for i in range(len(a[1].values))]

                # 记录返回每个期货的价格到字典
                for i in range(len(wind_price)):
                    C2P[wind_code[i]] = wind_price[i]

                # 迭代计算价差
                # 类别迭代
                for i in range(len(now_cls_code)):
                    # 同类别迭代
                    for j in range(len(now_cls_code[i]) - 1):
                        now_code = now_cls_code[i][j]
                        next_code = now_cls_code[i][j + 1]
                        now_dight = re.sub("\D", "", now_code)
                        next_dight = re.sub("\D", "", next_code)
                        if len(now_dight) != len(next_dight):
                            continue
                        else:
                            now_month = int(now_dight[-2:])
                            next_month = int(next_dight[-2:])
                            now_year = int(now_dight[:-2])
                            next_year = int(next_dight[:-2])
                            judge = (now_month + 1 == next_month and now_year == next_year) \
                                    or (now_month == 12 and next_month == 1 and now_year + 1 == next_year)
                            if not judge:
                                continue

                        now_price = C2P[now_cls_code[i][j]]
                        next_price = C2P[now_cls_code[i][j + 1]]

                        # 判断是否返回了数据
                        if now_price == 0 or next_price == 0:
                            continue

                        if now_price > next_price:
                            min_price = next_price
                        else:
                            min_price = now_price

                        percent = (now_price - next_price) / min_price

                        keystr = futures_info[i] + now_dight[-2:] + next_dight[-2:]
                        if keystr not in list(histroy_zc.keys()):
                            continue
                        histroy_item_zc_list = histroy_zc[keystr]
                        if len(histroy_item_zc_list)==0:
                            continue
                        histroy_item_zc_list.sort()
                        higher_number = searchNum(histroy_item_zc_list, percent)
                        item_position = 1 - (higher_number / len(histroy_item_zc_list))

                        # 判断是否之前已经在基差列表中
                        if (now_cls_code[i][j], now_cls_code[i][j + 1]) in zc_commodity:
                            if item_position <= position / 100:
                                continue
                            else:
                                zc_commodity.remove((now_cls_code[i][j], now_cls_code[i][j + 1]))
                        else:
                            # 不在基差列表的，若符合基差条件，则将期货代码记录
                            if item_position <= position / 100:
                                zc_commodity.append((now_cls_code[i][j], now_cls_code[i][j + 1]))
                                zc_choose_commodity.append((now_cls_code[i][j], now_cls_code[i][j + 1]))
                                zc_choose_diff.append(((str(abs(percent) * 100))[:5] + '%',
                                                       str(abs(item_position) * 100)[:5] + '%',
                                                       str(abs(max(histroy_item_zc_list)) * 100)[:5] + '%'))
                                '''
                                print('-----------------------------------------------------')
                                print(C2N[now_code] + ' ' + now_cls_code[i][j] + ' ' + now_cls_code[i][j+1])
                                print((str(abs(percent) * 100))[:5] + '%   ' + str(abs(item_position) * 100)[:5] + '%  '
                                      + str(len(histroy_item_zc_list)))
                                print(histroy_item_zc_list)
                                '''


                # 判断是否有符合基差的期货
                if len(zc_choose_commodity) != 0:
                    msg = todaystr + ' 符合当前基差在历史基差的排序比例前' + str(position) + '%的期货有:\n'
                    for i in range(len(zc_choose_commodity)):
                        item_code = zc_choose_commodity[i][0]
                        item_next_code = zc_choose_commodity[i][1]
                        itemstr = item_code + ' ' + C2N[item_code] + '  ' + item_next_code \
                                  + ' ' + C2N[item_next_code] + '  当前基差比例: ' + str(zc_choose_diff[i][0]) \
                                  + '  历史排序百分比：' + str(zc_choose_diff[i][1]) \
                                  + '  历史峰值：' + str(zc_choose_diff[i][2]) + '\n'
                        msg = msg + itemstr
                    print(msg)

                    # 告警
                    info(title='基差历史分布告警', msg=msg)

                    with open('log/' + today.strftime("%Y-%m-%d") + " 基差历史分布.txt", "a") as f:
                        f.write(msg + '\n')
                else:
                    print(todaystr + ' 基差历史分布条件没有选中期货')

            # 结束计时，并打印使用时间
            time_end = time.time()
            print('time cost', time_end - time_start, 's')

            # 生成下一执行时间
            iter_time = iter_now + period
            strnext_time = iter_time.strftime('%Y-%m-%d %H:%M:%S')
            # 继续循环，等待下一执行时间
            continue


if __name__ == '__main__':
    warnings.filterwarnings("ignore")
    runTask()