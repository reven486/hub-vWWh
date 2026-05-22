"""股票可视化与买卖时机分析。

- A 股（6 位数字代码）走 akshare
- 美股/港股（含字母的 ticker）走 yfinance
- 在同一张图绘制：收盘价 + 日波动率 + 周波动率 + 买卖信号
- 基于"局部极值 + 波动阈值"推荐最佳买卖点
"""
import argparse
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False


# ---------- 数据获取 ----------

def is_a_share(symbol: str) -> bool:
    return bool(re.fullmatch(r"\d{6}", symbol))


def fetch_a_share(symbol: str, start: str, end: str) -> pd.DataFrame:
    import akshare as ak

    df = ak.stock_zh_a_hist(
        symbol=symbol, period="daily", start_date=start, end_date=end, adjust="qfq"
    )
    if df.empty:
        raise RuntimeError(f"akshare 未返回数据：{symbol} {start}-{end}")
    df = df.rename(
        columns={"日期": "date", "开盘": "open", "收盘": "close", "最高": "high", "最低": "low"}
    )
    df["date"] = pd.to_datetime(df["date"])
    df = df.set_index("date").sort_index()
    return df[["open", "high", "low", "close"]]


def fetch_global(symbol: str, start: str, end: str) -> pd.DataFrame:
    import yfinance as yf

    start_iso = f"{start[:4]}-{start[4:6]}-{start[6:8]}"
    end_iso = f"{end[:4]}-{end[4:6]}-{end[6:8]}"
    df = yf.download(symbol, start=start_iso, end=end_iso, progress=False, auto_adjust=True)
    if df.empty:
        raise RuntimeError(f"yfinance 未返回数据：{symbol} {start}-{end}")
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df = df.rename(columns={"Open": "open", "High": "high", "Low": "low", "Close": "close"})
    df.index = pd.to_datetime(df.index)
    return df[["open", "high", "low", "close"]]


def fetch(symbol: str, start: str, end: str) -> pd.DataFrame:
    if is_a_share(symbol):
        print(f"[数据源] akshare（A 股 {symbol}）")
        return fetch_a_share(symbol, start, end)
    print(f"[数据源] yfinance（{symbol}）")
    return fetch_global(symbol, start, end)


# ---------- 波动率 ----------

def daily_fluctuation(df: pd.DataFrame) -> pd.Series:
    return (df["high"] - df["low"]) / df["close"] * 100


def weekly_fluctuation(df: pd.DataFrame) -> pd.Series:
    weekly = df.resample("W").agg({"high": "max", "low": "min", "close": "last"}).dropna()
    return (weekly["high"] - weekly["low"]) / weekly["close"] * 100


# ---------- 信号 ----------

def local_extremes(price: pd.Series, window: int = 10):
    win = 2 * window + 1
    rolling_min = price.rolling(win, center=True, min_periods=1).min()
    rolling_max = price.rolling(win, center=True, min_periods=1).max()
    lows = price.index[(price == rolling_min)]
    highs = price.index[(price == rolling_max)]
    return lows, highs


def recommend(df: pd.DataFrame, daily: pd.Series):
    price = df["close"]
    threshold = daily.quantile(0.75)
    lows, highs = local_extremes(price)

    buy_cand = [d for d in lows if daily.loc[d] >= threshold]
    sell_cand = [d for d in highs if daily.loc[d] >= threshold]

    best_buy = min(buy_cand, key=lambda d: price.loc[d]) if buy_cand else price.idxmin()

    after = [d for d in sell_cand if d > best_buy]
    if after:
        best_sell = max(after, key=lambda d: price.loc[d])
    else:
        tail = price[price.index > best_buy]
        best_sell = tail.idxmax() if not tail.empty else None

    return {
        "best_buy": best_buy,
        "best_sell": best_sell,
        "buy_candidates": buy_cand,
        "sell_candidates": sell_cand,
        "threshold": threshold,
    }


# ---------- 绘图 ----------

def plot(df, daily, weekly, signals, symbol, output_path):
    fig, ax1 = plt.subplots(figsize=(14, 7))
    price = df["close"]

    ax1.plot(price.index, price, color="#1f77b4", lw=1.6, label="收盘价", zorder=3)
    ax1.set_xlabel("日期")
    ax1.set_ylabel("价格", color="#1f77b4")
    ax1.tick_params(axis="y", labelcolor="#1f77b4")

    if signals["buy_candidates"]:
        ax1.scatter(
            signals["buy_candidates"],
            price.loc[signals["buy_candidates"]],
            marker="^", s=70, color="#2ca02c", alpha=0.6, label="候选买入", zorder=4,
        )
    if signals["sell_candidates"]:
        ax1.scatter(
            signals["sell_candidates"],
            price.loc[signals["sell_candidates"]],
            marker="v", s=70, color="#d62728", alpha=0.6, label="候选卖出", zorder=4,
        )

    bb, bs = signals["best_buy"], signals["best_sell"]
    if bb is not None:
        ax1.scatter([bb], [price.loc[bb]], marker="^", s=220, color="#2ca02c",
                    edgecolors="black", linewidths=1.5, label="最佳买入", zorder=5)
        ax1.annotate(
            f"买入\n{bb.strftime('%Y-%m-%d')}\n{price.loc[bb]:.2f}",
            xy=(bb, price.loc[bb]), xytext=(15, -40), textcoords="offset points",
            fontsize=10, color="#2ca02c", fontweight="bold",
            arrowprops=dict(arrowstyle="->", color="#2ca02c"),
        )
    if bs is not None:
        ax1.scatter([bs], [price.loc[bs]], marker="v", s=220, color="#d62728",
                    edgecolors="black", linewidths=1.5, label="最佳卖出", zorder=5)
        ax1.annotate(
            f"卖出\n{bs.strftime('%Y-%m-%d')}\n{price.loc[bs]:.2f}",
            xy=(bs, price.loc[bs]), xytext=(15, 30), textcoords="offset points",
            fontsize=10, color="#d62728", fontweight="bold",
            arrowprops=dict(arrowstyle="->", color="#d62728"),
        )

    ax2 = ax1.twinx()
    ax2.bar(daily.index, daily.values, width=1.0, color="gray", alpha=0.25,
            label="日波动率 (%)", zorder=1)
    ax2.plot(weekly.index, weekly.values, color="#ff7f0e", lw=2.0,
             label="周波动率 (%)", zorder=2)
    ax2.set_ylabel("波动率 (%)", color="gray")
    ax2.tick_params(axis="y", labelcolor="gray")
    ax2.set_ylim(0, max(daily.max(), weekly.max()) * 2.2)  # 压缩到下半区，避免遮挡价格

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left", framealpha=0.9)

    plt.title(f"{symbol} 走势分析（收盘价 + 日/周波动率 + 买卖信号）", fontsize=14, pad=12)
    fig.tight_layout()
    plt.savefig(output_path, dpi=120, bbox_inches="tight")
    plt.close()


# ---------- 主入口 ----------

def main():
    parser = argparse.ArgumentParser(description="股票走势可视化 + 买卖时机建议")
    parser.add_argument("symbol", help="A 股 6 位代码 或 美/港股 ticker")
    parser.add_argument("--start", default=None, help="开始日期 YYYYMMDD（默认一年前）")
    parser.add_argument("--end", default=None, help="结束日期 YYYYMMDD（默认今天）")
    parser.add_argument("--output", default="stock_analysis.png", help="输出图片路径")
    args = parser.parse_args()

    end = args.end or datetime.now().strftime("%Y%m%d")
    start = args.start or (datetime.now() - timedelta(days=365)).strftime("%Y%m%d")

    df = fetch(args.symbol, start, end)
    print(f"[数据] {len(df)} 条，{df.index.min().date()} 至 {df.index.max().date()}")

    daily = daily_fluctuation(df)
    weekly = weekly_fluctuation(df)
    signals = recommend(df, daily)

    print("\n=== 买卖建议 ===")
    bb, bs = signals["best_buy"], signals["best_sell"]
    print(f"波动阈值（日波动 75% 分位）：{signals['threshold']:.2f}%")
    if bb is not None:
        print(f"最佳买入：{bb.strftime('%Y-%m-%d')}  价格 {df['close'].loc[bb]:.2f}  "
              f"当日波动 {daily.loc[bb]:.2f}%")
    if bs is not None:
        gain = (df["close"].loc[bs] - df["close"].loc[bb]) / df["close"].loc[bb] * 100
        print(f"最佳卖出：{bs.strftime('%Y-%m-%d')}  价格 {df['close'].loc[bs]:.2f}  "
              f"当日波动 {daily.loc[bs]:.2f}%")
        print(f"潜在收益：{gain:+.2f}%")

    print(f"\n日波动 均值 {daily.mean():.2f}% / 最大 {daily.max():.2f}%")
    print(f"周波动 均值 {weekly.mean():.2f}% / 最大 {weekly.max():.2f}%")

    output = Path(args.output).resolve()
    plot(df, daily, weekly, signals, args.symbol, output)
    print(f"\n图表已保存：{output}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[错误] {e}", file=sys.stderr)
        sys.exit(1)
