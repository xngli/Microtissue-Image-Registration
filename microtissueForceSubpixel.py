import sys, os, numpy
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from skimage import feature
import matplotlib.pyplot as plt
from matplotlib.ticker import AutoMinorLocator 
import javabridge
import bioformats

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
        file_formats = "*.nd2"
        self.file_name = QFileDialog.getOpenFileName(self,
                                                     'Select data file',
                                                     file_formats)
        self.dirname = os.path.dirname(self.file_name)
        if self.file_name:
            print self.file_name
            self.reader = bioformats.ImageReader(self.file_name)
            image_np = self.reader.read(z=0, t=10)  # discard the first 10 frames
            image_np = image_np[:,:,1]
            image_np = numpy.uint8((image_np - image_np.min())/image_np.ptp()*255.0)
            image_q = QImage(image_np.data, 
                             image_np.shape[1], 
                             image_np.shape[0], 
                             image_np.shape[1], 
                             QImage.Format_Indexed8)
            self.image_qc = image_q.convertToFormat(QImage.Format_RGB32)
            self.image = QPixmap.fromImage(self.image_qc)
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
        msg = """Python program for image registration
    
        """
        QMessageBox.about(self, "About the demo", msg.strip())
        self.statusBar().showMessage('Opened data file %s' % self.file_name, 2000)
    
    def on_move(self, event):
        if hasattr(self, 'image_qc'):
            self.image = QPixmap.fromImage(self.image_qc)
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
        n = 500
        shift = numpy.zeros([n-10, 2])
        image_np = self.reader.read(z=0, t=10)  # discard the first 10 frames
        image_np = image_np[:,:,1]
        imWindow = image_np[y0:y1, x0:x1]
        for i in range(10, n):
            self.statusBar().showMessage('Processing %d of %d' % (i-9, n-10))
            image_np = self.reader.read(z=0, t=i)
            image_np = image_np[:,:,1]
            image_np = image_np[y0:y1, x0:x1]
            result = feature.register_translation(imWindow, 
                                                  image_np, 
                                                  upsample_factor=100)
            shift[i-10] = result[0]
        
        time = numpy.arange(0, n-10)
        time = numpy.multiply(timeUnit, time)
        
        shift = -shift
        x_min = min(shift[:,1])
        index = numpy.where(shift[:,1] == x_min)
        index = index[0][0]
        shift[:,1] = shift[:,1] - x_min
        shift[:,0] = shift[:,0] - shift[index,0]
        
        pixel_x = shift[:,1]
        pixel_y = shift[:,0]
        pixel = numpy.sqrt(pixel_x * pixel_x + pixel_y * pixel_y)
        
        displacement_x = shift[:,1] * scalebar
        displacement_y = shift[:,0] * scalebar
        displacement = numpy.sqrt(displacement_x * displacement_x + displacement_y * displacement_y)
        
        fig = plt.figure()
        ax = fig.gca()
        plt.plot(time, displacement_x, label = 'X')
        plt.plot(time, displacement_y, label = 'Y')
        plt.plot(time, displacement, label = 'Total')
        ax.yaxis.set_minor_locator(AutoMinorLocator(5))
        plt.xlabel('Time (s)')
        plt.ylabel('Displacement (um)')
        plt.legend(loc='lower right')
        plt.grid(which='minor', alpha=0.35)                                                
        plt.grid(which='major', alpha=1)
        plt.show()
        
        force_x = shift[:,1] * scalebar * springConstant
        force_y = shift[:,0] * scalebar * springConstant
        force = numpy.sqrt(force_x * force_x + force_y * force_y)
        
        plt.savefig(self.file_name[0:-4] + "_force.png", dpi=300)
        numpy.savetxt(self.file_name[0:-4] + "_force.csv", 
                      numpy.transpose([time, 
                                       pixel_x, 
                                       pixel_y, 
                                       pixel,
                                       displacement_x, 
                                       displacement_y, 
                                       displacement,
                                       force_x, 
                                       force_y, 
                                       force]), 
                      fmt='%1.3f', 
                      delimiter='\t',
                      header='t(s)\tpx\tpy\tp\tx(um)\ty(um)\ttotal(um)\tfx(uN)\tfy(uN)\tf(uN)',
                      comments='')
        
def main():
    javabridge.start_vm(class_path=bioformats.JARS)
    app = QApplication(sys.argv)
    form = AppForm()
    form.show()
    sys.exit(app.exec_())
    javabridge.kill_vm()

if __name__ == "__main__":
    main()


