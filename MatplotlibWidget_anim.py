import sys
import matplotlib

matplotlib.use("Qt5Agg")
from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import QApplication, QVBoxLayout, QSizePolicy, QWidget
# from PyQt5.QtWidgets import QVBoxLayout, QSizePolicy, QWidget
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

import matplotlib.animation as animation
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import numpy as np
import math

class MyMplCanvas(FigureCanvas):
    """FigureCanvas的最終的父類其實是QWidget。"""

    def __init__(self, parent=None):
        # Set the default font
        font = {'family' : 'Calibri',
                'size'   : 10}
        matplotlib.rc('font', **font)

        self.fig = Figure()     # 新建一個figure
        self.ax_1 = self.fig.add_subplot(221)
        self.ax_2 = self.fig.add_subplot(222, projection='3d')
        self.ax_3 = self.fig.add_subplot(223)
        self.ax_4 = self.fig.add_subplot(224, projection='polar')
        self.fig.tight_layout(pad=1.8, w_pad=1.0, h_pad=3.2)

        FigureCanvas.__init__(self, self.fig)
        self.setParent(parent)

        '''
		定義FigureCanvas的尺寸策略，意思是設定FigureCanvas，使之盡可能地向外填充空間。
		'''
        FigureCanvas.setSizePolicy(self,
                                   QSizePolicy.Expanding,
                                   QSizePolicy.Expanding)
        # FigureCanvas.updateGeometry(self)
        
        # Store x and y
        self.x = np.empty(610, dtype='O')
        self.x.fill(datetime(2000,1,1,0,0,0))
        self.mag = np.empty(610)
        self.mag.fill(np.nan)
        self.az = np.empty(610)
        self.az.fill(np.nan)
        self.u = 0
        self.v = 0
        self.w = 0
        self.r = 0
        self.theta = 0
        self.mark = np.array([], dtype='int')
        
        # Store a figure and ax
        self.line_1, = self.ax_1.plot(self.x, self.mag, zorder=1)
        self.sca_1 = self.ax_1.scatter(self.x[self.mark], self.mag[self.mark], facecolors='none', edgecolors='r', zorder=2)
        self.ax_1.grid(True)
        self.ax_1.set_title('Wind speed', fontsize=12)
        self.ax_1.set_xlabel('Time')
        self.ax_1.set_ylabel('Wind speed (m/s)')
        self.ax_1.tick_params(axis='x', labelrotation = 30)
        self.ax_1.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
        
        self.line_2 = self.ax_2.quiver(0,0,0,0,0,0, color="#28502E")
        self.ax_2.set_title('Instant wind', fontsize=12)
        self.ax_2.set_xlabel('x')
        self.ax_2.set_ylabel('y')
        self.ax_2.set_zlabel('z')
        self.ax_2.set_xlim(xmin=-0.5, xmax=0.5)
        self.ax_2.set_ylim(ymin=-0.5, ymax=0.5)
        self.ax_2.set_zlim(zmin=-0.5, zmax=0.5)
        
        
        self.line_3, = self.ax_3.plot(self.x, self.az, color="#F6BA42", zorder=1)
        self.sca_2 = self.ax_3.scatter(self.x[self.mark], self.az[self.mark], facecolors='none', edgecolors='r', zorder=2)
        self.ax_3.grid(True)
        self.ax_3.set_title('Wind azimuth', fontsize=12)
        self.ax_3.set_xlabel('Time')
        self.ax_3.set_ylabel('Azimuth (degree)')
        self.ax_3.set_ylim(ymin=0, ymax=360)
        self.ax_3.set_yticks([0,90,180,270,360])
        self.ax_3.tick_params(axis='x', labelrotation = 30)
        self.ax_3.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
        
        self.line_4 = self.ax_4.quiver(0,0,0,0, angles='xy', scale_units='xy', scale=1, color="#A30B37")
        self.ax_4.set_title('Instant wind azimuth', fontsize=12)
        self.ax_4.set_ylim(ymin=0, ymax=0.5)
        self.ax_4.set_theta_direction(-1)
        
        # Line object
        self.line = [self.line_1, self.line_2, self.line_3, self.line_4, self.sca_1, self.sca_2]
        
        # Call superclass constructors
        self.anim = animation.FuncAnimation(self.fig, self.animate, init_func=self.plot_init, 
                                            interval=500, blit=False)
        self.paused = True

    def plot_init(self):
        
        return self.line

    def animate(self, i):
        if i==0:
            self.anim.pause()
            return self.line
        self.line[0].set_xdata(self.x)
        self.line[0].set_ydata(self.mag)
        self.line[4].set_offsets(np.c_[self.x[self.mark], self.mag[self.mark]])
        self.ax_1.relim(visible_only=True)
        self.ax_1.autoscale_view(scalex=False, scaley=True)
            
        self.line[1].remove()
        self.line[1] = self.ax_2.quiver(0, 0, 0,self.u, self.v, self.w, color="#28502E")
        
        self.line[2].set_xdata(self.x)
        self.line[2].set_ydata(self.az)
        self.line[5].set_offsets(np.c_[self.x[self.mark], self.az[self.mark]])
        
        self.line[3].set_UVC(self.theta, self.r)
        try:
            self.ax_1.set_xlim(xmin=self.x[-1]-timedelta(minutes=1),xmax=self.x[-1])
            self.ax_3.set_xlim(xmin=self.x[-1]-timedelta(minutes=1),xmax=self.x[-1])
        except IndexError:
            pass
        return self.line
        
    def update_line_data(self, time, u, v, w, d2, mag, az):
        self.x = np.roll(self.x, -1)
        self.x[-1] = time
        self.mag = np.roll(self.mag, -1)
        self.mag[-1] = mag
        self.az = np.roll(self.az, -1)
        self.az[-1] = az
        
        self.u = u
        self.v = v
        self.w = w
        self.r = d2
        self.theta = math.radians(az)
        self.mark = self.mark-1
        self.mark = self.mark[self.mark>=0]
        
    def mark_data(self):
        self.mark = np.append(self.mark, 609)
    
    def toggle_pause(self, *args, **kwargs):
        if self.paused:
            self.anim.resume()
        else:
            self.anim.pause()
        self.paused = not self.paused
        
    def plot_clear(self):
        self.x = np.empty(610, dtype='O')
        self.x.fill(datetime(2000,1,1,0,0,0))
        self.mag = np.empty(610)
        self.mag.fill(np.nan)
        self.az = np.empty(610)
        self.az.fill(np.nan)
        self.u = 0
        self.v = 0
        self.w = 0
        self.r = 0
        self.theta = 0
        self.mark = np.array([], dtype='int')
        
        self.line[0].set_xdata(self.x)
        self.line[0].set_ydata(self.mag)
        self.line[4].set_offsets(np.c_[self.x[self.mark], self.mag[self.mark]])
        self.line[1].remove()
        self.line[1] = self.ax_2.quiver(0, 0, 0,self.u, self.v, self.w, color="#28502E")
        self.line[2].set_xdata(self.x)
        self.line[2].set_ydata(self.az)
        self.line[5].set_offsets(np.c_[self.x[self.mark], self.az[self.mark]])
        self.line[3].set_UVC(self.theta, self.r)
        self.draw()


class MatplotlibWidget_anim(QWidget):
    def __init__(self, parent=None):
        super(MatplotlibWidget_anim, self).__init__(parent)
        self.initUi()

    def initUi(self):
        self.mpl = MyMplCanvas(self)
        self.mpl_ntb = NavigationToolbar(self.mpl, self)  # 增加完整的 toolbar
        self.mpl_ntb.setFixedHeight(30)
        self.mpl_ntb.setIconSize(QSize(30, 30))
        
        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.mpl)
        self.layout.addWidget(self.mpl_ntb) #排列toolbar


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ui = MatplotlibWidget_anim()
    ui.show()
    sys.exit(app.exec_())
