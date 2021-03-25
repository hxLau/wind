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
    with open('./commodity_para.txt', "r") as f:
        s = f.read()
        para = s.split()
        chazhi = float(para[0])

    msg = "请设定参数,现在价差为： " + str(chazhi) + '%'
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


if __name__ == '__main__':
    while True:
        chazhi = set_par()
        with open('./commodity_para.txt', "w") as f:
            f.write(str(chazhi))
