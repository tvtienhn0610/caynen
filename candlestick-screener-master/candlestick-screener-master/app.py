import os, csv
import talib
import yfinance as yf
import pandas as pd
from flask import Flask, escape, request, render_template
from patterns import candlestick_patterns
from binance.client import Client
from datetime import datetime as dt
from datetime import timedelta as td
import schedule
import time


app = Flask(__name__)


# YOUR API KEYS HERE
api_key = "lmRl0bcG4my9tvoNDdgUCEuFKASmzwEPSUnvl4GIm3OUdNpdloQtGiTZcYioDen8"    #Enter your own API-key here
api_secret = "DgRJaDCnJvx5FJbx1qXbiduBbcLqtXxxjtxl360gC7RJnErlzQ5FnIC6hWa5Ydh3" #Enter your own API-secret here


@app.route('/download')
def snapshot():
    try :
        print("start download file !!!!")

        dir = 'datasets/daily'
        for f in os.listdir(dir):
            os.remove(os.path.join(dir, f))

        bclient = Client(api_key=api_key, api_secret=api_secret)
        
        file1 = open('datasets/symbols.txt', 'r')
        Lines = file1.readlines()
        for line in Lines:
            downloadData(line.strip(),bclient)
        return {
            "code": "success"
        }
    except :
        print("Error !!!!")


def downloadData( symbol , bclient):
    try :
        print("start download data {}".format(symbol))
        today = dt.now()
        dental =td(days=20)
        start_date = today - dental

        print(start_date)

        klines = bclient.get_historical_klines(symbol, Client.KLINE_INTERVAL_1DAY, start_date.strftime("%d %b %Y %H:%M:%S"), today.strftime("%d %b %Y %H:00:00"), 20)
        data = pd.DataFrame(klines, columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_av', 'trades', 'tb_base_av', 'tb_quote_av', 'ignore' ])
        data['timestamp'] = pd.to_datetime(data['timestamp'], unit='ms')

        data.set_index('timestamp', inplace=True)
        data.to_csv('datasets/daily/{}.csv'.format(symbol))
    except :
        print("Error download !!!!")



# def processPandata():
#     try:
#         print("start process pandas")
#         for filename in os.listdir('datasets/daily'):
#             print("start process {}".format(filename))
#             df = pd.read_csv('datasets/daily/{}'.format(filename))
#             df = ta.cdl_pattern

#     except :
#         print("Error process pandas")




@app.route('/')
def index():
    pattern  = request.args.get('pattern', False)
    stocks = {}

    print(pattern)
    file1 = open('datasets/symbols.txt', 'r')
    Lines = file1.readlines()
    count = 0
    for line in Lines:
        count += 1
        stocks[line.strip()] = {'company': line.strip()}


    if pattern:
        for filename in os.listdir('datasets/daily'):
            df = pd.read_csv('datasets/daily/{}'.format(filename))
            pattern_function = getattr(talib, pattern)
            symbol = filename.split('.')[0].strip()

            try:
                results = pattern_function(df['open'], df['high'], df['low'], df['close'])
                last = results.tail(1).values[0]

                if last > 0:
                    stocks[symbol][pattern] = 'bullish'
                elif last < 0:
                    stocks[symbol][pattern] = 'bearish'
                else:
                    stocks[symbol][pattern] = None
    
            except Exception as e:
                print('failed on filename: ', filename)
 

    return render_template('index.html', candlestick_patterns=candlestick_patterns, stocks=stocks, pattern=pattern)

class Symbol:
    def __init__(self, name, pattern , last , result):
        self.name = name
        self.pattern = pattern
        self.last = last
        self.result = result


@app.route('/home')
def index2():
    listdata = []
    listSymbol = []
    for pattern in candlestick_patterns:
    
        print(pattern)
        # file1 = open('datasets/symbols.txt', 'r')
        # Lines = file1.readlines()
        # for line in Lines:
        #     stocks[line.strip()] = {'company': line.strip()}


        if pattern:
            for filename in os.listdir('datasets/daily'):
                df = pd.read_csv('datasets/daily/{}'.format(filename))
                pattern_function = getattr(talib, pattern)
                symbol = filename.split('.')[0].strip()

                try:
                    results = pattern_function(df['open'], df['high'], df['low'], df['close'])
                    last = results.tail(1).values[0]

                    if last > 0:
                        x = Symbol(symbol,pattern,last,"bullish")
                        y = listSymbol.count(symbol)
                        if y == 0 :
                            listSymbol.append(symbol)
                            listdata.append(x)
                            
                    elif last < 0:
                        x = Symbol(symbol,pattern,last,"bearish")
                        y = listSymbol.count(symbol)
                        if y == 0 :
                            listSymbol.append(symbol)
                            listdata.append(x)

                except Exception as e:
                    print('failed on filename: ', filename)

    # print(len(listdata))

    return render_template('index.html', listdata=listdata)


schedule.every().day.at("00:01").do(snapshot)


while True:
    schedule.run_pending()
    time.sleep(1)
