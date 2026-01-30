# 定义了所有核心数据对象的结构。

# #### 主要对象

# - **RawBar**：原始K线数据
# - **NewBar**：去除包含关系后的K线
# - **FX**：分型对象
# - **BI**：笔对象
# - **ZS**：中枢对象
# - **Signal**：信号对象
# - **Factor**：因子对象
# - **Event**：事件对象
# - **Position**：持仓策略对象

from czsc.objects import Signal

# Signal 的格式：{k1}_{k2}_{k3}_{v1}_{v2}_{v3}_{score}
# 方式1: 使用完整的 signal 字符串
signal = Signal(
    signal="30分钟_D1_表里关系V230101_向上_任意_任意_0"
)

# Signal 会自动解析
print(f"signal: {signal.signal}")
print(f"k1 (周期): {signal.k1}")      # "30分钟"
print(f"k2: {signal.k2}")              # "D1"
print(f"k3 (信号名称): {signal.k3}")  # "表里关系V230101"
print(f"v1 (信号值): {signal.v1}")    # "向上"
print(f"v2: {signal.v2}")              # "任意"
print(f"v3: {signal.v3}")             # "任意"
print(f"score: {signal.score}")       # 0
print(f"key (属性): {signal.key}")     # "30分钟_D1_表里关系V230101"
print(f"value (属性): {signal.value}")  # "向上_任意_任意_0"

# 方式2: 使用 k1, k2, k3, v1, v2, v3, score 参数
signal2 = Signal(
    k1="30分钟",
    k2="D1",
    k3="表里关系V230101",
    v1="向上",
    v2="任意",
    v3="任意",
    score=0
)
print(f"\n方式2创建的signal: {signal2.signal}")