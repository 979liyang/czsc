## 项目概述

### 什么是 CZSC？

CZSC（缠中说禅）是一个基于缠论技术分析理论的 Python 量化交易工具库。它实现了缠论中的核心概念，包括：

- **分型识别**：自动识别顶分型和底分型
- **笔识别**：基于分型自动识别笔
- **中枢识别**：识别价格震荡区间
- **多级别联立分析**：支持多个时间周期的联合分析
- **信号系统**：基于缠论结构生成交易信号
- **策略回测**：完整的策略回测框架

### 项目特点

- ✅ 完整的缠论技术分析实现
- ✅ 支持多数据源（Tushare、聚宽、米筐、QMT等）
- ✅ 灵活的信号和策略系统
- ✅ 丰富的可视化工具
- ✅ 完善的回测框架
- ✅ 活跃的社区支持

### 版本信息

- 当前版本：0.9.69
- Python 要求：>= 3.8
- 主要依赖：pandas, numpy, loguru, plotly 等

---

# czsc - 缠中说禅技术分析工具

[![Downloads](https://static.pepy.tech/personalized-badge/czsc?period=total&units=international_system&left_color=red&right_color=orange&left_text=Downloads/Total)](https://pepy.tech/project/czsc)
[![Downloads](https://static.pepy.tech/personalized-badge/czsc?period=month&units=international_system&left_color=red&right_color=orange&left_text=Downloads/Month)](https://pepy.tech/project/czsc)
[![Downloads](https://static.pepy.tech/personalized-badge/czsc?period=week&units=international_system&left_color=red&right_color=orange&left_text=Downloads/Week)](https://pepy.tech/project/czsc)
[![Python 3.7](https://img.shields.io/badge/python-3.7-blue.svg)](https://www.python.org/downloads/release/python-370/)
[![PyPI](https://img.shields.io/pypi/v/czsc.svg)](https://pypi.org/project/czsc/)
[![Documentation Status](https://readthedocs.org/projects/czsc/badge/?version=latest)](https://czsc.readthedocs.io/en/latest/?badge=latest)

**[API文档](https://czsc.readthedocs.io/en/latest/modules.html)** |
**[项目文档](https://s0cqcxuy3p.feishu.cn/wiki/wikcn3gB1MKl3ClpLnboHM1QgKf)** |
**[投研数据共享](https://s0cqcxuy3p.feishu.cn/wiki/wikcnzuPawXtBB7Cj7mqlYZxpDh)** |
**[信号函数编写规范](https://s0cqcxuy3p.feishu.cn/wiki/wikcnCFLLTNGbr2THqo7KtWfBkd)** |
**[DEVIN生成的文档](https://deepwiki.com/waditu/czsc/1-overview)**

>源于[缠中说缠博客](http://blog.sina.com.cn/chzhshch)，原始博客中的内容不太完整，且没有评论，以下是网友整理的原文备份
* 备份网址1：http://www.fxgan.com
* 备份网址2：https://chzhshch.blog

* 已经开始用czsc库进行量化研究的朋友，欢迎[加入飞书群](https://applink.feishu.cn/client/chat/chatter/add_by_link?link_token=0bak668e-7617-452c-b935-94d2c209e6cf)，快点击加入吧！
* [B站视频教程合集（持续更新...）](https://space.bilibili.com/243682308/channel/series)

## 项目贡献

* **[择时策略研究框架](https://s0cqcxuy3p.feishu.cn/wiki/wikcnhizrtIOQakwVcZLMKJNaib)**
* 缠论的 `分型、笔` 的自动识别，详见 `czsc/analyze.py`
* 定义并实现 `信号-因子-事件-交易` 量化交易逻辑体系，因子是信号的线性组合，事件是因子的同类合并，详见 `czsc/objects.py`
* 定义并实现了若干信号函数，详见 `czsc/signals`
* 缠论多级别联立决策分析交易，详见 `CzscTrader`
* **[Streamlit 量化研究组件库](https://s0cqcxuy3p.feishu.cn/wiki/AATuw5vN7iN9XbkVPuwcE186n9f)**


## 安装使用

**注意:** python 版本必须大于等于 3.8

直接从github安装：
```
pip install git@github.com:waditu/czsc.git -U
```

直接从github指定分支安装最新版：
```
pip install git+https://github.com/waditu/czsc.git@V0.9.46 -U
```

从`pypi`安装：
```
pip install czsc -U -i https://pypi.python.org/simple
```

## 使用案例

1. [使用 tqsdk 进行期货交易](https://s0cqcxuy3p.feishu.cn/wiki/wikcn41lQIAJ1f8v41Dj5eAmrub)
2. [CTA择时：缠论30分钟笔非多即空](https://s0cqcxuy3p.feishu.cn/wiki/YPlewoj70ikwxakPnOucTP8lnYg)
3. [使用CTA研究UI页面进行策略研究](https://s0cqcxuy3p.feishu.cn/wiki/JWe3wo1VNiglO9kE999cGy8innh)

## 原文整理

* [缠中说禅重新编排版《论语》（整理版）](https://blog.csdn.net/baidu_25764509/article/details/109517775)
* [缠中说禅交易指南](https://blog.csdn.net/baidu_25764509/article/details/109598229)
* [缠中说禅技术原理](https://blog.csdn.net/baidu_25764509/article/details/109597255)
* [缠中说禅图解分析示范](https://blog.csdn.net/baidu_25764509/article/details/110195063)
* [缠中说禅：缠非缠、禅非禅，枯木龙吟照大千（整理版）](https://blog.csdn.net/baidu_25764509/article/details/110775662)
* [缠中说禅教你打坐（整理版）](https://blog.csdn.net/baidu_25764509/article/details/113735170)

**注意：** 如果CSDN的连接打不开，可以直接在 `czsc/docs` 目录下查看 html 文件


## 资料分享

* 链接：https://pan.baidu.com/s/1RXkP3188F0qu8Yk6CjbxRQ
* 提取码：vhue

# token

13029727256
15114579671Ly


## backend

# 从项目根目录运行
./backend/install.sh

# 1. 激活虚拟环境（从项目根目录）
source venv/bin/activate

# 2. 进入 backend 目录并安装依赖
cd backend
pip install -r requirements.txt

# 3. 运行服务
python run.py

## Demo：本地 .stock_data → CZSC 多周期分析 → 前端 /stock/:symbol

1）确保本地已有分钟数据（示例：600078.SH）：

- 目录应存在：`.stock_data/raw/minute_by_stock/stock_code=600078.SH/`

2）启动后端（FastAPI）：

```bash
cd backend
python run.py
```

3）启动前端（Vue3）：

```bash
cd frontend
npm run dev
```

4）浏览器打开（默认 sdt=20180101，demo=600078）：

- `http://localhost:5173/stock/600078.SH`

页面会从本地 `.stock_data` 读取分钟数据，并在后端计算 **30分钟 / 60分钟 / 日线** 三个维度的 CZSC 分析结果，前端用 `trading-vue-js` 展示。