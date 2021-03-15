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
    with open('./set.txt', "r") as f:
        s = f.read()
        para = s.split()
        chazhi = float(para[0])
        compare_day = int(para[1])

    msg = "请设定参数,现在涨幅差值为： " + str(chazhi) + '%  比较日期为： ' + str(compare_day) + '天'
    title = "设定参数"
    fieldNames = ["涨幅差值设定(单位%)（大于0，例如5）:", "AB涨幅比较多少天前(输入要求整数，如30):"]
    fieldValues = eg.multenterbox(msg, title, fieldNames)

    while True:
        # 点击取消按钮操作
        if fieldValues == None:
            break
        # 报错提示初始值
        errmsg = ""
        if fieldValues[0].strip() == "" or not is_number(fieldValues[0]):
            errmsg += ('涨幅差值设定(单位%)，只能设置为数字且不能为空\n')
        elif float(fieldValues[0]) <= 0:
            errmsg += ('涨幅差值设定，设定要大于0\n')

        if fieldValues[1].strip() == "" or not fieldValues[1].isdigit():
            errmsg += ('比较天数设定，只能设置为整数且不能为空\n')
        elif float(fieldValues[1])<=0:
            errmsg += ('比较天数设定，设定要大于0\n')

        # 无报错提示，退出程序，否则，报错提示，重新进入输入界面
        if errmsg == "":
            break
        fieldValues = eg.multenterbox(errmsg, title, fieldNames, fieldValues)

    return float(fieldValues[0]), int(fieldValues[1])


if __name__ == '__main__':
    while True:
        chazhi, compare_day = set_par()
        with open('./set.txt', "w") as f:
            f.write(str(chazhi) + ' ' + str(compare_day))
