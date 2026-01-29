# CZSC API 后端

基于FastAPI的CZSC缠论分析API服务。

## 项目结构

```
backend/
├── src/
│   ├── api/                    # API路由层
│   │   ├── v1/                 # API v1版本
│   │   └── dependencies.py     # API依赖
│   ├── services/               # 业务逻辑层
│   ├── storage/                # 数据存储层
│   ├── models/                 # 数据模型
│   ├── utils/                  # 工具函数
│   └── main.py                 # FastAPI应用入口
├── tests/                      # 测试代码
├── requirements.txt            # 依赖列表
└── README.md                   # 本文档
```

## 安装

```bash
pip install -r requirements.txt
```

## 运行

```bash
# 开发模式
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# 生产模式
uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## API文档

启动服务后，访问：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 环境变量

- `DATA_PATH`: 数据存储路径，默认为 `./data`
- `LOG_LEVEL`: 日志级别，默认为 `INFO`
