"""
股票分析 Skill - 支持日波动、周波动可视化及买卖时机建议
需要安装: pip install deepagents yfinance matplotlib pandas
"""

from deepagents import create_deep_agent
from langchain_openai import ChatOpenAI
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# 设置中文字体（解决图表中文显示问题）
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

from datetime import datetime, timedelta
from typing import Literal

# ============== 工具函数定义 ==============

def get_stock_data(
    symbol: str,
    period: Literal["1mo", "3mo", "6mo", "1y"] = "1mo",
    interval: Literal["1d", "1wk"] = "1d"
) -> dict:
    """
    获取股票数据

    Args:
        symbol: 股票代码，如 "AAPL", "000001.SZ"
        period: 数据时间范围
        interval: 数据间隔 ("1d"=日, "1wk"=周)
    """
    try:
        import yfinance as yf
        stock = yf.Ticker(symbol)
        df = stock.history(period=period, interval=interval)
        if df.empty:
            return {"error": f"未找到股票 {symbol} 的数据"}
        return {
            "symbol": symbol,
            "data": df.to_dict(orient="records"),
            "columns": list(df.columns),
            "start": str(df.index[0]),
            "end": str(df.index[-1])
        }
    except Exception as e:
        return {"error": str(e)}


def calculate_volatility(prices: list) -> dict:
    """计算波动率"""
    prices = np.array(prices)
    returns = np.diff(prices) / prices[:-1]
    daily_vol = np.std(returns) * 100  # 日波动率 %
    return {
        "daily_volatility": round(daily_vol, 2),
        "weekly_volatility": round(daily_vol * np.sqrt(5), 2),  # 周波动估算
        "max_price": float(np.max(prices)),
        "min_price": float(np.min(prices)),
        "avg_price": float(np.mean(prices))
    }


def analyze_buy_sell_timing(symbol: str, period: Literal["1mo", "3mo", "6mo"] = "1mo") -> dict:
    """
    分析股票买卖时机（基于波动率）

    Returns:
        包含分析结果和建议的字典
    """
    # 获取数据
    data = get_stock_data(symbol, period, "1d")
    if "error" in data:
        return data

    df = pd.DataFrame(data["data"])
    close_prices = df["Close"].tolist()

    # 计算波动
    vol_info = calculate_volatility(close_prices)
    daily_vol = vol_info["daily_volatility"]
    weekly_vol = vol_info["weekly_volatility"]

    # 计算日收益率序列
    prices = np.array(close_prices)
    returns = np.diff(prices) / prices[:-1]

    # 基于波动率给出建议
    current_price = close_prices[-1]

    if daily_vol < 1.5:
        signal = "观望"
        action = "低波动，当前适合观望，不建议追高"
        urgency = "低"
    elif daily_vol < 3.0:
        if returns[-1] > 0.02:
            signal = "买入"
            action = f"温和上涨+低波动，可考虑买入，当前价格: {current_price:.2f}"
            urgency = "中"
        elif returns[-1] < -0.02:
            signal = "卖出"
            action = f"温和下跌+低波动，建议减仓，当前价格: {current_price:.2f}"
            urgency = "中"
        else:
            signal = "持有"
            action = f"波动正常，建议持有观望，当前价格: {current_price:.2f}"
            urgency = "低"
    else:
        if returns[-1] > 0.03:
            signal = "卖出"
            action = f"高波动+快速上涨，建议止盈，当前价格: {current_price:.2f}"
            urgency = "高"
        elif returns[-1] < -0.03:
            signal = "买入"
            action = f"高波动+快速下跌，可能是买入机会，当前价格: {current_price:.2f}"
            urgency = "高"
        else:
            signal = "观望"
            action = "高波动环境，建议等待趋势明朗"
            urgency = "中"

    return {
        "symbol": symbol,
        "current_price": round(current_price, 2),
        "daily_volatility": daily_vol,
        "weekly_volatility": weekly_vol,
        "signal": signal,
        "action": action,
        "urgency": urgency,
        "price_range": f"{vol_info['min_price']:.2f} ~ {vol_info['max_price']:.2f}",
        "avg_price": round(vol_info['avg_price'], 2)
    }


def plot_stock_volatility(
    symbol: str,
    period: Literal["1mo", "3mo", "6mo", "1y"] = "1mo",
    save_path: str = None
) -> str:
    """
    绘制股票日波动和周波动对比图

    Args:
        symbol: 股票代码
        period: 数据时间范围
        save_path: 图片保存路径（可选）

    Returns:
        图片保存路径或错误信息
    """
    import yfinance as yf

    try:
        stock = yf.Ticker(symbol)

        # 获取日线和周线数据
        daily_df = stock.history(period=period, interval="1d")
        weekly_df = stock.history(period=period, interval="1wk")

        if daily_df.empty or weekly_df.empty:
            return f"未找到股票 {symbol} 的数据"

        # 计算波动率（日波动 = 日收益率标准差，周波动 = 周收益率标准差）
        daily_df['Return'] = daily_df['Close'].pct_change()
        weekly_df['Return'] = weekly_df['Close'].pct_change()

        # 计算滚动波动率（5日/4周）
        daily_df['Volatility_5d'] = daily_df['Return'].rolling(window=5).std() * 100
        weekly_df['Volatility_4w'] = weekly_df['Return'].rolling(window=4).std() * 100

        # 创建图表
        fig, axes = plt.subplots(3, 1, figsize=(14, 12))
        fig.suptitle(f'{symbol} 股票波动性分析 ({period})', fontsize=16, fontweight='bold')

        # 图1：价格走势
        ax1 = axes[0]
        ax1.plot(daily_df.index, daily_df['Close'], 'b-', linewidth=1.5, label='收盘价')
        ax1.fill_between(daily_df.index, daily_df['Close'], alpha=0.3)
        ax1.set_ylabel('价格 (USD)')
        ax1.set_title('价格走势')
        ax1.legend()
        ax1.grid(True, alpha=0.3)

        # 图2：日波动率
        ax2 = axes[1]
        ax2.plot(daily_df.index, daily_df['Volatility_5d'], 'r-', linewidth=1.5, label='5日波动率')
        ax2.axhline(y=daily_df['Volatility_5d'].mean(), color='orange', linestyle='--', label=f'均值: {daily_df["Volatility_5d"].mean():.2f}%')
        ax2.set_ylabel('波动率 (%)')
        ax2.set_title('日波动率 (5日滚动)')
        ax2.legend()
        ax2.grid(True, alpha=0.3)

        # 图3：周波动率
        ax3 = axes[2]
        ax3.bar(weekly_df.index, weekly_df['Volatility_4w'], color='green', alpha=0.7, width=5, label='4周波动率')
        ax3.axhline(y=weekly_df['Volatility_4w'].mean(), color='red', linestyle='--', label=f'均值: {weekly_df["Volatility_4w"].mean():.2f}%')
        ax3.set_ylabel('波动率 (%)')
        ax3.set_title('周波动率 (4周滚动)')
        ax3.legend()
        ax3.grid(True, alpha=0.3)

        plt.tight_layout()

        # 保存或返回
        if save_path is None:
            save_path = os.path.join(os.path.dirname(__file__), f"{symbol}_volatility_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
        plt.savefig(save_path, dpi=150, bbox_inches='tight')

    except Exception as e:
        return f"绘图失败: {str(e)}"


# ============== 创建 Agent ==============

model = ChatOpenAI(
    model="qwen-flash",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    api_key="sk-9c6195bf91f7435d88ea4b819073c92c"
)

agent = create_deep_agent(
    model=model,
    tools=[get_stock_data, analyze_buy_sell_timing, plot_stock_volatility],
    system_prompt="""你是一个专业的股票分析师助手。
    功能：
    1. 查询股票数据 - 使用 get_stock_data
    2. 分析买卖时机 - 使用 analyze_buy_sell_timing
    3. 可视化波动 - 使用 plot_stock_volatility
    回答时简洁专业，给出明确的投资建议。"""
)


# ============== 测试示例 ==============

if __name__ == "__main__":
    print("=== 股票分析 Agent 测试 ===\n")

    # 测试1：查询股票数据
    print("【测试1】查询 AAPL 股票数据...")
    result = agent.invoke({
        "messages": [{"role": "user", "content": "查询苹果公司(AAPL)的最近一个月日线数据"}]
    })
    print(f"结果: {result}\n")

    # 测试2：分析买卖时机
    print("【测试2】分析买卖时机...")
    result = agent.invoke({
        "messages": [{"role": "user", "content": "分析特斯拉(TSLA)最近的买卖时机，给出建议"}]
    })
    print(f"结果: {result}\n")

    # 测试3：可视化波动
    print("【测试3】生成波动性图表...")
    result = agent.invoke({
        "messages": [{"role": "user", "content": "绘制英伟达(NVDA)近3个月的日波动和周波动图"}]
    })
    print(f"结果: {result}")