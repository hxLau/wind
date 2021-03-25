import WindPy
import numpy as np
import datetime
import warnings
import pandas as pd
from tool import *


# 获取某一类的全部期货商品代码
def get_all_code(f_code):
    future_code = []
    today = datetime.datetime.today().strftime("%Y-%m-%d")
    for i in range(len(f_code)):
        data = WindPy.w.wset("futurecc","startdate="+ today + ";enddate="+ today + ";wind_code=" + f_code[i] + ";field=wind_code,last_trade_date", usedf=True)
        future_code.append(data[1]['wind_code'].values)
    return future_code


# 获取所有期货商品3年的价格，返回df
def get_history_price(code, now):
    df = WindPy.w.wsd(code, "close", "ED-3Y", now.strftime("%Y-%m-%d %H:%M:%S"), "ShowBlank=-1", usedf=True)[1]
    df = df.iloc[::-1]
    return df


# 计算所有期货商品的历史基差
def get_history_zc(df, cls_code):
    time_size = df.shape[0]
    zc_history = {}
    for i in range(len(cls_code)):
        # 同类别迭代
        for j in range(len(cls_code[i]) - 1):
            f_code = cls_code[i][j]
            a_code = cls_code[i][j + 1]
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
            zc_item_list = []
            for k in range(time_size):
                f_price = df.iloc[[k]][[a_code, f_code]].values[0][0]
                a_price = df.iloc[[k]][[a_code, f_code]].values[0][1]
                # if f_price == -1 and a_price == -1:
                #    break
                if f_price == -1 or a_price == -1:
                    break

                if f_price > a_price:
                    min_price = a_price
                else:
                    min_price = f_price

                item_zc = abs(f_price - a_price) / min_price
                zc_item_list.append(item_zc)
            key = (f_code, a_code)
            zc_history[key] = zc_item_list
    return zc_history


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

    # 加载股票数据信息
    futures_info = np.load('futures_info.npz', allow_pickle=True)['futures_code']
    # 分了类别的期货商品代码
    cls_code = get_all_code(futures_info)
    # 没分类的期货商品代码和名字
    commodity_code = [b for a in cls_code for b in a]
    name_df = WindPy.w.wsd(commodity_code, "sec_name", "ED0D", now.strftime("%Y-%m-%d"), "Fill=Previous",usedf=True)
    commodity_name = list(name_df[1]['SEC_NAME'].values)

    # 创建代码到名字的字典
    C2N = list2dic(commodity_code, commodity_name)

    # 记录一天符合基差在历史数据前5%的期货
    zc_commodity = []

    # 获取所有期货的历史价格
    print("正在计算所有商品的当前相邻月基差比例历史数据-------------------------------")
    histroy_price = get_history_price(commodity_code, now)
    histroy_zc = get_history_zc(histroy_price, cls_code)

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
            C2P = list2dic(commodity_code, [-1] * len(commodity_code))

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
            a = WindPy.w.wsq(commodity_code, "rt_last", usedf=True)

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
                for i in range(len(cls_code)):
                    # 同类别迭代
                    for j in range(len(cls_code[i]) - 1):
                        now_code = cls_code[i][j]
                        next_code = cls_code[i][j + 1]
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

                        now_price = C2P[cls_code[i][j]]
                        next_price = C2P[cls_code[i][j + 1]]

                        # 判断是否返回了数据
                        if now_price == 0 or next_price == 0:
                            continue

                        if now_price > next_price:
                            min_price = next_price
                        else:
                            min_price = now_price

                        percent = (now_price - next_price) / min_price
                        histroy_item_zc_list = histroy_zc[(now_code, next_code)]
                        histroy_item_zc_list.sort()
                        higher_number = searchNum(histroy_item_zc_list, percent)
                        item_position = 1 - (higher_number / len(histroy_item_zc_list))

                        # 判断是否之前已经在基差列表中
                        if (cls_code[i][j], cls_code[i][j + 1]) in zc_commodity:
                            if item_position <= position / 100:
                                continue
                            else:
                                zc_commodity.remove((cls_code[i][j], cls_code[i][j + 1]))
                        else:
                            # 不在基差列表的，若符合基差条件，则将期货代码记录
                            if item_position <= position / 100:
                                zc_commodity.append((cls_code[i][j], cls_code[i][j + 1]))
                                zc_choose_commodity.append((cls_code[i][j], cls_code[i][j + 1]))
                                zc_choose_diff.append(((str(abs(percent) * 100))[:5] + '%',
                                                       str(abs(item_position) * 100)[:5] + '%',
                                                       str(abs(max(histroy_item_zc_list)) * 100)[:5] + '%'))

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