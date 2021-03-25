import winsound
import time
import threading
import ctypes
import re
import easygui as eg


# 告警
def info(title='提示', msg='内容'):
    winsound.PlaySound('tishi.wav', winsound.SND_ALIAS)
    msgshow(title, msg)


# 判断字符串是否为数值
def is_number(num):
  pattern = re.compile(r'^[-+]?[-0-9]\d*\.\d*|[-+]?\.?[0-9]\d*$')
  result = pattern.match(num)
  if result:
    return True
  else:
    return False


# 弹窗告警
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


# 两列表创建字典
def list2dic(key, value):
    dic = {}
    for i in range(len(key)):
        dic[key[i]] = value[i]
    return dic


def set_par():
    msg = "请设定价差参数"
    title = "设定价差参数"
    fieldNames = ["价差设定(单位%)（大于0，例如5）:"]
    fieldValues = eg.multenterbox(msg, title, fieldNames)

    while True:
        # 点击取消按钮操作
        if fieldValues == None:
            break
        # 报错提示初始值
        errmsg = ""
        if fieldValues[0].strip() == "" or not is_number(fieldValues[0]):
            errmsg += ('价差设定(单位%)，只能设置为数字且不能为空\n')
        elif float(fieldValues[0]) <= 0:
            errmsg += ('价差设定，设定要大于0\n')

        # 无报错提示，退出程序，否则，报错提示，重新进入输入界面
        if errmsg == "":
            break
        fieldValues = eg.multenterbox(errmsg, title, fieldNames, fieldValues)

    print("价差设定为: " + str(float(fieldValues[0])) + '%')
    return float(fieldValues[0])


# 期货分类
def classification(code, name):
    prefix = name[0][:2]
    item_code_list = []
    cls_code_list = []
    for i in range(len(code)):
        if name[i][:2] == prefix:
            item_code_list.append(code[i])
        else:
            prefix = name[i][:2]
            cls_code_list.append(item_code_list)
            item_code_list = []
            item_code_list.append(code[i])
    return cls_code_list


