import sqlite3
import os
import time
import pandas as pd
from win32com.shell import shell, shellcon
import matplotlib.pyplot as plt
from datetime import date, timedelta, datetime, time


def logfile(date, cur_time, temp, baudrate, current_id, temp_over, esik, beni_bul, device_label, adress, unit):
    """
    Log almak için kullanılır. .db uzantısı ile kaydeder.
    :param date: Tarih verisi
    :param cur_time: Zaman verisi
    :param temp: Sıcaklık verisi
    :param baudrate: Baudrate modu
    :param current_id: id_numarası
    :param temp_over: sıcaklık eşiğin üzerinde ise 1 değilse 0
    :param esik: Esik sıcaklık değeri
    :param beni_bul: Beni bul butonunun durumu, Mavi ise 1, yesil ise 0
    :param device_label: ekranda device label ismi
    :param adress: kayıt adresi

    Kayıt 10 dakikada bir yapılacak. Son kayıt ne zaman atılmış onu bulup 10 dakika olmadı ise
    islemi hiçbir şey yapmadan bitiriyoruz.
    """
    adress = adress +"\logs.db"
    last_log = datetime.fromtimestamp(get_last_log(adress, f"device{unit}"))
    con = sqlite3.connect("{}".format(adress))
    cursor = con.cursor()
    delta = timedelta(seconds=600)

    if datetime.now() - last_log   >= timedelta(seconds=600):
        cursor.execute(f"CREATE TABLE IF NOT EXISTS \"device{unit}\" (date TEXT, time TEXT, temp TEXT, baudrate TEXT,"
                       f" current_id TEXT,temp_over TEXT, esik TEXT, BeniBul TEXT, device_label TEXT, timestamp INT)")

        con.commit()
        cursor.execute(f"INSERT INTO \"device{unit}\" VALUES(?,?,?,?,?,?,?,?,?,?)",
                       (date, cur_time, temp, baudrate, current_id, temp_over,
                        esik, beni_bul, device_label, datetime.now().timestamp()))
    else:
        pass

    con.commit()
    con.close()

def get_last_log(address, device):

    try:
        con = sqlite3.connect(address)
        cursor = con.cursor()
        cursor.execute(f"SELECT * FROM \"{device}\" ORDER BY timestamp DESC LIMIT 1")
        m = cursor.fetchone()[-1]
        con.close()
        return m
    except:
        return datetime(1970,1,3).timestamp()

def get_tables(adress):
    """
    son log kayıtlarını ekrana girmek için kullanılır.
    DÜZENLENECEK.....
    """
    class degerler():

        def __init__(self, temp, baudmode, id, temp_over, esik,  beni_bul, label):
            self.id = id
            self.baudmode = baudmode
            self.temp = temp
            self.temp_over = temp_over
            self.label = label
            self.esik = esik
            self.beni_bul = beni_bul
    try:
        last_log = []
        con = sqlite3.connect(adress)
        cursor = con.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        for table in tables:
            sonuc = cursor.execute(f'select * from \"{table[0]}\"').fetchall()[-1]
            last_log.append(degerler(sonuc[2], sonuc[3], sonuc[4], sonuc[5],
                                     sonuc[6], sonuc[7], sonuc[8]))
        con.close()
    except:
        pass

    return last_log

def get_graph(device, period, adress):
    device = "device" + device
    if period == "Son 100 Veri":
        days = 100
    if period == "Son 1000 Veri":
        days = 1000
    elif period == "Son 10000 Veri":
        days = 10000

    database = get_graph_table(device, days, adress)

    db = pd.DataFrame(database, columns=["Tarih", "Saat", "Sıcaklık", "BaudMode", "SlaveID",
                                         "Uyarı", "Esik", "BeniBul", "Label", "timestamp"])

    db = db.drop([db.columns[3], db.columns[4], db.columns[5], db.columns[6],
                  db.columns[7], db.columns[8], db.columns[9]], axis= 1)
    db['Sıcaklık'] = db['Sıcaklık'].astype(int)
    db_list = db['Sıcaklık'].values.tolist()
    time_list = db['Saat'].values.tolist()
    return [time_list, db_list]
    """
    db.plot(kind='line', x='Saat', y='Sıcaklık', color='red')
    plt.show()
    """

def database_to_excel(device, period, xlsx_ad, sql_ad):
    device = "device" + device
    if period == "Son 100 Veri":
        days = 100
    if period == "Son 1000 Veri":
        days = 1000
    elif period == "Son 10000 Veri":
        days = 10000

    database = get_graph_table(device, days, sql_ad)
    db = pd.DataFrame(database, columns=["Tarih", "Saat", "Sıcaklık", "BaudMode", "SlaveID",
                                         "EsikOn", "Esik", "BeniBul", "Label", "timestamp"])
    db.to_excel(xlsx_ad+"\{}.xlsx".format(device))

def get_graph_table(device, period, adress):
    """
    :param device: database de cihaza verilen ad
    :param period: Kaç günlük bir veri almak istediğinizi gösterir
    :return: olusturulan veritabanı return yapılır.
    """
    database = []
    con = sqlite3.connect(adress)
    cursor = con.cursor()
    cursor.execute(f"SELECT * FROM \"{device}\" ORDER BY timestamp DESC LIMIT \"{period}\"")
    database.extend(cursor.fetchall())
    con.close()
    return database

def dates(period):
    date_given = []
    today = datetime.now().date()
    start_date = today - timedelta(period-1)
    delta = today - start_date

    for i in range(delta.days+1):
        day = (start_date + timedelta(days=i)).strftime('%d.%m.%Y')
        date_given.append(day)
    return date_given

def open_register_folders():

    doc_folder = shell.SHGetFolderPath(0, shellcon.CSIDL_PERSONAL, None, 0)

    database_dir = r"{}".format(doc_folder) + "\AKGUN ESM\databases"
    log_dir = r"{}".format(doc_folder) + "\AKGUN ESM\logs"
    xlsx_dir = r"{}".format(doc_folder) + "\AKGUN ESM\ExcelOutput"


    if not os.path.exists(database_dir):
        os.makedirs(database_dir)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    if not os.path.exists(xlsx_dir):
        os.makedirs(xlsx_dir)

    return database_dir, log_dir, xlsx_dir


#database_to_excel("14", 7,r"C:\Users\ysnah\Documents\ModbusMaster\ExcelOutput", r"C:\Users\ysnah\Documents\ModbusMaster\logs\logs.db")
#logfile("A", "b","c", "d","a","f","f","f", "f",r"C:\Users\ysnah\Documents\ModbusMaster\logs" )
