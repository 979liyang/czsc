# -*- coding: utf-8 -*-
"""
author: zengbin93
email: zeng_bin8888@163.com
create_dt: 2023/3/26 21:21
describe: 
"""
import os

os.environ['czsc_verbose'] = '1'

import pandas as pd
import tushare as ts
from tqdm import tqdm
from loguru import logger
from czsc.data import TsDataCache

pd.set_option('expand_frame_repr', False)
pd.set_option('display.max_rows', 200)
pd.set_option('display.max_columns', 100)
pd.set_option('display.width', 1000)

dc = TsDataCache(r'C:\ts_data', sdt='20100101', edt='20230101')
pro = ts.pro_api()


def prepare_index_kline():
    index = pd.concat([pro.index_basic(market='SSE'), pro.index_basic(market='SZSE'), pro.index_basic(market='CICC')])
    # 保留综合指数和一级行业指数
    index = index[index['category'].isin(['综合指数', '一级行业指数', '规模指数'])]
    res_path = r"D:\CZSC投研数据\A股主要指数"
    index.to_excel(os.path.join(res_path, 'index.xlsx'), index=False)

    index_list = index.ts_code.tolist()
    symbols = []
    for index_ in tqdm(index_list, desc='下载指数数据'):
        if os.path.exists(os.path.join(res_path, f'{index_}.parquet')):
            symbols.append(index_)
            logger.info(f"{index_} 已经保存，跳过")
            continue

        try:
            # 读取最近10天的数据，如果没有数据，则不保存
            t1 = ts.pro_bar(ts_code=index_, asset='I', freq='1min', start_date='20221218', end_date='20230101')
            if len(t1) == 0:
                logger.info(f"{index_} 没有数据，不保存")
                continue
            else:
                logger.info(f"{index_} 有数据，数量：{len(t1)}")

            kline = dc.pro_bar_minutes(ts_code=index_, asset='I', freq='1min',
                                       sdt='20100101', edt='20230101', adj='hfq', raw_bar=True)
            df = pd.DataFrame(kline)
            if len(df) > 60000:
                symbols.append(index_)
                df.drop(['freq', 'cache', 'id'], axis=1, inplace=True)
                df.to_parquet(os.path.join(res_path, f'{index_}.parquet'))
        except Exception as e:
            print(e)

    # 保留有数据的指数
    index = index[index['ts_code'].isin(symbols)]
    index.to_excel(os.path.join(res_path, 'index.xlsx'), index=False)


def prepare_etf_kline():
    etfs = pro.fund_basic(market='E')
    # 只保留已发行的ETF
    etfs = etfs[etfs['status'] == 'L']
    # 去掉2018年之后上市的ETF
    etfs = etfs[etfs['list_date'] < '2018-01-01']
    # 去掉货币基金和LOF
    etfs = etfs[~etfs['name'].str.contains('货币|LOF')]
    # 只保留股票型ETF
    etfs = etfs[etfs['fund_type'].str.contains('股票型')]
    res_path = r"D:\CZSC投研数据\A股场内基金"
    etfs.to_excel(os.path.join(res_path, 'etfs.xlsx'), index=False)

    etf_list = etfs.ts_code.tolist()
    symbols = []
    for etf in tqdm(etf_list, desc='prepare etf kline'):
        if os.path.exists(os.path.join(res_path, f'{etf}.parquet')):
            symbols.append(etf)
            logger.info(f"{etf} 已经保存，跳过")
            continue

        try:
            # 读取最近10天的数据，如果没有数据，则不保存
            t1 = ts.pro_bar(ts_code=etf, asset='FD', freq='1min', start_date='20221218', end_date='20230101')
            if len(t1) == 0:
                logger.info(f"{etf} 没有数据，不保存")
                continue
            else:
                logger.info(f"{etf} 有数据，数量：{len(t1)}")

            kline = dc.pro_bar_minutes(ts_code=etf, asset='FD', freq='1min',
                                       sdt='20100101', edt='20230101', adj='hfq', raw_bar=True)
            df = pd.DataFrame(kline)
            if len(df) > 60000:
                symbols.append(etf)
                df.drop(['freq', 'cache', 'id'], axis=1, inplace=True)
                df.to_parquet(os.path.join(res_path, f'{etf}.parquet'))
        except Exception as e:
            print(e)

    # 保留有数据的ETF
    etfs = etfs[etfs['ts_code'].isin(symbols)]
    etfs.to_excel(os.path.join(res_path, 'etfs.xlsx'), index=False)


def prepare_index_members():
    dfw = dc.index_weight(index_code='000905.SH', trade_date='20210101')
    res_path = r"D:\CZSC投研数据\中证500成分股"
    dfw.to_excel(os.path.join(res_path, '中证500成分股20210101.xlsx'), index=False)

    symbols = dfw.con_code.tolist()
    for etf in tqdm(symbols, desc='prepare_index_members'):
        if os.path.exists(os.path.join(res_path, f'{etf}.parquet')):
            logger.info(f"{etf} 已经保存，跳过")
            continue

        try:
            kline = dc.pro_bar_minutes(ts_code=etf, asset='E', freq='1min',
                                       sdt='20100101', edt='20230101', adj='hfq', raw_bar=True)
            df = pd.DataFrame(kline)
            df.drop(['freq', 'cache', 'id'], axis=1, inplace=True)
            df.to_parquet(os.path.join(res_path, f'{etf}.parquet'))
        except Exception as e:
            print(e)


if __name__ == '__main__':
    # prepare_index_kline()
    # prepare_etf_kline()
    prepare_index_members()
