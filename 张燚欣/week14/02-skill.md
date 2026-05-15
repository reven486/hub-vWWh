---
name: 股票波动可视化与择时建议
description: 复用已有股票K线查询接口，绘制日/周波动双轴图，并根据历史波动率分位数给出买入/卖出区间建议。
---

# 依赖（复用已有 skill）
- `get_day_line` – 日K线数据（前复权）
- `get_week_line` – 周K线数据（前复权）

# 核心功能
1. 从已有接口获取指定股票的日K、周K数据。
2. 计算日波动率 = (最高 - 最低) / 收盘价，周波动率同理。
3. 使用 `matplotlib` 绘制双Y轴图：
   - 左轴：日波动率（蓝色）
   - 右轴：周波动率（红色）
4. 基于历史波动率的 30th 和 70th 分位数给出操作建议：
   - 当前波动 < 30分位 → 低波区，可能酝酿突破，可关注买入机会。
   - 当前波动 > 70分位 → 高波区，风险加大，建议注意回调或减仓。
   - 介于之间 → 正常波动，可持股观望。

# 使用前提
- 已部署的股票查询 skill 可用。
- Python 环境安装 `matplotlib pandas numpy`。

# 调用示例
```python
from existing_stock_skill import get_day_line, get_week_line  
# 实际导入路径需根据你的 skill 服务调整

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

def analyze_volatility(code: str, start: str = None, end: str = None):
    # 获取数据
    day = pd.DataFrame(get_day_line(code, start, end, type=1)['data'])
    week = pd.DataFrame(get_week_line(code, start, end, type=1)['data'])

    # 计算波动率
    day['vol'] = (day['high'] - day['low']) / day['close']
    week['vol'] = (week['high'] - week['low']) / week['close']

    # 绘图
    fig, ax1 = plt.subplots(figsize=(12, 5))
    ax1.plot(pd.to_datetime(day['date']), day['vol'], 'b-', alpha=0.7, label='Daily Vol')
    ax1.set_ylabel('Daily Volatility', color='blue')
    ax1.tick_params(axis='y', labelcolor='blue')

    ax2 = ax1.twinx()
    ax2.plot(pd.to_datetime(week['date']), week['vol'], 'r-', alpha=0.9, label='Weekly Vol')
    ax2.set_ylabel('Weekly Volatility', color='red')
    ax2.tick_params(axis='y', labelcolor='red')

    plt.title(f'{code} Volatility Analysis')
    fig.autofmt_xdate()
    plt.tight_layout()

    # 建议
    cur = day['vol'].iloc[-1]
    low, high = np.percentile(day['vol'], [30, 70])
    if cur < low:
        tip = "低波动区域，可能酝酿突破，建议关注买入。"
    elif cur > high:
        tip = "高波动区域，风险加大，注意回调或减仓。"
    else:
        tip = "正常波动区间，可持股观望或小仓位操作。"
    
    print(f"当前日波动: {cur:.4f} | 30%分位: {low:.4f} | 70%分位: {high:.4f}")
    print("操作建议:", tip)
    plt.show()

# 使用示例
analyze_volatility("000001", "20250101", "20250501")