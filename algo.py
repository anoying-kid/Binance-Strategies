from binance.client import Client
from key import api_key, api_secret, TOKEN
from time import sleep
import pandas as pd
import telebot

def get_data(limit):

    # parameters
    params = {
        'pair':'ETHUSDT',
        'contractType':'PERPETUAL',
        'interval':'30m',
        'limit':limit
    }

    # getting kline data
    candles = client.futures_continous_klines(**params)
    return candles

def get_frames():

    # getting data
    frame = pd.DataFrame(get_data(680))

    # cleaning data
    frame = frame.iloc[:,:6]

    # naming the columns
    frame.columns = ['Time', 'Open', 'High', 'Low', 'Close', 'Volume']

    # Typecasting the value to float
    frame[['Open', 'High', 'Low', 'Close','Volume']] = frame[['Open', 'High', 'Low', 'Close','Volume']].astype(float)

    # epoch to datetime
    frame.Time = pd.to_datetime(frame.Time, unit='ms')

    # getting ema in data
    frame['ema'] = frame.Close.ewm(span=200, adjust=False).mean()
    return frame

def cancel_active_orders(client):

    # checking last order
    last_order = client.futures_get_all_orders(symbol='ETHUSDT')[0]

    # getting size of last order
    size = float(last_order['origQty'])

    # trying buying and selling (easy to handle rather than finding if there are any trades or not)
    try:
        client.futures_create_order(symbol='ETHUSDT', side='BUY', type='MARKET', quantity=size, reduceOnly='true')
    except:
        try:
            client.futures_create_order(symbol='ETHUSDT', side='SELL', type='MARKET', quantity=size, reduceOnly='true')
        except:
            print("No active trades.")

def placingOrder(client, side):

    # cancel active orders if theirs any
    cancel_active_orders(client)

    # Getting usdt balance
    acc_balance = float(client.futures_account_balance()[6]['balance'])

    # Getting current eth price
    curr_price = float(client.get_symbol_ticker(symbol='ETHUSDT')['price'])

    # quantity
    quantity = float(f'{18*(acc_balance/curr_price):.3f}')

    # creating buy/sell order
    client.futures_create_order(symbol='ETHUSDT', side=side, type='MARKET', quantity= quantity)

if __name__ == '__main__':
    # authorizing
    client = Client(api_key, api_secret)
    print("logged in!\n")

    bot = telebot.TeleBot(TOKEN)

    # getting data
    data = get_frames()

    # conditions
    buy = data['Open'][678]<data['ema'][678] and data['Open'][679]>data['ema'][679]
    sell = data['Open'][678]>data['ema'][678] and data['Open'][679]<data['ema'][679]

    # applying conditions
    print(f"Time:{data['Time'][679]}")
    if buy:
        print("buy : {data['Time'][679]}")
        placingOrder(client, 'BUY')
        bot.send_message(1031729548, f"buy : {data['Time'][679]}")
    elif sell:
        print(f"sell: {data['Time'][679]}")
        placingOrder(client, 'SELL')
        bot.send_message(1031729548, f"sell : {data['Time'][679]}")
    else:
        if (data['Open'][678]>data['ema'][678] and data['Open'][679]>data['ema'][679]):
            print("Candle is above ema")
        else:
            print("Candle is below ema")
        print(f"open previous:{data['Open'][678]} open:{data['Open'][679]}\nema previous:{data['ema'][678]} ema:{data['ema'][679]}")
        client.close_connection()