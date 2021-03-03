import winsound
import WindPy
import numpy as np
import datetime
import time
import threading
import ctypes
import warnings


def info(title='提示', msg='内容'):
    duration = 2000  # millisecond
    freq = 440  # Hz
    winsound.Beep(freq, duration)
    msgshow(title, msg)


def msgshow(title='标题', msg='内容'):
    def worker(title, close_until_seconds):
        time.sleep(close_until_seconds)
        wd = ctypes.windll.user32.FindWindowA(0, title)
        ctypes.windll.user32.SendMessageA(wd, 0x0010, 0, 0)
        return

    def AutoCloseMessageBoxW(text, title, close_until_seconds):
        t = threading.Thread(target=worker, args=(title, close_until_seconds))
        t.start()
        ctypes.windll.user32.MessageBoxA(0, text, title, 0)

    AutoCloseMessageBoxW(msg.encode('gbk'), title.encode('gbk'), 6)


def list2dic(key, value):
    dic = {}
    for i in range(len(key)):
        dic[key[i]] = value[i]
    return dic


def runTask(day=0, hour=0, min=1, second=0):
    # 链接wind
    WindPy.w.start()
    WindPy.w.isconnected()

    # 加载股票数据信息
    A = np.load('stock_info.npz')
    stock_name = list(A['stock_name'])
    code_A = list(A['code_A'])
    code_B = list(A['code_B'])

    # 创建股票A和B转换字典
    A2B = list2dic(code_A, code_B)
    B2A = list2dic(code_B, code_A)

    # 创建股票AB和名字转换字典
    A2N = list2dic(code_A, stock_name)
    B2N = list2dic(code_B, stock_name)

    # 记录一天停涨的股票
    zhangting_stock = []
    AcB = []

    # 获得开始运行的系统时间
    now = datetime.datetime.now()
    format_pattern = '%Y-%m-%d %H:%M:%S'

    # 计算下一次运行时间
    period = datetime.timedelta(days=day, hours=hour, minutes=min, seconds=second)
    next_time = now + period
    strnext_time = next_time.strftime('%Y-%m-%d %H:%M:%S')
    market_open = True

    # 循环运行
    while True:
        # 获得当前的系统时间
        iter_now = datetime.datetime.now()
        iter_now_time = iter_now.strftime('%Y-%m-%d %H:%M:%S')

        # 用于判断是否已经越过了下一时间，若越过就要立刻执行工作
        cmp = (datetime.datetime.strptime(strnext_time, format_pattern) - datetime.datetime.strptime(iter_now_time,
                                                                                                     format_pattern))
        # 判断当前时间是否符合下一运行时间
        if str(iter_now_time) == str(strnext_time) or cmp.days < 0:
            # 开始运行程序工作内容
            # 开始计时
            time_start = time.time()
            # 存储选中的股票
            choose_stock = []
            AcB_stock = []

            # 创建存储A和B股最新价格的字典，初始化所有价格为-1，用于后面判断是否有股票没有价格
            neglist = [-1] * len(code_A)
            A2P = list2dic(code_A, neglist)
            B2P = list2dic(code_B, neglist)

            # 获取前十天的日期，找出上一个交易日
            today = datetime.datetime.today()
            todaystr = today.strftime("%Y-%m-%d %H:%M:%S")
            last_d = WindPy.w.tdaysoffset(-10, today.isoformat(), "Period=D;Days=Alldays")
            last_10_date = last_d.Times[0].strftime("%Y%m%d")
            last_trade_date = WindPy.w.tdays(last_10_date).Times[-2].strftime("%Y%m%d")

            # 获取前三十天的日期
            last_d30 = WindPy.w.tdaysoffset(-22, today.isoformat(), "Period=D;Days=Alldays")
            last_30_date = last_d30.Times[0].strftime("%Y%m%d")
            last_30_trade_date = WindPy.w.tdays(last_30_date).Times[0].strftime("%Y%m%d")

            # 计算出今天是星期几，是否为交易日
            weekday = today.weekday()
            # 判断是否为周六日的休市时间
            if weekday == 5 or weekday == 6:
                if market_open:
                    print('---------------------------------------------------------')
                    print('现在是' + todaystr)
                    print('周六日不在开市时间之中')
                    zhangting_stock = []
                    AcB = []
                    market_open = False
            else:
                # 获取上一分钟的时间
                last_min_date = today + datetime.timedelta(minutes=-1)
                #last_min_date = datetime.datetime(2021, 2, 25, 14, 59)
                hour = today.strftime("%Y-%m-%d %H:%M:%S")[11:13]
                minute = today.strftime("%Y-%m-%d %H:%M:%S")[14:16]
                total_minutes = int(hour) * 60 + int(minute)

                # 判断是否在工作日开市时间之中9:30-11:30 或 13:00-15:00
                if (total_minutes > 570 and total_minutes < 690) or (total_minutes > 780 and total_minutes < 900):
                #if True:
                    print('---------------------------------------------------------')
                    print('现在是' + todaystr)
                    print('在开市时间之中')

                    market_open = True

                    # 获取全部股票A和B市现在的分钟数据
                    error, data_A = WindPy.w.wsi(code_A, 'close', last_min_date, today, "Fill=Previous", usedf=True)
                    error, data_B = WindPy.w.wsi(code_B, 'close', last_min_date, today, "Fill=Previous", usedf=True)
                    #print('最新价格A股的数量为' + str(int(data_A.shape[0] / 2)))
                    #print('最新价格B股的数量为' + str(int(data_B.shape[0] / 2)))

                    # 获取A股票前一天的收盘价
                    last_cprice = WindPy.w.wsd(codes=code_A, fields="close", beginTime=last_trade_date,
                                        endTime=last_trade_date, options="returnType=1;PriceAdj=F", usedf=True)[
                        1].values

                    # 获取A和B股30个开市日前的收盘价
                    last_30_price_A = WindPy.w.wsd(codes=code_A, fields="close", beginTime=last_30_trade_date,
                                            endTime=last_30_trade_date, options="returnType=1;PriceAdj=F", usedf=True)[
                        1].values
                    # 获取30个开市日前的收盘价
                    last_30_price_B = WindPy.w.wsd(codes=code_B, fields="close", beginTime=last_30_trade_date,
                                            endTime=last_30_trade_date, options="returnType=1;PriceAdj=F", usedf=True)[
                        1].values

                    if len(last_30_price_A) != 82 or len(last_30_price_B) != 82:
                        print('30个工作日前返回的A和B股数量不同')
                        return
                    #print(data_A)
                    #print(data_B)
                    # 通过返回的df的列是否有close这一属性判断是否返回正常
                    if 'close' not in data_A.columns.values:
                        print('A股返回数据错误')
                        zhangting_stock = []
                        AcB = []
                    elif 'close' not in data_B.columns.values:
                        print('B股返回数据错误')
                        zhangting_stock = []
                        AcB = []
                    # 返回正常时
                    else:
                        wind_code_A = data_A['windcode'].values
                        all_price_A = data_A['close'].values
                        wind_code_B = data_B['windcode'].values
                        all_price_B = data_B['close'].values

                        # 记录返回每个A股的价格到字典
                        for i in range(int(len(all_price_A) / 2)):
                            A2P[wind_code_A[2 * i + 1]] = all_price_A[2 * i + 1]

                        # 记录返回每个B股的价格到字典
                        for i in range(int(len(all_price_B) / 2)):
                            B2P[wind_code_B[2 * i + 1]] = all_price_B[2 * i + 1]

                        for i in range(len(code_A)):
                            now_price_A = A2P[code_A[i]]
                            now_price_B = B2P[code_B[i]]
                            item_price = last_cprice[i][0]

                            # 打印各股票信息
                            #print(
                            #    str(i + 1) + '  ' + stock_name[i] + '  ' + code_A[i] + '  ' + str(now_price_A) + '   ' +
                            #    str(item_price) + '  ' + code_B[i] + '  ' + str(now_price_B))

                            if now_price_A != now_price_A:
                                continue

                            if A2P[code_A[i]] == -1:
                                #print(stock_name[i] + ' ' + code_A[i] + '没有A股数据')
                                continue

                                # 判断是否之前已经在涨停列表
                            if code_A[i] in zhangting_stock:
                                # 在涨停列表的话，就判断是否还是涨停状态
                                if now_price_A >= 1.099 * item_price:
                                    continue
                                else:
                                    zhangting_stock.remove(code_A[i])
                            else:
                                # 不在涨停列表的，若符合涨停条件，则将股票代码记录
                                if now_price_A >= 1.099 * item_price:
                                    choose_stock.append(code_A[i])
                                    zhangting_stock.append(code_A[i])

                            if now_price_B != now_price_B:
                                continue

                            if B2P[code_B[i]] == -1:
                                #print(stock_name[i] + ' ' + code_B[i] + '没有B股数据')
                                continue

                            # 计算A和B分别与三十个工作日前的价格的百分比变化
                            percentA = (now_price_A / last_30_price_A[i][0]) - 1
                            percentB = (now_price_B / last_30_price_B[i][0]) - 1

                            # 判断A股是否涨幅比B股大30%以上
                            if code_A[i] in AcB:
                                if percentA >= 1.30 * percentB:
                                    continue
                                else:
                                    AcB.remove(code_A[i])
                            else:
                                if percentA >= 1.30 * percentB:
                                    # print(stock_name[i] + ' ' + str(percentA) + ' ' + str(percentB))
                                    AcB_stock.append(code_A[i])
                                    AcB.append(code_A[i])

                        # 判断是否有停涨的股票
                        if len(choose_stock) != 0:
                            msg = todaystr + ' 停涨选中的股票有:\n'
                            for i in range(len(choose_stock)):
                                itemstr = A2N[choose_stock[i]] + '  A股代码: ' + choose_stock[i] \
                                          + '  B股代码: ' + A2B[choose_stock[i]] + '\n'
                                msg = msg + itemstr
                            print(msg)

                            # 告警
                            info(title='A股停涨告警', msg=msg)

                            with open('log/' + today.strftime("%Y-%m-%d") + " 停涨.txt", "a") as f:
                                f.write(msg + '\n')
                        else:
                            print(todaystr + ' 停涨没有选中股票')

                        # 判断是否有涨幅超30%的股票
                        if len(AcB_stock) != 0:
                            msg = todaystr + ' 涨幅大于30%选中的股票有:\n'
                            for i in range(len(AcB_stock)):
                                itemstr = A2N[AcB_stock[i]] + '  A股代码: ' + AcB_stock[i] \
                                          + '  B股代码: ' + A2B[AcB_stock[i]] + '\n'
                                msg = msg + itemstr
                            print(msg)

                            # 告警
                            info(title='A股比B股涨幅大于30%告警', msg=msg)

                            with open('log/' + today.strftime("%Y-%m-%d") + " 涨幅30%.txt", "a") as f:
                                f.write(msg + '\n')
                        else:
                            print(todaystr + ' 涨幅大于30%没有选中股票')
                else:
                    if market_open:
                        print('---------------------------------------------------------')
                        print('现在是' + todaystr)
                        print('不在开市时间之中 9:30-11:30或13:00-15:00')
                        zhangting_stock = []
                        AcB = []
                        market_open = False


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


