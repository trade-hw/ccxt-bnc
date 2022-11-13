import pandas as pd


#  RSI 구하기
def rsi_calc(ohlc: pd.DataFrame, period: int = 14):
    ohlc = ohlc[4].astype(float)
    delta = ohlc.diff()
    gains, declines = delta.copy(), delta.copy()
    gains[gains < 0] = 0
    declines[declines > 0] = 0

    _gain = gains.ewm(com=(period-1), min_periods=period).mean()
    _loss = declines.abs().ewm(com=(period-1), min_periods=period).mean()

    RS = _gain / _loss
    return pd.Series(100-(100/(1+RS)), name="RSI")

def rsi_binance(itv='1h', symbol=symbol):
    binance = ccxt.binance()
    ohlcv = binance.fetch_ohlcv(symbol=symbol, timeframe=itv, limit=200)
    df = pd.DataFrame(ohlcv)
    rsi = rsi_calc(df,14).iloc[-1]
    return rsi


# volatility breakout
def cal_target(exchange, symbol):
    btc = exchange.fetch_ohlcv(
        symbol=symbol,
        timeframe='3m',
        since=None,
        limit=10
    )
    
    df = pd.DataFrame(data=btc, columns=['datetime', 'open', 'high', 'low', 'close', 'volume'])
    df['datetime'] = pd.to_datetime(df['datetime'], unit='ms')
    df.set_index('datetime', inplace=True)
    
    #  MA 이동평균선 구하기
    ma5 = df['close'].rolling(5).mean()
    ma200 = df['close'].rolling(200).mean()
    
    yesterday = df.iloc[-2]
    today = df.iloc[-1]
    
    #  롱숏 타겟 구하기
    long_target = today['open'] + (yesterday['high'] - yesterday['low']) * 0.1
    short_target = today['open'] - (yesterday['high'] - yesterday['low']) * 0.1
    
    return long_target, short_target, ma5[-1], ma200[-1]
