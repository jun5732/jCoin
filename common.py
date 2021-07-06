import os
import requests
import pandas as pd
import time
import pyupbit
import numpy as np
import datetime
import threading
import pymysql

access = None
secret = None
id = None
pw = None

guser='jun'
gpasswd='@As73016463'
ghost='45.120.69.37'
# ghost='3.134.100.230'
gdb='coin'
totalGap = 0

#   업비트 로그인
def jun_LoginUpbit(inId = None, inPw = None):
    global upbit
    global id
    global pw
    access = None
    secret = None

    if inId is not None:
        id = inId
        pw = inPw
        myKey = Login()
        access = myKey[0]
        secret = myKey[1]
    else:
        f = open("key.txt", 'r')
        while True:
            line = f.readline()
            if not line: break
            access = line.split('|')[0]
            secret = line.split('|')[1]
        f.close()
    upbit = pyupbit.Upbit(access ,secret)
    return upbit

def jun_get_Gap(price):
    if price >= 2000000:
        tick_size = round(price / 1000) * 1000
    elif price >= 1000000:
        tick_size = round(price / 500) * 500
    elif price >= 500000:
        tick_size = round(price / 100) * 100
    elif price >= 100000:
        tick_size = round(price / 50) * 50
    elif price >= 10000:
        tick_size = round(price / 10) * 10
    elif price >= 1000:
        tick_size = round(price / 5) * 5
    elif price >= 100:
        tick_size = round(price / 1) * 1
    elif price >= 10:
        tick_size = round(price / 0.1) / 10
    else:
        tick_size = round(price / 0.01) / 100
    return tick_size

def jun_get_OlnyGap(price):
    if price >= 2000000:
        tick_size = 1000
    elif price >= 1000000:
        tick_size = 500
    elif price >= 500000:
        tick_size = 100
    elif price >= 100000:
        tick_size = 50
    elif price >= 10000:
        tick_size = 10
    elif price >= 1000:
        tick_size = 5
    elif price >= 100:
        tick_size = 1
    elif price >= 10:
        tick_size = 10
    else:
        tick_size = 100
    return tick_size

def jun_GetOrder(ticker):
    balances = upbit.get_balances()
    time.sleep(0.2)
    bEndTime = False
    for b in balances:
        if ticker == "KRW-" + b['currency']:
            return float(b['avg_buy_price'])
    return 0
            

def jun_AllOrderCancle(ticker):
    time.sleep(0.1)
    oders = upbit.get_order(ticker)
    for oder in oders:
        upbit.cancel_order(oder['uuid'])
        time.sleep(0.1)


def jun_SetPerOrder(ticker):
    balances = upbit.get_balances()

    for b in balances:
        if ticker ==  "KRW-" + b['currency']:
            #   평균 매수가
            fAvgPrice = float(b['avg_buy_price'])
            #   보유수량
            fCount = float(b['balance']) + float(b['locked'])

            fSelPrice = pyupbit.get_tick_size(fAvgPrice * 1.02)

            if fAvgPrice * fCount > 5000:
                oders = upbit.get_order(ticker)
                time.sleep(0.1)
                bCancle = False
                
                for oder in oders:
                    if float(fSelPrice) != float(oder['price']) or float(b['balance']) > 0:
                        if oder['side'] == 'ask':
                            upbit.cancel_order(oder['uuid'])
                            bCancle = True
                            time.sleep(0.1)
                time.sleep(0.1)
                if bCancle or len(oders) < 1:
                    print(ticker)
                    print(upbit.sell_limit_order(ticker, fSelPrice, fCount,True))
                    break

def jun_get_ticker_KRW():
    tickers = pyupbit.get_tickers("KRW")
    delTicker = ["KRW-KMD","KRW-ADX","KRW-LBC","KRW-IGNIS","KRW-DMT"
                ,"KRW-EMC2","KRW-TSHP","KRW-LAMB","KRW-EDR","KRW-PXL"
                ,"KRW-PICA","KRW-RDD","KRW-RINGX","KRW-VITE","KRW-ITAM"
                ,"KRW-SYS","KRW-NXT","KRW-BFT","KRW-NCASH","KRW-FSN"
                ,"KRW-PI","KRW-RCN","KRW-PRO","KRW-ANT","KRW-BASIC"]
    renTicker = list(set(tickers) - set(delTicker))
    
    return renTicker

def jun_get_ticker_KRW_DESC7():
    global totalGap
    tickers = jun_get_ticker_KRW()
    time.sleep(0.1)
    tOpen = []
    tClose = []
    tGap = []
    for ticker in tickers:
        df = pyupbit.get_ohlcv(ticker,interval="day", count=7)
        dg = 100 * df['close'][-1] / df['close'][0] - 100
        # dg = 100 * df['close'] / df['open'] - 100
        tGap.append(dg.mean())
        time.sleep(0.2)
    raw_data = {'ticker':tickers,"gap" : tGap}
    data = pd.DataFrame(raw_data)
    dataSort = data.sort_values(by=['gap'])        
    return dataSort



def jun_get_ticker_KRW_DESC():
    global totalGap
    tickers = jun_get_ticker_KRW()
    time.sleep(0.1)
    tOpen = []
    tClose = []
    tGap = []
    weekLow = SelectWeekBestLow()
    renTicker = list(set(tickers) - set(weekLow))
    for ticker in renTicker:
        df = pyupbit.get_ohlcv(ticker, count=1)
        tOpen.append(df['open'][0])
        tClose.append(df['close'][0])
        tGap.append(100 * df['close'][0] / df['open'][0] - 100)
        time.sleep(0.2)
    raw_data = {'ticker':tickers,'open' : tOpen ,'close': tClose,"gap" : tGap}
    data = pd.DataFrame(raw_data)
    dataSort = data.sort_values(by=['gap'])
    totalGap = sum(dataSort['gap'])
    
    # ticker    open    close   gap
    return dataSort['ticker'].tolist()

#   3평 구하기
def jun_get_ma3(df):
    return df['close'].rolling(3).mean()

#   5평 구하기
def jun_get_ma5(df):
    return df['close'].rolling(5).mean()
    
#   20평 구하기
def jun_get_ma20(df):
    return df['close'].rolling(20).mean()
    
#   40평 구하기
def jun_get_ma40(df):
    return df['close'].rolling(40).mean()

def jun_UpEvgVolume(df):
    if df['volume'].mean() < df['volume'].iloc[-1]:
        return True
    else:
        return False

#   RSI 가져오기
def jun_get_rsi(ohlc: pd.DataFrame, period: int = 14):
    ohlc["close"] = ohlc["close"]
    delta = ohlc["close"].diff()
    raw_data = {'close' : ohlc["close"] ,'delta': delta}
    data = pd.DataFrame(raw_data)
    gains, declines = delta.copy(), delta.copy()
    gains[gains < 0] = 0
    declines[declines > 0] = 0
    _gain = gains.ewm(com=(period - 1), min_periods=period).mean()
    _loss = declines.abs().ewm(com=(period - 1), min_periods=period).mean()

    RS = _gain / _loss
    return pd.Series(100 - (100 / (1 + RS)), name="RSI")

#   최저가 찾기(종가기준)
def jun_Find_MinPrice(ohlc):
    minClose =  min(ohlc['close'])
    minOpen =  min(ohlc['open'])

    if minClose < minOpen:
        return minClose
    else:
        return minOpen

def jun_Get_MyPrice(ticker):
    time.sleep(0.1)
    balances = upbit.get_balances()
    
    for b in balances:
        if "KRW-" + b['currency'] == ticker:
            continue
        #   평균 매수가
        fAvgPrice = float(b['avg_buy_price'])
        #   보유수량
        fCount = float(b['balance']) + float(b['locked'])

        if fAvgPrice * fCount > 3000:
            return True
    return False


def jun_SetPerOrder(ticker,interval):
    balances = upbit.get_balances()
    tabkerName = ticker
    for b in balances:
        if ticker == "KRW-" + b['currency']:
            
            #   평균 매수가
            fAvgPrice = float(b['avg_buy_price'])
            #   보유수량
            fCount = float(b['balance']) + float(b['locked'])

            fSelPrice = pyupbit.get_tick_size(fAvgPrice * 1.012)

            # if True:
            if fAvgPrice * fCount > 3000:
                time.sleep(0.1)
                df = pyupbit.get_ohlcv(ticker, interval="minute" + str(interval), count=1)

                now = datetime.datetime.now()
                start_time = df.index[-1] + datetime.timedelta(minutes=interval - 1)
                End_time = df.index[-1] + datetime.timedelta(minutes=interval)


                if start_time > now > End_time:
                    if fSelPrice < df['close'][0]:
                        print(upbit.sell_limit_order(ticker, fSelPrice, fCount,True))
                        return False

class jun_WhileSelPerOrder(threading.Thread):

    def __init__(self, ticker,interval):
        super().__init__()
        self.ticker = ticker
        self.interval = interval

    def run(self):
        while True :
            if jun_SetPerOrder(self.ticker,self.interval) == False:
                time.sleep(0.1)
                return

def jun_GetMyPrice(ticker):
    time.sleep(0.1)
    return upbit.get_balance_t(ticker) * upbit.get_avg_buy_price(ticker)


#########################################################################################################################################################
#   DB

juso_db = pymysql.connect(
    user=guser, 
    passwd=gpasswd, 
    host=ghost, 
    db=gdb, 
    charset='utf8'
)
cursor = juso_db.cursor(pymysql.cursors.DictCursor)

#######################################################################################
#   user
def Login():
    myKey = []
    sql = "SELECT * FROM user where id = '" + id + "' and pw = '" + pw + "';"
    cursor.execute(sql)
    result = cursor.fetchall()
    if result is not None:
        if len(result) > 0:
            myKey = [result[0]['access'] ,result[0]['secret']]
    return myKey

#######################################################################################
#   ticker
def SelectTicker(id):
    # g_myTicker = None
    sql = "SELECT currency FROM ticker where id = '" + id + "' "
    cursor.execute(sql)
    result = cursor.fetchall()
    final_result = [i['currency'] for i in result]
    return final_result
    
def UpdateArTicker(id,arcurrency):    
    for currency in arcurrency:
        sql = """update ticker set avgprice = 0 where  id = %s and  currency = %s"""
        cursor.execute(sql, (id, currency))
        juso_db.commit()

def UpdateTicker(id, currency, autouse):
    sql = """Update ticker set autouse = %s where id = %s and currency = %s"""
    cursor.execute(sql, (autouse, id, currency))
    juso_db.commit()

 
#######################################################################################
#   myticker
def DeleteMyTicker(id, currency):
    sql = """delete from myticker where id = %s and  currency = %s"""
    cursor.execute(sql, (id, currency))
    juso_db.commit()
    # UpdateTicker(id, currency, 1)


def InsertMyTicker(id, currency, openprice, buyprice, buyper):
    result = SelectMyTicker(id, currency)
    if result == None:
        result = SelectMyTicker(id, currency)
    if len(result) > 0:     # update        
        if result[0]['openprice'] == openprice and result[0]['buyprice'] == buyprice and result[0]['buyper'] == buyper:
            return False
        sql = """update myticker set openprice = %s, buyprice = %s, buyper = %s where  id = %s and  currency = %s"""
        cursor.execute(sql, (openprice, buyprice, buyper,id, currency))
        juso_db.commit()
    else:                   # insert
        sql = """insert into myticker(id, currency, openprice, buyprice, buyper) values (%s, %s, %s, %s, %s)"""
        cursor.execute(sql, (id, currency, openprice, buyprice, buyper))
        juso_db.commit()
        # UpdateTicker(id, currency, 0)
    return True
def InsertMyTicker(id, currency, openprice, buyper):
    result = SelectMyTicker(id, currency)
    if result == None:
        result = SelectMyTicker(id, currency)
    if len(result) > 0:     # update        
        if float(result[0]['openprice']) - float(openprice) == 0 and float(result[0]['buyper']) - float(buyper) == 0:
            return False
        if float(result[0]['buyper']) > float(buyper):
            return False
        sql = """update myticker set openprice = %s, buyper = %s where  id = %s and  currency = %s"""
        cursor.execute(sql, (openprice, buyper,id, currency))
        juso_db.commit()
    else:                   # insert
        sql = """insert into myticker(id, currency, openprice, buyper) values (%s, %s, %s, %s)"""
        print(id + "," +  currency + "," +   str(openprice) + "," +   str(buyper))
        cursor.execute(sql, (id, currency, openprice, buyper))
        juso_db.commit()
    return True

def InsertMyTicker_Open(id, currency, buytime, openprice, buyper=0):
    result = SelectMyTicker(id, currency)
    if result == None:
        result = SelectMyTicker(id, currency)
    if len(result) > 0:     # update
        if buyper == 0:
            sql = """update myticker set openprice = %s where  id = %s and  currency = %s"""
            cursor.execute(sql, (openprice,id, currency))
        else:
            sql = """update myticker set openprice = %s,buyper = %s where  id = %s and  currency = %s"""
            cursor.execute(sql, (openprice,buyper,id, currency))
    else:                   # insert
        sql = """insert into myticker(id, currency, buytime, openprice, buyper) values (%s, %s, %s, %s, %s)"""
        cursor.execute(sql, (id, currency, buytime, openprice, buyper))
    juso_db.commit()
    time.sleep(0.1)
    return True

def UpdateMyTickerPrice(id, currency, openprice):
    try:
        sql = """update myticker set openprice = %s  where id = %s and  currency = %s"""
        cursor.execute(sql, (openprice ,id, currency))
        juso_db.commit()     
    except Exception as x:
        print(x)
def SelectMyTickerAll(id):    
    global g_myTicker
    

    db = pymysql.connect(
        user=guser, 
        passwd=gpasswd, 
        host=ghost, 
        db=gdb, 
        charset='utf8'
    )
    conn = db.cursor(pymysql.cursors.DictCursor)

    try:
        sql = "SELECT * FROM myticker where id = '" + id + "' "
        conn.execute(sql)
        result = conn.fetchall()
        g_myTicker = result
        return result
    except Exception as x:
        print(x)
        conn.close()
        db.close()
        return None
    finally:
        conn.close()
        db.close()
        g_myTicker = result
        return result
    
    
def SelectMyTickerAll_OnlyCurrency(id):    
    global g_myTicker
    

    db = pymysql.connect(
        user=guser, 
        passwd=gpasswd, 
        host=ghost, 
        db=gdb, 
        charset='utf8'
    )
    conn = db.cursor(pymysql.cursors.DictCursor)

    try:
        sql = "SELECT * FROM myticker where id = '" + id + "' "
        conn.execute(sql)
        result = conn.fetchall()
        final_result = [i['currency'] for i in result]
        return final_result
    except Exception as x:
        print(x)
        conn.close()
        db.close()
        return None
    finally:
        conn.close()
        db.close()
        return final_result

def SelectMyTicker(id, currency):

    db = pymysql.connect(
        user=guser, 
        passwd=gpasswd, 
        host=ghost, 
        db=gdb, 
        charset='utf8'
    )
    conn = db.cursor(pymysql.cursors.DictCursor)
    try:
        # g_myTicker = None
        sql = "SELECT * FROM myticker where id = '" + id + "' "
        sql += " and currency = '" + currency + "';"
        conn.execute(sql)
        result = conn.fetchall()
        return result
    except Exception as x:
        print(x)
        conn.close()
        db.close()
        return None
    finally:
        conn.close()
        db.close()
        return result
    

#######################################################################################
#   joption
def select_jOption(id, name):
    
    db = pymysql.connect(
        user=guser, 
        passwd=gpasswd, 
        host=ghost, 
        db=gdb, 
        charset='utf8'
    )
    conn = db.cursor(pymysql.cursors.DictCursor)
    try:
        
        sql = "SELECT value FROM joption where id = '" + id + "' and name = '" + name + "';"
        conn.execute(sql)
        result = conn.fetchall()
        return result
    except Exception as x:
        print(x)
        conn.close()
        db.close()
        return None
    finally:
        conn.close()
        db.close()
        return result

def select_jOptionValue(id, name):
    try:
        result = select_jOption(id, name)
        return float(result[0]['value'])        
    except Exception as x:
        return 2

#######################################################################################
#   proc
def jun_PROC_InsertMyTicker(id, currency, buytime, openprice, buyper):
    global g_myTicker
    db = pymysql.connect(
        user=guser, 
        passwd=gpasswd, 
        host=ghost, 
        db=gdb, 
        charset='utf8'
    )
    conn = db.cursor(pymysql.cursors.DictCursor)
    try:
        # g_myTicker = None
        sql = "CALL PROC_InsertMyTicker('" + id + "','"  + currency + "','" + str(buytime) + "'," + str(openprice) + "," + str(buyper) + ")"
        print(sql)
        conn.execute(sql)
        result = conn.fetchall()

        data = None
        while result:
            data = result
            if conn.nextset():
                result = conn.fetchall()
            else:
                result = None

        final_result = None
        g_myTicker = data
        if len(data) > 0:
            final_result = [i['currency'] for i in data]

        return final_result
    except Exception as x:
        print(x)
        conn.close()
        db.close()
        return None
    finally:
        conn.close()
        db.close()
        return final_result

#######################################################################################
#   tickerGap3
def SelecttickerGap3(id):

    db = pymysql.connect(
        user=guser, 
        passwd=gpasswd, 
        host=ghost, 
        db=gdb, 
        charset='utf8'
    )
    conn = db.cursor(pymysql.cursors.DictCursor)
    try:
        # g_myTicker = None
        sql = "SELECT currency FROM tickerGap3 where id = '" + id + "';"
        conn.execute(sql)
        result = conn.fetchall()
        tickers = [item['currency'] for item in result]
        return tickers
    except Exception as x:
        print(x)
        conn.close()
        db.close()
        return None
    finally:
        conn.close()
        db.close()
        return tickers

def DeletetickerGap3(id, currency):
    sql = """delete from tickerGap3 where id = %s and  currency = %s"""
    cursor.execute(sql, (id, currency))
    juso_db.commit()
    # sql = """update myticker set openprice = 0 where  id = %s and  currency = %s"""
    # cursor.execute(sql, (id, currency))
    # juso_db.commit()
    UpdateTicker(id, currency, 1)


def InserttickerGap3(id, currency):
    sql = """insert into tickerGap3(id, currency) values (%s, %s)"""
    cursor.execute(sql, (id, currency))
    juso_db.commit()

#######################################################################################
#   weekbestlow
def SelectWeekBestLow(id, currency = None):

    db = pymysql.connect(
        user=guser, 
        passwd=gpasswd, 
        host=ghost, 
        db=gdb, 
        charset='utf8'
    )
    conn = db.cursor(pymysql.cursors.DictCursor)
    try:
        # g_myTicker = None
        sql = "SELECT * FROM weekbestlow where id = '" + id + "' "
        if currency is not None:
            sql += " and currency = '" + currency + "'"
        sql += ";"
        conn.execute(sql)
        result = conn.fetchall()
        return result
    except Exception as x:
        print(x)
        conn.close()
        db.close()
        return None
    finally:
        conn.close()
        db.close()
        return result

def DeleteWeekBestLow(id, currency):
    sql = """delete from weekbestlow where id = %s and  currency = %s"""
    cursor.execute(sql, (id, currency))
    juso_db.commit()
    # sql = """update myticker set openprice = 0 where  id = %s and  currency = %s"""
    # cursor.execute(sql, (id, currency))
    # juso_db.commit()
    UpdateTicker(id, currency, 1)


def InsertWeekBestLow(id, currency, openprice, buyprice, buyper):
    result = SelectWeekBestLow(id, currency)
    if result == None:
        result = SelectMyTicker(id, currency)
    if len(result) > 0:     # update        
        if result[0]['openprice'] == openprice and result[0]['buyprice'] == buyprice and result[0]['buyper'] == buyper:
            return False
        sql = """update weekbestlow set openprice = %s, buyprice = %s, buyper = %s where  id = %s and  currency = %s"""
        cursor.execute(sql, (openprice, buyprice, buyper,id, currency))
        juso_db.commit()
    else:                   # insert
        sql = """insert into weekbestlow(id, currency, openprice, buyprice, buyper) values (%s, %s, %s, %s, %s)"""
        cursor.execute(sql, (id, currency, openprice, buyprice, buyper))
        juso_db.commit()
        UpdateTicker(id, currency, 0)
    return True


    
#######################################################################################
#   mylog
def InsertMyLog(id, currency, buytime, openprice, type):
    sql = """insert into mylog(id, currency, buytime, type) values (%s, %s, %s, %s)"""
    cursor.execute(sql, (id, currency, buytime, openprice, type))
    juso_db.commit()

def SelectMyLog(id, currency):    
    db = pymysql.connect(
        user=guser, 
        passwd=gpasswd, 
        host=ghost, 
        db=gdb, 
        charset='utf8'
    )
    conn = db.cursor(pymysql.cursors.DictCursor)
    try:
        sql = "SELECT buytime FROM mylog where id = '" + id + "' and currency = '" + currency + "';"# and type != 0;"
        conn.execute(sql)
        result = conn.fetchall()

        return result
    except Exception as x:
        print(x)
        conn.close()
        db.close()
        return None
    finally:
        conn.close()
        db.close()
        return result

# jun_LoginUpbit('jun','wnsco11')