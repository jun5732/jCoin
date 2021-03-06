#!/usr/bin/python
#-*-coding utf-8-*-

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
import threading
import common as jun
import logging
import platform

if platform.system() == "Windows":
    logging.basicConfig(filename='trade10PerUp.txt', level=logging.ERROR)
else:
    logging.basicConfig(filename='/root/coin/jun/log/trade10PerUp.txt', level=logging.ERROR)


sleepTime = 0.2

arDf = pd.DataFrame(columns = ['time' , 'ticker'])
id = "jun"
pw = "wnsco11"

upbit = jun.jun_LoginUpbit(id ,pw)

iBuyPrice = 0
def_9Buy = 100
def_9Plus = 100
def_DelPer = 100


arTickers = []
arDelTickers = []

def GetOption():
    global iBuyPrice
    global def_9Buy
    global def_9Plus
    global def_DelPer
    result = jun.select_jOption(id)
    for rst in result:
        if rst['name'] == "BuyPrice":
            iBuyPrice = int(rst['value'])
        elif rst['name'] == "BuyPer":
            def_9Buy = int(rst['value'])
        elif rst['name'] == "SelPer":
            def_9Plus = int(rst['value'])
        elif rst['name'] == "DeathPer":
            def_DelPer = int(rst['value'])
        else:
            ik = 1



def jun_get_ticker_KRW():
    tickers = pyupbit.get_tickers("KRW")
    delTicker = ["KRW-EMC2"]
    renTicker = list(set(tickers) - set(delTicker))
    return renTicker

def Sell():
    try:        
        arTicer = []
        GetOption()
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

            df = pyupbit.get_ohlcv(tabkerName, count=1)
            # df = pyupbit.get_ohlcv(tabkerName, interval="minute60", count=1)

            if len(df) < 1:
                continue
            eTime = df.index[0] +  datetime.timedelta(days=1) - datetime.timedelta(minutes=1)
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
                        
            time.sleep(sleepTime)
            oders = upbit.get_order(tabkerName)
            
            for oder in oders:
                upbit.cancel_order(oder['uuid'])
                time.sleep(sleepTime)
            dBuy  = float(b['avg_buy_price'])
                            
            dm = dBuy - dBuy * 0.01 * float(def_DelPer)
            dp = dBuy + dBuy * 0.01 * float(def_9Plus)

            if tabkerName == "KRW-WAXP":
                print(tabkerName + " : " + str(dm) +  " > " +  str(dfData['close']))
            #   ??????                                ?????? ??????           ??????
            # if dp < float(dfData['close']) or eTime < now < sellEndTime or dm < float(dfData['close']):
            if dp < float(dfData['close']) or eTime < now < sellEndTime or dm > float(dfData['close']):
                odr = upbit.sell_market_order(tabkerName, b['balance'])
                time.sleep(sleepTime)
                if 'error' in odr:
                        print(odr)
                else:
                    jun.DeleteMyTicker(id,tabkerName)
                    arTicer.remove(tabkerName)
                    now = datetime.datetime.now()
                    sLog = str(now) + "  ) " + "Sell IS " + tabkerName 
                    print(sLog)
                    logging.error(sLog)
                    jun.InsertMyLog(id, tabkerName, now, 1)

        ttt = jun.SelectMyTickerAll_OnlyCurrency(id)
        renTicker = list(set(ttt) - set(arTicer))
        for ticker in renTicker:
            jun.DeleteMyTicker(id,ticker)
            now = datetime.datetime.now()
            jun.InsertMyLog(id, ticker, now, 2)
        renTicker = list(set(arTicer) - set(ttt))
        for ticker in renTicker:
            jun.InsertMyTicker_Open(id,ticker ,datetime.datetime.now() ,0,1)
            now = datetime.datetime.now()
            jun.InsertMyLog(id, ticker, now, 0)

    except Exception as x:
        logging.error(x)
        print(x)
        
def buy():
    global arDf
    try:
        GetOption()
        time.sleep(sleepTime)
        tickers = jun_get_ticker_KRW()

        for ticker in tickers:
            if len(jun.SelectMyTicker(id, ticker)) > 0:
                continue
            
            time.sleep(sleepTime)
            # df = pyupbit.get_ohlcv(ticker, interval="day1", count=1)
            # df = pyupbit.get_ohlcv(ticker, interval="minute60", count=1)
            df = pyupbit.get_ohlcv(ticker, count=1)                
            dfData = df.iloc[0]
            
            if float(dfData['close']) < float(dfData['open']):
                continue
            fMoney = 0
            fGap = 100 * float(dfData['close']) / float(dfData['open']) - 100
            dOpen = float(dfData['open'])
                                
            dBuy  = float(dfData['open']) + float(dfData['open']) * 0.01 * float(def_9Buy)
            now = datetime.datetime.now() 
            eTime = df.index[0] +  datetime.timedelta(days=1) - datetime.timedelta(minutes=1)         
            print(ticker + " : " + str(dfData['close']) +  " > "  + str(dBuy))
            if dfData['close'] > dBuy and now < eTime:
                time.sleep(sleepTime)
                dfTime = pyupbit.get_ohlcv(ticker, interval="minute10", count=1)
                if float(dfTime['close']) > float(dfTime['open']):
                    if now.hour != 9:
                        ttt = jun.SelectMyTickerAll_OnlyCurrency(id)
                        if len(ttt) > 5:
                            continue
                    
                    sLog = str(now) + "  ) " + ticker + " BUY " + str(iBuyPrice) 
                    print(sLog)
                    logging.error(sLog)

                    time.sleep(sleepTime)
                    odr = upbit.buy_market_order(ticker, iBuyPrice)                    
                    if 'error' in odr:
                        print(odr)
                    else:
                        jun.InsertMyTicker_Open(id, ticker, now, 0, 1)
                        jun.InsertMyLog(id, ticker, now, 0)
                        arDf.loc[ticker]=[ df.index[-1], ticker]
                        
    except Exception as x:
        logging.error(x)
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


GetOption()

now = datetime.datetime.now()
logging.error(' START => ' + str(now))
logging.error("iBuyPrice is " + str(iBuyPrice))
logging.error("def_9Buy is " + str(def_9Buy))
logging.error("def_9Plus is " + str(def_9Plus))
logging.error("def_DelPer is " + str(def_DelPer))

trBuy = ThreadBuy()
trBuy.start()

trSell = ThreadSell()
trSell.start()