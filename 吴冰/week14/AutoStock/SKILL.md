---
name: 股票信息查询
description: 查询第三方接口：https://api.autostock.cn 查询股票、指数、板块等信息
---

# 接口查询内容
### 1. 基础数据查询
- get_all_stock_code - 查询所有股票，支持代码/名称模糊搜索
- get_all_index_code - 查询所有指数
- get_stock_industry_code - 获取板块数据
- get_board_info - 获取大盘数据
- get_stock_info - 获取单只股票基础信息
### 2. 行情数据
- get_stock_rank - 股票排行（支持分页、排序、按行业筛选）
- get_stock_minute_data - 分时数据
### 3. K线数据
- get_month_line - 月K线数据
- get_week_line - 周K线数据
- get_day_line - 日K线数据

# 股票分析方法

### 1. 趋势分析
- **移动平均线 (SMA/EMA)** - 计算简单/指数移动平均线，判断价格趋势方向
- **均线多头排列** - 短期均线在长期均线上方，表明上涨趋势
- **均线空头排列** - 短期均线在长期均线下方，表明下跌趋势

### 2. 动量分析
- **MACD** - 指数平滑异同移动平均线，判断趋势强度和反转点
- **RSI** - 相对强弱指数，衡量价格变动的速度和幅度（0-100）
- **KDJ** - 随机指标，判断超买超卖状态

### 3. 波动性分析
- **布林带 (Bollinger Bands)** - 中轨为N日均线，上下轨为中轨±2倍标准差
- **ATR** - 平均真实波幅，衡量价格波动程度

### 4. 成交量分析
- **量价配合** - 上涨时放量、下跌时缩量，视为健康走势
- **量价背离** - 价格创新高但成交量萎缩，可能预示趋势反转
- **堆量分析** - 成交量逐步放大，可能有主力资金进场

### 5. 支撑压力分析
- **前期高点/低点** - 历史价格形成的支撑位和压力位
- **筹码分布** - 分析不同价格区间的持仓成本分布

### 6. 趋势线分析
- **上升趋势线** - 连接逐步抬高的低点形成的直线
- **下降趋势线** - 连接逐步降低的高点形成的直线
- **通道线** - 趋势线的平行线，形成价格运行通道

### 7. 形态分析
- **头肩顶/底** - 反转形态，预示趋势即将改变
- **双重顶/底** - M顶或W底形态
- **旗形整理** - 短暂整理后延续原趋势

---

## 分析方法选择建议

| 场景 | 推荐方法 |
|------|---------|
| 判断趋势方向 | SMA/EMA、趋势线 |
| 判断超买超卖 | RSI、KDJ、布林带 |
| 寻找买卖点 | MACD、量价配合 |
| 衡量波动风险 | ATR、布林带 |
| 确认趋势反转 | 背离、形态分析 |

---

## 使用示例

```
分析目标：贵州茅台(600519)
分析方法：日K线 + MA5/MA20/MA60 + RSI + MACD
分析周期：最近60个交易日
```


# 调用方法
```python

TOKEN = "zgaLG8unUPr"

import requests  # type: ignore
from typing import Annotated
from typing import Optional, Dict
import traceback
from fastapi import FastAPI, APIRouter  # type: ignore

app = FastAPI(
    name="Stock api Server",
    instructions="""This server provides stock basic tools.""",
)

# path get_stock_code http服务的路径
# operation_id get_stock_code mcp服务的名字
@app.get("/get_stock_code", operation_id="get_stock_codes")
async def get_all_stock_code(
        keyword: Annotated[Optional[str], "支持代码和名称模糊查询"] = None
) -> Dict:
    """所有股票，支持代码和名称模糊查询"""
    url = "https://api.autostock.cn/v1/stock/all" + "?token=" + TOKEN
    if keyword:
        url += "&keyWord=" + keyword

    payload = {}  # type: ignore
    headers = {}  # type: ignore
    try:
        response = requests.request("GET", url, headers=headers, data=payload, timeout=10)
        return response.json()
    except Exception:
        print(traceback.format_exc())
        return {}

@app.get("/get_index_code", operation_id="get_index_code")
async def get_all_index_code():
    """所有指数，支持代码和名称模糊查询"""
    url = "https://api.autostock.cn/v1/stock/index/all" + "?token=" + TOKEN
    payload = {}
    headers = {}

    try:
        response = requests.request("GET", url, headers=headers, data=payload, timeout=5)
        return response.json()
    except Exception as e:
        print(traceback.format_exc())
        return {}

@app.get("/get_industry_code", operation_id="get_industry_code")
async def get_stock_industry_code():
    """获取板块数据"""
    url = "https://api.autostock.cn/v1/stock/industry/rank" + "?token=" + TOKEN
    payload = {}
    headers = {}

    try:
        response = requests.request("GET", url, headers=headers, data=payload, timeout=5)
        return response.json()
    except Exception as e:
        print(traceback.format_exc())
        return {}

@app.get("/get_board_info", operation_id="get_board_info")
async def get_stock_board_info():
    """获取大盘数据"""
    url = "https://api.autostock.cn/v1/stock/board" + "?token=" + TOKEN
    payload = {}
    headers = {}

    try:
        response = requests.request("GET", url, headers=headers, data=payload, timeout=5)
        return response.json()
    except Exception as e:
        print(traceback.format_exc())
        return {}

@app.get("/get_stock_rank", operation_id="get_stock_rank")
async def get_stock_rank(
        node: Annotated[str, "股票市场/板块代码: {'a','b','ash','asz','bsh','bsz'} a(沪深A股)"],
        industryCode: Annotated[Optional[str], "行业代码，可选"] = None,
        pageIndex: Annotated[int, "页码"] = 1,
        pageSize: Annotated[int, "每页大小"] = 100,
        sort: Annotated[str, "排序字段: price,priceChange,pricePercent,buy,sell,open,close,high,low,volume,turnover 默认price(交易价格)。"] = "price",
        asc: Annotated[int, "排序方式: 0=降序(默认), 1=升序"] = 0
) -> Dict:
    """股票排行"""
    url = "https://api.autostock.cn/v1/stock/rank" + "?token=" + TOKEN
    headers = {}  # type: ignore

    try:
        payload = {
            "node": node,
            "industryCode": industryCode,
            "pageIndex": pageIndex,
            "pageSize": pageSize,
            "sort": sort,
            "asc": asc
        }
        response = requests.request("POST", url, headers=headers, json=payload, timeout=5)
        return response.json()
    except Exception as e:
        print(traceback.format_exc())
        return {}

@app.get("/get_month_line", operation_id="get_month_line")
async def get_stock_month_kline(
        code: Annotated[str, "股票代码"],
        startDate: Annotated[Optional[str], "开始时间(非必填)"] = None,
        endDate: Annotated[Optional[str], "结束时间(非必填)"] = None,
        type: Annotated[int, "0不复权,1前复权,2后复权"] = 0
) -> Dict:
    """月k"""
    url = "https://api.autostock.cn/v1/stock/kline/month" + "?token=" + TOKEN

    headers = {}  # type: ignore
    try:
        payload = {
            "code": code,
            "startDate": startDate,
            "endDate": endDate,
            "type": type
        }
        response = requests.request("GET", url, headers=headers, params=payload, timeout=10)
        return response.json()
    except Exception:
        print(traceback.format_exc())
        return {}

@app.get("/get_week_line", operation_id="get_week_line")
async def get_stock_week_kline(
        code: Annotated[str, "股票代码"],
        startDate: Annotated[Optional[str], "开始时间(非必填)"] = None,
        endDate: Annotated[Optional[str], "结束时间(非必填)"] = None,
        type: Annotated[int, "0不复权,1前复权,2后复权"] = 0
):
    """周k"""
    url = "https://api.autostock.cn/v1/stock/kline/week" + "?token=" + TOKEN

    headers = {}  # type: ignore
    try:
        payload = {
            "code": code,
            "startDate": startDate,
            "endDate": endDate,
            "type": type
        }
        response = requests.request("GET", url, headers=headers, params=payload, timeout=10)
        return response.json()
    except Exception:
        print(traceback.format_exc())
        return {}

@app.get("/get_day_line", operation_id="get_day_line")
async def get_stock_day_kline(
        code: Annotated[str, "股票代码"],
        startDate: Annotated[Optional[str], "开始时间(非必填)"] = None,
        endDate: Annotated[Optional[str], "结束时间(非必填)"] = None,
        type: Annotated[int, "0不复权,1前复权,2后复权"] = 0
) -> Dict:
    """日k"""
    url = "https://api.autostock.cn/v1/stock/kline/day" + "?token=" + TOKEN

    headers = {}  # type: ignore
    try:
        payload = {
            "code": code,
            "startDate": startDate,
            "endDate": endDate,
            "type": type
        }
        response = requests.request("GET", url, headers=headers, params=payload, timeout=10)
        return response.json()
    except Exception:
        print(traceback.format_exc())
        return {}

@app.get("/get_stock_info", operation_id="get_stock_info")
async def get_stock_info(code: Annotated[str, "股票代码"]) -> Dict:
    """股票基础信息"""
    url = "https://api.autostock.cn/v1/stock" + "?token=" + TOKEN + "&code=" + code

    payload = {}  # type: ignore
    headers = {}  # type: ignore
    try:
        response = requests.request("GET", url, headers=headers, data=payload, timeout=10)
        return response.json()
    except Exception:
        print(traceback.format_exc())
        return {}

@app.get("/get_stock_minute_data", operation_id="get_stock_minute_data")
async def get_stock_minute_data(code: str):
    """分时信息"""
    url = "https://api.autostock.cn/v1/stock/min" + "?token=" + TOKEN + "&code=" + code

    payload = {}  # type: ignore
    headers = {}  # type: ignore
    try:
        response = requests.request("GET", url, headers=headers, data=payload, timeout=10)
        return response.json()
    except Exception:
        print(traceback.format_exc())
        return {}


```
