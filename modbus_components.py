from PyQt5 import QtWidgets,QtGui
from PyQt5.QtWidgets import *

from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal, QSize
from PyQt5.QtGui import QFont, QPixmap, QIcon, QIntValidator
from win32com.shell import shell, shellcon

import pandas as pd
import sys
import sqlite3
import os
import time
import matplotlib
import random
from pymodbus.client.sync import ModbusTcpClient as ModbusClient
from pymodbus.transaction import ModbusRtuFramer
import re


matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure

class main_window(QWidget):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("AKGÜN ESM")
        os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
        path = os.getcwd()
        path = r"" + path + "/includes/akgun.ico"
        #print(path)
        #icon = r"C:\Users\ysnah\Desktop\AKGUN_STAJ\modbusV2\includes\akgun.ico"
        self.setWindowIcon(QtGui.QIcon(path))
        self.regex = '^(\w|\.|\_|\-)+[@](\w|\_|\-|\.)+[.]\w{2,3}$'


        self.UI()
        self.showMaximized()


        self.show()

    def UI(self):



        lyt = QVBoxLayout()

        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("QTabBar::tab { height: 50px; width: 300px;}")
        self.tabs.setFont(QFont("Arial", 20))
        self.tabs.addTab(self.layout1(),"Cihaz Takip Paneli")
        self.tabs.addTab(self.baglanti_paneli(), "Bağlantı Paneli")
        lyt.addWidget(self.tabs)
        self.setLayout(lyt)
        self.integer_validator = QIntValidator()

        "integer validator"


    def layout1(self):
        g1_tab = QWidget()
        layout = QVBoxLayout()
        self.h_list = []
        self.components = []
        colors = ["lemonchiffon","paleturquoise"]
        cnt = 0
        for i in range(4):
            h_box = QHBoxLayout()
            for j in range(8):
                self.h_list.append(self.layout_comp(QVBoxLayout(), QVBoxLayout(), QVBoxLayout(),
                                               QHBoxLayout(), QHBoxLayout(), QVBoxLayout()))
                self.components.append(self.ekran_parcasi(QLabel("------"), QLineEdit(), QLineEdit(),
                                                     QCheckBox(), QLineEdit(), QLineEdit(),
                                                     QPushButton(), QLineEdit(),
                                                          QPushButton(), QPushButton()))

                self.h_list[cnt].v1.addWidget(self.components[cnt].label)
                self.h_list[cnt].v2.addWidget(self.components[cnt].sol1)
                self.h_list[cnt].v2.addWidget(self.components[cnt].sol2)
                self.h_list[cnt].h1.addLayout(self.h_list[cnt].v2)
                self.h_list[cnt].h1.addWidget(self.components[cnt].temp)
                self.h_list[cnt].v4.addWidget(self.components[cnt].start)
                self.h_list[cnt].v4.addWidget(self.components[cnt].sag1)
                self.h_list[cnt].h1.addLayout(self.h_list[cnt].v4)

                self.h_list[cnt].v1.addLayout(self.h_list[cnt].h1)


                self.h_list[cnt].h2.addWidget(self.components[cnt].checkbox)
                self.h_list[cnt].h2.addWidget(self.components[cnt].alt1)
                self.h_list[cnt].h2.addWidget(self.components[cnt].alt2)
                self.h_list[cnt].h2.addWidget(self.components[cnt].alt3)

                self.h_list[cnt].v1.addLayout(self.h_list[cnt].h2)


                self.h_list[cnt].v1.setSpacing(0)
                self.h_list[cnt].v1.addStretch()
                self.h_list[cnt].v1.addSpacing(5)
                h_box.addLayout(self.h_list[cnt].v1)

                cnt +=1
            layout.addLayout(h_box)
            layout.addStretch(1)
        g1_tab.setLayout(layout)
        #g1_tab.setStyleSheet('background-color: beige')
        #g1_tab.setStyleSheet("background-image: url(includes/akgun1.PNG);")
        return g1_tab

    def property_window(self, index):

        self.pushed_button_index = index
        self.property_dialog = QDialog()
        grid = QGridLayout()
        grid.setSpacing(0)
        V_box = QVBoxLayout()
        V_box.setSpacing(0)
        H_box = QHBoxLayout()
        H_box.setSpacing(0)
        self.property_dialog.setGeometry(300,300,300,250)
        self.property_dialog.setMaximumSize(350,300)
        self.property_dialog.setWindowTitle("Ayar Penceresi")


        button_send = QPushButton("Çıkış")
        button_cancel = QPushButton("ONAYLA")
        self.line_edits = list()
        for i in range(5):
            self.line_edits.append(QLineEdit())
        for i in range(1,5):
            self.line_edits[i].setValidator(self.integer_validator)

        grid.addWidget(QLabel("Cihaz Etiketi:"), 1, 1, Qt.AlignLeft)
        grid.addWidget(QLabel("Baudrate:"), 2, 1, Qt.AlignLeft)
        grid.addWidget(QLabel("ID:"), 3, 1, Qt.AlignLeft)
        grid.addWidget(QLabel("Alt Sıcaklık:"), 4, 1, Qt.AlignLeft)
        grid.addWidget(QLabel("Üst Sıcaklık:"), 5, 1, Qt.AlignLeft)
        grid.addWidget(self.line_edits[0], 1, 2, Qt.AlignLeft)
        grid.addWidget(self.line_edits[1], 2, 2, Qt.AlignLeft)
        grid.addWidget(self.line_edits[2], 3, 2, Qt.AlignLeft)
        grid.addWidget(self.line_edits[3], 4, 2, Qt.AlignLeft)
        grid.addWidget(self.line_edits[4], 5, 2, Qt.AlignLeft)


        V_box.addLayout(grid)
        H_box.addWidget(button_cancel)
        H_box.addWidget(button_send)
        V_box.addLayout(H_box)
        self.property_dialog.setLayout(V_box)
        button_cancel.clicked.connect(lambda :self.property_close(self.pushed_button_index))
        button_send.clicked.connect(self.property_Jclose)

        if self.components[index].label.text() != "------":
            self.line_edits[0].setText(self.components[index].label.text())

        self.property_dialog.setModal(True)
        self.property_dialog.exec()

    def mail_window(self):
        self.mail_dialog = QDialog()
        self.mail_dialog.setWindowTitle("Mail Ekleme Penceresi")
        self.mail_dialog.setGeometry(900,250,200,150)
        self.mail_dialog.setMaximumSize(250,200)
        grid_mail = QGridLayout()
        v_box = QVBoxLayout()
        self.list_mailD = []
        mail_label1 = QLabel("Mail Adresleri")
        mail_label1.setAlignment(Qt.AlignCenter)
        mail_label1.setFont(QFont("Arial",20))
        v_box.addWidget(mail_label1)

        for i in range(1, 6):
            self.list_mailD.append(self.mail_class(QCheckBox(), QLineEdit()))
            grid_mail.addWidget(self.list_mailD[i - 1].checkB, i, 1, Qt.AlignLeft)
            grid_mail.addWidget(self.list_mailD[i - 1].lineE, i, 2, Qt.AlignLeft)
        v_box.addLayout(grid_mail)
        button_kaydet = QPushButton("Kaydet")
        button_cıkıs = QPushButton("Çıkış")
        hbox = QHBoxLayout()
        hbox.addWidget(button_kaydet)
        hbox.addWidget(button_cıkıs)
        hbox.setSpacing(0)
        v_box.addLayout(hbox)
        v_box.setSpacing(0)
        self.mail_dialog.setLayout(v_box)

        doc_folder = shell.SHGetFolderPath(0, shellcon.CSIDL_PERSONAL, None, 0)
        doc_folder = doc_folder + r"\AKGUN ESM\databases\mailler.db"
        con = sqlite3.connect(doc_folder)
        cursor = con.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS mail_db (id INTEGER, mail TEXT, checkB bool)")
        con.commit()
        items = cursor.execute(f"SELECT * FROM mail_db").fetchall()
        if items != []:
            for i in range(len(items)):
                index = items[i][0]-1
                self.list_mailD[index].lineE.setText(items[i][1])
                self.list_mailD[index].checkB.setChecked(int(items[i][2]))
        button_kaydet.clicked.connect(lambda: self.mail_kaydet(cursor, con, items))
        button_cıkıs.clicked.connect(self.mail_dialog.close)
        self.mail_dialog.setModal(True)
        self.mail_dialog.exec()

    def mail_kaydet(self, cursor, con, items):


        for i in range(len(self.list_mailD)):
            if re.search(self.regex, self.list_mailD[i].lineE.text()):
                if self.list_mailD[i].lineE.text() not in items:
                    cursor.execute("DELETE FROM mail_db WHERE id = ?", (i+1,))
                    cursor.execute("INSERT INTO mail_db VALUES(?, ?, ?)", (i+1, self.list_mailD[i].lineE.text(),
                                                                           self.list_mailD[i].checkB.isChecked()))
                    con.commit()

        mail_list = cursor.execute(f"SELECT * FROM mail_db").fetchall()
        self.mail_dialog.close()
        self.MAIL_LIST(mail_list)

    class mail_class():
        def __init__(self, checkB, lineE):
            self.checkB = checkB
            self.lineE = lineE

    def baglanti_paneli(self):
        "ELEMANLARI TANIMLIYORUZ"

        self.baglanti_widget = QWidget() #pencere
        self.msg_box = QMessageBox()
        self.Hbox_main = QHBoxLayout()
        self.Vbox_left = QVBoxLayout()
        self.Vbox_timeout = QVBoxLayout()
        self.Vbox_polltime = QVBoxLayout()
        self.Vbox_button = QVBoxLayout()
        self.Vbox_port = QVBoxLayout()
        self.Hbox_leftTop = QHBoxLayout()
        self.Hbox_ip = QHBoxLayout()
        self.Hbox_dev = QHBoxLayout()
        self.Hbox_list = QHBoxLayout()
        self.Vbox_ip = QVBoxLayout()
        self.Vbox_dev =QVBoxLayout()


        self.label_timeout = QLabel("Timeout")
        self.label_polltime = QLabel("PollTime")
        self.label_port = QLabel("PORT")
        self.text_timeout = QLineEdit()
        self.text_polltime = QLineEdit()
        self.text_port = QLineEdit()
        self.button_start = QPushButton("BAŞLAT")
        self.button_stop = QPushButton("DURDUR")
        self.list_ip = QListWidget()

        self.list_dev = QListWidget()

        self.label_ip = QLabel("IP")
        self.label_dev = QLabel("CİHAZLAR")
        self.button_ip_add = QPushButton("EKLE")
        self.button_ip_del = QPushButton("SİL")
        self.button_dev_add = QPushButton("EKLE")
        self.button_dev_del = QPushButton("SİL")

        "LAYOUT YERLEŞİMİ"
        self.Vbox_timeout.addWidget(self.label_timeout)
        self.Vbox_timeout.addWidget(self.text_timeout)

        self.Vbox_polltime.addWidget(self.label_polltime)
        self.Vbox_polltime.addWidget(self.text_polltime)

        self.Vbox_button.addWidget(self.button_start)
        self.Vbox_button.addWidget(self.button_stop)

        self.Vbox_port.addWidget(self.label_port)
        self.Vbox_port.addWidget(self.text_port)


        self.Hbox_leftTop.addLayout(self.Vbox_timeout)
        self.Hbox_leftTop.addLayout(self.Vbox_polltime)
        self.Hbox_leftTop.addLayout(self.Vbox_port)
        self.Hbox_leftTop.addLayout(self.Vbox_button)

        self.Hbox_ip.addWidget(self.button_ip_add)
        self.Hbox_ip.addWidget(self.button_ip_del)

        self.Vbox_ip.addWidget(self.label_ip)
        self.Vbox_ip.addWidget(self.list_ip)
        self.Vbox_ip.addLayout(self.Hbox_ip)

        self.Hbox_dev.addWidget(self.button_dev_add)
        self.Hbox_dev.addWidget(self.button_dev_del)

        self.Vbox_dev.addWidget(self.label_dev)
        self.Vbox_dev.addWidget(self.list_dev)
        self.Vbox_dev.addLayout(self.Hbox_dev)

        self.Hbox_list.addLayout(self.Vbox_ip)
        self.Hbox_list.addLayout(self.Vbox_dev)

        self.Vbox_left.addLayout(self.Hbox_leftTop)
        #self.Vbox_left.addSpacing(30)

        self.Hbox_leftAll = QHBoxLayout()
        self.label_line = QLabel()
        self.Hbox_leftAll.addLayout(self.Vbox_left)
        self.Hbox_leftAll.addWidget(self.label_line)
        #self.Hbox_leftAll.addSpacing(80)

        "Orta Taraf"
        self.label_mid = QLabel("KONFİGÜRASYON AYARLARI")
        self.label_line2 = QLabel()
        self.label_mid1 = QLabel("Anlık ID")
        self.label_mid2 = QLabel("Anlık Baud")
        self.label_mid3 = QLabel("Güncel ID")
        self.label_mid4 = QLabel("Güncel Baud")
        self.text_mid1 = QLineEdit()
        self.text_mid2 = QLineEdit()
        self.text_mid3 = QLineEdit()
        self.text_mid4 = QLineEdit()
        self.button_mid1 = QPushButton("AYARLA")
        self.button_mid1_1 = QPushButton("Mail Aktif")
        self.button_mid1_2 = QPushButton("Mail Listesi")
        self.button_mid2 = QPushButton("Sesi Kapat")
        self.button_mid3 = QPushButton("SIFIRLA")
        self.Hbox_mid_bot = QHBoxLayout()
        self.cmd_plus = QListWidget()
        #self.button_mid2 = QPushButton("YAZ")
        self.Vbox_mid = QVBoxLayout()
        self.grid_mid = QGridLayout()
        self.grid_mid.addWidget(self.label_mid1, 1, 1, Qt.AlignCenter)
        self.grid_mid.addWidget(self.label_mid2, 2, 1, Qt.AlignCenter)
        self.grid_mid.addWidget(self.label_mid3, 3, 1, Qt.AlignCenter)
        self.grid_mid.addWidget(self.label_mid4, 4, 1, Qt.AlignCenter)
        self.grid_mid.addWidget(self.text_mid1, 1, 2, Qt.AlignCenter)
        self.grid_mid.addWidget(self.text_mid2, 2, 2, Qt.AlignCenter)
        self.grid_mid.addWidget(self.text_mid3, 3, 2, Qt.AlignCenter)
        self.grid_mid.addWidget(self.text_mid4, 4, 2, Qt.AlignCenter)
        self.grid_mid.addWidget(self.button_mid1, 5, 2, Qt.AlignCenter)
        #self.grid_mid.addWidget(self.button_mid2, 5, 2, Qt.AlignCenter)

        self.Vbox_mid.addWidget(self.label_mid)
        self.Vbox_mid.addLayout(self.grid_mid)
        #self.Vbox_mid.setAlignment(Qt.AlignCenter)
        self.Vbox_mid.addWidget(self.label_line2)
        self.Hbox_mid_bot.addWidget(self.button_mid1_1)
        self.Hbox_mid_bot.addWidget(self.button_mid1_2)
        self.Hbox_mid_bot.addWidget(self.button_mid2)
        self.Hbox_mid_bot.addWidget(self.button_mid3)
        self.Vbox_mid.addLayout(self.Hbox_mid_bot)
        self.Vbox_mid.addWidget(self.cmd_plus)





        "SAG TARAF"
        self.Vbox_RightAll = QVBoxLayout()

        self.label_tarih = QLabel("Tarih Aralığı")
        self.label_cihazID = QLabel("Cihaz ID")
        self.button_excel = QPushButton("EXCEL'E\nAKTAR")
        self.button_cizim = QPushButton("GRAFİK\nAL")
        self.label_klavuz = QLabel()
        self.pixmap = QPixmap(r'includes\usage.PNG')
        self.label_klavuz.setPixmap(self.pixmap)
        self.label_marka = QLabel()
        self.pixmap2 = QPixmap(r'includes\akgun.PNG')
        self.label_marka.setPixmap(self.pixmap2)
        self.label_line1 = QLabel()


        self.combobox_tarih = QComboBox()
        self.combobox_ID = QComboBox()
        self.Hbox_tarih = QHBoxLayout()
        self.Hbox_cihaz = QHBoxLayout()
        self.Hbox_button = QHBoxLayout()
        self.Hbox_output = QHBoxLayout()
        self.Vbox_output = QVBoxLayout()
        self.Hbox_rightAll = QHBoxLayout()

        self.Hbox_tarih.addWidget(self.label_tarih)
        self.Hbox_tarih.addWidget(self.combobox_tarih)
        self.Hbox_cihaz.addWidget(self.label_cihazID)
        self.Hbox_cihaz.addWidget(self.combobox_ID)
        self.Hbox_button.addWidget(self.button_cizim)
        self.Hbox_button.addWidget(self.button_excel)
        self.Vbox_output.addLayout(self.Hbox_tarih)
        self.Vbox_output.addLayout(self.Hbox_cihaz)
        self.Vbox_output.addLayout(self.Hbox_button)
        self.Vbox_output.addWidget(self.label_klavuz)
        self.Vbox_output.addWidget(self.label_marka)
        self.Hbox_rightAll.addWidget(self.label_line1)
        #self.Hbox_rightAll.addSpacing(300)

        self.Hbox_rightAll.addLayout(self.Vbox_output)


        self.Vbox_left.addLayout(self.Hbox_list)

        self.Hbox_main.addLayout(self.Hbox_leftAll)
        #self.Hbox_main.setSpacing(5)

        self.Hbox_main.addLayout(self.Vbox_mid)
        #self.Hbox_main.addSpacing(30)

        self.Hbox_main.addLayout(self.Hbox_rightAll)
        self.baglanti_widget.setLayout(self.Hbox_main)
        self.baglanti_paneli_ayarlar()
        return self.baglanti_widget

    def baglanti_paneli_ayarlar(self):
        "SOL TARAF"
        self.label_timeout.setFont(QFont("Arial", 20))
        self.label_timeout.setFixedSize(150, 50)
        #self.label_timeout.setStyleSheet("color:red")
        self.label_timeout.setAlignment(Qt.AlignCenter)

        self.label_polltime.setFont(QFont("Arial",20))
        self.label_polltime.setFixedSize(150, 50)
        #self.label_polltime.setStyleSheet("color:red")
        self.label_polltime.setAlignment(Qt.AlignCenter)

        self.label_port.setFont(QFont("Arial", 20))
        self.label_port.setFixedSize(150, 50)
        #self.label_port.setStyleSheet("color:red")
        self.label_port.setAlignment(Qt.AlignCenter)

        self.text_timeout.setFixedSize(150, 50)
        self.text_polltime.setFixedSize(150, 50)
        self.text_port.setFixedSize(150, 50)
        self.text_port.setFont(QFont("Arial",25))
        self.text_timeout.setFont(QFont("Arial",25))
        self.text_polltime.setFont(QFont("Arial",25))
        self.text_port.setValidator(QIntValidator())
        self.text_timeout.setValidator(QIntValidator())
        self.text_polltime.setValidator(QIntValidator())


        self.button_stop.setFixedSize(150, 50)
        #self.button_stop.setStyleSheet("background-color:orange")
        self.button_stop.setFont(QFont("Arial",20))
        self.button_start.setFixedSize(150, 50)
        #self.button_start.setStyleSheet("background-color:orange")
        self.button_start.setFont(QFont("Arial",20))

        self.label_ip.setFont(QFont("Arial", 30))
        self.label_ip.setFixedSize(320, 60)
        #self.label_ip.setStyleSheet("color:red")
        self.label_ip.setAlignment(Qt.AlignCenter)

        self.label_dev.setFont(QFont("Arial", 30))
        self.label_dev.setFixedSize(320, 60)
        #self.label_dev.setStyleSheet("color:red")
        self.label_dev.setAlignment(Qt.AlignCenter)

        self.list_ip.setFixedSize(320,500)
        self.list_dev.setFixedSize(320,500)

        self.button_dev_add.setFixedSize(150,40)
        self.button_ip_add.setFixedSize(150,40)
        self.button_dev_del.setFixedSize(150,40)
        self.button_ip_del.setFixedSize(150,40)
        #self.button_dev_add.setStyleSheet("background-color:orange")
        #self.button_ip_del.setStyleSheet("background-color:orange")
        #self.button_ip_add.setStyleSheet("background-color:orange")
        #self.button_dev_del.setStyleSheet("background-color:orange")
        self.button_ip_add.setFont(QFont("Arial",20))
        self.button_dev_add.setFont(QFont("Arial",20))
        self.button_dev_del.setFont(QFont("Arial",20))
        self.button_ip_del.setFont(QFont("Arial",20))
        self.Hbox_ip.setSpacing(0)
        self.Hbox_dev.setSpacing(0)
        self.Hbox_leftTop.setAlignment(Qt.AlignLeft)
        self.Hbox_list.setAlignment(Qt.AlignLeft)
        self.Vbox_left.setAlignment(Qt.AlignTop)
        self.label_line.setFixedSize(5, 950)
        self.label_line.setStyleSheet("border :5px solid ;"
                    "border-color : black; ")
        self.label_line.setAlignment(Qt.AlignTop)

        "MİD LAYOUT"
        self.label_mid.setFixedSize(600,50)
        self.label_mid.setFont(QFont("Arial",20))
        #self.label_mid.setStyleSheet("color:red")
        self.label_mid.setAlignment(Qt.AlignCenter)

        self.label_mid1.setFixedSize(200,50)
        self.label_mid1.setFont(QFont("Arial",20))
        #self.label_mid1.setStyleSheet("color:red")

        self.label_mid2.setFixedSize(200,50)
        self.label_mid2.setFont(QFont("Arial",20))
        #self.label_mid2.setStyleSheet("color:red")

        self.label_mid3.setFixedSize(200,50)
        self.label_mid3.setFont(QFont("Arial",20))
        #self.label_mid3.setStyleSheet("color:red")

        self.label_mid4.setFixedSize(200,50)
        self.label_mid4.setFont(QFont("Arial",20))
        #self.label_mid4.setStyleSheet("color:red")

        self.text_mid1.setFixedSize(200,50)
        self.text_mid2.setFixedSize(200,50)
        self.text_mid3.setFixedSize(200,50)
        self.text_mid4.setFixedSize(200,50)
        self.text_mid1.setFont(QFont("Arial",25))
        self.text_mid2.setFont(QFont("Arial",25))
        self.text_mid3.setFont(QFont("Arial",25))
        self.text_mid4.setFont(QFont("Arial",25))
        intval = QIntValidator()
        self.text_mid3.setValidator(intval)
        self.text_mid2.setValidator(intval)
        self.text_mid4.setValidator(intval)
        self.text_mid1.setValidator(intval)

        self.button_mid1.setFixedSize(200,50)
        #self.button_mid1.setStyleSheet("background-color:orange")
        self.button_mid1.setFont(QFont("Arial", 20))
        self.button_mid2.setFixedSize(150,50)
        #self.button_mid2.setStyleSheet("background-color:orange")
        self.button_mid2.setFont(QFont("Arial", 20))
        self.button_mid3.setFixedSize(150,50)
        #self.button_mid3.setStyleSheet("background-color:orange")
        self.button_mid3.setFont(QFont("Arial", 20))

        self.button_mid1_1.setFixedSize(150,50)

        self.button_mid1_1.setFont(QFont("Arial", 20))

        self.button_mid1_2.setFixedSize(150,50)
        self.button_mid1_2.setFont(QFont("Arial", 20))


        self.label_line2.setFixedSize(700, 5)
        self.label_line2.setStyleSheet("border :5px solid ;"
                    "border-color : black; ")
        self.label_line2.setAlignment(Qt.AlignCenter)
        self.Vbox_mid.setAlignment(Qt.AlignCenter)
        self.Vbox_mid.setAlignment(Qt.AlignTop)
        self.cmd_plus.setStyleSheet("background-color:black; color:white")
        self.cmd_plus.setFont(QFont("Arial",13))



        "Right Layout"
        self.label_line1.setFixedSize(5, 950)
        self.label_line1.setStyleSheet("border :5px solid ;"
                    "border-color : black; ")
        self.label_line1.setAlignment(Qt.AlignTop)

        self.label_tarih.setFont(QFont("Arial", 20))
        self.label_tarih.setFixedSize(150, 50)
        #self.label_tarih.setStyleSheet("color:red")
        self.label_tarih.setAlignment(Qt.AlignCenter)
        self.label_cihazID.setFont(QFont("Arial", 20))
        self.label_cihazID.setFixedSize(150, 50)
        #self.label_cihazID.setStyleSheet("color:red")
        self.label_cihazID.setAlignment(Qt.AlignCenter)

        self.button_excel.setFixedSize(150,70)
        #self.button_excel.setStyleSheet("background-color:orange")
        self.button_excel.setFont(QFont("Arial",20))
        self.button_cizim.setFixedSize(150,70)
        #self.button_cizim.setStyleSheet("background-color:orange")
        self.button_cizim.setFont(QFont("Arial",20))

        self.combobox_ID.setFixedSize(150, 50)
        self.combobox_ID.setFont(QFont("Arial",25))

        self.combobox_tarih.setFixedSize(150, 50)
        self.combobox_tarih.setFont(QFont("Arial",15))

        self.list_dev.setFont(QFont("Arial",20))
        self.list_ip.setFont(QFont("Arial",20))

    class ekran_parcasi():

        def __init__(self, label, sol1, sol2, checkbox, alt1, alt2, alt3, temp, start, sag1):
            self.label = label
            self.sol1 = sol1
            self.sol2 = sol2
            self.checkbox = checkbox
            self.alt1 = alt1
            self.alt2 = alt2
            self.alt3 = alt3
            self.temp = temp
            self.start = start
            self.sag1 = sag1

            "AYARLAR SİZE"
            self.label.setFixedSize(QSize(200, 50))
            self.label.setAlignment(Qt.AlignCenter)
            self.sol1.setFixedSize(QSize(50, 50))
            self.sol2.setFixedSize(QSize(50, 50))
            self.checkbox.setStyleSheet("QCheckBox::indicator"
                                   "{"
                                   "width :50px;"
                                   "height : 50px;"
                                   "}")
            self.checkbox.setFixedSize(QSize(50, 50))
            self.alt1.setFixedSize(QSize(50, 50))
            self.alt2.setFixedSize(QSize(50, 50))
            self.alt3.setFixedSize(QSize(50, 50))
            self.temp.setFixedSize(QSize(100, 100))
            self.start.setStyleSheet("QPushButton{background-image: url(includes/settings_but.PNG)}")
            self.temp.setAlignment(Qt.AlignCenter)
            self.alt2.setAlignment(Qt.AlignCenter)
            self.alt1.setAlignment(Qt.AlignCenter)
            self.sol2.setAlignment(Qt.AlignCenter)
            self.sol1.setAlignment(Qt.AlignCenter)

            self.start.setFixedSize(QSize(50, 50))
            self.sag1.setFixedSize(QSize(50,50))
            self.sag1.setStyleSheet("background-color:green")
            "AYARLAR FONT"
            self.start.setFont(QFont("Arial",13, weight=QFont.Bold))
            self.sag1.setFont(QFont("Arial",20))
            self.sol1.setFont(QFont("Arial",20))
            self.label.setStyleSheet("color:red")
            self.label.setFont(QFont("arial",15))
            self.temp.setFont(QFont("arial",40))
            self.sol2.setFont(QFont("arial",20))
            self.alt3.setFont(QFont("arial",20))
            self.alt2.setFont(QFont("arial",20))
            self.alt1.setFont(QFont("arial",20))
            "AYARLAR BACKGROUND"
            #self.start.setStyleSheet("background-color:orange")
            self.sol2.setStyleSheet("background-color:lemonchiffon")
            self.sol1.setStyleSheet("background-color:lemonchiffon")
            self.alt2.setStyleSheet("background-color:lemonchiffon")
            self.alt3.setStyleSheet("background-color:green")
            self.alt1.setStyleSheet("background-color:lemonchiffon")
            self.temp.setStyleSheet("background-color:lemonchiffon")

    class layout_comp():

        def __init__(self, v1, v2, v3, h1, h2, v4):
            """
            :param v1: label + h1 birleşimi
            :param v2: s1, s2, cb birleşimi
            :param v3: temp + h2 birleşimi
            :param v4: start button +sag1 birlesimi
            :param h1: v2 + v3 birleşimi + button
            :param h2: alt text

            """
            self.v1 = v1
            self.v2 = v2
            self.v3 = v3
            self.h1 = h1
            self.h2 = h2
            self.v4 = v4

    class PlotCanvas(FigureCanvasQTAgg):

        def __init__(self, database, label="Sıcaklık", parent=None, width=5, height=4, dpi=100):
            fig = Figure(figsize=(width, height), dpi=dpi)
            self.axes = fig.add_subplot(111)
            self.dTime = database[0]
            self.database = database[1]
            self.label = label
            FigureCanvasQTAgg.__init__(self, fig)
            self.setParent(parent)

            FigureCanvasQTAgg.setSizePolicy(self,
                    QSizePolicy.Expanding,
                    QSizePolicy.Expanding)
            FigureCanvasQTAgg.updateGeometry(self)

            self.plot()
        def plot(self):
            self.axes.plot(self.dTime, self.database, 'r-')
            self.axes.set_title(f'{self.label} Takip')
            self.draw()

