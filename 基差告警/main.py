import WindPy
import numpy as np
import datetime
import warnings
from tool import *


def get_all_code(f_code):
    future_code = []
    today = datetime.datetime.today().strftime("%Y-%m-%d")
    for i in range(len(f_code)):
        data = WindPy.w.wset("futurecc","startdate="+ today + ";enddate="+ today + ";wind_code=" + f_code[i] + ";field=wind_code,last_trade_date", usedf=True)
        future_code.append(data[1]['wind_code'].values)
    return future_code


def runTask(day=0, hour=0, min=1, second=0):
    difference_value = set_par()
    with open('./commodity_para.txt', "w") as f:
        f.write(str(difference_value))

    # 链接wind
    print("正在连接wind金融终端------------------------------------------")
    WindPy.w.start()
    WindPy.w.isconnected()

    # 获得开始运行的系统时间
    now = datetime.datetime.now()
    format_pattern = '%Y-%m-%d %H:%M:%S'

    # 加载股票数据信息
    futures_info = np.load('futures_info.npz', allow_pickle=True)['futures_code']
    cls_code = get_all_code(futures_info)
    commodity_code = [b for a in cls_code for b in a]
    name_df = WindPy.w.wsd(commodity_code, "sec_name", "ED0D", now.strftime("%Y-%m-%d"), "Fill=Previous",usedf=True)
    commodity_name = list(name_df[1]['SEC_NAME'].values)

    # 创建代码到名字的字典
    C2N = list2dic(commodity_code, commodity_name)

    # 记录一天基差的期货
    zc_commodity = []

    # 判断打印信息的bool变量
    marketopen_tip = True

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
            with open('./commodity_para.txt', "r") as f:
                s = f.read()
                para = s.split()
                difference_value = float(para[0])

            # 计算出今天是星期几，是否为交易日
            today = datetime.datetime.today()
            todaystr = today.strftime("%Y-%m-%d %H:%M:%S")
            weekday = today.weekday()

            # 判断是否为周六日的休市时间
            if weekday == 5 or weekday == 6:
                if marketopen_tip:
                    print('---------------------------------------------------------')
                    print('现在是' + todaystr)
                    print('周六日不在开市时间之中')
                    zc_commodity = []
                    marketopen_tip = False
            else:
                if True:
                    print('---------------------------------------------------------')
                    print('现在是' + todaystr)

                    marketopen_tip = True
                    # 获取全部期货现在的分钟数据
                    a = WindPy.w.wsq(commodity_code, "rt_last", usedf=True)

                    if len(list(a[1].index))==0:
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
                            for j in range(len(cls_code[i])-1):
                                now_code = cls_code[i][j]
                                next_code = cls_code[i][j+1]
                                now_dight = re.sub("\D", "", now_code)
                                next_dight = re.sub("\D", "", next_code)
                                if len(now_dight) != len(next_dight):
                                    continue
                                else:
                                    now_month = int(now_dight[-2:])
                                    next_month = int(next_dight[-2:])
                                    now_year = int(now_dight[:-2])
                                    next_year = int(next_dight[:-2])
                                    judge = (now_month+1 == next_month and now_year == next_year) \
                                            or (now_month == 12 and next_month == 1 and now_year+1 == next_year)
                                    if not judge:
                                        continue

                                now_price = C2P[cls_code[i][j]]
                                next_price = C2P[cls_code[i][j+1]]

                                # 判断是否返回了数据
                                if now_price == 0 or next_price == 0:
                                    continue

                                if now_price > next_price:
                                    min_price = next_price
                                else:
                                    min_price = now_price

                                percent = (now_price - next_price) / min_price

                                # 判断是否之前已经在基差列表中
                                if (cls_code[i][j], cls_code[i][j+1]) in zc_commodity:
                                    if abs(percent) > difference_value / 100:
                                        continue
                                    else:
                                        zc_commodity.remove((cls_code[i][j], cls_code[i][j+1]))
                                else:
                                    # 不在基差列表的，若符合基差条件，则将期货代码记录
                                    if abs(percent) > difference_value / 100:
                                        zc_commodity.append((cls_code[i][j], cls_code[i][j+1]))
                                        zc_choose_commodity.append((cls_code[i][j], cls_code[i][j+1]))
                                        zc_choose_diff.append(str(abs(percent)*100)[:5] + '%')

                        # 判断是否有符合基差的期货
                        if len(zc_choose_commodity) != 0:
                            msg = todaystr + ' 符合基差条件价差大于' + str(difference_value) + '%的期货有:\n'
                            for i in range(len(zc_choose_commodity)):
                                item_code = zc_choose_commodity[i][0]
                                item_next_code = zc_choose_commodity[i][1]
                                itemstr = item_code + ' ' + C2N[item_code] + '  ' + item_next_code \
                                          + ' ' + C2N[item_next_code] + '  价差: ' + str(zc_choose_diff[i]) + '\n'
                                msg = msg + itemstr
                            print(msg)

                            # 告警
                            info(title='基差告警', msg=msg)

                            with open('log/' + today.strftime("%Y-%m-%d") + " 基差.txt", "a") as f:
                                f.write(msg + '\n')
                        else:
                            print(todaystr + ' 基差条件没有选中期货')
                else:
                    if marketopen_tip:
                        print('---------------------------------------------------------')
                        print('现在是' + todaystr)
                        print('不在开市时间之中 9:30-11:30或13:00-15:00')
                        zc_commodity = []
                        marketopen_tip = False

            # 结束计时，并打印使用时间
            time_end = time.time()
            if marketopen_tip:
                print('time cost', time_end - time_start, 's')

            # 生成下一执行时间
            iter_time = iter_now + period
            strnext_time = iter_time.strftime('%Y-%m-%d %H:%M:%S')
            # 继续循环，等待下一执行时间
            continue


if __name__ == '__main__':
    warnings.filterwarnings("ignore")
    runTask()
