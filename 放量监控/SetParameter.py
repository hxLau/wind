import re
import easygui as eg


def is_number(num):
  pattern = re.compile(r'^[-+]?[-0-9]\d*\.\d*|[-+]?\.?[0-9]\d*$')
  result = pattern.match(num)
  if result:
    return True
  else:
    return False


def set_par():
    # 读取参数
    with open('./parameter.txt', "r") as f:
        s = f.read()
        para = s.split()
        H_volume = float(para[0])
        Q_change = float(para[1])

    msg = "请设定参数,现在放量比较值为： " + str(H_volume) + "%" + "，涨跌幅比较值为：" + str(Q_change) + "%"
    title = "设定放量和涨跌幅比较值参数"
    fieldNames = ["放量比较值设定(单位%)（大于0，例如70）:", "涨跌幅比较值设定(单位%)（大于0，例如1.5）:"]
    fieldValues = eg.multenterbox(msg, title, fieldNames)

    while True:
        # 点击取消按钮操作
        if fieldValues == None:
            break
        # 报错提示初始值
        errmsg = ""
        if fieldValues[0].strip() == "" or not is_number(fieldValues[0]):
            errmsg += ('放量比较值设定，只能设置为数字且不能为空\n')
        elif float(fieldValues[0]) <= 0:
            errmsg += ('价差设定，设定要大于0\n')

        if fieldValues[1].strip() == "" or not is_number(fieldValues[1]):
            errmsg += ('涨跌幅比较值设定，只能设置为数字且不能为空\n')
        elif float(fieldValues[1]) <= 0:
            errmsg += ('价差设定，设定要大于0\n')

        # 无报错提示，退出程序，否则，报错提示，重新进入输入界面
        if errmsg == "":
            break
        fieldValues = eg.multenterbox(errmsg, title, fieldNames, fieldValues)

    return float(fieldValues[0]), float(fieldValues[1])


if __name__ == '__main__':
    while True:
        H_volume, Q_change = set_par()
        with open('./parameter.txt', "w") as f:
            f.write(str(H_volume) + ' ' + str(Q_change))


