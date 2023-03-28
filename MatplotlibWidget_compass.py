import sys
import matplotlib

matplotlib.use("Qt5Agg")
from PyQt5.QtWidgets import QApplication, QVBoxLayout, QSizePolicy, QWidget
# from PyQt5.QtWidgets import QVBoxLayout, QSizePolicy, QWidget
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
# from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
# from matplotlib import cycler, rcParams
from matplotlib.figure import Figure

import numpy as np


class MyMplCanvas(FigureCanvas):
    """FigureCanvas的最終的父類其實是QWidget。"""

    def __init__(self, parent=None):
        # Set the default font
        font = {'family' : 'Calibri',
                'size'   : 10}
        matplotlib.rc('font', **font)
        
        # Create a new figure
        self.fig = Figure(tight_layout=True)
        self.ax_1 = self.fig.add_subplot(121, projection='polar')
        self.ax_2 = self.fig.add_subplot(122, projection='polar')

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
        
        # Store a figure and ax
        self.line_moment1 = self.ax_1.quiver(0,0,0,0, angles='xy', scale_units='xy', scale=1, color="#196157",
                                             width=0.01, headwidth=6, headlength=8)
        self.line_period1 = self.ax_1.quiver([],[],[],[], angles='xy', scale_units='xy', scale=1, color="#196157", alpha=0.5,
                                             width=0.01, headwidth=6, headlength=8)
        self.ax_1.set_title('Wind azimuth', fontsize=12)
        self.ax_1.set_ylim(ymin=0, ymax=0.5)
        self.ax_1.set_theta_direction(-1)
        
        self.line_moment2 = self.ax_2.quiver(0,0,0,0, angles='xy', scale_units='xy', scale=1, color="#196157",
                                             width=0.01, headwidth=6, headlength=8)
        self.line_period2 = self.ax_1.quiver([],[],[],[], angles='xy', scale_units='xy', scale=1, color="#196157", alpha=0.5,
                                             width=0.01, headwidth=6, headlength=8)
        self.ax_2.set_title('Wind elevation', fontsize=12)
        self.ax_2.set_thetamin(-90)
        self.ax_2.set_thetamax(90)
        self.ax_2.set_ylim(ymin=0, ymax=0.5)

    def plot_moment_compass(self, d2, mag, az, el):
        self.line_moment1.set_UVC(np.radians(az), d2)
        self.line_moment2.set_UVC(np.radians(el), mag)
        self.draw()
        
    def plot_period_compass(self, d2, mag, az, el):
        data_size = d2.size
        self.line_period1.remove()
        self.line_period2.remove()
        self.line_period1 = self.ax_1.quiver(np.zeros(data_size), np.zeros(data_size), 
                          np.radians(az), d2, angles='xy', scale_units='xy', scale=1, color="#196157", alpha=0.5,
                          width=0.01, headwidth=6, headlength=8)
        self.line_period2 = self.ax_2.quiver(np.zeros(data_size), np.zeros(data_size), 
                          np.radians(el), mag, angles='xy', scale_units='xy', scale=1, color="#196157", alpha=0.5,
                          width=0.01, headwidth=6, headlength=8)
        self.draw()
        
    def show_moment_compass(self):
        print('show')
        self.line_moment1.set_visible(True)
        self.line_moment2.set_visible(True)
        self.draw()
        
    def hide_moment_compass(self):
        print('hide')
        self.line_moment1.set_visible(False)
        self.line_moment2.set_visible(False)
        self.draw()
        
    def show_period_compass(self):
        self.line_period1.set_visible(True)
        self.line_period2.set_visible(True)
        self.draw()
        
    def hide_period_compass(self):
        self.line_period1.set_visible(False)
        self.line_period2.set_visible(False)
        self.draw()
        
    def radius_change(self, r):
        self.ax_1.set_ylim(ymin=0, ymax=r)
        self.ax_2.set_ylim(ymin=0, ymax=r)
        self.draw()
        


class MatplotlibWidget_compass(QWidget):
    def __init__(self, parent=None):
        super(MatplotlibWidget_compass, self).__init__(parent)
        self.initUi()

    def initUi(self):
        self.layout = QVBoxLayout(self)
        self.mpl = MyMplCanvas(self)
        # self.mpl_ntb = NavigationToolbar(self.mpl, self)  # 增加完整的 toolbar

        self.layout.addWidget(self.mpl)
        # self.layout.addWidget(self.mpl_ntb) #排列toolbar


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ui = MatplotlibWidget_compass()
    ui.show()
    sys.exit(app.exec_())
