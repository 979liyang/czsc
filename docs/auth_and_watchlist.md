# 登录与自选股

## 概述

- **登录/注册**：未登录用户访问业务页会跳转到 `/login`，注册或登录成功后返回原页面或首页。
- **自选股**：登录用户可在「自选股」页添加/删除股票代码，不同用户的自选股相互隔离；首页会展示当前用户的自选股快捷入口。

## 环境变量（后端）

在项目根目录或 `backend/.env` 中可配置（均以 `CZSC_` 为前缀）：

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `CZSC_JWT_SECRET` | JWT 签发与校验密钥，生产环境务必修改 | `czsc-api-secret-change-in-production` |
| `CZSC_JWT_EXPIRE_MINUTES` | Token 有效时间（分钟） | `10080`（7 天） |

MySQL 需存在 `user`、`watchlist` 表，见下方「创建表」。

## 创建 user / watchlist 表

项目未使用 Alembic，认证表需单独创建。从**项目根目录**执行：

```bash
cd backend
python -c "
import sys
sys.path.insert(0, '.')
from src.models.mysql_models import User, Watchlist
from src.storage.mysql_db import get_engine
engine = get_engine()
User.__table__.create(engine, checkfirst=True)
Watchlist.__table__.create(engine, checkfirst=True)
print('user、watchlist 表已就绪')
"
```

或运行脚本（需在 `backend` 目录下）：

```bash
cd backend
python scripts/create_auth_tables.py
```

## API 说明

- **POST /api/v1/auth/register**：注册，body `{ "username": "xxx", "password": "xxx" }`，返回 `access_token` 与 `user`。
- **POST /api/v1/auth/login**：登录，同上。
- **GET /api/v1/auth/me**：获取当前用户（Header: `Authorization: Bearer <token>`）。
- **GET /api/v1/watchlist**：当前用户自选股列表。
- **POST /api/v1/watchlist**：添加自选，body `{ "symbol": "000001.SZ" }`。
- **DELETE /api/v1/watchlist/{symbol}**：删除自选。

除登录/注册和健康检查外，业务接口均需在请求头携带 `Authorization: Bearer <token>`，否则返回 401。
