# Implementation Plan: CZSC API与前端界面增强

**Branch**: `001-czsc-api-ui` | **Date**: 2025-01-27 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-czsc-api-ui/spec.md`

## Summary

基于CZSC核心库构建Web应用系统，提供REST API接口和Vue3前端界面，使非技术用户也能使用缠论分析功能。系统包括：后端API服务（FastAPI）、历史数据存储模块、Vue3前端应用、信号函数文档系统和更多策略示例代码。所有功能基于czsc库现有接口，不修改czsc核心代码。

## Technical Context

**Language/Version**: Python 3.8+, TypeScript 5.0+  
**Primary Dependencies**: 
- 后端：FastAPI, czsc, pandas, sqlalchemy
- 前端：Vue 3, ElementPlus, TailwindCSS, TypeScript, Vue Router, Axios
- 数据存储：SQLite/PostgreSQL（用于元数据），文件系统（用于K线数据）  
**Storage**: 
- 历史K线数据：文件系统（Parquet格式，按symbol/freq组织）
- 元数据：SQLite/PostgreSQL（股票列表、信号函数信息、策略配置等）
- 缓存：内存缓存（Redis可选）  
**Testing**: pytest（后端），Vitest（前端）  
**Target Platform**: 
- 后端：Linux/Windows服务器
- 前端：现代浏览器（Chrome, Firefox, Safari, Edge）  
**Project Type**: Web应用（前后端分离）  
**Performance Goals**: 
- API响应：K线查询<1s，信号计算<3s，回测<30s
- 前端：首屏加载<3s，交互响应<100ms
- 数据存储：支持5000只股票10年数据，总大小<500GB  
**Constraints**: 
- 不修改czsc核心库代码
- 所有功能基于czsc现有接口
- 前端必须响应式设计
- API必须RESTful规范  
**Scale/Scope**: 
- 支持100并发用户
- 15+策略示例
- 300+信号函数文档
- 5000只股票数据存储

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- ✅ 不修改czsc核心库
- ✅ 基于czsc现有能力设计
- ✅ 前后端分离架构
- ✅ 使用成熟技术栈

## Project Structure

### Documentation (this feature)

```text
specs/001-czsc-api-ui/
├── plan.md              # This file (/speckit.plan command output)
├── spec.md              # Feature specification
├── checklists/          # Quality checklists
└── tasks.md             # Implementation tasks (to be created by /speckit.tasks)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── api/                    # API路由层
│   │   ├── __init__.py
│   │   ├── v1/                 # API v1版本
│   │   │   ├── __init__.py
│   │   │   ├── bars.py         # K线数据接口
│   │   │   ├── signals.py      # 信号计算接口
│   │   │   ├── analysis.py     # 缠论分析接口
│   │   │   ├── backtest.py     # 策略回测接口
│   │   │   ├── symbols.py      # 股票列表接口
│   │   │   └── docs.py         # 信号函数文档接口
│   │   └── dependencies.py     # API依赖（认证、限流等）
│   ├── services/               # 业务逻辑层
│   │   ├── __init__.py
│   │   ├── data_service.py     # 数据获取服务
│   │   ├── analysis_service.py # 缠论分析服务
│   │   ├── signal_service.py   # 信号计算服务
│   │   ├── backtest_service.py # 回测服务
│   │   └── doc_service.py      # 文档生成服务
│   ├── storage/                # 数据存储层
│   │   ├── __init__.py
│   │   ├── kline_storage.py    # K线数据存储
│   │   ├── metadata_storage.py # 元数据存储
│   │   └── cache.py            # 缓存管理
│   ├── models/                 # 数据模型
│   │   ├── __init__.py
│   │   ├── schemas.py          # Pydantic模型
│   │   └── database.py         # 数据库模型
│   ├── utils/                  # 工具函数
│   │   ├── __init__.py
│   │   ├── czsc_adapter.py    # CZSC适配器封装
│   │   └── validators.py       # 数据验证
│   └── main.py                 # FastAPI应用入口
├── tests/                      # 测试代码
│   ├── __init__.py
│   ├── test_api/
│   ├── test_services/
│   └── test_storage/
├── alembic/                    # 数据库迁移
├── requirements.txt
└── README.md

frontend/
├── src/
│   ├── api/                    # API调用层
│   │   ├── index.ts           # API客户端配置
│   │   ├── bars.ts            # K线数据API
│   │   ├── signals.ts         # 信号API
│   │   ├── analysis.ts        # 分析API
│   │   ├── backtest.ts        # 回测API
│   │   └── docs.ts            # 文档API
│   ├── router/                 # 路由配置
│   │   ├── index.ts
│   │   └── routes.ts
│   ├── views/                  # 页面组件
│   │   ├── Home.vue           # 首页
│   │   ├── Analysis.vue       # 缠论分析页面
│   │   ├── Signals.vue        # 信号函数文档页面
│   │   ├── Examples.vue        # 策略示例页面
│   │   └── Backtest.vue       # 回测页面
│   ├── components/             # 通用组件
│   │   ├── KlineChart.vue     # K线图组件
│   │   ├── BiList.vue         # 笔列表组件
│   │   ├── FxList.vue         # 分型列表组件
│   │   └── SignalCard.vue     # 信号卡片组件
│   ├── stores/                 # 状态管理（Pinia）
│   │   ├── index.ts
│   │   ├── analysis.ts
│   │   └── signals.ts
│   ├── utils/                  # 工具函数
│   │   ├── formatters.ts
│   │   └── validators.ts
│   ├── App.vue
│   └── main.ts
├── public/
├── tests/
├── package.json
├── tsconfig.json
├── tailwind.config.js
├── vite.config.ts
└── README.md

data/                           # 历史数据存储（独立文件夹）
├── klines/                     # K线数据（Parquet格式）
│   ├── {symbol}/
│   │   ├── {freq}/
│   │   │   └── data.parquet
│   └── index.json              # 数据索引
├── metadata/                   # 元数据
│   ├── symbols.json            # 股票列表
│   └── signals.json            # 信号函数信息
└── cache/                      # 缓存数据

examples/                       # 更多策略示例
├── strategies/
│   ├── stock/                  # 股票策略
│   ├── future/                 # 期货策略
│   └── etf/                    # ETF策略
└── README.md
```

**Structure Decision**: 采用前后端分离架构，后端使用FastAPI提供REST API，前端使用Vue3构建单页应用。历史数据存储在独立的`data/`文件夹中，使用文件系统存储K线数据（Parquet格式），数据库存储元数据。这种设计简单直接，充分利用czsc现有能力，避免过度设计。

## Technology Stack

### Backend
- **Framework**: FastAPI (高性能、自动文档生成)
- **Data Processing**: czsc库（核心分析功能）
- **Data Storage**: 
  - K线数据：Parquet文件（高效压缩、快速读取）
  - 元数据：SQLite（轻量级，无需额外服务）
- **Caching**: Python `functools.lru_cache` + 内存缓存（简单高效）
- **Validation**: Pydantic（数据验证和序列化）

### Frontend
- **Framework**: Vue 3 (Composition API)
- **UI Library**: ElementPlus（成熟的中文UI组件库）
- **Styling**: TailwindCSS（实用优先的CSS框架）
- **Language**: TypeScript（类型安全）
- **Routing**: Vue Router 4
- **State Management**: Pinia（Vue 3官方推荐）
- **HTTP Client**: Axios
- **Build Tool**: Vite（快速开发构建）

### Data Storage Design

**K线数据存储方案**：
```
data/klines/
├── {symbol}/              # 按股票代码组织
│   ├── {freq}/           # 按周期组织
│   │   └── data.parquet  # Parquet格式，包含所有历史数据
│   └── metadata.json      # 该股票的数据元信息（时间范围、数据量等）
└── index.json             # 全局索引（所有股票列表、数据更新时间）
```

**优势**：
- Parquet格式：列式存储，压缩率高，查询速度快
- 文件系统组织：简单直观，易于备份和迁移
- 支持增量更新：只需追加新数据到Parquet文件
- 兼容czsc：可直接读取为DataFrame，转换为RawBar

**元数据存储**：
- SQLite数据库，包含：
  - symbols表：股票列表、分组信息
  - signals表：信号函数信息（名称、参数、分类）
  - strategies表：策略示例信息

## API Design

### RESTful API Endpoints

**Base URL**: `/api/v1`

#### 1. K线数据接口
- `GET /bars` - 获取K线数据
  - Query params: `symbol`, `freq`, `sdt`, `edt`
  - Response: `List[RawBar]` (JSON格式)

#### 2. 缠论分析接口
- `POST /analysis/czsc` - 执行缠论分析
  - Body: `{symbol, freq, sdt, edt}`
  - Response: `{bis: List[BI], fxs: List[FX], zss: List[ZS]}`

#### 3. 信号计算接口
- `GET /signals/calculate` - 计算单个信号
  - Query params: `symbol`, `freq`, `signal_name`, `**kwargs`
  - Response: `{signals: Dict[str, str]}`

- `POST /signals/batch` - 批量计算信号
  - Body: `{symbol, freq, signal_configs: List}`
  - Response: `{signals: Dict[str, str]}`

#### 4. 策略回测接口
- `POST /backtest/run` - 执行策略回测
  - Body: `{strategy_config, symbol, sdt, edt}`
  - Response: `{pairs: Dict, operates: List, positions: List}`

#### 5. 股票列表接口
- `GET /symbols` - 获取股票列表
  - Query params: `group` (可选，分组名称)
  - Response: `List[str]`

#### 6. 信号函数文档接口
- `GET /docs/signals` - 获取所有信号函数列表
  - Response: `List[SignalInfo]`

- `GET /docs/signals/{signal_name}` - 获取信号函数详情
  - Response: `{name, description, params, examples}`

## Data Models

### Backend Models (Pydantic)

```python
# schemas.py
from pydantic import BaseModel
from datetime import datetime
from typing import List, Dict, Optional

class BarRequest(BaseModel):
    symbol: str
    freq: str
    sdt: str  # YYYYMMDD
    edt: str  # YYYYMMDD

class BarResponse(BaseModel):
    symbol: str
    freq: str
    bars: List[Dict]  # RawBar序列化

class AnalysisRequest(BaseModel):
    symbol: str
    freq: str
    sdt: str
    edt: str

class AnalysisResponse(BaseModel):
    symbol: str
    freq: str
    bis: List[Dict]  # BI序列化
    fxs: List[Dict]  # FX序列化
    zss: List[Dict]  # ZS序列化

class SignalRequest(BaseModel):
    symbol: str
    freq: str
    signal_name: str
    params: Dict = {}

class SignalResponse(BaseModel):
    signals: Dict[str, str]

class BacktestRequest(BaseModel):
    strategy_config: Dict
    symbol: str
    sdt: str
    edt: str

class BacktestResponse(BaseModel):
    pairs: Dict
    operates: List[Dict]
    positions: List[Dict]
```

### Frontend Types (TypeScript)

```typescript
// types/index.ts
export interface Bar {
  symbol: string;
  id: number;
  dt: string;
  freq: string;
  open: number;
  close: number;
  high: number;
  low: number;
  vol: number;
  amount: number;
}

export interface BI {
  symbol: string;
  direction: '向上' | '向下';
  power: number;
  // ... 其他字段
}

export interface FX {
  symbol: string;
  mark: '顶分型' | '底分型';
  dt: string;
  // ... 其他字段
}

export interface SignalInfo {
  name: string;
  category: string;
  description: string;
  params: ParamInfo[];
  examples: string[];
}

export interface ParamInfo {
  name: string;
  type: string;
  default: any;
  description: string;
}
```

## Key Implementation Details

### 1. CZSC适配器封装

创建`czsc_adapter.py`，封装czsc常用操作：

```python
# backend/src/utils/czsc_adapter.py
from czsc.analyze import CZSC
from czsc.objects import RawBar, Freq
from czsc.traders import CzscSignals, CzscTrader
from czsc.utils import BarGenerator
from czsc.connectors import research

class CZSCAdapter:
    """CZSC适配器，封装常用操作"""
    
    @staticmethod
    def get_bars(symbol: str, freq: str, sdt: str, edt: str) -> List[RawBar]:
        """获取K线数据"""
        return research.get_raw_bars(symbol, Freq(freq), sdt, edt)
    
    @staticmethod
    def analyze(bars: List[RawBar]) -> CZSC:
        """执行缠论分析"""
        return CZSC(bars)
    
    @staticmethod
    def calculate_signals(bg: BarGenerator, signals_config: List[Dict]) -> Dict:
        """计算信号"""
        cs = CzscSignals(bg=bg, signals_config=signals_config)
        return dict(cs.s)
```

### 2. 数据存储服务

```python
# backend/src/storage/kline_storage.py
import pandas as pd
from pathlib import Path

class KlineStorage:
    """K线数据存储服务"""
    
    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    def save_bars(self, symbol: str, freq: str, bars: List[RawBar]):
        """保存K线数据"""
        df = self._bars_to_df(bars)
        file_path = self.base_path / symbol / freq / "data.parquet"
        file_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(file_path, compression='snappy')
    
    def load_bars(self, symbol: str, freq: str, sdt: str, edt: str) -> List[RawBar]:
        """加载K线数据"""
        file_path = self.base_path / symbol / freq / "data.parquet"
        if not file_path.exists():
            return []
        df = pd.read_parquet(file_path)
        # 过滤时间范围
        df = df[(df['dt'] >= sdt) & (df['dt'] <= edt)]
        return self._df_to_bars(df, symbol, freq)
```

### 3. 信号函数文档生成

自动分析`czsc/signals`目录，提取信号函数信息：

```python
# backend/src/services/doc_service.py
import inspect
from czsc.signals import *

class DocService:
    """信号函数文档服务"""
    
    def get_all_signals(self) -> List[SignalInfo]:
        """获取所有信号函数信息"""
        signals = []
        # 遍历czsc.signals模块，提取函数信息
        for name, func in inspect.getmembers(czsc.signals, inspect.isfunction):
            if name.startswith('_'):
                continue
            doc = inspect.getdoc(func)
            sig = inspect.signature(func)
            signals.append({
                'name': name,
                'category': self._get_category(name),
                'description': doc,
                'params': self._extract_params(sig),
            })
        return signals
```

### 4. 前端API层

```typescript
// frontend/src/api/bars.ts
import axios from 'axios';
import type { Bar, BarRequest } from '@/types';

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
});

export const barsApi = {
  async getBars(params: BarRequest): Promise<Bar[]> {
    const response = await api.get<Bar[]>('/bars', { params });
    return response.data;
  },
};
```

## Testing Strategy

### Backend Tests
- **Unit Tests**: 测试services和storage层
- **API Tests**: 使用FastAPI TestClient测试API端点
- **Integration Tests**: 测试完整的业务流程

### Frontend Tests
- **Component Tests**: 使用Vitest测试Vue组件
- **API Mock**: 使用MSW模拟API响应
- **E2E Tests**: 使用Playwright测试关键用户流程

## Deployment

### Development
- 后端：`uvicorn backend.src.main:app --reload`
- 前端：`npm run dev`

### Production
- 后端：使用Gunicorn + Uvicorn workers
- 前端：构建静态文件，使用Nginx服务
- 数据：定期备份`data/`目录

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

无违反项。
