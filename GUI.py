import modbus_components
from logfile import logfile, get_tables, get_graph, database_to_excel, open_register_folders
#from send_mail import SMTP_MAIL
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import QFont
import pandas as pd
import sys
import sqlite3
import locale
from win32com.shell import shell, shellcon
import smtplib
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import date, timedelta, datetime
import winsound
from pymodbus.client.sync import ModbusTcpClient as ModbusClient
from pymodbus.transaction import ModbusRtuFramer
from pymodbus.exceptions import ModbusIOException
locale.setlocale(locale.LC_ALL, 'tr')

class C_Thread(QObject):

    result = pyqtSignal(list)
    client_message = pyqtSignal(bool)
    closing_signal = pyqtSignal(bool)
    uyari_Signal = pyqtSignal(list)
    BeniBul_Signal = pyqtSignal(list)
    Write_other_Signal = pyqtSignal(list)
    configurate_Signal = pyqtSignal(list)
    smpt_Signal = pyqtSignal(str)
    def __init__(self, parent=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.Color_Green = "#008000"
        self.Color_Red = "#FF0000"
        self.Color_Blue = "#0000FF"
        self.write_registers = [4, 6, 8]

    @pyqtSlot(list)
    def Start_TCP_Client(self, client_info):
        self.ip = client_info[0]
        self.port = client_info[1]
        self.unit = client_info[2]
        self.polltime = client_info[3]
        self.timeout = client_info[4]
        self.client = ModbusClient(self.ip, port=self.port, framer=ModbusRtuFramer, timeout= self.timeout)
        connection = self.client.connect()
        self.client_message.emit(connection)
        self.quit = False

    @pyqtSlot(bool)
    def read_registers(self, m):
        wait_time = len(self.unit)*100
        wait_Time1 = self.polltime*1000 - wait_time
        while True:

            for i in range(len(self.unit)):
                register = self.client.read_holding_registers(0,9, unit = int(self.unit[i]))
                if isinstance(register, ModbusIOException):
                    self.result.emit([ModbusIOException, self.unit[i]])
                else:
                    self.result.emit([register.registers, self.unit[i]])
                QThread.msleep(100)
            if self.quit == True:
                closed_connection = self.client.close()
                self.closing_signal.emit(True)
                break
            if wait_Time1 > 0:
                QThread.msleep(wait_Time1)

    def Close_Connection(self, m):
        self.quit = True

    def Uyari_Toggle(self, m):
        """
        m[0] => yazılacak adres
        m[1] => yazılacak unit
        m[2] => renk
        m[3] => buton indexi, Dönüşte hangi butonun rengini değiştireceğimizde
        kullanılacak

        """
        if m[2] == self.Color_Green:
            self.client.write_register(m[0], 1, unit = m[1])
            self.uyari_Signal.emit([m[3], f"background-color:{self.Color_Red}",
                                    f"{m[1]}---> Uyarı => 1 yapıldı", True])
        else:
            self.client.write_register(m[0], 0, unit = m[1])
            self.uyari_Signal.emit([m[3], f"background-color:{self.Color_Green}",
                                    f"{m[1]}---> Uyarı => 0 yapıldı", True])

    def Beni_Bul(self, m):
        """
        m[0] => yazılacak adres
        m[1] => yazılacak unit
        m[2] => renk
        m[3] => buton indexi, Dönüşte hangi butonun rengini değiştireceğimizde
        kullanılacak
        """
        if m[2] == self.Color_Green:
            self.client.write_register(m[0], 1, unit = m[1])
            QThread.msleep(500)
            self.BeniBul_Signal.emit([m[3], f"background-color:{self.Color_Blue}",
                                    f"{m[1]}---> Beni Bul => 1 yapıldı", True])
        else:
            self.client.write_register(m[0], 0, unit = m[1])
            QThread.msleep(500)
            self.BeniBul_Signal.emit([m[3], f"background-color:{self.Color_Green}",
                                    f"{m[1]}---> Beni Bul => 0 yapıldı", True])

    def Write_other_registers(self, m):
        """
        m[0] => Properties ( Register Class ını içeriyor )
        .baudrate
        .ID = ID
        .max_temp
        ÖZELLİKLERİNE YAZMA YAPACAGIZ
        m[1] => Unit
        m[2] => button index
        """
        out = []
        change_list = [m[0].baudrate, m[0].ID, m[0].max_temp]

        for i in range(len(change_list)):
            if change_list[i] != '':
                try:
                    self.client.write_register(self.write_registers[i], int(change_list[i]), unit = m[1])
                    out.append(f"{m[1]} : {self.write_registers[i]}. nolu adrese {change_list[i]} yazıldı")
                except:
                    pass
        self.Write_other_Signal.emit([out, m[2]])

    def New_Device_Configurate(self, m):
        """
        m[0] => IP
        m[1] => port
        m[2] => baud / 4 e yazılacak
        m[3] => ID / 6 ya yazılacak
        """
        configurate_client = ModbusClient(m[0], port = m[1], framer = ModbusRtuFramer)
        started = configurate_client.connect()
        if started:
            configurate_client.write_register(4, m[2], unit = 1)
            configurate_client.write_register(6, m[3], unit = 1)
            self.configurate_Signal.emit(["Cihazın Konfigürasyon Ayarları Yapıldı"
                                         f"Yeni ID: {m[3]} / Yeni Baud: {m[2]}",
                                          True, m[3]])
            configurate_client.close()
        else:
            self.configurate_Signal.emit(["Konfigürasyon Sırasında Hata.. Tekrar Deneyin", False])

    def SMTP_MAIL(self, input):
        """
        :param input[0] => mail_icerigi:
        :param input[1] => mail_list:
        """
        try:
            strFrom = 'akgunelektrik.arge@gmail.com'
            for i in input[1]:
                msgRoot = MIMEMultipart('related')
                msgRoot['From'] = strFrom
                msgRoot['Subject'] = 'AKGUN ESM'
                msgRoot['To'] = i
                msgRoot.preamble = '====================================================='
                msgAlternative = MIMEMultipart('alternative')
                msgRoot.attach(msgAlternative)
                msgText = msgText = MIMEText(f'{input[0]}<br><img src="cid:image1"><br>', 'html')
                msgAlternative.attach(msgText)
                # msgText = MIMEText('<b>This is the <i>HTML</i> content of this email</b> it contains an image.<br><img src="cid:image1"><br>', 'html')
                # Attach the above html content MIMEText object to the msgAlternative object.
                # msgAlternative.attach(msgText)
                fp = open(r'includes\mail_logo.PNG', 'rb')
                msgImage = MIMEImage(fp.read())
                fp.close()
                msgImage.add_header('Content-ID', '<image1>')
                msgRoot.attach(msgImage)
                smtp = smtplib.SMTP('smtp.gmail.com', 587)
                smtp.ehlo()
                smtp.starttls()
                smtp.login('akgunelektrik.arge@gmail.com', 'Misafir2020')
                smtp.sendmail(strFrom, i, msgRoot.as_string())
                smtp.quit()
                self.smpt_Signal.emit("Sıcaklık Aşımından Dolayı Mail Gönderildi")
        except:
            self.smpt_Signal.emit("Sıcaklık Aşımından Dolayı Mail Gönderme İşlemi Başarısız")

class functions(modbus_components.main_window):

    client_Signal = pyqtSignal(list)
    pool_Signal = pyqtSignal(bool)
    close_Signal = pyqtSignal(bool)
    uyari_toggle_Signal = pyqtSignal(list)
    Benibul_Signal = pyqtSignal(list)
    Other_Registers = pyqtSignal(list)
    configurate_Signal = pyqtSignal(list)
    mail_Signal = pyqtSignal(list)
    def __init__(self):
        super().__init__()
        self.load_info()
        self.components_clicked()
        self.Start_Thread()

    "ELEMANLARA TIKLANDIGINDA NEREYE BAGLANACAK SECİLİR"
    def components_clicked(self):
        self.button_mid1_2.clicked.connect(self.mail_window)
        self.button_mid1_1.clicked.connect(self.mail_toggle)
        self.button_start.clicked.connect(self.TCP_client_start)
        self.button_stop.clicked.connect(self.TCP_client_stop)
        self.button_ip_add.clicked.connect(self.add_ip)
        self.button_ip_del.clicked.connect(self.del_ip)
        self.button_dev_add.clicked.connect(self.add_device)
        self.button_dev_del.clicked.connect(self.del_device)
        self.button_cizim.clicked.connect(self.drawWindow)
        self.button_excel.clicked.connect(self.output_excel)
        self.button_mid1.clicked.connect(self.configurate)
        self.button_mid2.clicked.connect(self.toggle_voice)
        self.button_mid3.clicked.connect(self.cmd_clear)
        self.components[0].alt3.clicked.connect(lambda : self.toggle_uyari(0))
        self.components[1].alt3.clicked.connect(lambda : self.toggle_uyari(1))
        self.components[2].alt3.clicked.connect(lambda : self.toggle_uyari(2))
        self.components[3].alt3.clicked.connect(lambda : self.toggle_uyari(3))
        self.components[4].alt3.clicked.connect(lambda : self.toggle_uyari(4))
        self.components[5].alt3.clicked.connect(lambda : self.toggle_uyari(5))
        self.components[6].alt3.clicked.connect(lambda : self.toggle_uyari(6))
        self.components[7].alt3.clicked.connect(lambda : self.toggle_uyari(7))
        self.components[8].alt3.clicked.connect(lambda : self.toggle_uyari(8))
        self.components[9].alt3.clicked.connect(lambda : self.toggle_uyari(9))
        self.components[10].alt3.clicked.connect(lambda : self.toggle_uyari(10))
        self.components[11].alt3.clicked.connect(lambda : self.toggle_uyari(11))
        self.components[12].alt3.clicked.connect(lambda : self.toggle_uyari(12))
        self.components[13].alt3.clicked.connect(lambda : self.toggle_uyari(13))
        self.components[14].alt3.clicked.connect(lambda : self.toggle_uyari(14))
        self.components[15].alt3.clicked.connect(lambda : self.toggle_uyari(15))
        self.components[16].alt3.clicked.connect(lambda : self.toggle_uyari(16))
        self.components[17].alt3.clicked.connect(lambda : self.toggle_uyari(17))
        self.components[18].alt3.clicked.connect(lambda : self.toggle_uyari(18))
        self.components[19].alt3.clicked.connect(lambda : self.toggle_uyari(19))
        self.components[20].alt3.clicked.connect(lambda : self.toggle_uyari(20))
        self.components[21].alt3.clicked.connect(lambda : self.toggle_uyari(21))
        self.components[22].alt3.clicked.connect(lambda : self.toggle_uyari(22))
        self.components[23].alt3.clicked.connect(lambda : self.toggle_uyari(23))
        self.components[24].alt3.clicked.connect(lambda : self.toggle_uyari(24))
        self.components[25].alt3.clicked.connect(lambda : self.toggle_uyari(25))
        self.components[26].alt3.clicked.connect(lambda : self.toggle_uyari(26))
        self.components[27].alt3.clicked.connect(lambda : self.toggle_uyari(27))
        self.components[28].alt3.clicked.connect(lambda : self.toggle_uyari(28))
        self.components[29].alt3.clicked.connect(lambda : self.toggle_uyari(29))
        self.components[30].alt3.clicked.connect(lambda : self.toggle_uyari(30))
        self.components[31].alt3.clicked.connect(lambda : self.toggle_uyari(31))
        self.components[0].start.clicked.connect(lambda: self.property_window(0))
        self.components[1].start.clicked.connect(lambda: self.property_window(1))
        self.components[2].start.clicked.connect(lambda: self.property_window(2))
        self.components[3].start.clicked.connect(lambda: self.property_window(3))
        self.components[4].start.clicked.connect(lambda: self.property_window(4))
        self.components[5].start.clicked.connect(lambda: self.property_window(5))
        self.components[6].start.clicked.connect(lambda: self.property_window(6))
        self.components[7].start.clicked.connect(lambda: self.property_window(7))
        self.components[8].start.clicked.connect(lambda: self.property_window(8))
        self.components[9].start.clicked.connect(lambda: self.property_window(9))
        self.components[10].start.clicked.connect(lambda: self.property_window(10))
        self.components[11].start.clicked.connect(lambda: self.property_window(11))
        self.components[12].start.clicked.connect(lambda: self.property_window(12))
        self.components[13].start.clicked.connect(lambda: self.property_window(13))
        self.components[14].start.clicked.connect(lambda: self.property_window(14))
        self.components[15].start.clicked.connect(lambda: self.property_window(15))
        self.components[16].start.clicked.connect(lambda: self.property_window(16))
        self.components[17].start.clicked.connect(lambda: self.property_window(17))
        self.components[18].start.clicked.connect(lambda: self.property_window(18))
        self.components[19].start.clicked.connect(lambda: self.property_window(19))
        self.components[20].start.clicked.connect(lambda: self.property_window(20))
        self.components[21].start.clicked.connect(lambda: self.property_window(21))
        self.components[22].start.clicked.connect(lambda: self.property_window(22))
        self.components[23].start.clicked.connect(lambda: self.property_window(23))
        self.components[24].start.clicked.connect(lambda: self.property_window(24))
        self.components[25].start.clicked.connect(lambda: self.property_window(25))
        self.components[26].start.clicked.connect(lambda: self.property_window(26))
        self.components[27].start.clicked.connect(lambda: self.property_window(27))
        self.components[28].start.clicked.connect(lambda: self.property_window(28))
        self.components[29].start.clicked.connect(lambda: self.property_window(29))
        self.components[30].start.clicked.connect(lambda: self.property_window(30))
        self.components[31].start.clicked.connect(lambda: self.property_window(31))
        self.components[0].sag1.clicked.connect(lambda: self.toggle_beni_bul(0))
        self.components[1].sag1.clicked.connect(lambda: self.toggle_beni_bul(1))
        self.components[2].sag1.clicked.connect(lambda: self.toggle_beni_bul(2))
        self.components[3].sag1.clicked.connect(lambda: self.toggle_beni_bul(3))
        self.components[4].sag1.clicked.connect(lambda: self.toggle_beni_bul(4))
        self.components[5].sag1.clicked.connect(lambda: self.toggle_beni_bul(5))
        self.components[6].sag1.clicked.connect(lambda: self.toggle_beni_bul(6))
        self.components[7].sag1.clicked.connect(lambda: self.toggle_beni_bul(7))
        self.components[8].sag1.clicked.connect(lambda: self.toggle_beni_bul(8))
        self.components[9].sag1.clicked.connect(lambda: self.toggle_beni_bul(9))
        self.components[10].sag1.clicked.connect(lambda: self.toggle_beni_bul(10))
        self.components[11].sag1.clicked.connect(lambda: self.toggle_beni_bul(11))
        self.components[12].sag1.clicked.connect(lambda: self.toggle_beni_bul(12))
        self.components[13].sag1.clicked.connect(lambda: self.toggle_beni_bul(13))
        self.components[14].sag1.clicked.connect(lambda: self.toggle_beni_bul(14))
        self.components[15].sag1.clicked.connect(lambda: self.toggle_beni_bul(15))
        self.components[16].sag1.clicked.connect(lambda: self.toggle_beni_bul(16))
        self.components[17].sag1.clicked.connect(lambda: self.toggle_beni_bul(17))
        self.components[18].sag1.clicked.connect(lambda: self.toggle_beni_bul(18))
        self.components[19].sag1.clicked.connect(lambda: self.toggle_beni_bul(19))
        self.components[20].sag1.clicked.connect(lambda: self.toggle_beni_bul(20))
        self.components[21].sag1.clicked.connect(lambda: self.toggle_beni_bul(21))
        self.components[22].sag1.clicked.connect(lambda: self.toggle_beni_bul(22))
        self.components[23].sag1.clicked.connect(lambda: self.toggle_beni_bul(23))
        self.components[24].sag1.clicked.connect(lambda: self.toggle_beni_bul(24))
        self.components[25].sag1.clicked.connect(lambda: self.toggle_beni_bul(25))
        self.components[26].sag1.clicked.connect(lambda: self.toggle_beni_bul(26))
        self.components[27].sag1.clicked.connect(lambda: self.toggle_beni_bul(27))
        self.components[28].sag1.clicked.connect(lambda: self.toggle_beni_bul(28))
        self.components[29].sag1.clicked.connect(lambda: self.toggle_beni_bul(29))
        self.components[30].sag1.clicked.connect(lambda: self.toggle_beni_bul(30))
        self.components[31].sag1.clicked.connect(lambda: self.toggle_beni_bul(31))
        "buton basili değilse değer göstermesin. Inaktif için de"

    def mail_toggle(self):
        if self.button_mid1_1.text() == "Mail Aktif":
            self.button_mid1_1.setText("Mail İnaktif")
            self.mail_enable = False
        else:
            self.button_mid1_1.setText("Mail Aktif")
            self.mail_enable = False

    "ONCEKİ AYARLARIN VE DEGERLERİN GERİ YÜKLENMESİ"
    def load_info(self):
        """
        Daha önce kaydedilmiş olan veritabanları yüklenir
        Fonksiyonların komutları fonksiyon combobox ına yüklenir.
        """
        self.Client_on = False
        self.noise_enable = True
        self.mail_enable = True
        self.colors = ["green", "orange", "red"]
        self.database_address, self.log_address, self.xlsx_address = open_register_folders()
        self.text_timeout.setText("2")
        self.text_polltime.setText("2")
        self.text_mid1.setText("1")
        self.text_mid2.setText("13")
        self.text_port.setText("502")
        tarihler = ["Son 100 Veri", "Son 1000 Veri", "Son 10000 Veri"]
        self.combobox_tarih.addItems(tarihler)



        " IP database yükleme "
        try:
            ip_adress = self.database_address + "\ip_database.db"
            con = sqlite3.connect(r"{}".format(ip_adress))
            cursor = con.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            tables = tables[0][0]
            database = pd.read_sql_query(f"SELECT *  from {tables}", con)
            database = database.values.tolist()
            for i in database:
                self.list_ip.insertItem(0, i[0])
            con.close()
        except:
            pass
        try:
            dev_adress = self.database_address + "\dev_database.db"
            con = sqlite3.connect(r"{}".format(dev_adress))
            cursor = con.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            tables = tables[0][0]
            database = pd.read_sql_query(f"SELECT *  from {tables}", con)
            database = database.values.tolist()
            for i in database:
                #box = QCheckBox(i[0])
                #dev_item = QListWidgetItem()
                #self.list_dev.addItem(dev_item)

                #self.list_dev.setItemWidget(dev_item, box)
                self.list_dev.insertItem(0, i[0])
            con.close()
        except:
            pass

        "BAZI BUTONLAR BASLANGICTA INAKTIF OLACAK"
        self.button_stop.setEnabled(False)

        self.cihazlar = [self.list_dev.item(i).text() for i in range(self.list_dev.count())]
        self.combobox_ID.addItems(self.cihazlar)


        past_data = get_tables(self.log_address + "\logs.db")
        for i in range(len(past_data)):
            self.components[i].label.setText(past_data[i].label)
            self.components[i].temp.setText(past_data[i].temp)
            self.temp_background(i)
            self.components[i].sol1.setText(past_data[i].id)
            self.components[i].sol2.setText(past_data[i].baudmode)
            self.components[i].alt2.setText(past_data[i].esik)
            "sağ1 ve esik eklenecek." \
            "sıcaklık icin temp_sensor fonksyionu yazılacak"

            self.properties = [self.registers("", "", "", "", "", 0) for i in range(32)]

        doc_folder = shell.SHGetFolderPath(0, shellcon.CSIDL_PERSONAL, None, 0)
        doc_folder = doc_folder + r"\AKGUN ESM\databases\mailler.db"
        con = sqlite3.connect(doc_folder)
        cursor = con.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS mail_db (id INTEGER, mail TEXT, checkB bool)")
        con.commit()
        items = cursor.execute(f"SELECT * FROM mail_db").fetchall()
        self.mail_list = []
        for i in items:
            if i[2] == 1:
                self.mail_list.append(i[1])
    "SES FONKSIYONLARI"
    def toggle_voice(self):
        if self.button_mid2.text() == "Sesi Kapat":
            self.button_mid2.setText("Sesi Aç")
            self.noise_enable = False
        else:
            self.button_mid2.setText("Sesi Kapat")
            self.noise_enable = True

    def Start_Beep(self):
        if self.noise_enable == True:
            winsound.PlaySound(r"includes\beep3.wav", winsound.SND_FILENAME | winsound.SND_ASYNC)

    "UYARI TOGGLE BUTONU ICIN FONKSIYON"
    def toggle_uyari(self, button_index):
        if len(self.cihazlar) > button_index:
            if self.components[button_index].checkbox.isChecked() and self.Client_on == True:
                self.components[button_index].alt3.setEnabled(False)
                unit = int(self.UNIT[button_index])
                color = self.components[button_index].alt3.palette().button().color().name()
                self.uyari_toggle_Signal.emit([3, unit, color, button_index])

    "UYARIDAN GELEN SONUCLAR BURADA YAZDIRILIR"
    @pyqtSlot(list)
    def toggle_uyari_GUI(self, output):
        """
        output[0] => Buton indexi
        output[1] => Buton Renk ifadesi
        output[2] => Cmd ekran ifadesi
        output[3] => Buton İcin True/False
        """
        loop = QEventLoop()
        QTimer.singleShot(500, loop.quit)
        loop.exec_()

        self.components[output[0]].alt3.setStyleSheet(output[1])
        self.cmd_plus.insertItem(0, output[2])
        self.components[output[0]].alt3.setEnabled(output[3])

    "BENİ BUL TOGGLE BUTONU ICIN FONKSIYON"
    def toggle_beni_bul(self, button_index):
        if len(self.cihazlar) > button_index:
            if self.components[button_index].checkbox.isChecked() and self.Client_on == True:
                self.components[button_index].sag1.setEnabled(False)
                unit = int(self.UNIT[button_index])
                color = self.components[button_index].sag1.palette().button().color().name()
                self.Benibul_Signal.emit([0, unit, color, button_index])

    "BENİ BUL DAN GELEN SONUCLAR BURADA YAZDIRILIR"
    @pyqtSlot(list)
    def toggle_BeniBul_GUI(self, output):
        """
        output[0] => Buton indexi
        output[1] => Buton Renk ifadesi
        output[2] => Cmd ekran ifadesi
        output[3] => Buton İcin True/False
        """
        loop = QEventLoop()
        QTimer.singleShot(500, loop.quit)
        loop.exec_()
        self.components[output[0]].sag1.setStyleSheet(output[1])
        self.cmd_plus.insertItem(0, output[2])
        self.components[output[0]].sag1.setEnabled(output[3])

    "CİHAZ TAKİP PANELİ ÖZELLİKLERİ BU CLASS ALTINDA KAYDEDİLİR"
    class registers():
        def __init__(self, baslik, uyari, baudrate, ID, max_temp, min_temp, send_mail = True):
            self.baslik = baslik
            self.uyari = uyari
            self.baudrate = baudrate
            self.ID = ID
            self.max_temp = max_temp
            self.min_temp = min_temp
            self.send_mail = send_mail

    "SICAKLIGA GÖRE ARKAPLAN DEĞİŞİMİ"
    def temp_background(self, index):
        try:

            if int(self.components[index].temp.text()) < int(self.properties[index].min_temp):
                self.components[index].temp.setStyleSheet(f"background-color:{self.colors[0]}")
                self.properties[index].send_mail = True
            elif int(self.components[index].temp.text()) >= int(self.properties[index].min_temp)\
                    and int(self.components[index].temp.text()) < int(self.properties[index].max_temp):
                self.components[index].temp.setStyleSheet(f"background-color:{self.colors[1]}")
                self.properties[index].send_mail = True
            else:
                self.components[index].temp.setStyleSheet(f"background-color:{self.colors[2]}")
                self.Start_Beep()
                if self.mail_enable == True:
                    if self.properties[index].send_mail == True:
                        self.properties[index].send_mail = False
                        self.mail_Signal.emit([(f"<p><b>Tarih:</b> {datetime.now().strftime('%d %B %Y %H:%M')}</p>"
                                  f"<p><b>Etiket:</b> {self.components[index].label.text()}, <b>ID:</b> {self.components[index].sol1.text()}</p>"
                                  f"<p><b>Cihazının sıcaklık değeri eşik değerini aşmıştır</b></p>"
                                  f"<p><b>Eşik Sıcaklığı:</b> {self.properties[index].max_temp}</p>"
                                  f"<p><b>Anlık Sıcaklık:</b> {self.components[index].temp.text()}</p>"),
                                  self.mail_list])
        except:
            pass

    def MAIL_LIST(self, liste):
        self.mail_list = []
        for i in liste:
            if i[2] == 1:
                self.mail_list.append(i[1])
    "CİHAZ PANELİ AYARLAR KISMI KAPATILDIĞINDA YAPILACAKLAR"

    def property_close(self, button_index):
        if len(self.cihazlar) > button_index:
            self.properties[button_index].baslik = self.line_edits[0].text()
            if len(self.properties[button_index].baslik) >= 15:

                self.components[self.pushed_button_index].label.setText(self.properties[button_index].baslik[0:15] +
                                                                        "\n" + self.properties[button_index].baslik[
                                                                               15:])
            else:
                self.components[self.pushed_button_index].label.setText(self.properties[button_index].baslik)
            if self.Client_on == True:
                self.properties[button_index].baudrate = self.line_edits[1].text()
                self.properties[button_index].ID = self.line_edits[2].text()
                self.properties[button_index].min_temp = self.line_edits[3].text()
                self.properties[button_index].max_temp = self.line_edits[4].text()
                self.property_dialog.close()
                try:
                    unit = int(self.UNIT[button_index])

                    self.Other_Registers.emit([self.properties[button_index], unit, button_index])
                except:
                    pass
            self.property_dialog.close()
        else:
            self.property_dialog.close()

    @pyqtSlot(list)
    def Properties_GUI(self, output):
        """
        output[0][0] => .baudrate
        output[0][1] => .ID
        output[0][2] => .max_temp
        output[1] => button index
        """
        for i in range(len(output[0])):
            self.cmd_write(output[0][i])

    def property_Jclose(self):
        self.property_dialog.close()

    "GRAFİK ÇİZDİRİR"
    def drawWindow(self):
        try:
            graph_time, graph_var = get_graph(self.combobox_ID.currentText(), self.combobox_tarih.currentText(),
                                     self.log_address + "\logs.db")
            print(graph_var, graph_time)
            if self.tabs.count() == 3:
                self.tabs.removeTab(2)
            self.tabs.addTab(self.PlotCanvas([graph_time, graph_var]), "Çizim Paneli")
            self.tabs.setCurrentIndex(2)
        except:
            self.msg_box.setIcon(QtWidgets.QMessageBox.Warning)
            self.msg_box.setText("HATA !")
            self.msg_box.exec()

    "EXCEL CIKTISI ALIR"
    def output_excel(self):
        try:
            database_to_excel(self.combobox_ID.currentText(),
                              self.combobox_tarih.currentText(),
                              self.xlsx_address,
                              self.log_address + "\logs.db")
            self.msg_box.setIcon(QtWidgets.QMessageBox.Information)
            self.msg_box.setText("Excel Dosyası Oluşturuldu")
            self.msg_box.exec()
        except:
            self.msg_box.setIcon(QtWidgets.QMessageBox.Warning)
            self.msg_box.setText("HATA !")
            self.msg_box.exec()

    "IP LIST E EKLEME YAPAR"
    def add_ip(self):
        """
        Yeni IP eklemesi burada yapılır. Girilen IP zaten ekli ise ekleme yapılmaz.
        Girilen Ip yeni bir IP ise hem listeye ekler. Hem de databaseye kaydeder.
        """
        try:
            new_ip = QtWidgets.QInputDialog.getText(self, 'Yeni IP Girişi', 'Yeni Ip adresini giriniz, Girdiğiniz Ip'
                                                                            'daha önceden eklenmiş ise ekleme yapılmayacak')[
                0]
            if len(new_ip) != 0:
                add_on = True
                items = [self.list_ip.item(i).text() for i in range(self.list_ip.count())]
                for i in items:
                    if new_ip == i:
                        add_on = False
                        break
                if add_on == True:
                    self.list_ip.insertItem(0, new_ip)
                    self.db_add_del("IP", "ADD", new_ip)
        except:
            pass

    "IP LIST DEN SILME YAPAR"
    def del_ip(self):
        """
        Üzerinde seçili durulan liste elemanını siler
        ***Burada radiobutton da ekleyip coklu sildirme yapabilirim.***
        """
        try:
            index = self.list_ip.currentRow()
            item = self.list_ip.item(index)
            self.list_ip.takeItem(index)
            self.db_add_del("IP", "DEL", item.text())
            del item

        except:
            pass

    "DEVICE LIST E EKLEME YAPAR"
    def add_device(self):
        """
        Yeni device eklemesi burada yapılır. Girilen IP zaten ekli ise ekleme yapılmaz.
        Girilen Ip yeni bir IP ise hem listeye ekler. Hem de databaseye kaydeder.
        """
        try:
            new_dev = \
            QtWidgets.QInputDialog.getText(self, 'Yeni Device Girişi', 'Yeni device portunu giriniz, Girdiğiniz port'
                                                                       'daha önceden eklenmiş ise ekleme yapılmayacak')[
                0]
            if len(new_dev) != 0:
                add_on = True

                items = [self.list_dev.item(i).text() for i in range(self.list_dev.count())]
                for i in items:
                    if new_dev == i:
                        add_on = False
                        break
                if add_on == True:
                    self.list_dev.insertItem(0, str(new_dev))
                    self.db_add_del("DEV", "ADD", new_dev)

        except:
            pass

    "DEVICE LIST DEN SILME YAPAR"
    def del_device(self):
        """
        Üzerinde seçili durulan liste elemanını siler
        ***Burada radiobutton da ekleyip coklu sildirme yapabilirim.***
        """
        try:
            index = self.list_dev.currentRow()
            item = self.list_dev.item(index)
            self.list_dev.takeItem(index)
            self.db_add_del("DEV", "DEL", item.text())
            del item

        except:
            pass

    "EKLENEN/ SILINEN IP VE DEVICE LAR ICIN DATABASE ISLEMLERI"
    def db_add_del(self, IP_dv, add_del, reg):
        """
        :param IP_dv: IP mi Device mi seçimi. Seçili olan değere bağlanılacak
        :param add_del: ADD mi Delete mi seçimi. Seçili olana göre işlem yapılacak
        :param reg: Kaydedilecek veya silinecek olan değer


        Burası çok uzun oldu düzenleme yapılacak.
        IP_dv olarak gelen şey direk database ismi olursa sadece bir tane conn kurarak islemleri halledebiliriz.
        Kod tektarından cıkılır. Çünkü adresi buna bağlı olarak belirliyoruz.
        :return:
        """
        if IP_dv == "IP":

            adress = self.database_address + "\ip_database.db"

            con = sqlite3.connect(r"{}".format(adress))
            cursor = con.cursor()
            if add_del == "ADD":
                cursor.execute("CREATE TABLE IF NOT EXISTS ip_list (id TEXT)")
                con.commit()
                cursor.execute("INSERT INTO ip_list VALUES(?)", (reg,))
                con.commit()
            else:
                cursor.execute("DELETE FROM ip_list WHERE id = ?", (reg,))  # BURADA SORUN VAR.....
                con.commit()
            con.close()


        else:
            adress = self.database_address + "\dev_database.db"
            con = sqlite3.connect(adress)
            cursor = con.cursor()
            if add_del == "ADD":
                cursor.execute("CREATE TABLE IF NOT EXISTS dev_list (id TEXT)")
                con.commit()
                cursor.execute("INSERT INTO dev_list VALUES(?)", (reg,))
                con.commit()
            else:
                cursor.execute("DELETE FROM dev_list WHERE id = ?", (reg,))  # BURADA SORUN VAR.....
                con.commit()
            con.close()

    "THREAD ACILIS SINYAL BAGLANTILARININ YAPILMASI"
    def Start_Thread(self):
        self.client_thread = QThread()
        self.My_Thread = C_Thread(result=self.Write_data,
                                  client_message=self.CONNECTION,
                                  closing_signal = self.CLOSED,
                                  uyari_Signal = self.toggle_uyari_GUI,
                                  BeniBul_Signal = self.toggle_BeniBul_GUI,
                                  Write_other_Signal = self.Properties_GUI,
                                  configurate_Signal = self.configurate_GUI,
                                  smpt_Signal = self.Mail_Cevabi)
        self.client_Signal.connect(self.My_Thread.Start_TCP_Client)
        self.pool_Signal.connect(self.My_Thread.read_registers)
        self.close_Signal.connect(self.My_Thread.Close_Connection)
        self.uyari_toggle_Signal.connect(self.My_Thread.Uyari_Toggle)
        self.Benibul_Signal.connect(self.My_Thread.Beni_Bul)
        self.Other_Registers.connect(self.My_Thread.Write_other_registers)
        self.configurate_Signal.connect(self.My_Thread.New_Device_Configurate)
        self.mail_Signal.connect(self.My_Thread.SMTP_MAIL)
        self.My_Thread.moveToThread(self.client_thread)
        self.client_thread.start()

    def Mail_Cevabi(self, output):
        self.cmd_write(output)

    "CLIENT BASLATILMASI VE GERİ DÖNÜŞLER"
    def TCP_client_start(self):
        """
        Bağlantının yapılması.
        Bağlantı yapılamazsa, uyarı ile bildirilir.
        Start butonuna basılmadan ADD/DELETE Butonları harici butonlar inaktiftir.
        START Butonuna basıldığında, start butonu inaktif olur.
        STOP butonu ve diğer butonlar aktif duruma geçer.
        """
        try:
            self.Client_on = False
            self.UNIT = [self.list_dev.item(i).text() for i in
                         range(self.list_dev.count())]  # Slave seçimi için bunu değiştiriyoruz.
            self.UNIT.reverse()
            self.first_start = [True for i in range(len(self.UNIT))]
            self.counter_list = [0 for i in range(len(self.UNIT))]
            self.properties = [self.registers("", "", "", "", 25, 0) for i in range(len(self.UNIT))]
            self.timer_list = [datetime.now() for i in range(len(self.UNIT))]
            self.IP = self.list_ip.currentItem().text()
            self.PORT = int(self.text_port.text())
            self.timeout = int(self.text_timeout.text())
            self.polltime = int(self.text_polltime.text())
            """Yeni bağlantı için thread i öldürmemiz gerek."""
            self.Start_Connection()

        except:
            self.msg_box.setIcon(QtWidgets.QMessageBox.Warning)
            self.msg_box.setText("Bağlantı sağlanamadı, tekrar deneyin")
            self.msg_box.exec()

    @pyqtSlot()
    def Start_Connection(self):
        self.client_Signal.emit([self.IP, self.PORT, self.UNIT, self.polltime, self.timeout])

    @pyqtSlot(bool)
    def CONNECTION(self, client_status):
        self.Client_on = client_status
        if client_status == True:
            self.msg_box.setIcon(QtWidgets.QMessageBox.Information)
            self.msg_box.setText("Bağlantı sağlandı")
            self.msg_box.exec()
            self.button_start.setEnabled(False)
            self.button_stop.setEnabled(True)
            self.pool_Signal.emit(True)
        else:
            self.msg_box.setIcon(QtWidgets.QMessageBox.Warning)
            self.msg_box.setText("Bağlantı sağlanamadı, tekrar deneyin")
            self.msg_box.exec()

    "CLIENT DURDURULMASI VE ISLEMLER"
    @pyqtSlot()
    def TCP_client_stop(self):
        self.close_Signal.emit(True)

    @pyqtSlot(bool)
    def CLOSED(self, client_stat):
        try:
            self.msg_box.setIcon(QtWidgets.QMessageBox.Information)
            self.msg_box.setText("Bağlantı kesildi")
            self.msg_box.exec()
            self.button_start.setEnabled(True)
            self.button_stop.setEnabled(False)
        except:
            self.msg_box.setIcon(QtWidgets.QMessageBox.Information)
            self.msg_box.setText("Bağlantı kesilemedi, tekrar deneyin")
            self.msg_box.exec()

    "GELEN VERININ YAZILMASI"
    @pyqtSlot(list)
    def Write_data(self, output):
        """
        :param output: Output değeri okunan registerin bütün değerlerini bir liste halinde içerir. Bu
        listenin ikinci elemanı olarak ise Unit indexi vardır. Böylece okunan unit izleme ekranında yazılabilir
        Gelen örnek liste
        output = [[0, 28000, 28, 0, 0, 1, 0, 13, 0], 0]
        Burada
        output[0] = [0, 28000, 28, 0, 0, 1, 0, 13, 0]
        Sırasıyla
        03 OKUMA MODU 06 YAZMA MODU
        output[0][0] ->beni_bul (06),   1 ise mavi, 0 ise normal renk
        output[0][1] ->sayac (03),      bir islem yapılmıyor, sadece veri geldiğini göstermek için
        output[0][2] ->sıcaklık (03),   cihaz sıcaklık verisi
        output[0][3] ->uyarı(06),       1 ise kırmızı 0 ise normal renk yanar
        output[0][4] ->baud_secim(06),  baudrade seçimi için kullanılır
        output[0][5] ->baud_modu(03),   baud modunu okumak için kullanılır
        output[0][6] ->id_secim(06),    slave id seçimi yapmak için kullanılır
        output[0][7] ->id_oku(03),      slave id okumak için kullanılır.
        output[0][8] ->esik(06)         sıcaklık > esik ise kırmızı led yanar
        output[1] = 0 dır ( unit index )
        """
        index = self.UNIT.index(output[1])
        date = datetime.now().date().strftime('%d/%m/%Y')
        cur_time = datetime.now().time().strftime("%H:%M:%S")

        if self.components[index].checkbox.isChecked():
            "Checkbox isaretli ise verileri göstereceğiz yoksa göstermeyeceğiz."
            if output[0] != ModbusIOException:
                self.timer_list[index] = datetime.now()
                self.first_start[index] = False
                self.cmd_plus.insertItem(0, str(output[1]) + "---->" + str(output[0]))
                try:
                    self.components[index].temp.setText(str(output[0][2]))  # sıcaklık
                    self.components[index].alt2.setText(str(output[0][8]))  # esik
                    self.properties[index].max_temp = int(output[0][8]) # max cihaz sıcaklığı kaydedildi
                    self.temp_background(index) # sıcaklık arkaplan ayarı
                    self.components[index].sol1.setText(str(output[0][7]))  # adres
                    self.components[index].sol2.setText(str(output[0][5]))  # baudrate
                    self.components[index].alt1.setStyleSheet("background-color:darkkhaki") #veri GELDİ - GELMEDİ
                    logfile(date, cur_time, output[0][2], output[0][5], output[0][7], output[0][3],
                            output[0][8], output[0][0],
                            self.components[index].label.text(), self.log_address, self.UNIT[index])
                except:
                    pass

            else:
                self.cmd_plus.insertItem(0, str(output[1]) + "---->" + "Veri Alınamadı")
                if self.first_start[index] == True:
                    self.no_data(index)
                    self.first_start[index] = False
                elif datetime.now() - self.timer_list[index] >= timedelta(seconds=20):
                    self.no_data(index)

    "GELEN VERININ BAGLANTI PANELDE CMD EKRANINA YAZILMASI VE SILINMESI"
    def cmd_write(self, output):
        self.cmd_plus.insertItem(0, output)

    def cmd_clear(self):
        self.cmd_plus.clear()

    "DATA GELMEDİĞİNDE YAPILACAK ISLEMLER"
    def no_data(self, index):
        self.components[index].alt1.setStyleSheet("background-color:mediumorchid")
        self.components[index].temp.setStyleSheet("background-color:lemonchiffon")

    "FABRIKA CIKISI CIHAZLAR ICIN ID ve BAUDRATE AYARLAMA FONKSIYONLARI"
    def configurate(self):
        if self.Client_on == True:
            try:
                self.configurate_Signal.emit([self.list_ip.currentItem().text(),
                                              int(self.text_port.text()),
                                              int(self.text_mid4.text()),
                                              int(self.text_mid3.text())])
                self.button_mid1.setEnabled(False)
            except:
                self.msg_box.setIcon(QtWidgets.QMessageBox.Warning)
                self.msg_box.setText("Konfigürasyon Başarısız !")
                self.msg_box.exec()


    @pyqtSlot(list)
    def configurate_GUI(self, output):
        """
        output[0] => Cmd yazılacak ifade
        output[1] => İslem Basarılı ise True değilse False
        output[2] => İslem basarılı ise ID / Basarısız ise yok.
        """
        self.button_mid1.setEnabled(True)
        if output[1] == True:

            cevap = self.msg_box.question(self, "Konfigürasyon Kayıt",
                                          "Konfigürasyonunu yaptığınız cihaz, Cihaz Listesine"
                                          " Eklensin mi ?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if cevap == QMessageBox.Yes:
                self.list_dev.insertItem(0, output[2])
            self.cmd_write(output[0])
        else:
            self.cmd_write(output[0])
            self.msg_box.setIcon(QtWidgets.QMessageBox.Warning)
            self.msg_box.setText("İslem Başarısız")
            self.msg_box.exec()

app = QApplication(sys.argv)
pen = functions()
app.exec_()