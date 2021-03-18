import WindPy
import numpy as np
import datetime
import warnings
from tool import *


def runTask(day=0, hour=0, min=1, second=0):
    difference_value, compare_day = set_par()
    with open('./set.txt', "w") as f:
        f.write(str(difference_value) + ' ' + str(compare_day))

    # 链接wind
    print("正在连接wind金融终端------------------------------------------")
    WindPy.w.start()
    WindPy.w.isconnected()

    # 加载股票数据信息
    A = np.load('ABH_stock_info.npz', allow_pickle=True)
    AB_stockname = list(A['AB_stockname'])
    AB_A_code = list(A['AB_A_code'])
    AB_B_code = list(A['AB_B_code'])
    AH_stockname = list(A['AH_stockname'])
    AH_A_code = list(A['AH_A_code'])
    AH_H_code = list(A['AH_H_code'])

    # 把AH股拆成两份
    AH_A_code1 = AH_A_code[:82]
    AH_A_code2 = AH_A_code[82:]
    AH_H_code1 = AH_H_code[:82]
    AH_H_code2 = AH_H_code[82:]

    # 创建股票ABH转换字典
    AB_A2B = list2dic(AB_A_code, AB_B_code)
    AB_B2A = list2dic(AB_B_code, AB_A_code)
    AH_A2H = list2dic(AH_A_code, AH_H_code)
    AH_H2A = list2dic(AH_H_code, AH_A_code)

    # 创建股票ABH和名字转换字典
    AB_A2N = list2dic(AB_A_code, AB_stockname)
    AB_B2N = list2dic(AB_B_code, AB_stockname)
    AH_A2N = list2dic(AH_A_code, AH_stockname)
    AH_H2N = list2dic(AH_H_code, AH_stockname)
    

    # 记录一天停涨和涨幅的股票
    AB_zhangting_stock = []
    AH_zhangting_stock = []
    AB_zhangfu_stock = []
    AH_zhangfu_stock = []

    # 两个判断打印信息的bool变量
    marketopen_tip = True
    tradeday_tip = True

    # 获得开始运行的系统时间
    now = datetime.datetime.now()
    format_pattern = '%Y-%m-%d %H:%M:%S'

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
        cmp_time = (datetime.datetime.strptime(strnext_time, format_pattern) - datetime.datetime.strptime(iter_now_time,
                                                                                                     format_pattern))
        # 判断当前时间是否符合下一运行时间
        if str(iter_now_time) == str(strnext_time) or cmp_time.days < 0:
            # 开始运行程序工作内容
            # 开始计时
            time_start = time.time()

            # 存储选中的股票的信息
            AB_zt_choose_stock = []
            AB_zf_choose_stock = []
            AB_zhangfu_value = []

            AH_zt_choose_stock = []
            AH_zf_choose_stock = []
            AH_zhangfu_value = []
            
            # 创建存储ABh最新价格的字典，初始化所有价格为-1，用于后面判断是否有股票没有价格
            AB_A2P = list2dic(AB_A_code, [-1] * len(AB_A_code))
            AB_B2P = list2dic(AB_B_code, [-1] * len(AB_A_code))
            AH_A2P = list2dic(AH_A_code, [-1] * len(AH_A_code))
            AH_H2P = list2dic(AH_H_code, [-1] * len(AH_A_code))

            # 读取参数
            with open('./set.txt', "r") as f:
                s = f.read()
                para = s.split()
                difference_value = float(para[0])
                compare_day = int(para[1])

            # 获取前十天的日期，找出上一个交易日
            today = datetime.datetime.today()
            todaystr = today.strftime("%Y-%m-%d %H:%M:%S")
            last_d = WindPy.w.tdaysoffset(-10, today.isoformat(), "Period=D;Days=Alldays")
            last_10_date = last_d.Times[0].strftime("%Y%m%d")
            yes_trade_date = WindPy.w.tdays(last_10_date).Times[-2].strftime("%Y%m%d")

            # 获取涨幅比较的日期
            last_zf_d = WindPy.w.tdaysoffset(-compare_day, today.isoformat(), "Period=D;Days=Alldays")
            last_zf_date = last_zf_d.Times[0].strftime("%Y%m%d")
            last_zf_tradeday = WindPy.w.tdays(last_zf_date).Times[0].strftime("%Y%m%d")

            # 打印交易日的提示
            if tradeday_tip:
                print('---------------------------------------------------------')
                print(str(compare_day) + '天前的交易日是' + last_zf_tradeday)
                tradeday_tip=False

            # 计算出今天是星期几，是否为交易日
            weekday = today.weekday()
            # 判断是否为周六日的休市时间
            if weekday == 5 or weekday == 6:
                if marketopen_tip:
                    print('---------------------------------------------------------')
                    print('现在是' + todaystr)
                    print('周六日不在开市时间之中')
                    AB_zhangting_stock = []
                    AH_zhangting_stock = []
                    AB_zhangfu_stock = []
                    AH_zhangfu_stock = []
                    marketopen_tip = False
            else:
                # 获取上一分钟的时间
                last_min_date = today + datetime.timedelta(minutes=-1)
                hour = today.strftime("%Y-%m-%d %H:%M:%S")[11:13]
                minute = today.strftime("%Y-%m-%d %H:%M:%S")[14:16]
                total_minutes = int(hour) * 60 + int(minute)

                # 判断是否在工作日开市时间之中9:30-11:30 或 13:00-15:00
                if (total_minutes > 570 and total_minutes < 690) or (total_minutes > 780 and total_minutes < 900):
                    print('---------------------------------------------------------')
                    print('现在是' + todaystr)

                    marketopen_tip = True

                    # 获取全部股票A和B市现在的分钟数据
                    error, AB_A_data = WindPy.w.wsi(AB_A_code, 'close', last_min_date, today, "Fill=Previous", usedf=True)
                    error, AB_B_data = WindPy.w.wsi(AB_B_code, 'close', last_min_date, today, "Fill=Previous", usedf=True)

                    # 获取全部股票A和H市现在的分钟数据
                    error, AH_A_data1 = WindPy.w.wsi(AH_A_code1, 'close', last_min_date, today, "Fill=Previous", usedf=True)
                    error, AH_A_data2 = WindPy.w.wsi(AH_A_code2, 'close', last_min_date, today, "Fill=Previous",
                                                     usedf=True)
                    error, AH_H_data1 = WindPy.w.wsi(AH_H_code1, 'close', last_min_date, today, "Fill=Previous", usedf=True)
                    error, AH_H_data2 = WindPy.w.wsi(AH_H_code2, 'close', last_min_date, today, "Fill=Previous",
                                                    usedf=True)


                    # 获取AB和AH中A股票前一天的收盘价
                    AB_A_all_yes_price = WindPy.w.wsd(codes=AB_A_code, fields="close", beginTime=yes_trade_date,
                                        endTime=yes_trade_date, options="returnType=1;PriceAdj=F", usedf=True)[
                        1].values
                    AH_A_all_yes_price = WindPy.w.wsd(codes=AH_A_code, fields="close", beginTime=yes_trade_date,
                                        endTime=yes_trade_date, options="returnType=1;PriceAdj=F", usedf=True)[
                        1].values

                    # 获取AB和AH股比较日期前的收盘价
                    AB_A_last_zf_price = WindPy.w.wsd(codes=AB_A_code, fields="close", beginTime=last_zf_tradeday,
                                            endTime=last_zf_tradeday, options="returnType=1;PriceAdj=F", usedf=True)[
                        1].values
                    AB_B_last_zf_price = WindPy.w.wsd(codes=AB_B_code, fields="close", beginTime=last_zf_tradeday,
                                            endTime=last_zf_tradeday, options="returnType=1;PriceAdj=F", usedf=True)[
                        1].values

                    AH_A_last_zf_price = WindPy.w.wsd(codes=AH_A_code, fields="close", beginTime=last_zf_tradeday,
                                            endTime=last_zf_tradeday, options="returnType=1;PriceAdj=F", usedf=True)[
                        1].values
                    AH_H_last_zf_price = WindPy.w.wsd(codes=AH_H_code, fields="close", beginTime=last_zf_tradeday,
                                            endTime=last_zf_tradeday, options="returnType=1;PriceAdj=F", usedf=True)[
                        1].values

                    '''
                    if len(AB_A_last_zf_price) != 82 or len(AB_B_last_zf_price) != 82:
                        print('30个工作日前返回的A和B股数量不同')
                        return
                    '''

                    # 通过返回的df的列是否有close这一属性判断是否返回正常
                    if 'close' not in AB_A_data.columns.values or 'close' not in AH_A_data1.columns.values:
                        print('A股返回数据错误')
                        AB_zhangting_stock = []
                        AB_zhangfu_stock = []
                        AH_zhangting_stock = []
                        AH_zhangfu_stock = []
                    elif 'close' not in AB_B_data.columns.values:
                        print('B股返回数据错误')
                        AB_zhangting_stock = []
                        AB_zhangfu_stock = []
                        AH_zhangting_stock = []
                        AH_zhangfu_stock = []
                    elif 'close' not in AH_H_data1.columns.values:
                        print('H股返回数据错误')
                        AB_zhangting_stock = []
                        AB_zhangfu_stock = []
                        AH_zhangting_stock = []
                        AH_zhangfu_stock = []
                    # 返回正常时
                    else:
                        # 获取AB和AH股的代码和当前价格
                        wind_AB_A_code = AB_A_data['windcode'].values
                        AB_A_all_price = AB_A_data['close'].values
                        wind_AB_B_code = AB_B_data['windcode'].values
                        AB_B_all_price = AB_B_data['close'].values

                        wind_AH_A_code = np.append(AH_A_data1['windcode'].values, AH_A_data2['windcode'].values)
                        AH_A_all_price = np.append(AH_A_data1['close'].values, AH_A_data2['close'].values)
                        wind_AH_H_code = np.append(AH_H_data1['windcode'].values, AH_H_data2['windcode'].values)
                        AH_H_all_price = np.append(AH_H_data1['close'].values, AH_H_data2['close'].values)

                        # 记录返回每个ABH股的价格到字典
                        for i in range(int(len(AB_A_all_price) / 2)):
                            AB_A2P[wind_AB_A_code[2 * i + 1]] = AB_A_all_price[2 * i + 1]

                        for i in range(int(len(AB_B_all_price) / 2)):
                            AB_B2P[wind_AB_B_code[2 * i + 1]] = AB_B_all_price[2 * i + 1]

                        for i in range(int(len(AH_A_all_price) / 2)):
                            AH_A2P[wind_AH_A_code[2 * i + 1]] = AH_A_all_price[2 * i + 1]

                        for i in range(int(len(AH_H_all_price) / 2)):
                            AH_H2P[wind_AH_H_code[2 * i + 1]] = AH_H_all_price[2 * i + 1]

                        # 对AB股每只股票迭代判断
                        for i in range(len(AB_A_code)):
                            AB_A_now_price = AB_A2P[AB_A_code[i]]
                            AB_B_now_price = AB_B2P[AB_B_code[i]]
                            AB_A_item_yes_price = AB_A_all_yes_price[i][0]

                            # 判断是否为nan
                            if AB_A_now_price != AB_A_now_price:
                                continue
                            
                            # 判断是否返回了数据
                            if AB_A2P[AB_A_code[i]] == -1:
                                #print(AB_stockname[i] + ' ' + AB_A_code[i] + '没有A股数据')
                                continue

                            # 判断是否之前已经在涨停列表
                            if AB_A_code[i] in AB_zhangting_stock:
                                # 在涨停列表的话，就判断是否还是涨停状态
                                if AB_A_now_price >= 1.099 * AB_A_item_yes_price:
                                    continue
                                else:
                                    AB_zhangting_stock.remove(AB_A_code[i])
                            else:
                                # 不在涨停列表的，若符合涨停条件，则将股票代码记录
                                if AB_A_now_price >= 1.099 * AB_A_item_yes_price:
                                    AB_zt_choose_stock.append(AB_A_code[i])
                                    AB_zhangting_stock.append(AB_A_code[i])

                            if AB_B_now_price != AB_B_now_price:
                                continue

                            if AB_B2P[AB_B_code[i]] == -1:
                                #print(AB_stockname[i] + ' ' + AB_B_code[i] + '没有B股数据')
                                continue

                            # 计算A和B分别与比较工作日前的价格的百分比变化
                            AB_A_zf_percent = (AB_A_now_price / AB_A_last_zf_price[i][0]) - 1
                            AB_B_zf_percent = (AB_B_now_price / AB_B_last_zf_price[i][0]) - 1

                            # 判断A股是否涨幅比B股大于设定差值以上
                            if AB_A_code[i] in AB_zhangfu_stock:
                                if abs(AB_A_zf_percent -AB_B_zf_percent) > difference_value/100 \
                                        and AB_A_zf_percent > 0 and AB_B_zf_percent > 0:
                                    continue
                                else:
                                    AB_zhangfu_stock.remove(AB_A_code[i])
                            else:
                                if abs(AB_A_zf_percent -AB_B_zf_percent) > difference_value/100 \
                                        and AB_A_zf_percent > 0 and AB_B_zf_percent > 0:
                                    AB_zf_choose_stock.append(AB_A_code[i])
                                    AB_zhangfu_stock.append(AB_A_code[i])
                                    AB_zhangfu_value.append(str(abs(AB_A_zf_percent-AB_B_zf_percent)*100)[:5] + '%')
                                    # 打印各股票信息
                                    '''
                                    print(
                                        str(i + 1) + '  ' + AB_stockname[i] + '  ' + AB_A_code[i] + '  ' + str(
                                           AB_A_now_price) + '   '
                                        + str(AB_A_last_zf_price[i][0]) + '   ' +
                                        '  ' + AB_B_code[i] + '  ' + str(AB_B_now_price) + '   '
                                        + str(AB_B_last_zf_price[i][0]))
                                    '''
                        
                        # 对AH股每只股票迭代判断
                        for i in range(len(AH_A_code)):
                            AH_A_now_price = AH_A2P[AH_A_code[i]]
                            AH_H_now_price = AH_H2P[AH_H_code[i]]
                            AH_A_item_yes_price = AH_A_all_yes_price[i][0]

                            # 判断是否为nan
                            if AH_A_now_price != AH_A_now_price:
                                continue
                            
                            # 判断是否返回了数据
                            if AH_A2P[AH_A_code[i]] == -1:
                                continue

                            # 判断是否之前已经在涨停列表
                            if AH_A_code[i] in AH_zhangting_stock:
                                # 在涨停列表的话，就判断是否还是涨停状态
                                if AH_A_now_price >= 1.099 * AH_A_item_yes_price:
                                    continue
                                else:
                                    AH_zhangting_stock.remove(AH_A_code[i])
                            else:
                                # 不在涨停列表的，若符合涨停条件，则将股票代码记录
                                if AH_A_now_price >= 1.099 * AH_A_item_yes_price:
                                    AH_zt_choose_stock.append(AH_A_code[i])
                                    AH_zhangting_stock.append(AH_A_code[i])

                            if AH_H_now_price != AH_H_now_price:
                                continue

                            if AH_H2P[AH_H_code[i]] == -1:
                                continue

                            # 计算A和H分别与比较工作日前的价格的百分比变化
                            AH_A_zf_percent = (AH_A_now_price / AH_A_last_zf_price[i][0]) - 1
                            AH_H_zf_percent = (AH_H_now_price / AH_H_last_zf_price[i][0]) - 1

                            # 判断A股是否涨幅比H股大于设定差值以上
                            if AH_A_code[i] in AH_zhangfu_stock:
                                if abs(AH_A_zf_percent -AH_H_zf_percent) > difference_value/100 \
                                        and AH_A_zf_percent > 0 and AH_H_zf_percent > 0:
                                    continue
                                else:
                                    AH_zhangfu_stock.remove(AH_A_code[i])
                            else:
                                if abs(AH_A_zf_percent -AH_H_zf_percent) > difference_value/100 \
                                        and AH_A_zf_percent > 0 and AH_H_zf_percent > 0:
                                    AH_zf_choose_stock.append(AH_A_code[i])
                                    AH_zhangfu_stock.append(AH_A_code[i])
                                    AH_zhangfu_value.append(str(abs(AH_A_zf_percent-AH_H_zf_percent)*100)[:5] + '%')

                        # 判断AB是否有停涨的股票
                        if len(AB_zt_choose_stock) != 0:
                            msg = todaystr + ' AB股中A股停涨选中的股票有:\n'
                            for i in range(len(AB_zt_choose_stock)):
                                itemstr = AB_A2N[AB_zt_choose_stock[i]] + '  A股代码: ' + AB_zt_choose_stock[i] \
                                          + '  B股代码: ' + AB_A2B[AB_zt_choose_stock[i]] + '\n'
                                msg = msg + itemstr
                            print(msg)

                            # 告警
                            info(title='AB股中A股停涨告警', msg=msg)

                            with open('log/' + today.strftime("%Y-%m-%d") + " AB股A股停涨.txt", "a") as f:
                                f.write(msg + '\n')
                        else:
                            print(todaystr + ' AB股A股停涨没有选中股票')

                        # 判断AB是否有涨幅超设定阈值的股票
                        if len(AB_zf_choose_stock) != 0:
                            msg = todaystr + ' AB股涨幅差值大于' + str(difference_value) +'%选中的股票有(' + str(compare_day) + '天前):\n'
                            for i in range(len(AB_zf_choose_stock)):
                                itemstr = AB_A2N[AB_zf_choose_stock[i]] + '  A股代码: ' + AB_zf_choose_stock[i] \
                                          + '  B股代码: ' + AB_A2B[AB_zf_choose_stock[i]] + ' 涨幅差值: ' + AB_zhangfu_value[i] + '\n'
                                msg = msg + itemstr
                            print(msg)

                            # 告警
                            info(title='A股比B股涨幅差值大于' + str(difference_value) + '%告警', msg=msg)

                            with open('log/' + today.strftime("%Y-%m-%d") + " AB股涨幅.txt", "a") as f:
                                f.write(msg + '\n')
                        else:
                            print(todaystr + ' AB股涨幅差值大于' + str(difference_value) + '%没有选中股票(' + str(compare_day) + '天前)')

                        # 判断AH是否有停涨的股票
                        if len(AH_zt_choose_stock) != 0:
                            msg = todaystr + ' AH股中A股停涨选中的股票有:\n'
                            for i in range(len(AH_zt_choose_stock)):
                                itemstr = AH_A2N[AH_zt_choose_stock[i]] + '  A股代码: ' + AH_zt_choose_stock[i] \
                                          + '  H股代码: ' + AH_A2H[AH_zt_choose_stock[i]] + '\n'
                                msg = msg + itemstr
                            print(msg)

                            # 告警
                            info(title='AH股中A股停涨告警', msg=msg)

                            with open('log/' + today.strftime("%Y-%m-%d") + " AH股A股停涨.txt", "a") as f:
                                f.write(msg + '\n')
                        else:
                            print(todaystr + ' AH股A股停涨没有选中股票')

                        # 判断AH是否有涨幅超设定阈值的股票
                        if len(AH_zf_choose_stock) != 0:
                            msg = todaystr + ' AH股涨幅差值大于' + str(difference_value) + '%选中的股票有(' + str(
                                compare_day) + '天前):\n'
                            for i in range(len(AH_zf_choose_stock)):
                                itemstr = AH_A2N[AH_zf_choose_stock[i]] + '  A股代码: ' + AH_zf_choose_stock[i] \
                                          + '  H股代码: ' + AH_A2H[AH_zf_choose_stock[i]] + ' 涨幅差值: ' + \
                                          AH_zhangfu_value[i] + '\n'
                                msg = msg + itemstr
                            print(msg)

                            # 告警
                            info(title='A股比H股涨幅差值大于' + str(difference_value) + '%告警', msg=msg)

                            with open('log/' + today.strftime("%Y-%m-%d") + " AH股涨幅.txt", "a") as f:
                                f.write(msg + '\n')
                        else:
                            print(todaystr + ' AH股涨幅差值大于' + str(difference_value) + '%没有选中股票(' + str(
                                compare_day) + '天前)')
                else:
                    if marketopen_tip:
                        print('---------------------------------------------------------')
                        print('现在是' + todaystr)
                        print('不在开市时间之中 9:30-11:30或13:00-15:00')
                        AB_zhangting_stock = []
                        AB_zhangfu_stock = []
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




