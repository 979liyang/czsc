# 安装运行

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate

# czsc安装
pip install --upgrade pip setuptools wheel
cp setup_fixed.py setup.py && pip install -e .

# rs_czsc 安装

pip install rs_czsc
```

## 安装与配置

### 1. 安装 CZSC

#### 从 GitHub 安装（推荐）
```bash
pip install git+https://github.com/waditu/czsc.git -U
```

#### 从 PyPI 安装
```bash
pip install czsc -U -i https://pypi.python.org/simple
```

#### 从本地源码安装
```bash
git clone https://github.com/waditu/czsc.git
cd czsc
pip install -e .
```

### 2. 安装依赖

主要依赖已包含在 requirements.txt 中，安装时会自动安装。如需手动安装：

```bash
pip install -r requirements.txt
```

### 3. 环境配置

#### 日志配置
CZSC 使用 `loguru` 进行日志记录，默认会输出到控制台。可以通过环境变量配置：

```python
import os
os.environ['CZSC_LOG_LEVEL'] = 'INFO'  # DEBUG, INFO, WARNING, ERROR
```

#### 缓存配置
CZSC 使用本地缓存存储数据，默认路径在用户主目录下的 `.czsc` 文件夹：

```python
from czsc.utils import home_path
print(home_path)  # 查看缓存路径

# 清空缓存
from czsc.utils import empty_cache_path
empty_cache_path()
```

#### 数据源配置

**Tushare 配置**：
```python
# 在 tushare_config.json 中配置
{
    "token": "your_tushare_token",
    "pro_api": "https://api.tushare.pro"
}
```

**其他数据源**：根据具体连接器文档配置相应的 API Key 或连接信息。

## 存储的数据格式

```python
      symbol                  dt         open        close         high          low        vol      amount
0  000001.SH 2010-01-04 09:31:00  3292.049072  3293.325928  3295.279053  3292.049072  203927696  2358753536
```

## 前端使用

https://github.com/tvjsx/trading-vue-js?tab=readme-ov-file

### 指数
symbols/SSE-000001/

### 指标 

- 收藏
- 我的脚本

### 技术指标

#### 指标

#### 策略

### 形态

### 从某个股票之后开始跑数据
python scripts/fetch_tushare_minute_data_stk_mins.py --freq 1min --start-date "2018-01-01 09:00:00" --end-date "2026-01-31 19:00:00" --resume-after 000615.SZ

### 另外如果你想用自动断点续跑
python scripts/fetch_tushare_minute_data_stk_mins.py --freq 1min --start-date "2018-01-01 09:00:00" --end-date "2026-01-31 19:00:00" --checkpoint


sz	深圳证券交易所
000001-004999（主板）
300000-309999（创业板）
002000-002999（中小板）


sh	上海证券交易所	
600000-603999（主板）
605000-605999（主板）
688000-688999（科创板）