# wind
wind系统python api应用，使用时要保证wind金融终端开启，并修复python接口  
主要实现两个功能：   
1. 均线方差变动选股功能
2. AB股告警系统
3. 基差告警系统
4. 放量监控系统

### 均线方差变动选股
该功能主要实现利用多条均线的方差体现股票（期货）某段时间的波动率还进行选股（期货），对最新交易日的方差小于历史记录方差的5%（可自行设置）的股票（期货）进行选择并记录。
* 股票：使用了MA5, MA10, MA20, MA60, MA250 均线
* 期货：使用了MA5, MA10, MA21, MA55, MA250 均线

### ABH股告警系统
该功能主要针对AB股和AH股，主要是实现了实时告警的功能，告警通过系统弹窗和提示音的方式实现。

告警逻辑有两个：  
1. A股涨停
2. A股在某段时间的涨幅大于B（H）股涨幅的30%（可设定）

### 基差告警系统
该功能主要是针对商品期货，对于各类商品，在相邻月份对比他们的价格差，如果价格差在5%（可设定）以上，那就告警

### 放量监控系统
该功能主要是针对A股和H股的股票，根据条件实施实时告警的功能

告警的逻辑有三个：
1. 涨跌幅大于1.5%
2. 放量大于70%， 放量=当天成交额/区间日均成交额（一个月）-1
3. 趋势为上升，判断趋势的条件是，当MA5>MA10, MA10>MA2O, MA20>MA60时为上升趋势

### 打包注意事项
当使用python的pyinstaller对使用了windpy包进行打包时，常常会出现错误，是因为windpy的包不是放在python下，而是在wind金融终端的安装目录下，首先要在安装目录找到x64文件夹下的windpy.py文件，修改里面读取windpy.dll的路径（建议改成相对路径，这样就可以直接把windpy.dll放到与打包文件同目录下就可以运行），而windpy.dll会根据安装目录的位置不同而不同，所以不同电脑使用需要将自己电脑的windpy.dll复制过去。
