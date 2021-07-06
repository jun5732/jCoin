#-*- coding:utf-8 -*-
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


juso_db = pymysql.connect(
    user=guser, 
    passwd=gpasswd, 
    host=ghost, 
    db=gdb, 
    port=3307,
    charset='utf8'    
)
cursor = juso_db.cursor(pymysql.cursors.DictCursor)

sql = "SELECT * FROM user where id = 'jun' and pw = '@As73016463';"
cursor.execute(sql)
result = cursor.fetchall()
print(result)






