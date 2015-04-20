import glob, numpy
import matplotlib.pyplot as plt
import Tkinter as Tk
from PIL import Image
from skimage import feature

path = 'file 10 point 5 hz avi file for force analysis/'
imNameList = glob.glob(path + '*.gif')

imName = imNameList[0]
im = Image.open(imName)
imArray = numpy.asarray(im)

canvas_width = 552
canvas_height =296
windowSize = 100
margin = 20
timeUnit = 0.01
scalebar = 500/80
E = 1e6
R = 250e-6
L = 250e-6
springConstant = E*R*R*R*R/(2*L*L*L)

master = Tk.Tk()
frame = Tk.Frame(master)
frame.pack()

# to be modified
#redbutton = Tk.Button(frame, text='askopenfile', command=frame.askopenfile)
#redbutton.pack( side = "top")

canvas = Tk.Canvas(frame, 
           width=canvas_width, 
           height=canvas_height)
canvas.pack(side="top")

img = Tk.PhotoImage(file=imName)
canvas.create_image(margin, margin, anchor='nw', image=img)

global i, j
i = canvas.create_line(0, 0, 0, 0, fill="red")
j = canvas.create_line(0, 0, 0, 0, fill="red")
#function to be called when mouse is clicked
def selectWindow(event):
    global x, y
    x, y = event.x,event.y
#    canvas.create_rectangle(x, y, x+windowSize, y+windowSize)
    canvas.coords(i, margin, y, canvas_width - margin, y)
    canvas.coords(j, x, margin, x, canvas_height - margin)
    canvas.update();

global tag
tag = False    
def selectWindow2(event):
    global imWindow, x0, y0, x1, y1, tag
    if tag == False:
        x0, y0 = event.x,event.y
        print x0, y0
        canvas.create_line(margin, y0, canvas_width - margin, y0, fill="blue")
        canvas.create_line(x0, margin, x0, canvas_height - margin, fill="blue")
        canvas.update();
        tag = True;
    else:
        x1, y1 = event.x,event.y
        print x1, y1
        canvas.create_line(margin, y1, canvas_width - margin, y1, fill="blue")
        canvas.create_line(x1, margin, x1, canvas_height - margin, fill="blue")
        canvas.update();
        imWindow = imArray[x0:x1, y0:y1]
#mouseclick event
canvas.bind("<Motion>", selectWindow)
canvas.bind("<Button-1>", selectWindow2)

Tk.mainloop()

result = []
n = len(imNameList)
shift = numpy.zeros([n, 2])
for i in range(0, n):
    print i
    im = Image.open(imNameList[i])
    imArray = numpy.asarray(im)
    imArray = imArray[x0:x1, y0:y1]
    result = feature.register_translation(imWindow, imArray, upsample_factor=100)
    shift[i] = result[0]

    
time = numpy.arange(0, n)
time = numpy.multiply(timeUnit, time)

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

numpy.savetxt("force.csv", numpy.transpose([time, force_x, force_y]), fmt='%1.3f', delimiter='\t')
