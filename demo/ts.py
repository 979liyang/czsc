import tushare as ts
import pandas as pd
import os
import json
from datetime import datetime, timedelta
import time

# 配置文件路径
CONFIG_FILE = 'tushare_config.json'

def load_or_set_token():
    """加载或设置Tushare Token"""
    # 尝试从配置文件加载Token
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                token = config.get('token', '')
                if token:
                    print(f"从配置文件加载Tushare Token: {token[:4]}****{token[-4:]}")
                    return token
        except:
            print("配置文件格式错误，将重新设置Token")
    
    # 如果未找到有效Token，提示用户输入
    print("="*50)
    print("未找到有效的Tushare Token")
    print("请访问 https://tushare.pro 注册并获取API Token")
    print("（注册后可在个人中心查看Token）")
    print("="*50)
    
    while True:
        token = input("请输入您的Tushare Token: ").strip()
        if len(token) != 32 or not token.isalnum():
            print("无效的Token格式！Token应为32位字母数字组合")
            print("请重新输入（或按Ctrl+C退出）")
        else:
            # 保存Token到配置文件
            with open(CONFIG_FILE, 'w') as f:
                json.dump({'token': token}, f)
            print(f"Token已保存到配置文件: {CONFIG_FILE}")
            return token

def get_stock_data(stock_codes, start_date=None, end_date=None, save_dir='stock_data'):
    """
    获取多个股票的历史数据并保存为Parquet文件
    
    参数:
    stock_codes -- 股票代码列表，例如 ['000001.SZ', '600000.SH']
    start_date -- 开始日期，格式 'YYYYMMDD'，默认3个月前
    end_date -- 结束日期，格式 'YYYYMMDD'，默认今天
    save_dir -- 保存文件的目录
    """
    # 加载或设置Token
    token = load_or_set_token()
    ts.set_token(token)
    pro = ts.pro_api()
    
    # 设置日期范围
    end_date = end_date or datetime.now().strftime('%Y%m%d')
    start_date = start_date or (datetime.now() - timedelta(days=90)).strftime('%Y%m%d')
    
    # 创建保存目录
    os.makedirs(save_dir, exist_ok=True)
    
    # 计数器
    success_count = 0
    fail_list = []
    
    print(f"\n准备获取 {len(stock_codes)} 只股票的日线数据 ({start_date} 至 {end_date})...")
    
    # 测试Token有效性
    print("\n测试Token有效性...")
    try:
        test_data = pro.query('trade_cal', exchange='', start_date=start_date, end_date=end_date)
        if test_data.empty:
            print("警告: Token可能无效，获取测试数据失败")
        else:
            print(f"Token验证通过! 获取到 {len(test_data)} 条交易日历")
    except Exception as e:
        print(f"Token测试失败: {str(e)}")
        print("可能原因: Token无效、网络问题或API限制")
        retry = input("是否继续尝试获取股票数据? (y/n): ").lower()
        if retry != 'y':
            print("程序终止")
            return
    
    for i, ts_code in enumerate(stock_codes, 1):
        try:
            print(f"\n[{i}/{len(stock_codes)}] 获取 {ts_code} 数据...")
            
            # 获取股票日线数据
            df = pro.daily(
                ts_code=ts_code,
                start_date=start_date,
                end_date=end_date
            )
            
            if df.empty:
                print(f"  警告: 未获取到 {ts_code} 的数据")
                fail_list.append(ts_code)
                continue
            
            # 数据处理
            df = df.sort_values('trade_date')
            df['trade_date'] = pd.to_datetime(df['trade_date'], format='%Y%m%d')
            
            # 保存为Parquet
            file_name = f"{ts_code.replace('.', '_')}.parquet"
            file_path = os.path.join(save_dir, file_name)
            df.to_parquet(file_path, index=False)
            
            print(f"  成功保存: {file_path}")
            print(f"  数据量: {len(df)} 条, 日期范围: {df['trade_date'].min().date()} 至 {df['trade_date'].max().date()}")
            success_count += 1
            
            # 遵守API调用频率限制
            if i < len(stock_codes) and i % 5 == 0:
                print("  暂停12秒以遵守API调用限制...")
                time.sleep(12)
        
        except Exception as e:
            print(f"  获取 {ts_code} 数据时出错: {str(e)}")
            fail_list.append(ts_code)
            # 如果是Token错误，删除无效Token
            if "token无效" in str(e) or "未注册" in str(e):
                print("检测到Token无效，删除配置文件")
                if os.path.exists(CONFIG_FILE):
                    os.remove(CONFIG_FILE)
    
    # 打印总结报告
    print("\n" + "="*50)
    print(f"数据获取完成!")
    print(f"成功获取: {success_count} 只股票")
    if fail_list:
        print(f"失败股票: {len(fail_list)} 只")
        print("失败列表:", ", ".join(fail_list))
    print(f"文件保存至目录: {os.path.abspath(save_dir)}")
    print("="*50)

def update_token():
    """更新Token"""
    if os.path.exists(CONFIG_FILE):
        os.remove(CONFIG_FILE)
        print("已删除旧Token配置文件")
    print("请设置新的Tushare Token")
    load_or_set_token()

def main_menu():
    """显示主菜单"""
    while True:
        print("\n" + "="*50)
        print("Tushare 股票数据下载器")
        print("="*50)
        print("1. 下载股票数据")
        print("2. 更新Tushare Token")
        print("3. 退出程序")
        print("="*50)
        
        choice = input("请选择操作 (1-3): ").strip()
        
        if choice == '1':
            # 获取股票列表
            stock_input = input("\n请输入股票代码列表(用逗号分隔，例如: 000001.SZ,600000.SH): ").strip()
            stock_list = [code.strip() for code in stock_input.split(',') if code.strip()]
            
            # 验证股票代码格式
            valid_codes = []
            invalid_codes = []
            
            for code in stock_list:
                if '.' in code and len(code.split('.')[0]) == 6 and code.split('.')[1] in ['SH', 'SZ']:
                    valid_codes.append(code)
                else:
                    invalid_codes.append(code)
            
            if invalid_codes:
                print(f"\n以下股票代码格式无效: {', '.join(invalid_codes)}")
                print("正确格式应为: 6位数字 + '.' + 交易所代码(SH/SZ)，例如: 000001.SZ")
            
            if valid_codes:
                # 时间范围选择
                print("\n请选择时间范围:")
                print("1. 最近3个月 (默认)")
                print("2. 自定义时间范围")
                time_choice = input("请选择 (1-2): ").strip() or '1'
                
                start_date = None
                end_date = None
                
                if time_choice == '2':
                    start_date = input("请输入开始日期 (YYYYMMDD): ").strip()
                    end_date = input("请输入结束日期 (YYYYMMDD): ").strip()
                    print(f"自定义时间范围: {start_date} 至 {end_date}")
                
                # 执行下载
                get_stock_data(valid_codes, start_date, end_date)
            else:
                print("没有有效的股票代码可下载")
        
        elif choice == '2':
            update_token()
        
        elif choice == '3':
            print("程序退出")
            break
        
        else:
            print("无效选择，请重新输入")

if __name__ == "__main__":
    # 创建示例配置文件（如果不存在）
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'w') as f:
            json.dump({'token': 'your_default_token_here'}, f)
    
    # 运行主菜单
    main_menu()