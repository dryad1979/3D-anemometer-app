# coding: utf-8

import sys
from PyQt5.QtCore import pyqtSignal, QSettings, QThread, QTimer
from PyQt5.QtWidgets import QApplication, QFileDialog, QMainWindow, QMessageBox, QTabBar, QWidget
from airflow_mainWindow import Ui_MainWindow

import logging
from logging.handlers import TimedRotatingFileHandler
import traceback
import re
import os
import serial
import serial.tools.list_ports
from datetime import datetime, timedelta
import numpy as np

def setupLogger():
    # Produce formater first
    formatter = logging.Formatter('%(asctime)s - line:%(lineno)s - %(levelname)s - %(message)s')
    # Setup Handler
    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG)
    console.setFormatter(formatter)
    # Setup File Handler
    if not os.path.exists('./log/'):
        os.makedirs('./log/')
    filename = './log/Air Flow Monitor.log'
    timedfile = TimedRotatingFileHandler(filename=filename, 
                                         when='midnight', backupCount=60, 
                                         encoding='utf-8')
    timedfile.suffix = "%Y-%m-%d.log"
    timedfile.extMatch = re.compile(r"^\d{4}-\d{2}-\d{2}.log$")
    timedfile.setLevel(logging.DEBUG)
    timedfile.setFormatter(formatter)
    # Setup Logger
    logger.handlers.clear()
    logger.addHandler(console)
    logger.addHandler(timedfile)
    logger.setLevel(logging.DEBUG)

# Call the logger
logger = logging.getLogger(__name__)

class TabBar(QTabBar):
    def sizeHint(self):
        hint = super().sizeHint()
        if self.isVisible() and self.parent():
            if not self.shape() & self.RoundedEast:
                # horizontal
                hint.setWidth(self.parent().width())
            else:
                # vertical
                hint.setHeight(self.parent().height())
        return hint

    def tabSizeHint(self, index):
        hint = super().tabSizeHint(index)
        if not self.shape() & self.RoundedEast:
            hint.setHeight(50)
            averageSize = int(self.width() / self.count())
            if super().sizeHint().width() < self.width() and hint.width() < averageSize:
                hint.setWidth(averageSize)
        else:
            hint.setWidth(50)
            averageSize = self.height() / self.count()
            if super().sizeHint().height() < self.height() and hint.height() < averageSize:
                hint.setHeight(averageSize)
        return hint
    
class SerialThread(QThread):
    signal_ser_raw = pyqtSignal(str, datetime)
    signal_ser_empty = pyqtSignal()
    signal_ser_status = pyqtSignal()
    def __init__(self,myWin,parent=None):
        super(SerialThread,self).__init__(parent)
        self.myWin=myWin
        self.active=False

    def run(self):
        logger.info('Start moniroting thread')
        #parameter setting
        self.active=True
        while self.active:
            # read data from serial port
            try:
                raw_data = self.myWin.ser.read_until(b'\r').decode().strip().strip(b'\x00'.decode())
                raw_time = datetime.now()
                if not len(raw_data):
                    self.signal_ser_empty.emit()
                else:
                    self.signal_ser_raw.emit(raw_data, raw_time)
            except UnicodeDecodeError:
                logger.error(f'{traceback.format_exc()}')
            except Exception:
                logger.error(f'{traceback.format_exc()}')
                self.active=False
                continue
            # print(raw_time)
            # print(raw_data)
        logger.info('Stop moniroting thread')
        self.signal_ser_status.emit()
        
    def exit(self):
        self.active=False

class MyMainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        super(MyMainWindow, self).__init__(parent)
        self.setupUi(self)
        self.setup_control()
        
    # to do or start up
    def setup_control(self):
        # setup logger
        setupLogger()
        logger.debug('Begin of application: Air Flow Monitor')
        # set main window's title
        self.setWindowTitle('Air Flow Monitor v1.6')
        # set up tab
        self.tabBar=TabBar(self.tabWidget)
        self.tabWidget.setTabBar(self.tabBar)
        self.tab1 = QWidget()
        self.tab2 = QWidget()
        self.tabWidget.addTab(self.tab1, "Real-Time Record")
        self.tabWidget.addTab(self.tab2, "History Data Analysis")
        self.tabWidget.setStyleSheet('QTabBar { font-size: 14pt; font-family: Gill Sans MS; }')
        # get COM ports list
        port_list = serial.tools.list_ports.comports()
        com_list = []
        for com in port_list:
            com=str(com).split()
            self.comboBox_port.addItem(com[0])
            com_list.append(com[0])
        # set default setting
        self.settings = QSettings('Air_Flow_Monitor', 'v1')
        keys = self.settings.allKeys()
        if len(keys)<3:
            self.settings.setValue('COM port', self.comboBox_port.currentText())
            self.settings.setValue('save route', './')
            self.settings.setValue('load file', './')
        # load setting
        if self.settings.value('COM port') not in com_list:
            self.settings.setValue('COM port', self.comboBox_port.currentText())
        self.comboBox_port.setCurrentText(self.settings.value('COM port'))
        self.textEdit_saveroute.setText(self.settings.value('save route'))
        self.textEdit_loadfile.setText(self.settings.value('load file'))
        # variables
        self.wind = ''
        self.slider_time_array = np.array([])
        # connect signal
        self.push_renew.clicked.connect(self.renew_port)
        self.comboBox_port.currentTextChanged.connect(lambda: self.settings.setValue('COM port', self.comboBox_port.currentText()))
        self.push_saveroute.clicked.connect(self.saveroute_choose)
        self.textEdit_saveroute.textChanged.connect(lambda: self.settings.setValue('save route', self.textEdit_saveroute.toPlainText()))
        self.push_start.clicked.connect(self.monitor_state)
        self.push_mark.clicked.connect(self.mark_data)
        self.push_clear.clicked.connect(self.clear_data)
        self.push_save.clicked.connect(self.save_data)
        self.push_loadfile.clicked.connect(self.load_file)
        self.textEdit_loadfile.textChanged.connect(lambda: self.settings.setValue('load file', self.textEdit_loadfile.toPlainText()))
        self.push_plot_trend.clicked.connect(self.hist_trend)
        self.dateTimeEdit_start.dateTimeChanged.connect(self.time_range_change)
        self.dateTimeEdit_end.dateTimeChanged.connect(self.time_range_change)
        self.checkBox_mark.stateChanged.connect(self.show_mark)
        self.radioButton_moment.toggled.connect(self.compass_type)
        self.radioButton_period.toggled.connect(self.compass_type)
        self.dateTimeEdit_moment.dateTimeChanged.connect(self.edit_pointer_change)
        self.horizontalSlider_moment.valueChanged.connect(self.slider_pointer_change)
        self.dateTimeEdit_period_start.dateTimeChanged.connect(self.edit_period_change)
        self.dateTimeEdit_period_end.dateTimeChanged.connect(self.edit_period_change)
        self.horizontalSlider_period.valueChanged.connect(self.slider_period_change)
        self.push_plot_compass.clicked.connect(self.period_compass)
        self.doubleSpinBox_radius.valueChanged.connect(self.compass_radius_change)
        
    def renew_port(self):
        # clear old list and add new list
        old = self.comboBox_port.currentText()
        self.comboBox_port.clear()
        port_list = serial.tools.list_ports.comports()
        com_list = []
        for com in port_list:
            com=str(com).split()
            self.comboBox_port.addItem(com[0])
            com_list.append(com[0])
        if old in com_list:
            self.comboBox_port.setCurrentText(old)
            
    def saveroute_choose(self):
        folder_path = QFileDialog.getExistingDirectory(self,
                  "Choose save folder",
                   self.textEdit_saveroute.toPlainText())     # start path
        if folder_path:
            self.textEdit_saveroute.setText(folder_path)
            
    def monitor_state(self):
        if self.push_start.isChecked():
            self.push_start.setText("Monitoring...")
            self.lineEdit_COM.setText("searching...")
            self.lineEdit_COM.setStyleSheet("color: blue; font-size: 10pt; font-family: Calibri;")
            # create serial, thread and timer instance
            try:
                self.ser=serial.Serial(self.comboBox_port.currentText(),38400,timeout=2)
            except serial.SerialException:
                logger.error(f'{traceback.format_exc()}')
                QMessageBox.critical(self, 'Error', 
                                     'The access to the COM port is denied.\nPlease choose a right COM port.')
                self.push_start.setChecked(False)
                self.push_start.setText("Start")
                self.lineEdit_COM.setText("disconnected")
                self.lineEdit_COM.setStyleSheet("color: red; font-size: 10pt; font-family: Calibri;")
                return
            self.ser_thread = SerialThread(myWin=self)
            # connect signal from thread to main window
            self.ser_thread.signal_ser_raw.connect(self.data_process)
            self.ser_thread.signal_ser_empty.connect(self.COM_empty)
            self.ser_thread.signal_ser_status.connect(self.change_status_text)
            # start the thread and plot
            self.ser_thread.start()
            self.plot_anim.mpl.toggle_pause()
            # calculate the delta time and start the single shot timer
            time1 = datetime.now()
            # time2 = time1+timedelta(minutes=1)
            # time2 = datetime(time2.year, time2.month, time2.day, time2.hour, time2.minute, 2)
            time2 = time1+timedelta(days=1)
            time2 = datetime(time2.year, time2.month, time2.day, 0, 0, 2)
            delta = time2-time1
            self.timer_midnight = QTimer()
            self.timer_midnight.setSingleShot(True)
            self.timer_midnight.timeout.connect(self.save_midnight)
            self.timer_midnight.start(round(delta.total_seconds()*1000))
        else:
            self.ser_thread.exit()
            # # end monitoring
            # self.push_start.setText("Start")
            # try:
            #     # stop the thread and timer
            #     self.timer_midnight.stop()
            #     self.plot_anim.mpl.toggle_pause()
            #     self.ser_thread.exit()
            #     self.ser.close()
            #     # delete the serial, thread and timer instance
            #     del self.ser_thread
            #     del self.ser
            #     del self.timer_midnight
            # except Exception:
            #     logger.error(f'{traceback.format_exc()}')
            
    def data_process(self, raw, time):
        result_raw = re.match('((\s+)?(-)?\d+\.\d){7}$', raw)
        if result_raw:
            self.lineEdit_COM.setText("connected")
            self.lineEdit_COM.setStyleSheet("color: green; font-size: 10pt; font-family: Calibri;")
            data = [float(n) for n in raw.split()]
        else:
            self.lineEdit_COM.setText("wrong format")
            self.lineEdit_COM.setStyleSheet("color: orange; font-size: 10pt; font-family: Calibri;")
            logger.warning(f'Data format from serial port is wrong. Raw string: {raw}')
            return
        raw = re.sub('\s+', ',', raw)
        result_raw = re.match(',', raw)
        if not result_raw:
            raw = ','+raw
        self.wind = self.wind+time.strftime('%Y-%m-%d %H:%M:%S.%f')+raw+',0\n'
        self.plot_anim.mpl.update_line_data(time, data[0], data[1], data[2], 
                                            data[3], data[4], data[5])
        
    def COM_empty(self):
        if self.push_start.isChecked():
            self.lineEdit_COM.setText("searching...")
            self.lineEdit_COM.setStyleSheet("color: blue; font-size: 10pt; font-family: Calibri;")
            logger.warning(f'{self.comboBox_port.currentText()} is empty.')
            
    def change_status_text(self):
        self.push_start.setChecked(False)
        self.lineEdit_COM.setText("disconnected")
        self.lineEdit_COM.setStyleSheet("color: red; font-size: 10pt; font-family: Calibri;")
        # end monitoring
        self.push_start.setText("Start")
        # stop the thread and timer
        self.timer_midnight.stop()
        self.plot_anim.mpl.toggle_pause()
        # self.ser_thread.exit()
        self.ser.close()
        # delete the serial, thread and timer instance
        del self.ser_thread
        del self.ser
        del self.timer_midnight
        
    def mark_data(self):
        if self.push_start.isChecked():
            self.plot_anim.mpl.mark_data()
            self.wind = re.sub('0\n$', '1\n', self.wind)
    
    def clear_data(self):
        self.wind = ''
        self.plot_anim.mpl.plot_clear()
        
    def save_data(self):
        fileTime = datetime.now().strftime('%y%m%d_%H%M%S')
        fileName = os.path.join(self.textEdit_saveroute.toPlainText(),fileTime+'.txt')
        name = QFileDialog.getSaveFileName(self, 'Save File',
                                           fileName,
                                           "Text files (*.txt)")
        if name[0]:
            with open(name[0],'w') as f:
                f.write(self.wind)
                
    def save_midnight(self):
        # save daily data
        # fileTime = datetime.now()-timedelta(minutes=1)
        # fileName = os.path.join(self.textEdit_saveroute.toPlainText(),fileTime.strftime('%y%m%d_%H%M00')+'.txt')
        # split_time = datetime.now().strftime('%Y-%m-%d %H:%M')
        # wind_split = re.split(split_time, self.wind, 1)
        # self.wind = split_time+wind_split[1]
        # with open(fileName,'w') as f:
        #     f.write(wind_split[0])
        fileTime = datetime.now()-timedelta(days=1)
        fileName = os.path.join(self.textEdit_saveroute.toPlainText(),fileTime.strftime('%y%m%d')+'.txt')
        split_time = datetime.now().strftime('%Y-%m-%d')
        wind_split = re.split(split_time, self.wind, 1)
        self.wind = split_time+wind_split[1]
        with open(fileName,'w') as f:
            f.write(wind_split[0])
        # set the next timer
        time1 = datetime.now()
        # time2 = time1+timedelta(minutes=1)
        # time2 = datetime(time2.year, time2.month, time2.day, time2.hour, time2.minute, 2)
        time2 = time1+timedelta(days=1)
        time2 = datetime(time2.year, time2.month, time2.day, 0, 0, 2)
        delta = time2-time1
        self.timer_midnight = QTimer()
        self.timer_midnight.setSingleShot(True)
        self.timer_midnight.timeout.connect(self.save_midnight)
        self.timer_midnight.start(round(delta.total_seconds()*1000))
        
    def load_file(self):
        name = QFileDialog.getOpenFileName(self, 'Load History Data',
                                           self.textEdit_loadfile.toPlainText(),
                                           "Text files (*.txt)")
        if name[0]:
            self.textEdit_loadfile.setText(name[0])
            
    def hist_trend(self):
        try:
            with open(self.textEdit_loadfile.toPlainText()) as f:
                # if the file is for 3D anemometer
                test = f.readline()
                result_raw = re.match('\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{6}(,(-)?\d+\.\d+){7}(,\d)$', test)
                if not result_raw:
                    QMessageBox.critical(self, 'Error', 
                                         'The format of content is wrong.')
                    return
                # read the left content
                text = f.read().rstrip()
        except FileNotFoundError:
            QMessageBox.critical(self, 'Error', 
                                 'Can not find the file.')
            self.push_run.setChecked(False)
            return
        # get variables
        text_list = re.split('[,\n]', text)
        hist_wind = np.array(text_list).reshape((-1,9))
        self.hist_time = hist_wind[:,0].astype('datetime64')
        self.hist_d2 = hist_wind[:,4].astype('float')
        self.hist_mag = hist_wind[:,5].astype('float')
        self.hist_az = hist_wind[:,6].astype('float')
        self.hist_el = hist_wind[:,7].astype('float')
        hist_mark = hist_wind[:,8].astype('bool')
        self.plot_trend.mpl.plot_trend(self.hist_time, self.hist_mag, 
                                       self.hist_az, self.hist_el, hist_mark)
        # set start and end time
        self.dateTimeEdit_start.setDateTime(self.hist_time[0].tolist())
        self.dateTimeEdit_end.setDateTime(self.hist_time[-1].tolist())
        # set pointer slider
        self.slider_time_array = np.arange(np.datetime64(self.hist_time[0], 's'), self.hist_time[-1], 
                                           np.timedelta64(1,'s'), dtype='datetime64')
        self.horizontalSlider_moment.setRange(0,self.slider_time_array.size-1)
        self.horizontalSlider_moment.setValue(0)
        self.dateTimeEdit_moment.setDateTime(self.slider_time_array[0].tolist())
        # set range slider
        self.horizontalSlider_period.setRange(0, self.slider_time_array.size-1)
        self.horizontalSlider_period.setValue([0,self.slider_time_array.size-1])
        
    def time_range_change(self):
        if self.slider_time_array.size > 0:
            start = self.dateTimeEdit_start.dateTime().toString('yyyy-MM-dd HH:mm:ss')
            start = np.array(start, dtype='datetime64')
            end = self.dateTimeEdit_end.dateTime().toString('yyyy-MM-dd HH:mm:ss')
            end = np.array(end, dtype='datetime64')
            # mark the text in red if the time is conflicted
            if start >= end:
                self.dateTimeEdit_start.setStyleSheet("color: red; font-size: 10pt; font-family: Calibri;")
                self.dateTimeEdit_end.setStyleSheet("color: red; font-size: 10pt; font-family: Calibri;")
                return
            self.dateTimeEdit_start.setStyleSheet("color: black; font-size: 10pt; font-family: Calibri;")
            self.dateTimeEdit_end.setStyleSheet("color: black; font-size: 10pt; font-family: Calibri;")
            # adjust trend chart range
            self.plot_trend.mpl.change_time_range(start, end)
            # adjust pointer slider
            self.slider_time_array = np.arange(start, end+np.timedelta64(1,'s'), 
                                               np.timedelta64(1,'s'), dtype='datetime64')
            self.horizontalSlider_moment.setRange(0,self.slider_time_array.size-1)
            self.edit_pointer_change(self.dateTimeEdit_moment.dateTime())
            # adjust range slider
            self.horizontalSlider_period.setRange(0, self.slider_time_array.size-1)
            self.edit_period_change()
            
        
    def show_mark(self):
        if self.checkBox_mark.isChecked():
            self.plot_trend.mpl.show_scatter()
        else:
            self.plot_trend.mpl.hide_scatter()
            
    def compass_type(self):
        if self.sender().text()=='moment':
            if self.radioButton_moment.isChecked():
                self.slider_pointer_change(self.horizontalSlider_moment.value())
                self.plot_trend.mpl.show_vline()
                self.plot_compass.mpl.show_moment_compass()
            else:
                self.plot_trend.mpl.hide_vline()
                self.plot_compass.mpl.hide_moment_compass()
        elif self.sender().text()=='period':
            if self.radioButton_period.isChecked():
                self.slider_period_change(self.horizontalSlider_period.value())
                self.plot_trend.mpl.show_span()
                self.plot_compass.mpl.show_period_compass()
            else:
                self.plot_trend.mpl.hide_span()
                self.plot_compass.mpl.hide_period_compass()
            
    def edit_pointer_change(self, pointer_time):
        if self.slider_time_array.size > 0:
            pointer_time = pointer_time.toString('yyyy-MM-dd HH:mm:ss')
            pointer_time = np.array(pointer_time, dtype='datetime64')
            if pointer_time < self.slider_time_array[0]:
                self.dateTimeEdit_moment.setDateTime(self.slider_time_array[0].tolist())
                return
            elif pointer_time > self.slider_time_array[-1]:
                self.dateTimeEdit_moment.setDateTime(self.slider_time_array[-1].tolist())
                return
            ind = np.where(self.slider_time_array==pointer_time)
            self.horizontalSlider_moment.setValue(ind[0][0])
        
    def slider_pointer_change(self, ind):
        if self.slider_time_array.size > 0:
            pointer_time = self.slider_time_array[ind]
            self.dateTimeEdit_moment.setDateTime(pointer_time.tolist())
            if self.radioButton_moment.isChecked():
                self.plot_trend.mpl.move_pointer(pointer_time)
                deltas = np.absolute(self.hist_time - pointer_time)
                target_ind = np.argmin(deltas)
                target_d2 = self.hist_d2[target_ind]
                target_mag = self.hist_mag[target_ind]
                target_az = self.hist_az[target_ind]
                target_el = self.hist_el[target_ind]
                self.plot_compass.mpl.plot_moment_compass(target_d2, target_mag, 
                                                          target_az, target_el)
            
    def edit_period_change(self):
        if self.slider_time_array.size > 0:
            position_time1 = self.dateTimeEdit_period_start.dateTime().toString('yyyy-MM-dd HH:mm:ss')
            position_time1 = np.array(position_time1, dtype='datetime64')
            position_time2 = self.dateTimeEdit_period_end.dateTime().toString('yyyy-MM-dd HH:mm:ss')
            position_time2 = np.array(position_time2, dtype='datetime64')
            position_ind1 = np.where(self.slider_time_array==position_time1)
            position_ind2 = np.where(self.slider_time_array==position_time2)
            if position_ind1[0].size == 0:
                self.dateTimeEdit_period_start.setDateTime(self.slider_time_array[0].tolist())
                return
            if position_ind2[0].size == 0:
                self.dateTimeEdit_period_end.setDateTime(self.slider_time_array[-1].tolist())
                return
            if position_time1 >= position_time2:
                self.dateTimeEdit_period_start.setStyleSheet("color: red; font-size: 10pt; font-family: Calibri;")
                self.dateTimeEdit_period_end.setStyleSheet("color: red; font-size: 10pt; font-family: Calibri;")
                return
            self.dateTimeEdit_period_start.setStyleSheet("color: black; font-size: 10pt; font-family: Calibri;")
            self.dateTimeEdit_period_end.setStyleSheet("color: black; font-size: 10pt; font-family: Calibri;")
            self.horizontalSlider_period.setValue([position_ind1[0][0], position_ind2[0][0]])
            
    def slider_period_change(self, ind):
        if self.slider_time_array.size > 0:
            position_time1 = self.slider_time_array[ind[0]]
            position_time2 = self.slider_time_array[ind[1]]
            self.dateTimeEdit_period_start.setDateTime(position_time1.tolist())
            self.dateTimeEdit_period_end.setDateTime(position_time2.tolist())
            if self.radioButton_period.isChecked():
                self.plot_trend.mpl.move_span(position_time1, position_time2)
        
    def period_compass(self):
        if self.slider_time_array.size > 0 & self.radioButton_period.isChecked():
            period_ind = self.horizontalSlider_period.value()
            deltas = np.absolute(self.hist_time - self.slider_time_array[period_ind[0]])
            target_ind1 = np.argmin(deltas)
            deltas = np.absolute(self.hist_time - self.slider_time_array[period_ind[1]])
            target_ind2 = np.argmin(deltas)
            target_d2 = self.hist_d2[target_ind1:target_ind2]
            target_mag = self.hist_mag[target_ind1:target_ind2]
            target_az = self.hist_az[target_ind1:target_ind2]
            target_el = self.hist_el[target_ind1:target_ind2]
            self.plot_compass.mpl.plot_period_compass(target_d2, target_mag, 
                                                      target_az, target_el)
        
    def compass_radius_change(self, r):
        self.plot_compass.mpl.radius_change(r)
        
    def closeEvent(self, event):
        if self.push_start.isChecked():
            self.push_start.setChecked(False)
            self.monitor_state()
        # clear handlers of logger and shutdown logger
        logger.debug('End of application: Air Flow Monitor')
        logger.handlers.clear()
        logging.shutdown()

if __name__=="__main__":  
    app = QApplication(sys.argv)  
    myWin = MyMainWindow()  
    myWin.show()  
    sys.exit(app.exec_())  