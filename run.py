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
long_target, short_target = larry.cal_target(binance, symbol)  # 계산식/지표 불러오기
balance = binance.fetch_balance()
usdt = balance['total']['USDT']
op_mode = False
position = {
    "type": None,
    "amount": 0
}

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


def cal_amount(usdt_balance, cur_price):
    portion = 0.1
    usdt_trade = usdt_balance * portion
    amount = math.floor((usdt_trade * 1000000)/cur_price) / 1000000
    return amount


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
    now = datetime.datetime.now()
    long_target, short_target = larry.cal_target(binance, symbol)
    balance = binance.fetch_balance()
    usdt = balance['total']['USDT']
    ticker = binance.fetch_ticker(symbol)
    cur_price = ticker['last']  # 현재가격 얻기
    amount = cal_amount(usdt, cur_price)
    
    #  봉 시작시, 포지션 진입금지
    if (now.minute % timeframe == 0) and (1 <= now.second <= 2):
        op_mode = False  # 포지션 진입금지

    # 제한시간 이후, 포지션 진입가능
    if (now.minute % timeframe == 3) and (4 <= now.second <= 5):
        op_mode = True  # 포지션 진입가능

    if op_mode and position['type'] is None:
        enter_position(binance, symbol, cur_price, long_target, short_target, amount, position)

    print(now, cur_price)
    time.sleep(1)
