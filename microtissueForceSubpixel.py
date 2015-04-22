import glob, numpy
import matplotlib.pyplot as plt
import Tkinter as Tk
import tkFileDialog
from PIL import Image
from skimage import feature

canvas_width = 512
canvas_height =256
windowSize = 100
global margin
margin = 20
timeUnit = 0.01
scalebar = 500/80
E = 1e6
R = 250e-6
L = 250e-6
springConstant = E*R*R*R*R/(2*L*L*L)
dirname = ''

app = Tk.Tk()
app.title("Calculation of Microtissue Contractile Force")

def selectDir():
    global dirname, imNameList, imArray, canvas, img, i, j
    dirname = tkFileDialog.askdirectory(parent=app,initialdir="/",title='Please select a directory')
    
    tv.set(dirname)

    imNameList = glob.glob(dirname + '/*.gif')
    imName = imNameList[0]
    im = Image.open(imName)
    imArray = numpy.asarray(im)
    img = Tk.PhotoImage(file=imName)
    canvas.create_image(0, 0, anchor="nw", image=img)
    i = canvas.create_line(0, 0, 0, 0, fill="red")
    j = canvas.create_line(0, 0, 0, 0, fill="red")
    canvas.bind("<Motion>", selectWindow)
    canvas.bind("<Button-1>", selectWindow2)

# button for select directory    
button = Tk.Button(app, text='Select Directory', padx=5, pady=5, command=selectDir)
button.grid(row=0, column=0, padx=10, pady=10)

# label displaying selected directory
tv = Tk.StringVar() 
label = Tk.Label(app, textvariable=tv, width=80, height=5)
label.grid(row=0, column=1, sticky="w")

# canvas for selecting ROI on the image
canvas = Tk.Canvas(app, width=canvas_width, height=canvas_height)
canvas.grid(row=1, columnspan=2, pady=10)

# calculate force
def calculateForce():
    result = []
    n = len(imNameList)
    shift = numpy.zeros([n, 2])
    for i in range(0, n):
        print "processing", i+1, "of", n
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
    force_x = -shift[:,1] * scalebar * springConstant / 1000
    force_y = -shift[:,0] * scalebar * springConstant / 1000
    plt.plot(time, force_x, label = 'Fx')
    plt.plot(time, force_y, label = 'Fy')
    plt.xlabel('Time (s)')
    plt.ylabel('Contractile force (mN)')
    plt.legend()
    
    plt.savefig(dirname+"/force.png")
    numpy.savetxt(dirname+"/force.csv", numpy.transpose([time, force_x, force_y]), fmt='%1.3f', delimiter='\t')

buttonSubmit = Tk.Button(app, text='Start', padx=5, pady=5, command=calculateForce)
buttonSubmit.grid(row=2, column=0, padx=10, pady=10)

# functions for selecting ROI
def selectWindow(event):
    global x, y
    x, y = event.x,event.y
    canvas.coords(i, 0, y, canvas_width-1, y)
    canvas.coords(j, x, 0, x, canvas_height-1)
    canvas.update();

global tag
tag = False    
def selectWindow2(event):
    global imWindow, x0, y0, x1, y1, tag
    if tag == False:
        x0, y0 = event.x,event.y
        print "First corner:", x0, y0
        canvas.create_line(0, y0, canvas_width-1, y0, fill="blue")
        canvas.create_line(x0, 0, x0, canvas_height-1, fill="blue")
        canvas.update();
        tag = True;
    else:
        x1, y1 = event.x,event.y
        print "Second corner:", x1, y1
        canvas.create_line(0, y1, canvas_width-1, y1, fill="blue")
        canvas.create_line(x1, 0, x1, canvas_height-1, fill="blue")
        canvas.update();
        imWindow = imArray[y0:y1, x0:x1]
        
Tk.mainloop()


