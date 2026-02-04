import tushare as ts
pro = ts.pro_api( token = '不用管这里') # 不用管，不留空即可
# ⬇️⬇️找到 pro_api 所在行
pro._DataApi__token 	= '5049652140394706635'
pro._DataApi__http_url 	= 'http://stk_mins.xiximiao.com/dataapi'
# ⬆️⬆️添加两行代码⬆️⬆️

#【❗💡💡 同理，在你已有代码中，搜索 pro_api 所在行，随后在pro_api添加以上两行】

#获取浦发银行60000.SH的历史分钟数据
df = pro.stk_mins(ts_code='600000.SH', freq='1min', start_date='2018-01-01 09:00:00', end_date='2026-02-02 19:00:00')
print(df)
#获取沪深300ETF华夏510330.SH的历史分钟数据
# df2 = pro.stk_mins(ts_code='510330.SH', freq='1min', start_date='2025-06-20 09:00:00', end_date='2025-06-20 19:00:00')
# print(df2)

# 分钟权限包括的三个集合竞价接口名
# stk_auction  /  stk_auction_o  /  stk_auction_c
#获取2025年2月18日开盘集合竞价成交情况
#df = pro.stk_auction(trade_date='20250218',fields='ts_code, trade_date,vol,price,amount,turnover_rate,volume_ratio')

# 
#dfdaily = pro.daily(ts_code='000001.SZ', start_date='20180701', end_date='20180718')
#print(dfdaily)