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

sMyName = os.path.basename(sys.argv[0]).split('.')[0]

if platform.system() == "Windows":
    logging.basicConfig(filename=sMyName + '.txt', level=logging.ERROR)
else:
    logging.basicConfig(filename='/root/coin/jun/log/' + sMyName + '.txt', level=logging.ERROR)



################################################################################
#   1. istick 이 iBuyPer% 상승하면 매수
#   2. 평균매수가 기준으로  iSelPer% 상승하면 매도
#   3. 매도와 같은 istick에는 매수 하지 않음
#   4. 평균 매수가 기준으로 iAddBuyPer% 하락하면 추가 매수
#   5. 평균매수가 기준으로  iSelPer% 상승하면 매도
#   6. 매도와 같은 istick에는 매수 하지 않음
#   7. 1 ~ 6 반복
################################################################################

iBuyPrice = 7000
istick = 60
iBuyPer = 3
iSelPer = 3
iAddBuyPer = 5


sleepTime = 0.2
DBsleepTime = 0.1

id = "jun"
pw = "wnsco11"

upbit = jun.jun_LoginUpbit(id ,pw)


def AllSell():
    balances = upbit.get_balances()
    HavePrice = 0
    for b in balances:
        
        if b['currency'] == "KRW":
            HavePrice = float(b['balance'])
            continue        
        
        if (float(b['balance']) + float(b['locked'])) * float(b['avg_buy_price']) < 5000.0:
            continue         
        ticker = "KRW-" + b['currency']
        time.sleep(sleepTime)
        odr = upbit.sell_market_order(ticker, b['balance'])
        if 'error' in odr:
                print(odr)
        else:
            jun.DeleteMyTicker(id,ticker)
            now = datetime.datetime.now()
            sLog = str(now) + "  ) " + "Sell IS " + ticker
            WriteLog(sLog)
            jun.InsertMyLog(id, ticker, now, 1)

#LOG 저장
def WriteLog(str):
    logging.error(str)
    print(str)

#   옵션 조회
def GetOption():
    global iBuyPrice
    global istick
    global iBuyPer
    global iSelPer
    global iAddBuyPer
    
    result = jun.select_jOption(id)
    for rst in result:
        if rst['name'] == "BuyPrice":
            iBuyPrice = int(rst['value'])
        elif rst['name'] == "istick":
            istick = int(rst['value'])
        elif rst['name'] == "iBuyPer":
            iBuyPer = int(rst['value'])
        elif rst['name'] == "iSelPer":
            iSelPer = int(rst['value'])
        elif rst['name'] == "iAddBuyPer":
            iAddBuyPer = int(rst['value'])
        else:
            ik = 1

#   같은 봉에 매도했는지 조회한다.
def IsSameTimeTicker(ticker):
    time.sleep(sleepTime)
    dfTime = pyupbit.get_ohlcv(ticker, interval="minute" + str(istick), count=1)
    result = jun.SelectMyLogTime(id,ticker)
    
    if len(result) > 0:
        oldTime = datetime.datetime.strptime(result[0]['buytime'], '%Y-%m-%d %H:%M:%S.%f')
        
        if dfTime.index[0] < oldTime and oldTime < dfTime.index[0] +  datetime.timedelta(minutes=istick):
            return False
        else:
            return True
    return False

# iBuyPer 보다 높은 종목을 찾는다.
def FindUpTicker():
    time.sleep(sleepTime)
    tickers = pyupbit.get_tickers("KRW")
    for ticker in tickers:
        if len(jun.SelectMyTicker(id, ticker)) > 0:
            continue
        time.sleep(sleepTime)
        df = pyupbit.get_ohlcv(ticker, interval="minute" + str(istick), count=1)      
        if df is None:
            continue
        dfData = df.iloc[0]
        if float(dfData['close']) < float(dfData['open']):
            continue
        fGap = 100 * float(dfData['close']) / float(dfData['open']) - 100
        if fGap > iBuyPer:
            if IsSameTimeTicker(ticker):
                return ticker
    return None

# iSelPer 기준 매도 iAddBuyPer 기준 추가매수
def WaitSell(ticker):
    time.sleep(sleepTime)
    
    balances = upbit.get_balances()
    myAvgPrice = 0
    myBalance = 0

    for b in balances:        
        if "KRW-" + b['currency'] == ticker:            
            myAvgPrice = float(b['avg_buy_price'])  
            myBalance = b['balance']          
        
            time.sleep(sleepTime)
            df = pyupbit.get_ohlcv(ticker, count=1)      
            dfData = df.iloc[0]
    
            fGap = 100 * float(dfData['close']) / myAvgPrice - 100
            print(ticker + " is " + str(fGap))
            #   익절
            if fGap > iSelPer:
                time.sleep(sleepTime)
                odr = upbit.sell_market_order(ticker, b['balance'])
                time.sleep(sleepTime)
                if 'error' in odr:
                        print(odr)
                else:
                    jun.DeleteMyTicker(id,ticker)
                    time.sleep(DBsleepTime)
                    now = datetime.datetime.now()
                    sLog = str(now) + "  ) " + "Sell IS " + ticker
                    WriteLog(sLog)
                    jun.InsertMyLog(id, ticker, now, 1)
            #   추가매수
            if fGap < 0 and abs(fGap) / iAddBuyPer > 1:
                time.sleep(sleepTime)
                iPer = abs(fGap) / iAddBuyPer
                bPrice = iBuyPrice * (iPer + 1)
                odr = upbit.buy_market_order(ticker, bPrice)
                if 'error' in odr:
                    print(odr)
                else:
                    sLog = str(now) + "  ) " + "Add Buy " + ticker
                    WriteLog(sLog)
                    now = datetime.datetime.now() 
                    jun.InsertMyTicker_Open(id, ticker, now, 0, 1)
                    time.sleep(DBsleepTime)
                    jun.InsertMyLog(id, ticker, now, 0)
        



class ThreadBuy(threading.Thread):
    def __init__(self):
        super().__init__()
    def run(self):
        while True:
            myTicker = jun.SelectMyTickerAll(id)
            if len(myTicker) > 0:
                WaitSell(myTicker[0]['currency'])
            else:
                ticker = FindUpTicker()
            time.sleep(0.3)



now = datetime.datetime.now()
WriteLog(' START => ' + str(now))
WriteLog("iBuyPrice is " + str(iBuyPrice))
WriteLog("istick is " + str(istick))
WriteLog("iBuyPer is " + str(iBuyPer))
WriteLog("iSelPer is " + str(iSelPer))
WriteLog("iAddBuyPer is " + str(iAddBuyPer))

trSell = ThreadBuy()
trSell.start()