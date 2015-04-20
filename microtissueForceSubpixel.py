import glob, numpy
import matplotlib.pyplot as plt
#import matplotlib.cm as cm
import Tkinter as Tk
from PIL import Image, ImageTk
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
canvas = Tk.Canvas(master, 
           width=canvas_width, 
           height=canvas_height)
canvas.pack()

img = Tk.PhotoImage(file=imName)
canvas.create_image(margin, margin, anchor='nw', image=img)

#function to be called when mouse is clicked
def selectWindow(event):
    global imWindow, x, y
    x, y = event.x,event.y
    print x, y
    canvas.create_rectangle(x, y, x+windowSize, y+windowSize)
    canvas.update();
    imWindow = imArray[y-margin:y-margin+windowSize, x-margin:x-margin+windowSize]
#mouseclick event
canvas.bind("<Button 1>", selectWindow)
Tk.mainloop()

result = []
n = len(imNameList)
shift = numpy.zeros([n, 2])
for i in range(0, n):
    print i
    im = Image.open(imNameList[i])
    imArray = numpy.asarray(im)
    imArray = imArray[y-margin:y-margin+windowSize, x-margin:x-margin+windowSize]
#    result = match_template(imArray, imWindow)
    result = feature.register_translation(imWindow, imArray, upsample_factor=100)
    shift[i] = result[0]
#    ij = numpy.unravel_index(numpy.argmax(result), result.shape)
#    x, y = ij[::-1]
#    print x, y
    
time = numpy.arange(0, n)
time = numpy.multiply(timeUnit, time)
fig = plt.figure()
axes = fig.add_axes([0.1, 0.1, 0.8, 0.8]) # left, bottom, width, height (range 0 to 1)
plt.plot(time, -shift[:,1], label = 'X')
plt.plot(time, shift[:,0], label = 'Y')
axes.set_xlabel('Time (s)')
axes.set_ylabel('Displacement (Pixel)')
#axes.set_title('Post Deflection (Pixel)');
plt.legend()

fig = plt.figure()
axes = fig.add_axes([0.1, 0.1, 0.8, 0.8]) # left, bottom, width, height (range 0 to 1)
plt.plot(time, -shift[:,1] * scalebar, label = 'X')
plt.plot(time, shift[:,0] * scalebar, label = 'Y')
axes.set_xlabel('Time (s)')
axes.set_ylabel('Displacement (um)')
plt.legend()

fig = plt.figure()
axes = fig.add_axes([0.1, 0.1, 0.8, 0.8]) # left, bottom, width, height (range 0 to 1)
plt.plot(time, -shift[:,1] * scalebar * springConstant, label = 'Contractile force')
axes.set_xlabel('Time (s)')
axes.set_ylabel('Contractile force (uN)')
plt.legend()
