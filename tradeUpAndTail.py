import matplotlib.pyplot as plt
import matplotlib.patches as patches
import math 
from os import system
import sys, os
from pandas.core.indexes.base import Index
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
import requests
import pandas as pd
import time
import pyupbit
import numpy as np
import datetime
from bs4 import BeautifulSoup
import threading
import common as jun

#   거래금액
iBuyPrice = 7000

#   9시(가장 변동이 심함) 매입
def_9Buy = 5
def_9Plus = 50
def_9Minus = 10
#   9시 이후의 매입
def_1Buy = 5
def_1Plus = 50
def_1Minus = 10
 #   물타기 시점
def_DelPer = 10


sleepTime = 0.2

arDf = pd.DataFrame(columns = ['time' , 'ticker'])
id = "jun"
pw = "wnsco11"

upbit = jun.jun_LoginUpbit(id ,pw)

arTickers = []
arDelTickers = []

def jun_get_ticker_KRW():
    tickers = pyupbit.get_tickers("KRW")
    delTicker = ["KRW-EMC2"]
    renTicker = list(set(tickers) - set(delTicker))
    return renTicker

def Sell():
    iBuyPer = def_1Buy
    ipGap = def_1Plus
    iMinus = def_1Minus
    try:
        arTicer = []
        time.sleep(sleepTime)
        balances = upbit.get_balances()
        HavePrice = 0
        for b in balances:
            
            if b['currency'] == "KRW":
                HavePrice = float(b['balance'])
                continue        
            
            if (float(b['balance']) + float(b['locked'])) * float(b['avg_buy_price']) < 5000.0:
                continue            

            tabkerName = "KRW-" + b['currency']
            arTicer.append(tabkerName)
            time.sleep(sleepTime)
            now = datetime.datetime.now()

            # df = pyupbit.get_ohlcv(tabkerName, count=1)
            df = pyupbit.get_ohlcv(tabkerName, interval="minute60", count=1)

            if len(df) < 1:
                continue
            eTime = df.index[0] +  datetime.timedelta(days=1) - datetime.timedelta(minutes=10)
            sellEndTime = df.index[0] +  datetime.timedelta(days=1)
                        
            mDb = jun.SelectMyTicker(id, tabkerName)
            if len(mDb) < 1:
                jun.DeleteMyTicker(id,tabkerName)
                continue
            myPer = float(mDb[0]['buyper'])
            myPrice = float(b['avg_buy_price'])
            
            if float(mDb[0]['openprice']) > 0:
                myPrice = float(mDb[0]['openprice'])
            else:
                jun.InsertMyTicker_Open(id, tabkerName, now, myPrice, 1)

            dfData = df.iloc[0]
            nowPer = (100 - float(dfData['close']) / float(b['avg_buy_price']) * 100)
            InsertPer = int(nowPer / def_DelPer) + 1
                            

            # if InsertPer > myPer:
            #     jun.InsertMyTicker_Open(id, tabkerName, now, myPrice, int(InsertPer))

            if True:
            # if now < eTime:
                time.sleep(sleepTime)
                oders = upbit.get_order(tabkerName)
                
                for oder in oders:
                    upbit.cancel_order(oder['uuid'])
                    time.sleep(sleepTime)
                dBuy  = float(b['avg_buy_price'])
                
                # ipGap = def_9Plus
                # iMinus = def_9Minus
                if now.time == 9:
                    ipGap = def_9Plus
                    iMinus = def_9Minus
                else:
                    ipGap = def_1Plus
                    iMinus = def_1Minus
                
                dm = dBuy - dBuy * 0.01 * float(iMinus)
                dp = dBuy + dBuy * 0.01 * float(ipGap)


                print(dm < float(dfData['close'])
                
                if dp < float(dfData['close']) or eTime < sellEndTime or dm < float(dfData['close']):
                    bSel = True
                    # if now.time == 9:
                    #     if float(dfData['open']) < float(dfData['close']):
                    #         bSel = False
                    # if bSel:
                    if float(dfData['open']) < float(dfData['close']):
                        odr = upbit.sell_market_order(tabkerName, b['balance'])
                        # odr = upbit.sell_limit_order(tabkerName, dfData['close'] ,b['balance'])
                        time.sleep(sleepTime)
                        if 'error' in odr:
                                print(odr)
                        else:
                            jun.DeleteMyTicker(id,tabkerName)
                            arTicer.remove(tabkerName)
                            now = datetime.datetime.now()
                            print(str(now) + "  ) " + "Sell GOOD IS " + tabkerName)
                #   추가매수
                # if nowPer > def_DelPer:
                #     InsertPer = myPer + int(nowPer / def_DelPer)
                #     if True:
                #     # if InsertPer > myPer:
                #         # if dfData['close'] > dfData['open']:                        
                #         buyPrice = iBuyPrice * InsertPer
                #         if HavePrice >= buyPrice:
                #             now = datetime.datetime.now()
                #             print(str(now) + "  ) " + tabkerName + " ADD BUY " + str(buyPrice))
                #             odr = upbit.buy_market_order(tabkerName, buyPrice)
                #             time.sleep(sleepTime)
                #             if 'error' in odr:
                #                 print(odr)
                #             else:
                #                 jun.InsertMyTicker_Open(id, tabkerName, now, myPrice, InsertPer)
                
                
                    


        ttt = jun.SelectMyTickerAll_OnlyCurrency(id)
        renTicker = list(set(ttt) - set(arTicer))
        for ticker in renTicker:
            jun.DeleteMyTicker(id,ticker)
        renTicker = list(set(arTicer) - set(ttt))
        for ticker in renTicker:
            jun.InsertMyTicker_Open(id,ticker ,datetime.datetime.now() ,0,1)

        # ttt = jun.SelectMyTickerAll_OnlyCurrency(id)
        # print(ttt)
        # 

                # elif float(dfData['close']) < dm:
                #     print(tabkerName)
                #     print("close " + str(dfData['close']))
                #     print("avg_buy_price " + str(b['avg_buy_price']))
                #     print("dm " + str(dm))
                #     print("dp " + str(dp))
                #     print("Sell BAD IS " + tabkerName)``
                #     upbit.sell_market_order(tabkerName, b['balance'])
                #     arDelTickers.append(tabkerName)
                    # print(upbit.sell_limit_order(tabkerName, dfData['close'] , b['balance']))
    except Exception as x:
        print(x)
def FinMyTicker(ticker):    
    balances = upbit.get_balances()
    for b in balances:
        if b['currency'] == "KRW":
            continue        
        tabkerName = "KRW-" + b['currency']
        if tabkerName == ticker:
            return True
    return False

def buy():
    global arDf
    iBuyPer = def_1Buy
    ipGap = def_1Plus
    iMinus = def_1Minus
    try:
        time.sleep(sleepTime)
        now = datetime.datetime.now()

        if True:
        # if 0 <= now.minute <= 55:
            time.sleep(sleepTime)
            tickers = jun_get_ticker_KRW()

            for ticker in tickers:
                if len(jun.SelectMyTicker(id, ticker)) > 0:
                    continue
                

                iC = 0
                bSell = False
                bBuy = False
                time.sleep(sleepTime)
                df = pyupbit.get_ohlcv(ticker, interval="minute1", count=1)
                # df = pyupbit.get_ohlcv(ticker, interval="minute60", count=1)
                # df = pyupbit.get_ohlcv(ticker, count=1)
                
                if len(arDf) > 0:
                    bc = False
                    for tm, tk in zip(arDf['time'], arDf['ticker']):
                        if ticker == tk:
                            bc = True
                            break
                    if bc == True:
                        date_diff = df.index[-1] - arDf.loc[ticker]['time']
                        if date_diff.seconds / 60 < 5:
                            continue
                dfData = df.iloc[0]
                # print(df)
                # print(dfData)
                
                if float(dfData['close']) < float(dfData['open']):
                    continue
                fMoney = 0
                fGap = 100 * float(dfData['close']) / float(dfData['open']) - 100
                dOpen = float(dfData['open'])
                
                if now.hour == 9:
                    iBuyPer = def_9Buy
                    ipGap = def_9Plus
                    iMinus = def_9Minus
                else:
                    iBuyPer = def_1Buy
                    ipGap = def_1Plus
                    iMinus = def_1Minus
                    
                dBuy  = float(dfData['open']) + float(dfData['open']) * 0.01 * float(iBuyPer)
                dM = dBuy - dBuy * 0.01 * float(iMinus)
                dP = dBuy + dBuy * 0.01 * float(ipGap)    
                
                # print(ticker + " " + str(dfData['open']) + " " + str(dfData['close']) + " > " +  str(dBuy))

                if dfData['close'] > dBuy:
                    if now.hour != 9:
                        ttt = jun.SelectMyTickerAll_OnlyCurrency(id)
                        if len(ttt) > 5:
                            continue
                    now = datetime.datetime.now()
                    print(str(now) + "  ) " + ticker + " BUY " + str(iBuyPrice))
                    odr = upbit.buy_market_order(ticker, iBuyPrice)                    
                    if 'error' in odr:
                        print(odr)
                    else:
                        jun.InsertMyTicker_Open(id, ticker, now, 0, 1)
                        arDf.loc[ticker]=[ df.index[-1], ticker]
                        
                    # jun.InserttickerGap3(id,ticker)
    except Exception as x:
        print(x)
        time.sleep(10)


class ThreadBuy(threading.Thread):
    def __init__(self):
        super().__init__()
    def run(self):
        while True:
            buy()
            time.sleep(0.3)

class ThreadSell(threading.Thread):
    def __init__(self):
        super().__init__()
    def run(self):
        while True:
            Sell()
            time.sleep(0.3)


# balances = upbit.get_balances()
# HavePrice = 0
# for b in balances:    
#     if b['currency'] == "KRW":
#         continue        
#     tabkerName = "KRW-" + b['currency']
#     print(b['balance'])
#     print(b['locked'])
#     print(upbit.sell_market_order(tabkerName,float(b['balance']) + float(b['locked'])))
#     time.sleep(0.1)

trBuy = ThreadBuy()
trBuy.start()

trSell = ThreadSell()
trSell.start()