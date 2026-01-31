# -*- coding: utf-8 -*-
"""
author: zengbin93
email: zeng_bin8888@163.com
create_dt: 2023/3/25 21:04
describe:
"""
import os
from loguru import logger
from ctalib.data import dr, get_symbols


symbols = get_symbols('future')

res_path = r"D:\期货主力1分钟后复权K线"
os.makedirs(res_path, exist_ok=True)
for symbol in symbols:
    try:
        df = dr.get_da(symbol, start_date='20100101', end_date='20230901', freq='1m', ed_type='post')
        cols = ['open', 'close', 'high', 'low', 'vol', 'amount', 'factor', 'symbol', 'contract', 'datetime']
        df = df[cols].copy().reset_index(drop=True)
        df.to_parquet(os.path.join(res_path, f"{symbol}.parquet"), index=False)
    except:
        logger.exception(f"Error: {symbol}")


