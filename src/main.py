from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.animation import FuncAnimation
from PIL import Image
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
import matplotlib.pyplot as plt
import numpy as np
import sys
import time
import threading
import glfw
import ctypes
import serial
import pygame

pygame.init()
pygame.font.init()
user32 = ctypes.WinDLL('user32')
font = pygame.font.SysFont('font.ttf', 55)
black = (0, 0, 0)
white = (255, 255, 255)
gVertexArraySeparate = np.zeros((3, 3))

gCamAng = 0.
gCamHeight = 3.
vertices = None 
normals = None
faces = None
dropped = 0
modeFlag = 0
distanceFromOrigin = 45

gCamRotX = 0.
gCamRotY = 0.
gCamRotZ = 0.

h = 0

# ser = serial.Serial(
#     port='COM8',
#     baudrate = '9600',
#     # parity=serial.PARITY_NONE,
#     # stopbits=serial.STOPBITS_ONE,
#     # bytesize=serial.EIGHTBITS
#     # timeout=1             
# )

def dropCallback(window, paths):
    global vertices, normals, faces, dropped, gVertexArraySeparate
    numberOfFacesWith3Vertices = 0
    numberOfFacesWith4Vertices = 0
    numberOfFacesWithMoreThan4Vertices = 0
    dropped = 1
    if(paths[0].split('.')[-1].lower() != "obj"):
        print("[잘못된 파일 형식]\n.obj 파일을 실행해주세요.")
        return
    with open(paths[0]) as f:
        lines = f.readlines()
        vStrings = [x.strip('v') for x in lines if x.startswith('v ')]
        vertices = convertVertices(vStrings)
        if np.amax(vertices) <= 1.2:
            vertices /= np.amax(vertices)
        else:
            vertices /= np.amax(vertices)/2
        vnStrings = [x.strip('vn') for x in lines if x.startswith('vn')]
        if not vnStrings:
            normals = fillNormalsArray(len(vStrings))
        else:
            normals = convertVertices(vnStrings)
        faces = [x.strip('f') for x in lines if x.startswith('f')]
    for face in faces: 
        if len(face.split()) == 3:
            numberOfFacesWith3Vertices +=1
        elif len(face.split()) == 4:
            numberOfFacesWith4Vertices +=1
        else:
            numberOfFacesWithMoreThan4Vertices +=1
    if(numberOfFacesWith4Vertices > 0 or numberOfFacesWithMoreThan4Vertices > 0):
        faces = triangulate()
    gVertexArraySeparate = createVertexArraySeparate()
    faces = []
    normals = []
    vertices = []

def fillNormalsArray(numberOfVertices):
    normals = np.zeros((numberOfVertices, 3))
    i = 0
    for vertice in vertices:
        normals[i] = normalized(vertice)
        i +=1
    return normals

def convertVertices(verticesStrings):
    v = np.zeros((len(verticesStrings), 3))
    i = 0
    for vertice in verticesStrings:
        j = 0
        for t in vertice.split():
            try:
                v[i][j] = (float(t))
            except ValueError:
                pass
            j+=1
        i+=1
    return v

def triangulate():
    facesList = []
    nPolygons = []
    for face in faces:
        if(len(face.split())>=4):
            nPolygons.append(face)
        else:
            facesList.append(face)
    for face in nPolygons:
        for i in range(1, len(face.split())-1):
            seq = [str(face.split()[0]), str(face.split()[i]), str(face.split()[i+1])]
            string = ' '.join(seq)
            facesList.append(string)
    return facesList

def createVertexArraySeparate():
    varr = np.zeros((len(faces)*6,3), 'float32')
    i=0
    normalsIndex = 0
    verticeIndex = 0
    for face in faces:
        for f in face.split():
            if '//' in f:
                verticeIndex = int(f.split('//')[0])-1 
                normalsIndex = int(f.split('//')[1])-1
            elif '/' in f: 
                if len(f.split('/')) == 2:
                    verticeIndex = int(f.split('/')[0])-1 
                    normalsIndex = int(f.split('/')[0])-1
                else:
                    verticeIndex = int(f.split('/')[0])-1 
                    normalsIndex = int(f.split('/')[2])-1
            else:
                verticeIndex = int(f.split()[0])-1 
                normalsIndex = int(f.split()[0])-1
            varr[i] = normals[normalsIndex]
            varr[i+1] = vertices[verticeIndex]
            i+=2
    return varr

def render(ang):
    global gCamAng, gCamHeight, distanceFromOrigin, dropped, gCamRotX, gCamRotY, gCamRotZ, h
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    glEnable(GL_DEPTH_TEST)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(distanceFromOrigin, 1, 1, 10)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    gluLookAt(5 * np.sin(gCamAng), gCamHeight, 5 * np.cos(gCamAng), 0, 0, 0, 0, 1, 0)

    glViewport(0, 0, 1080, 1080)
    drawFrame()
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glEnable(GL_LIGHT1)
    glEnable(GL_LIGHT2)
    glPushMatrix()
    lightPos0 = (1., 2., 3., 1.)
    lightPos1 = (3., 2., 1., 1.)
    lightPos2 = (2., 3., 1., 1.)
    glLightfv(GL_LIGHT0, GL_POSITION, lightPos0)
    glLightfv(GL_LIGHT1, GL_POSITION, lightPos1)
    glLightfv(GL_LIGHT2, GL_POSITION, lightPos2)
    glPopMatrix()
    ambientLightColor0 = (.1, .1, .1, 1.)
    diffuseLightColor0 = (1., 1., 1., 1.)
    specularLightColor0 = (1., 1., 1., 1.)
    ambientLightColor1 = (.075, .075, .075, 1.)
    diffuseLightColor1 = (0.75, 0.75, 0.75, 0.75)
    specularLightColor1 = (0.75, 0.75, 0.75, 0.75)
    ambientLightColor2 = (.05, .05, .05, 1.)
    diffuseLightColor2 = (0.5, 0.5, 0., 0.5)
    specularLightColor2 = (0.5, 0.5, 0., 0.5)
    glLightfv(GL_LIGHT0, GL_AMBIENT, ambientLightColor0)
    glLightfv(GL_LIGHT0, GL_DIFFUSE, diffuseLightColor0)
    glLightfv(GL_LIGHT0, GL_SPECULAR, specularLightColor0)
    glLightfv(GL_LIGHT1, GL_AMBIENT, ambientLightColor1)
    glLightfv(GL_LIGHT1, GL_DIFFUSE, diffuseLightColor1)
    glLightfv(GL_LIGHT1, GL_SPECULAR, specularLightColor1)
    glLightfv(GL_LIGHT2, GL_AMBIENT, ambientLightColor2)
    glLightfv(GL_LIGHT2, GL_DIFFUSE, diffuseLightColor2)
    glLightfv(GL_LIGHT2, GL_SPECULAR, specularLightColor2)
    diffuseObjectColor = (0.4, 0.6, 0.5, 1.)
    specularObjectColor = (0.6, 0.3, 0.3, .5)
    glMaterialfv(GL_FRONT, GL_AMBIENT_AND_DIFFUSE, diffuseObjectColor)
    glPushMatrix()

    # if ser.readable() :
    #         x=ser.readline()
    #         try : 
    #             x= list(map(float, x.decode('utf-8').rstrip().split(',')))
    #             print(x)
    #             gCamRotX = x[0]
    #             gCamRotY = x[2]
    #             gCamRotZ = -x[1]
    #             h = x[3]
    #         except :
    #             pass

    glRotatef(gCamRotX, 1, 0, 0)
    glRotatef(gCamRotY, 0, 1, 0)
    glRotatef(gCamRotZ, 0, 0, 1)
    
    if dropped == 1:
        draw_glDrawArray()
    glPopMatrix()
    glDisable(GL_LIGHTING)

def draw_glDrawArray():
    global gVertexArraySeparate
    varr = gVertexArraySeparate
    glEnableClientState(GL_VERTEX_ARRAY)
    glEnableClientState(GL_NORMAL_ARRAY)
    glNormalPointer(GL_FLOAT, 6*varr.itemsize, varr)
    glVertexPointer(3, GL_FLOAT, 6*varr.itemsize, ctypes.c_void_p(varr.ctypes.data + 3*varr.itemsize))
    glDrawArrays(GL_TRIANGLES, 0, int(varr.size/6))

def drawFrame():
    glBegin(GL_LINES)
    glColor3ub(255, 0, 0)
    glVertex3fv(np.array([0.,0.,0.]))
    glVertex3fv(np.array([1.,0.,0.]))
    glColor3ub(0, 255, 0)
    glVertex3fv(np.array([0.,0.,0.]))
    glVertex3fv(np.array([0.,1.,0.]))
    glColor3ub(0, 0, 255)
    glVertex3fv(np.array([0.,0.,0]))
    glVertex3fv(np.array([0.,0.,1.]))
    glEnd()

def key_callback(window, key, scancode, action, mods):
    global gCamAng, gCamHeight, modeFlag, distanceFromOrigin
    if action==glfw.PRESS or action==glfw.REPEAT:
        if key==glfw.KEY_1:
            gCamAng += np.radians(-10%360)
        elif key==glfw.KEY_2:
            gCamAng += np.radians(10%360)
        
        # 회전 테스트
        # elif key==glfw.KEY_Q:
        #     w_x += 0.05
        # elif key==glfw.KEY_W:
        #     w_x -= 0.05
        # elif key==glfw.KEY_E:
        #     w_y += 0.05
        # elif key==glfw.KEY_R:
        #     w_y -= 0.05
        # elif key==glfw.KEY_T:
        #     w_z += 0.05
        # elif key==glfw.KEY_Y:
        #     w_z -= 0.05

def gl_window_thread():
    global gVertexArraySeparate
    if not glfw.init():
        return
    window = glfw.create_window(1080, 1080, 'Gepri GUI (3D Model)', None, None)
    if not window:
        glfw.terminate()
        return
    glfw.make_context_current(window)
    glfw.set_key_callback(window, key_callback)
    glfw.set_framebuffer_size_callback(window, framebuffer_size_callback)
    glfw.set_drop_callback(window, dropCallback)

    window_x, window_y = 0, 0  
    glfw.set_window_pos(window, window_x, window_y)

    glfw.swap_interval(1)
    count = 0
    while not glfw.window_should_close(window):
        glfw.poll_events()
        count += 1
        ang = count % 360
        render(ang)
        count += 1
        glfw.swap_buffers(window)
    glfw.terminate()

def l2norm(v):
    return np.sqrt(np.dot(v, v))

def normalized(v):
    l = l2norm(v)
    return 1/l * np.array(v)

def framebuffer_size_callback(window, width, height):
    glViewport(0, 0, width, height)

class RealTimePlotter(QMainWindow):
    def __init__(self):
        super().__init__()

        self.initUI()
        self.x_data = []
        self.y_data = []
        self.line, = self.ax.plot([], [], lw=2)
        self.start_time = time.time()

    def initUI(self):
        self.setWindowTitle('Gepri GUI (Altitude Graph)')
        self.setGeometry(1080, 0, 800, 600)

        self.central_widget = QWidget()
        self.central_widget.setStyleSheet("background-color: black;")
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout(self.central_widget)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        self.fig, self.ax = plt.subplots()
        self.fig.patch.set_facecolor('black')
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setStyleSheet("background-color: black;") 
        self.layout.addWidget(self.canvas)

        self.ax.xaxis.label.set_color('white')
        self.ax.yaxis.label.set_color('white')

        self.ax.set_facecolor('black') 
        self.ax.set_xlim(0, 10)
        self.ax.set_ylim(0, 100)
        
        self.ax.tick_params(axis='x', colors='white')
        self.ax.tick_params(axis='y', colors='white')

        self.ax.spines['top'].set_color('white')
        self.ax.spines['bottom'].set_color('white')
        self.ax.spines['left'].set_color('white')
        self.ax.spines['right'].set_color('white')

        self.ax.set_title('Altitude by Time', color='white')
        self.ax.set_xlabel('t (s)', color='white')
        self.ax.set_ylabel('Height (m)', color='white')

        self.anim = FuncAnimation(self.fig, self.update_plot, interval=10)

    def update_plot(self, frame):
        global h
        current_time = time.time()
        x = current_time - self.start_time 
        y = h

        self.x_data.append(x)
        self.y_data.append(y)

        self.line.set_data(self.x_data, self.y_data)

        self.ax.set_xlim(max(0, x - 10), x)
        
        if min(self.y_data) != self.ax.get_ylim()[0] or max(self.y_data) != self.ax.get_ylim()[1]:
            self.ax.set_ylim(min(self.y_data), max(self.y_data))

        return self.line,

class RECT(ctypes.Structure):
    _fields_ = [("left", ctypes.c_int),
                ("top", ctypes.c_int),
                ("right", ctypes.c_int),
                ("bottom", ctypes.c_int)]

def set_window_position(hwnd, x, y):
    rect = RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(rect))
    user32.MoveWindow(hwnd, x, y, rect.right - rect.left, rect.bottom - rect.top, True)

def render_text(text, font, color, surface, position):
    textobj = font.render(text, True, color)
    textrect = textobj.get_rect()
    textrect.topleft = position
    surface.blit(textobj, textrect)

def load_gif_frames(image_path):
    with Image.open(image_path) as img:
        frames = []
        try:
            while True:
                frame = pygame.image.fromstring(img.tobytes(), img.size, img.mode)
                frames.append(frame)
                img.seek(img.tell() + 1)
        except EOFError:
            pass
    return frames

def pygame_window_thread():
    global width, height, gCamRotX, gCamRotY, gCamRotZ, h
    width, height = 800, 480
    pygame_screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption('Gepri GUI (Data)')

    hwnd = pygame.display.get_wm_info()['window']
    set_window_position(hwnd, 1072, 600)

    image_path = 'src/image.gif'
    frames = load_gif_frames(image_path)
    frame_index = 1
    
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        pygame_screen.fill(black)
        xtext = "X: "+str((360 + gCamRotX % 360) % 360)+ "°"
        ytext = "Y: "+str((360 + gCamRotY % 360) % 360)+ "°"
        ztext = "Z: "+str((360 + gCamRotZ % 360) % 360)+ "°"
        htext = "Height: "+str(h)+"m"
        render_text(htext, font, white, pygame_screen, (25, 25))
        render_text(xtext, font, white, pygame_screen, (25, 125))
        render_text(ytext, font, white, pygame_screen, (25, 175))
        render_text(ztext, font, white, pygame_screen, (25, 225))
        pygame_screen.blit(frames[frame_index], (525, 190))

        frame_index = (frame_index + 1) % (len(frames))
        if frame_index == 0:
            frame_index = 1
        pygame.display.flip()
        pygame.time.Clock().tick(30)

if __name__ == '__main__':

    gl_thread = threading.Thread(target=gl_window_thread)
    gl_thread.start()

    pygame_thread = threading.Thread(target=pygame_window_thread)
    pygame_thread.start()

    app = QApplication(sys.argv)
    main = RealTimePlotter()
    main.show()
    sys.exit(app.exec_())

    gl_thread.join()