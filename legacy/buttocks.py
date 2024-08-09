from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
from OpenGL.GL import *
from OpenGL.GLU import *
import numpy as np
import glfw
import ctypes

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

acceleration_data = {'x': [], 'y': [], 'z': []}
angularV_data = {'x': [], 'y': [], 'z': []}
height = []

a_x = 0
a_y = 0
a_z = 0
w_x = 0
w_y = 0
w_z = 0
h = 0

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
    global gCamAng, gCamHeight, distanceFromOrigin, dropped, gCamRotX, gCamRotY, gCamRotZ
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    glEnable(GL_DEPTH_TEST)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(distanceFromOrigin, 1, 1, 10)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    gluLookAt(5 * np.sin(gCamAng), gCamHeight, 5 * np.cos(gCamAng), 0, 0, 0, 0, 1, 0)

    glViewport(0, 0, 720, 720)
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

    gCamRotX += w_x
    gCamRotY += w_y
    gCamRotZ += w_z

    glRotatef(gCamRotX, 1, 0, 0)
    glRotatef(gCamRotY, 0, 1, 0)
    glRotatef(gCamRotZ, 0, 0, 1)
    if dropped == 1:
        draw_glDrawArray()
    glPopMatrix()
    glDisable(GL_LIGHTING)

    ########## 연결 필요 #########
    acceleration_data['x'].append(a_x)
    acceleration_data['y'].append(a_y)
    acceleration_data['z'].append(a_z)
    angularV_data['x'].append(w_x)
    angularV_data['y'].append(w_y)
    angularV_data['z'].append(w_z)
    height.append(h)

    glViewport(720, 0, 1160, 720)
    plot_Acceleration_graph()
    plot_AngularV_graph()
    plot_Altitude_graph()

def plot_Acceleration_graph():
    fig = Figure(figsize=(6, 3.5), dpi=100, facecolor='black')
    canvas = FigureCanvas(fig)
    ax = fig.add_subplot(111, facecolor='black')
    
    ax.plot(acceleration_data['x'], label='a_x', color='red')
    ax.plot(acceleration_data['y'], label='a_y', color='green')
    ax.plot(acceleration_data['z'], label='a_z', color='blue')
    
    legend = ax.legend()
    for text in legend.get_texts():
        text.set_color('gray')
    
    ax.xaxis.label.set_color('white')
    ax.yaxis.label.set_color('white')


    ax.tick_params(axis='x', colors='white')
    ax.tick_params(axis='y', colors='white')

    ax.spines['top'].set_color('white')
    ax.spines['bottom'].set_color('white')
    ax.spines['left'].set_color('white')
    ax.spines['right'].set_color('white')

    ax.set_title('Acceleration by Time', color='white')
    ax.set_xlabel('t (s)', color='white')
    ax.set_ylabel('a (m/s^2)', color='white')
    fig.subplots_adjust(left=0.2, right=0.9, top=0.9, bottom=0.2)

    canvas.draw()
    renderer = canvas.get_renderer()
    raw_data = np.frombuffer(renderer.buffer_rgba(), dtype=np.uint8)
    raw_data = raw_data.reshape(int(renderer.height), int(renderer.width), 4)
    raw_data = np.flipud(raw_data)

    glWindowPos2d(720, 350) 
    glDrawPixels(int(renderer.width), int(renderer.height), GL_RGBA, GL_UNSIGNED_BYTE, raw_data)

def plot_Altitude_graph():
    fig = Figure(figsize=(6, 3.5), dpi=100, facecolor='black')
    canvas = FigureCanvas(fig)
    ax = fig.add_subplot(111, facecolor='black')
    
    ax.plot(height, color='red')

    
    ax.xaxis.label.set_color('white')
    ax.yaxis.label.set_color('white')

    ax.tick_params(axis='x', colors='white')
    ax.tick_params(axis='y', colors='white')

    ax.spines['top'].set_color('white')
    ax.spines['bottom'].set_color('white')
    ax.spines['left'].set_color('white')
    ax.spines['right'].set_color('white')

    ax.set_title('Altitude by Time', color='white')
    ax.set_xlabel('t (s)', color='white')
    ax.set_ylabel('Height (m)', color='white')
    fig.subplots_adjust(left=0.2, right=0.9, top=0.9, bottom=0.2)

    canvas.draw()
    renderer = canvas.get_renderer()
    raw_data = np.frombuffer(renderer.buffer_rgba(), dtype=np.uint8)
    raw_data = raw_data.reshape(int(renderer.height), int(renderer.width), 4)
    raw_data = np.flipud(raw_data)

    glWindowPos2d(720, 10) 
    glDrawPixels(int(renderer.width), int(renderer.height), GL_RGBA, GL_UNSIGNED_BYTE, raw_data)

def plot_AngularV_graph():
    fig = Figure(figsize=(6, 3.5), dpi=100, facecolor='black')
    canvas = FigureCanvas(fig)
    ax = fig.add_subplot(111, facecolor='black')
    
    ax.plot(angularV_data['x'], label='w x', color='red')
    ax.plot(angularV_data['y'], label='w_y', color='green')
    ax.plot(angularV_data['z'], label='w_z', color='blue')

    legend = ax.legend()
    for text in legend.get_texts():
        text.set_color('gray')
    
    ax.xaxis.label.set_color('white')
    ax.yaxis.label.set_color('white')

    ax.tick_params(axis='x', colors='white')
    ax.tick_params(axis='y', colors='white')

    ax.spines['top'].set_color('white')
    ax.spines['bottom'].set_color('white')
    ax.spines['left'].set_color('white')
    ax.spines['right'].set_color('white')

    ax.set_title('Angular Velocity by Time', color='white')
    ax.set_xlabel('t (s)', color='white')
    ax.set_ylabel('w (deg/s)', color='white')
    fig.subplots_adjust(left=0.2, right=0.9, top=0.9, bottom=0.2)

    canvas.draw()
    renderer = canvas.get_renderer()
    raw_data = np.frombuffer(renderer.buffer_rgba(), dtype=np.uint8)
    raw_data = raw_data.reshape(int(renderer.height), int(renderer.width), 4)
    raw_data = np.flipud(raw_data)

    glWindowPos2d(1280, 350) 
    glDrawPixels(int(renderer.width), int(renderer.height), GL_RGBA, GL_UNSIGNED_BYTE, raw_data)

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
    global gCamAng, gCamHeight, modeFlag, distanceFromOrigin, w_x, w_y, w_z
    if action==glfw.PRESS or action==glfw.REPEAT:
        if key==glfw.KEY_1:
            gCamAng += np.radians(-10%360)
        elif key==glfw.KEY_2:
            gCamAng += np.radians(10%360)
        
        # 회전 테스트
        elif key==glfw.KEY_Q:
            w_x += 0.05
        elif key==glfw.KEY_W:
            w_x -= 0.05
        elif key==glfw.KEY_E:
            w_y += 0.05
        elif key==glfw.KEY_R:
            w_y -= 0.05
        elif key==glfw.KEY_T:
            w_z += 0.05
        elif key==glfw.KEY_Y:
            w_z -= 0.05

gVertexArraySeparate = np.zeros((3, 3))

def main():
    global gVertexArraySeparate
    if not glfw.init():
        return
    window = glfw.create_window(1880, 720,'Gepri_GUI_DDDONG', None,None)
    if not window:
        glfw.terminate()
        return
    glfw.make_context_current(window)
    glfw.set_key_callback(window, key_callback)
    glfw.set_framebuffer_size_callback(window, framebuffer_size_callback)
    glfw.set_drop_callback(window, dropCallback)
    glfw.swap_interval(1)
    count = 0
    while not glfw.window_should_close(window):
        glfw.poll_events()
        count+=1
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

if __name__ == "__main__":
    main()
