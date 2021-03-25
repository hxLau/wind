import WindPy
import numpy as np
import datetime
import warnings
import pandas as pd
from tool import *


# 获取全部A股代码
def get_A_stock(todaystr):
    A_stock = WindPy.w.wset("sectorconstituent", "date=" + todaystr + ";sectorid=a001010100000000")
    A_code = A_stock.Data[1]
    A_name = A_stock.Data[2]
    return A_code, A_name


# 获取全部H股代码
def get_HK_stock(todaystr):
    HK_stock = WindPy.w.wset("sectorconstituent","date=" + todaystr + ";sectorid=a002010100000000")
    HK_code = HK_stock.Data[1]
    HK_name = HK_stock.Data[2]
    return HK_code, HK_name


# 获取全部泸股通或深股通代码
def get_LS_stock(todaystr):
    LGT_stock = WindPy.w.wset("sectorconstituent","date=" + todaystr + ";sectorid=1000014938000000")
    LGT_code = LGT_stock.Data[1]
    SGT_stock = WindPy.w.wset("sectorconstituent","date=" + todaystr + ";sectorid=1000023475000000")
    SGT_code = SGT_stock.Data[1]
    LS_code = LGT_code + SGT_code
    return LS_code


# 获取全部港股通代码
def get_GGT_stock(todaystr):
    GGT_stock = WindPy.w.wset("sectorconstituent","date=" + todaystr + ";sectorid=1000025142000000")
    GGT_code = GGT_stock.Data[1]
    return GGT_code


# 获取MA或者区间日均交易额数据
def get_data_by_wss(code, variable, para):
    result = []
    divide_size = int(len(code)/2000) + 1
    for i in range(divide_size):
        if i == divide_size - 1:
            zfv = WindPy.w.wss(code[i*2000:], variable, para, usedf=True)[1]
        else:
            zfv = WindPy.w.wss(code[i*2000:(i+1)*2000], variable, para, usedf=True)[1]
        item_list = list(zfv[variable].values)
        for j in range(len(item_list)):
            result.append(item_list[j])
    return result


def runTask(day=0, hour=0, min=1, second=0):
    H_volume, Q_change = set_par()
    with open('./parameter.txt', "w") as f:
        f.write(str(H_volume) + ' ' + str(Q_change))

    # 链接wind
    print("正在连接wind金融终端------------------------------------------")
    WindPy.w.start()
    WindPy.w.isconnected()

    # 获得开始运行的系统时间
    now = datetime.datetime.now()
    format_pattern = '%Y-%m-%d %H:%M:%S'
    nowstr = now.strftime(format_pattern)

    # 加载股票数据信息
    A_code, A_name = get_A_stock(nowstr)
    HK_code, HK_name = get_HK_stock(nowstr)
    LS_code = get_LS_stock(nowstr)
    GGT_code = get_GGT_stock(nowstr)

    # 创建代码到名字的字典
    A2N = list2dic(A_code, A_name)
    H2N = list2dic(HK_code, HK_name)

    # 记录一天符合放量监控的股票
    A_stock = []
    HK_stock = []

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

            # 存储选中的股票的信息
            A_choose_stock = []
            HK_choose_stock = []
            A_choose_value = []
            HK_choose_value = []

            # 创建存储股票最新价格的字典，初始化所有价格为-1，用于后面判断是否有股票没有价格
            A2P = list2dic(A_code, [-1] * len(A_code))
            HK2P = list2dic(A_code, [-1] * len(A_code))

            # 读取参数
            with open('./parameter.txt', "r") as f:
                s = f.read()
                para = s.split()
                H_volume = float(para[0])
                Q_change = float(para[1])

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
                    A_stock = []
                    HK_stock = []
                    marketopen_tip = False
            else:
                hour = today.strftime("%Y-%m-%d %H:%M:%S")[11:13]
                minute = today.strftime("%Y-%m-%d %H:%M:%S")[14:16]
                total_minutes = int(hour) * 60 + int(minute)

                # if (total_minutes > 570 and total_minutes < 690) or (total_minutes > 780 and total_minutes < 900):
                if True:
                    print('---------------------------------------------------------')
                    print('现在是' + todaystr)

                    marketopen_tip = True

                    A_change = []
                    A_volumn = []
                    HK_change = []
                    HK_volumn = []

                    # 获取A和H股的涨跌幅和交易额数据wsq一次只能获取4000条
                    for i in range(3):
                        if i==2:
                            zfv = WindPy.w.wsq(A_code[i * 2000:], "rt_pct_chg,rt_amt", usedf=True)[1]
                        else:
                            zfv = WindPy.w.wsq(A_code[i*2000:(i+1)*2000], "rt_pct_chg,rt_amt", usedf=True)[1]
                        zf_item_list = list(zfv['RT_PCT_CHG'].values)
                        v_item_list = list(zfv['RT_AMT'].values)
                        for j in range(len(zf_item_list)):
                            A_change.append(zf_item_list[j])
                        for j in range(len(v_item_list)):
                            A_volumn.append(v_item_list[j])

                    for i in range(2):
                        if i == 1:
                            zfv = WindPy.w.wsq(HK_code[i * 2000:], "rt_pct_chg,rt_amt", usedf=True)[1]
                        else:
                            zfv = WindPy.w.wsq(HK_code[i * 2000:(i + 1) * 2000], "rt_pct_chg,rt_amt", usedf=True)[1]
                        zf_item_list = list(zfv['RT_PCT_CHG'].values)
                        v_item_list = list(zfv['RT_AMT'].values)
                        for j in range(len(zf_item_list)):
                            HK_change.append(zf_item_list[j])
                        for j in range(len(v_item_list)):
                            HK_volumn.append(v_item_list[j])

                    last30_date = WindPy.w.tdaysoffset(-30, today.isoformat(),
                                                     "Period=D;Days=Alldays").Times[0].strftime("%Y%m%d")

                    # 获取A和H股的MA和区间日均交易额数据wsq一次只能获取2000条
                    A_MA5 = get_data_by_wss(A_code, "MA", "tradeDate=" + today.strftime("%Y-%m-%d")
                                            + ";MA_N=5;priceAdj=F;cycle=D")
                    A_MA10 = get_data_by_wss(A_code, "MA", "tradeDate=" + today.strftime("%Y-%m-%d")
                                            + ";MA_N=10;priceAdj=F;cycle=D")
                    A_MA20 = get_data_by_wss(A_code, "MA", "tradeDate=" + today.strftime("%Y-%m-%d")
                                            + ";MA_N=20;priceAdj=F;cycle=D")
                    A_MA60 = get_data_by_wss(A_code, "MA", "tradeDate=" + today.strftime("%Y-%m-%d")
                                            + ";MA_N=60;priceAdj=F;cycle=D")
                    A_aver_volumn = get_data_by_wss(A_code, "AVG_AMT_PER", "unit=1;startDate=" + last30_date +
                                                    ";endDate=" + today.strftime("%Y-%m-%d"))

                    HK_MA5 = get_data_by_wss(HK_code, "MA", "tradeDate=" + today.strftime("%Y-%m-%d")
                                            + ";MA_N=5;priceAdj=F;cycle=D")
                    HK_MA10 = get_data_by_wss(HK_code, "MA", "tradeDate=" + today.strftime("%Y-%m-%d")
                                             + ";MA_N=10;priceAdj=F;cycle=D")
                    HK_MA20 = get_data_by_wss(HK_code, "MA", "tradeDate=" + today.strftime("%Y-%m-%d")
                                             + ";MA_N=20;priceAdj=F;cycle=D")
                    HK_MA60 = get_data_by_wss(HK_code, "MA", "tradeDate=" + today.strftime("%Y-%m-%d")
                                             + ";MA_N=60;priceAdj=F;cycle=D")
                    HK_aver_volumn = get_data_by_wss(HK_code, "AVG_AMT_PER", "unit=1;startDate=" + last30_date +
                                                    ";endDate=" + today.strftime("%Y-%m-%d"))

                    if len(A_change)==0:
                        print('返回数据错误')
                        A_stock = []
                        HK_stock = []
                    else:
                        # 对A股迭代判断是否有符合条件的股票
                        for i in range(len(A_code)):
                            qs_judge = A_MA5[i] > A_MA10[i] and A_MA10[i] > A_MA20[i] and A_MA20[i] > A_MA60[i]
                            zf_judge = A_change[i] > (Q_change / 100)
                            fangliang = A_volumn[i] / A_aver_volumn[i] - 1
                            fl_judge = fangliang > (H_volume / 100)

                            # 判断是否之前已经在选中股票列表中
                            if A_code[i] in A_stock:
                                if qs_judge and zf_judge and fl_judge:
                                    continue
                                else:
                                    A_stock.remove(A_code[i])
                            else:
                                # 不在选中股票列表的，若符合放量条件，则将期票代码记录
                                if qs_judge and zf_judge and fl_judge:
                                    A_stock.append(A_code[i])
                                    A_choose_stock.append(A_code[i])
                                    A_choose_value.append((str(fangliang*100)[:5]+'%', str(A_change[i]*100)[:5]+'%'))

                        # 对H股迭代判断是否有符合条件的股票
                        for i in range(len(HK_code)):
                            qs_judge = HK_MA5[i] > HK_MA10[i] and HK_MA10[i] > HK_MA20[i] and HK_MA20[i] > HK_MA60[i]
                            zf_judge = HK_change[i] > (Q_change / 100)
                            fangliang = HK_volumn[i] / HK_aver_volumn[i] - 1
                            fl_judge = fangliang > (H_volume / 100)

                            # 判断是否之前已经在选中股票列表中
                            if HK_code[i] in HK_stock:
                                if qs_judge and zf_judge and fl_judge:
                                    continue
                                else:
                                    HK_stock.remove(HK_code[i])
                            else:
                                # 不在选中股票列表的，若符合放量条件，则将期票代码记录
                                if qs_judge and zf_judge and fl_judge:
                                    HK_stock.append(HK_code[i])
                                    HK_choose_stock.append(HK_code[i])
                                    HK_choose_value.append((str(fangliang*100)[:5]+'%', str(HK_change[i]*100)[:5]+'%'))

                        # 判断A股是否有符合条件的股票
                        if len(A_choose_stock) != 0:
                            msg = todaystr + ' A股符合条件放量大于' + str(H_volume) + "%，涨跌幅大于" \
                                  + str(Q_change) + '%的股票有:\n'
                            for i in range(len(A_choose_stock)):
                                item_code = A_choose_stock[i]
                                itemstr = item_code + ' ' + A2N[item_code] + '  放量: ' + A_choose_value[i][0] + \
                                          '  涨跌幅: ' + A_choose_value[i][1] + '  '
                                if item_code in LS_code:
                                    itemstr = itemstr + '泸股通/深股通：是 \n'
                                else:
                                    itemstr = itemstr + '泸股通/深股通：否 \n'
                                msg = msg + itemstr
                            print(msg)

                            # 告警
                            info(title='放量监控告警', msg=msg)

                            with open('log/' + today.strftime("%Y-%m-%d") + " A股放量监控.txt", "a") as f:
                                f.write(msg + '\n')
                        else:
                            print(todaystr + ' A股没有选中股票')

                        # 判断H股是否有符合条件的股票
                        if len(HK_choose_stock) != 0:
                            msg = todaystr + ' H股符合条件放量大于' + str(H_volume) + "%，涨跌幅大于" \
                                  + str(Q_change) + '%的股票有:\n'
                            for i in range(len(HK_choose_stock)):
                                item_code = HK_choose_stock[i]
                                itemstr = item_code + ' ' + H2N[item_code] +  '  放量: ' + HK_choose_value[i][0] + \
                                          '  涨跌幅: ' + HK_choose_value[i][1] + '  '
                                if item_code in GGT_code:
                                    itemstr = itemstr + '港股通：是 \n'
                                else:
                                    itemstr = itemstr + '港股通：否 \n'
                                msg = msg + itemstr
                            print(msg)

                            # 告警
                            info(title='放量监控告警', msg=msg)

                            with open('log/' + today.strftime("%Y-%m-%d") + " H股放量监控.txt", "a") as f:
                                f.write(msg + '\n')
                        else:
                            print(todaystr + ' H股没有选中股票')
                else:
                    if marketopen_tip:
                        print('---------------------------------------------------------')
                        print('现在是' + todaystr)
                        print('不在开市时间之中 9:30-11:30或13:00-15:00')
                        A_stock = []
                        HK_stock = []
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
