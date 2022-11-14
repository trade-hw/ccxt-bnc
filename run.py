import ccxt
import pprint
import time
import datetime
import pandas as pd
import larry
import math


with open("../api.txt") as f:
    lines = f.readlines()
    api_key = lines[0].strip()
    secret  = lines[1].strip()


binance = ccxt.binance(config={
    'apiKey': api_key,
    'secret': secret,
    'enableRateLimit': True,
    'options': {
        'defaultType': 'future'
    }
})


symbol = "BTC/USDT"  # 코인지정
long_target, short_target, ma5, ma200 = larry.cal_target(binance, symbol)  # 계산식/지표 불러오기
balance = binance.fetch_balance()
usdt = balance['total']['USDT']
timeframe = binance.fetch_ohlcv(symbol)
op_mode = False
position = {
    "type": None,
    "amount": 0
}

''' ( 뭔가 자꾸 오류가 나서 보류. 웹/앱 에서 직접 설정 가능)
# --- 레버리지 구간 ---
markets = binance.load_markets()
symbol = "symbol"
market = binance.market(symbol)
leverage = 5  # 레버리지 설정

resp = binance.fapiPrivate_post_leverage({
    'symbol': market['id'],
    'leverage': leverage
})

order = binance.create_market_buy_order(
    symbol=symbol,
    amount=amount,
)
# --- 레버리지 구간 ---
'''


def cal_amount(usdt_balance, cur_price):
    portion = 0.1
    usdt_trade = usdt_balance * portion
    amount = math.floor((usdt_trade * 1000000)/cur_price) / 1000000
    return amount


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
    ohlcv = binance.fetch_ohlcv(symbol=symbol, timeframe=itv, limit=210)
    df = pd.DataFrame(ohlcv)
    rsi = rsi_calc(df,14).iloc[-1]
    return rsi


def enter_position(exchange, symbol, cur_price, long_target, short_target, amount, position):
    if cur_price > long_target:     # 현재가 > long 목표가
        position['type'] = 'long'
        position['amount'] = amount
        exchange.create_market_buy_order(symbol=symbol, amount=amount)
    elif cur_price < short_target:  # 현재가 < short 목표가
        position['type'] = 'short'
        position['amount'] = amount
        exchange.create_market_sell_order(symbol=symbol, amount=amount)


def exit_position(exchange, symbol, position):
    amount = position['amount']
    if position['type'] == 'long':
        exchange.create_market_sell_order(symbol=symbol, amount=amount)
        position['type'] = None
    elif position['type'] == 'short':
        exchange.create_market_buy_order(symbol=symbol, amount=amount)
        position['type'] = None


while True:
    try:
        now = datetime.datetime.now()
        long_target, short_target, ma5, ma200 = larry.cal_target(binance, symbol)
        balance = binance.fetch_balance()
        usdt = balance['total']['USDT']
        ticker = binance.fetch_ticker(symbol)
        cur_price = ticker['last']  # 현재가격 얻기
        amount = cal_amount(usdt, cur_price)

        #  봉 시작시, 포지션 진입금지
        if now.minute and (0 <= now.second <= 2):
            op_mode = False  # 포지션 진입금지

        # 제한시간 이후, 포지션 진입가능
        if now.minute and (3 <= now.second <= 5):
            op_mode = True  # 포지션 진입가능

        if op_mode and position['type'] is None:
            enter_position(binance, symbol, cur_price, long_target, short_target, amount, position)

        print(f"\n{op_mode}\nRSI 03.45 : {round(rsi_binance(itv='3m'), 2)}\nRSI 60.63 : {round(rsi_binance(itv='1h'), 2)}\n\n현재시간 : {now}\n현재가격 : {cur_price}\n상승진입 : {long_target}\n하락진입 : {short_target}\n보유잔고 : {usdt}\n현재상황 : {position}\n\nㅡ ㅡ ㅡ ㅡ ㅡ\n\n{ma5}\n{ma200}")
        time.sleep(3)
    except:
        print('[ SYSTEM RESET !! ]'
