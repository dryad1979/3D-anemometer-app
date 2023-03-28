import sys
import matplotlib

matplotlib.use("Qt5Agg")
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtWidgets import QApplication, QHBoxLayout, QSizePolicy, QWidget
# from PyQt5.QtWidgets import QVBoxLayout, QSizePolicy, QWidget
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib import cycler, rcParams
from matplotlib.figure import Figure

import numpy as np
import matplotlib.dates as mdates
# from datetime import datetime, timedelta


class MyMplCanvas(FigureCanvas):
    """FigureCanvas的最終的父類其實是QWidget。"""

    def __init__(self, parent=None):
        # Set the default color cycle
        rcParams['axes.prop_cycle'] = cycler(color=["#326186", "#28502E", "#F6BA42", "#A30B37", "#F26419",
                                                    "#196157", "#70B8FF"]) 
        font = {'family' : 'Calibri',
                'size'   : 10}
        matplotlib.rc('font', **font)
        # rcParams.update({'font.size': 10})

        # Create a new figure
        self.fig = Figure(tight_layout=True)
        self.ax_1 = self.fig.add_subplot(311)
        self.ax_2 = self.fig.add_subplot(312, sharex=self.ax_1)
        self.ax_3 = self.fig.add_subplot(313, sharex=self.ax_1)
        
        # Store x and y
        # time = []
        # mag = []
        # az = []
        # el = []
        time = np.array([np.datetime64('NaT')], dtype='datetime64')
        # time.fill(datetime(2000,1,1,0,0,0))
        mag = np.array([np.nan])
        # mag = np.empty(0)
        # mag.fill(np.nan)
        az = np.array([np.nan])
        # az = np.empty(0)
        # az.fill(np.nan)
        el = np.array([np.nan])
        # el = np.empty(0)
        # el.fill(np.nan)
        mark = np.array([], dtype='int')
        
        # Store a figure and ax
        self.line_1, = self.ax_1.plot(time, mag, zorder=1)
        self.line_1v = self.ax_1.axvline(c='#F26419', lw=0.5, zorder=2)
        self.sca_1 = self.ax_1.scatter(time[mark], mag[mark], facecolors='none', edgecolors='r', zorder=3)
        self.sca_1.set_visible(False)
        self.span_1 = self.ax_1.axvspan(xmin=time[0], xmax=time[0], fc='#F26419', alpha=0.3, zorder=4)
        self.span_1.set_visible(False)
        self.ax_1.set_title('Overall wind speed', fontsize=12)
        self.ax_1.set_xlabel('Time')
        self.ax_1.set_ylabel('Speed (m/s)')
        self.ax_1.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
        
        self.line_2, = self.ax_2.plot(time, az, zorder=1)
        self.line_2v = self.ax_2.axvline(c='#F26419', lw=0.5, zorder=2)
        self.sca_2 = self.ax_2.scatter(time[mark], az[mark], facecolors='none', edgecolors='r', zorder=3)
        self.sca_2.set_visible(False)
        self.span_2 = self.ax_2.axvspan(xmin=time[0], xmax=time[0], fc='#F26419', alpha=0.3, zorder=4)
        self.span_2.set_visible(False)
        self.ax_2.set_title('Wind azimuth', fontsize=12)
        self.ax_2.set_xlabel('Time')
        self.ax_2.set_ylabel('Azimuth (degree)')
        self.ax_2.set_ylim(ymin=0, ymax=360)
        self.ax_2.set_yticks([0,90,180,270,360])
        self.ax_2.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
        
        self.line_3, = self.ax_3.plot(time, el, zorder=1)
        self.line_3v = self.ax_3.axvline(c='#F26419', lw=0.5, zorder=2)
        self.sca_3 = self.ax_3.scatter(time[mark], el[mark], facecolors='none', edgecolors='r', zorder=3)
        self.sca_3.set_visible(False)
        self.span_3 = self.ax_3.axvspan(xmin=time[0], xmax=time[0], fc='#F26419', alpha=0.3, zorder=4)
        self.span_3.set_visible(False)
        self.ax_3.set_title('Wind elevation', fontsize=12)
        self.ax_3.set_xlabel('Time')
        self.ax_3.set_ylabel('Elevation (degree)')
        self.ax_3.set_ylim(ymin=-90, ymax=90)
        self.ax_3.set_yticks([-90,-45,0,45,90])
        self.ax_3.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))

        FigureCanvas.__init__(self, self.fig)
        self.setParent(parent)

        '''
		定義FigureCanvas的尺寸策略，意思是設定FigureCanvas，使之盡可能地向外填充空間。
		'''
        FigureCanvas.setSizePolicy(self,
                                   QSizePolicy.Expanding,
                                   QSizePolicy.Expanding)
        # FigureCanvas.updateGeometry(self)
        

    def plot_trend(self, time, mag, az, el, mark):
        # self.ax_1.cla()
        
        self.line_1.set_xdata(time)
        self.line_1.set_ydata(mag)
        self.line_1v.set_xdata(time[0])
        self.sca_1.set_offsets(np.c_[time[mark].astype('O'), mag[mark]])
        self.ax_1.relim()
        self.ax_1.autoscale_view(scalex=False, scaley=True)
        self.ax_1.grid(True)
        
        self.line_2.set_xdata(time)
        self.line_2.set_ydata(az)
        self.line_2v.set_xdata(time[0])
        self.sca_2.set_offsets(np.c_[time[mark].astype('O'), az[mark]])
        self.ax_2.grid(True)
        
        self.line_3.set_xdata(time)
        self.line_3.set_ydata(el)
        self.line_3v.set_xdata(time[0])
        self.sca_3.set_offsets(np.c_[time[mark].astype('O'), el[mark]])
        self.ax_3.grid(True)
        
        try:
            # self.ax_1.set_xlim(xmin=time[0], xmax=time[-1])
            self.ax_2.set_xlim(xmin=time[0], xmax=time[-1])
            # self.ax_3.set_xlim(xmin=time[0], xmax=time[-1])
        except IndexError:
            pass
        self.draw()
        
    def change_time_range(self, start, end):
        self.ax_2.set_xlim(xmin=start, xmax=end)
        self.draw()
        
    def move_pointer(self, pointer):
        self.line_1v.set_xdata(pointer)
        self.line_2v.set_xdata(pointer)
        self.line_3v.set_xdata(pointer)
        self.draw()
        
    def move_span(self, span_min, span_max):
        ts_min = (span_min - np.datetime64(0, 's')) / np.timedelta64(86400, 's')
        ts_max = (span_max - np.datetime64(0, 's')) / np.timedelta64(86400, 's')
        self.span_1.set_xy(np.array([[ts_min, 0], [ts_min, 1], 
                                      [ts_max, 1], [ts_max, 0], 
                                      [ts_min, 0]]))
        self.span_2.set_xy(np.array([[ts_min, 0], [ts_min, 1], 
                                      [ts_max, 1], [ts_max, 0], 
                                      [ts_min, 0]]))
        self.span_3.set_xy(np.array([[ts_min, 0], [ts_min, 1], 
                                      [ts_max, 1], [ts_max, 0], 
                                      [ts_min, 0]]))
        self.draw()
        
    def show_scatter(self):
        self.sca_1.set_visible(True)
        self.sca_2.set_visible(True)
        self.sca_3.set_visible(True)
        self.draw()
        
    def hide_scatter(self):
        self.sca_1.set_visible(False)
        self.sca_2.set_visible(False)
        self.sca_3.set_visible(False)
        self.draw()
        
    def show_vline(self):
        self.line_1v.set_visible(True)
        self.line_2v.set_visible(True)
        self.line_3v.set_visible(True)
        self.draw()
        
    def hide_vline(self):
        self.line_1v.set_visible(False)
        self.line_2v.set_visible(False)
        self.line_3v.set_visible(False)
        self.draw()
        
    def show_span(self):
        self.span_1.set_visible(True)
        self.span_2.set_visible(True)
        self.span_3.set_visible(True)
        self.draw()
        
    def hide_span(self):
        self.span_1.set_visible(False)
        self.span_2.set_visible(False)
        self.span_3.set_visible(False)
        self.draw()


class MatplotlibWidget_trend(QWidget):
    def __init__(self, parent=None):
        super(MatplotlibWidget_trend, self).__init__(parent)
        self.initUi()

    def initUi(self):
        self.layout = QHBoxLayout(self)
        self.mpl = MyMplCanvas(self)
        self.mpl_ntb = NavigationToolbar(self.mpl, self)  # 增加完整的 toolbar
        self.mpl_ntb.setOrientation(Qt.Vertical)
        self.mpl_ntb.setFixedWidth(30)
        self.mpl_ntb.setIconSize(QSize(30, 30))

        self.layout.addWidget(self.mpl)
        self.layout.addWidget(self.mpl_ntb) #排列toolbar


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ui = MatplotlibWidget_trend()
    ui.show()
    sys.exit(app.exec_())
