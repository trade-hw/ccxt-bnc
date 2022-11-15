import ccxt
import pprint
import time
import datetime
import pandas as pd
import larry
import math


with open("api.txt") as f:
    lines = f.readlines()
    api_key = lines[0].strip()
    secret  = lines[1].strip()

# 바이낸스 객체 생성
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
usdt_check = usdt  # 보유 달러 체크 주문명
timeframe = binance.fetch_ohlcv(symbol)  # 캔들 시간봉 명칭
op_mode = False  # 봇 시작기 기본 상태 (포지션 조건 맞으면 자동 트루)
position = {
    "type": None,
    "amount": 0
}


# 프로그램 시작시 usdt 머니 check !!
if usdt_check < 5:  # 최소 5달러 이상 있어야할것!
    usdtck = False
else:
    usdtck = True


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
    ohlcv = binance.fetch_ohlcv(symbol=symbol, timeframe=itv, limit=200)
    df = pd.DataFrame(ohlcv)
    rsi = rsi_calc(df,14).iloc[-1]
    return rsi


# 포지션 진입
def enter_position(exchange, symbol, cur_price, long_target, short_target, amount, position):
    if cur_price > long_target:     # 현재가 > long 목표가 (추가조건 작성필요)
        position['type'] = 'long'
        position['amount'] = amount
        exchange.create_market_buy_order(symbol=symbol, amount=amount)
    elif cur_price < short_target:  # 현재가 < short 목표가 (추가조건 작성필요)
        position['type'] = 'short'
        position['amount'] = amount
        exchange.create_market_sell_order(symbol=symbol, amount=amount)


# 시장 상황이 반대일때, 포지션 반대매매
def reverse_position(exchange, symbol, cur_price, long_target, short_target, position):
    amount = position['amount']
    if position['type'] == 'long' and cur_price < long_target:     # 현재가 < long 목표가 (추가조건 작성필요)
        exchange.create_market_sell_order(symbol=symbol, amount=amount)
        position['type'] = None
    elif position['type'] == 'short' and cur_price > short_target:  # 현재가 > short 목표가 (추가조건 작성필요)
        exchange.create_market_buy_order(symbol=symbol, amount=amount)
        position['type'] = None


while True:
    try:
        now = datetime.datetime.now()
        long_target, short_target, ma5, ma200 = larry.cal_target(binance, symbol)
        balance = binance.fetch_balance()
        usdt = balance['total']['USDT']
        usdt_check = usdt
        ticker = binance.fetch_ticker(symbol)
        cur_price = ticker['last']  # 현재가격 얻기
        amount = cal_amount(usdt, cur_price)
        amount_check = amount  # amount 포지션 수량 체크 


        # 프로그램 시작시 usdt 머니 check !!
        if usdt_check < 5:  # 최소 5달러 이상 있어야할것!
            usdtck = False
        else:
            usdtck = True

        # 프로그램 시작시 amount 수량 check !!
        if amount_check < 1:  # 최소 1수량 이상 있어야할것!
            amountck = False
        else:
            amountck = True

        # 시장현황 분석 후, 반대조건 충족시 매도실행
        if op_mode and amountck is True:
            if position['type'] == 'long' or position['type'] == 'short':
                reverse_position(exchange, symbol, cur_price, long_target, short_target, position)
                op_mode = False

        # 봉 시작시, 포지션 진입금지
        if now.minute and (0 <= now.second <= 3):
            op_mode = False  # 포지션 진입금지

        # 제한시간 이후, 포지션 진입가능
        if now.minute and (3 <= now.second <= 6):
            op_mode = True  # 포지션 진입가능

        # 포지션 목표가 / 롱숏 조건 확인 후 진입시도
        if op_mode and position['type'] is None:
            enter_position(binance, symbol, cur_price, long_target, short_target, amount, position)

        print(f"\n* 현재시간 :  {now.hour}:{now.minute}:{now.second} * *\n* 실행상태 :  {op_mode}\n - - - - - - - - - -\n▲ 상승진입 :  {round(long_target)}\n= 현재가격 :  {round(cur_price)}\n▼ 하락진입 :  {round(short_target)}\n\n♨ 보유잔고 :  {usdtck}  ＄{round(usdt)}\n♨ 현재상황 :  {position} {amountck}\n\n* RSI 60.63 :  {round(rsi_binance(itv='1h'), 2)}\n* RSI 03.45 :  {round(rsi_binance(itv='3m'), 2)}\n\n / / / / / / / /")
        time.sleep(3)
    except:
        print('[ SYSTEM RESET !! ]')
