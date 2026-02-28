#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
极简日线拉取测试脚本：无 Tushare/DB/网络依赖，仅用于验证“被 scheduled_tasks 或 API 子进程调用时退出码为 0”。

用法：
    python scripts/daily/fetch_daily_simple.py

或通过 scheduled_tasks：python scripts/scheduled_tasks.py fetch_daily --test-simple
"""
import sys

if __name__ == "__main__":
    print("daily_fetch_simple_ok")
    sys.exit(0)
