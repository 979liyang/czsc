# fetch_stock_data.py 依赖分析报告

## 命令
```bash
python scripts/fetch_stock_data.py --stock 600078.SH --start-date 20240101 --end-date 20241231
```

## 实际使用的文件

### backend/data/ 目录
1. **akshare_client.py** ✓
   - 类：`AkShareClient`
   - 方法：`fetch_minute_data()`, `fetch_historical_data()`, `clean_and_format_minute_data()`
   - 依赖：`backend.utils.market_utils` (仅在 `collect_historical_data_by_market()` 中使用，fetch_stock_data.py 不调用)

2. **raw_data_storage.py** ✓
   - 类：`RawDataStorage`
   - 方法：`save_minute_data_by_stock()`, `save_daily_data_by_stock()`
   - 依赖：
     - `backend.data.storage_manager.StorageManager`
     - `backend.utils.compression_config.get_parquet_write_options()`
     - `backend.data.schema_registry.SchemaRegistry`

3. **storage_manager.py** ✓
   - 类：`StorageManager` (基类)
   - 依赖：
     - `backend.utils.partition_utils.PartitionPathGenerator`
     - `backend.utils.compression_config.get_parquet_write_options()`, `get_parquet_engine_options()`

4. **schema_registry.py** ✓
   - 类：`SchemaRegistry`
   - 无外部依赖

### backend/utils/ 目录
1. **compression_config.py** ✓
   - 函数：`get_parquet_write_options()`, `get_parquet_engine_options()`
   - 无外部依赖

2. **partition_utils.py** ✓
   - 类：`PartitionPathGenerator`
   - 无外部依赖

3. **market_utils.py** ⚠️ (可选)
   - 函数：`normalize_market_code()`
   - 仅在 `akshare_client.collect_historical_data_by_market()` 中使用
   - `fetch_stock_data.py` 不调用该方法，已改为延迟导入

## 已删除的不适用文件

### backend/data/ 目录
- ❌ **processed_data_storage.py** - 未使用
- ❌ **repository.py** - 未使用

### backend/utils/ 目录
- ❌ **czsc_utils.py** - 未使用（包含CZSC相关工具，fetch_stock_data.py 不涉及CZSC分析）
- ❌ **date_utils.py** - 未使用
- ❌ **file_utils.py** - 未使用
- ❌ **logger.py** - 未使用（所有文件直接使用 `loguru.logger`）

## 保留但未直接使用的文件

### backend/data/ 目录
- ⚠️ **raw_data_loader.py** - 未在 fetch_stock_data.py 中使用
  - 用途：数据加载（读取已存储的数据）
  - fetch_stock_data.py 只负责数据采集和存储，不涉及数据加载
  - 建议：保留，可能在其他分析脚本中使用

## 优化建议

1. ✅ 已优化 `market_utils.py` 的导入方式（延迟导入）
2. ✅ 已删除所有未使用的工具文件
3. ✅ 已删除未使用的数据存储文件

## 依赖关系图

```
fetch_stock_data.py
├── backend.data.akshare_client
│   └── backend.utils.market_utils (延迟导入，可选)
├── backend.data.raw_data_storage
│   ├── backend.data.storage_manager
│   │   ├── backend.utils.partition_utils
│   │   └── backend.utils.compression_config
│   ├── backend.utils.compression_config
│   └── backend.data.schema_registry
```

## 总结

- **实际使用的文件**：6个（backend/data: 4个, backend/utils: 2个）
- **已删除的文件**：6个
- **代码简化**：移除了所有与数据采集无关的工具函数和存储类
