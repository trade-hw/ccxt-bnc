import pandas as pd


# 롱숏 진입 계산
def cal_target(exchange, symbol):  # 심볼에 대한 ohlcv (지정시간)캔들 데이터 얻기
    data = exchange.fetch_ohlcv(
        symbol=symbol,
        timeframe='3m',  # 지정시간
        since=None,
    )  #  limit=10  # 리밋을 추가하여 갯수제한적 데이터 추출가능
    
    # 위 (지정시간)캔들 데이터를, 데이터프레임 객체로 변환
    df = pd.DataFrame(data=data, columns=['datetime', 'open', 'high', 'low', 'close', 'volume'])
    df['datetime'] = pd.to_datetime(df['datetime'], unit='ms')
    df.set_index('datetime', inplace=True)
    
    #  MA 이동평균선 구하기
    ma5 = df['close'].rolling(5).mean()
    ma200 = df['close'].rolling(200).mean()
    
    # 이전 / 현재 데이터로 목표가 계산
    yesterday = df.iloc[-2]  # 이전
    today = df.iloc[-1]  # 현재
    
    #  롱 / 숏 목표가 구하기
    long_target = today['open'] + (yesterday['high'] - yesterday['low']) * 0.1
    short_target = today['open'] - (yesterday['high'] - yesterday['low']) * 0.1
    
    return long_target, short_target, ma5[-1], ma200[-1]
