import sys, os, glob, numpy
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PIL import Image
from skimage import feature
import matplotlib.pyplot as plt

image_width = 512
image_height = 256
windowSize = 100
margin = 20
timeUnit = 0.01
scalebar = 6.27
E = 1e6
R = 250e-6
L = 1000e-6
springConstant = E*R*R*R*R/(2*L*L*L)
dirname = ''

class AppForm(QMainWindow):
    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent)
        self.setWindowTitle('Calculation of Microtissue Contractile Force')
        self.create_menu()
        self.create_main_frame()
        self.create_status_bar()
        
    def create_menu(self):        
        self.file_menu = self.menuBar().addMenu("&File")
        
        open_file_action = self.create_action("&Open data",
            shortcut="Ctrl+O", slot=self.open_data, 
            tip="Select the data file")
        load_file_action = self.create_action("&Save plot",
            shortcut="Ctrl+S", slot=self.save_plot, 
            tip="Save the plot")
        quit_action = self.create_action("&Quit", slot=self.close, 
            shortcut="Ctrl+Q", tip="Close the application")
        
        self.add_actions(self.file_menu, 
            (open_file_action, None, load_file_action, None, quit_action))
        
        self.help_menu = self.menuBar().addMenu("&Help")
        about_action = self.create_action("&About", 
            shortcut='F1', slot=self.on_about, 
            tip='About the demo')
        
        self.add_actions(self.help_menu, (about_action,))
        
    def create_main_frame(self):
        """create a series of buttons and a canvas."""
        self.main_frame = QWidget()
        grid = QGridLayout()
        grid.setSpacing(10)
        # button for select directory
        self.button_select = QPushButton("&Select Directory")
        grid.addWidget(self.button_select, 0, 0)
#        self.connect(self.button_select, SIGNAL('clicked()'), self.open_data)
        self.button_select.clicked.connect(self.open_data)
        # label displaying selected directory
        self.label = QLabel('Selected file')
        grid.addWidget(self.label, 1, 0)
        
        # canvas for displaying image and selecting points
        self.image = QPixmap(image_width, image_height)
        self.image.fill(Qt.white)
        self.canvas = QLabel()
        self.canvas.setPixmap(self.image)
        self.canvas.setMouseTracking(True)
        self.canvas.mouseMoveEvent = self.on_move
        self.canvas.mousePressEvent = self.on_click
        grid.addWidget(self.canvas, 2, 0)
        
        # list for storing the markers
        self.markers = []
         
#        # button for rotation
#        self.button_rotate = tk.Button(self, text='Rotate', padx=5, pady=5)
#        self.button_rotate.grid(row=2, column=0, padx=10, pady=10, sticky="w")
#        self.button_rotate.bind("<1>", self.rotate_image)
        
        # button for calculating force
        self.button_calculate = QPushButton("Calculte")
        grid.addWidget(self.button_calculate, 3, 0)
        self.button_calculate.clicked.connect(self.on_calculate)

        self.main_frame.setLayout(grid)
        self.setCentralWidget(self.main_frame)
#        # button for exit
#        self.buttonExit = tk.Button(self, text='Exit', padx=5, pady=5, 
#                                    command=self.destroy)
#        self.buttonExit.grid(row=2, column=2, padx=10, pady=10, sticky="e")
        
    def create_status_bar(self):
        self.status_text = QLabel("This is a demo")
        self.statusBar().addWidget(self.status_text, 1)
        
    def add_actions(self, target, actions):
        for action in actions:
            if action is None:
                target.addSeparator()
            else:
                target.addAction(action)

    def create_action(  self, text, slot=None, shortcut=None, 
                        icon=None, tip=None, checkable=False, 
                        signal="triggered()"):
        action = QAction(text, self)
        if icon is not None:
            action.setIcon(QIcon(":/%s.png" % icon))
        if shortcut is not None:
            action.setShortcut(shortcut)
        if tip is not None:
            action.setToolTip(tip)
            action.setStatusTip(tip)
        if slot is not None:
            self.connect(action, SIGNAL(signal), slot)
        if checkable:
            action.setCheckable(True)
        return action
        
    def open_data(self):
        file_formats = "*.gif"
        self.file_name = QFileDialog.getOpenFileName(self,
                                                     'Select data file',
                                                     file_formats)
        self.dirname = os.path.dirname(self.file_name)
        if self.file_name:
            print(self.file_name)
            self.image = QPixmap(self.file_name);
            self.canvas.setPixmap(self.image)
            self.canvas.show()
            self.label.setText(self.file_name)
        
    def save_plot(self):
        file_formats = "PNG (*.png)|*.png"
        
        path = QFileDialog.getSaveFileName(self, 
                        'Save file', '', 
                        file_formats)
        if path:
            self.canvas.print_figure(path, dpi=self.dpi)
            self.statusBar().showMessage('Saved to %s' % path, 2000)
            
    def on_about(self):
        msg = """Electrical signal analyzer for piezoelectric device
    
        """
        QMessageBox.about(self, "About the demo", msg.strip())
        self.statusBar().showMessage('Opened data file %s' % self.file_name, 2000)
    
    def on_move(self, event):
        if hasattr(self, 'file_name'):
            self.image = QPixmap(self.file_name)
        else:
            self.image = QPixmap(image_width, image_height)
            self.image.fill(Qt.white)
        
        painter = QPainter(self.image)
        painter.setPen(QPen(Qt.red))
        for marker in self.markers:
            # draw horizontal line
            self.point_h_start = QPoint(0, marker.y())
            self.point_h_end = QPoint(image_width, marker.y())
            painter.drawLines(self.point_h_start, self.point_h_end)
            
            # draw vertical line
            self.point_v_start = QPoint(marker.x(), 0)
            self.point_v_end = QPoint(marker.x(), image_height)
            painter.drawLines(self.point_v_start, self.point_v_end)
            
        painter.setPen(QPen(Qt.blue))    
        # draw horizontal line
        self.point_h_start = QPoint(0, event.y())
        self.point_h_end = QPoint(image_width, event.y())
        painter.drawLines(self.point_h_start, self.point_h_end)
        # draw vertical line
        self.point_v_start = QPoint(event.x(), 0)
        self.point_v_end = QPoint(event.x(), image_height)
        painter.drawLines(self.point_v_start, self.point_v_end)

        self.canvas.setPixmap(self.image)
        self.canvas.show()
        painter.end()
        self.statusBar().showMessage('x=%d y=%d' % (event.x(), event.y()))
    
    def on_click(self, event):
        if len(self.markers) == 2:
            self.markers = []
        self.markers.append(QPoint(event.x(), event.y()))
        
        painter = QPainter(self.image)
        painter.setPen(QPen(Qt.red))
        for marker in self.markers:
            # draw horizontal line
            self.point_h_start = QPoint(0, marker.y())
            self.point_h_end = QPoint(image_width, marker.y())
            painter.drawLines(self.point_h_start, self.point_h_end)
            
            # draw vertical line
            self.point_v_start = QPoint(marker.x(), 0)
            self.point_v_end = QPoint(marker.x(), image_height)
            painter.drawLines(self.point_v_start, self.point_v_end)
        self.canvas.setPixmap(self.image)
        self.canvas.show()
        painter.end()

    def on_calculate(self):
        # calculate force
        if len(self.markers) < 2:
            return
        
        x0 = min(self.markers[0].x(), self.markers[1].x())
        x1 = max(self.markers[0].x(), self.markers[1].x())
        y0 = min(self.markers[0].y(), self.markers[1].y())
        y1 = max(self.markers[0].y(), self.markers[1].y())
        result = []
        imNameList = glob.glob(self.dirname + '/*.gif')
        n = len(imNameList)
        shift = numpy.zeros([n, 2])
        im = Image.open(imNameList[0])
        imArray = numpy.asarray(im)
        imWindow = imArray[y0:y1, x0:x1]
        for i in range(0, n):
            print("processing ", i+1, " of ", n)
            im = Image.open(imNameList[i])
            imArray = numpy.asarray(im)
            imArray = imArray[y0:y1, x0:x1]
            result = feature.register_translation(imWindow, imArray, upsample_factor=100)
            shift[i] = result[0]
        
        time = numpy.arange(0, n)
        time = numpy.multiply(timeUnit, time)
        
        plt.figure()
        plt.subplot(2, 2, 1)
        plt.plot(time, -shift[:,1], label = 'X')
        plt.plot(time, -shift[:,0], label = 'Y')
        plt.xlabel('Time (s)')
        plt.ylabel('Displacement (Pixel)')
        plt.legend()
        
        plt.subplot(2, 2, 2)
        plt.plot(time, -shift[:,1] * scalebar, label = 'X')
        plt.plot(time, -shift[:,0] * scalebar, label = 'Y')
        plt.xlabel('Time (s)')
        plt.ylabel('Displacement (um)')
        plt.legend()
        
        plt.subplot(2, 2, 3)
        force_x = -shift[:,1] * scalebar * springConstant
        force_y = -shift[:,0] * scalebar * springConstant
        force = numpy.sqrt(force_x * force_x + force_y * force_y)
        plt.plot(time, force_x, label = 'Fx')
        plt.plot(time, force_y, label = 'Fy')
        plt.plot(time, force, label = 'F')
        plt.xlabel('Time (s)')
        plt.ylabel('Contractile force (uN)')
        plt.legend()
        
        plt.savefig(self.dirname+"/force.png")
        numpy.savetxt(self.dirname+"/force.csv", 
                      numpy.transpose([time, force_x, force_y, force]), 
                      fmt='%1.3f', delimiter='\t')
        
def main():
    app = QApplication(sys.argv)
    form = AppForm()
    form.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()


