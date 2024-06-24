import pygame
import serial
import struct
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import numpy as np
import math
import matplotlib.pyplot as plt


long  = 1
width = 0.8
hight = 0.2

# Cube vertices and faces
vertices_1 = [
    [long, -width, -hight], [long, width, -hight], [-long, width, -hight], [-long, -width, -hight],
    [long, -width, hight], [long, width, hight], [-long, width, hight], [-long, -width, hight]
]

vertices_2 = [
    [long+3, -width, -hight], [long+3, width, -hight], [-long+3, width, -hight], [-long+3, -width, -hight],
    [long+3, -width, hight], [long+3, width, hight], [-long+3, width, hight], [-long+3, -width, hight]
]

face_edges = (
    (0, 1, 2, 3),
    (4, 5, 6, 7),
    (0, 4, 7, 3),
    (1, 5, 6, 2),
    (0, 1, 5, 4),
    (3, 2, 6, 7)
)

line_edges = [
    [0, 1], [1, 2], [2, 3], [3, 0],
    [0, 4], [1, 5], [2, 6], [3, 7],
    [4, 5], [5, 6], [6, 7], [7, 4]
]

blue_gray_1   = (0.68, 0.84, 1)
red_gray_1 = (255, 0.84, 1)
line_white  = (1,1,1)

face_colors_1 = [blue_gray_1 for i in range(6)]
face_colors_2 = [red_gray_1 for i in range(6)]

x_list = []
y_list = []
z_list = []

def eulerAnglesToRotationMatrix(theta) :

    R_x = np.array([[1,         0,                  0                   ],
                    [0,         math.cos(theta[0]), -math.sin(theta[0]) ],
                    [0,         math.sin(theta[0]), math.cos(theta[0])  ]
                    ])



    R_y = np.array([[math.cos(theta[1]),    0,      math.sin(theta[1])  ],
                    [0,                     1,      0                   ],
                    [-math.sin(theta[1]),   0,      math.cos(theta[1])  ]
                    ])

    R_z = np.array([[math.cos(theta[2]),    -math.sin(theta[2]),    0],
                    [math.sin(theta[2]),    math.cos(theta[2]),     0],
                    [0,                     0,                      1]
                    ])


    R = np.dot(R_z, np.dot( R_y, R_x ))

    return R

def draw_cube_A(vertices_1, xtheta, ytheta, ztheta):
    vertices_1 = np.array(vertices_1)@np.array(eulerAnglesToRotationMatrix([xtheta, ytheta, ztheta]))
    vertices_1[:,0] -= 1.5
    glBegin(GL_QUADS)
    for face in range(len(face_edges)):
        glColor3fv(face_colors_1[face])
        for vertex in face_edges[face]:
            glVertex3fv(vertices_1[vertex])
    glEnd()

    glColor3f(line_white[0], line_white[1], line_white[2])
    glBegin(GL_LINES)
    for edge in line_edges:
        for vertex in edge:
            glVertex3fv(vertices_1[vertex])
    glEnd()

def draw_cube_B(vertices_1, xtheta, ytheta, ztheta):
    vertices_2 = np.array(vertices_1)@np.array(eulerAnglesToRotationMatrix([xtheta, ytheta, ztheta]))
    vertices_2[:,0] += 1.5
    glBegin(GL_QUADS)
    for face in range(len(face_edges)):
        glColor3fv(face_colors_2[face])
        for vertex in face_edges[face]:
            glVertex3fv(vertices_2[vertex])
    glEnd()

    glColor3f(line_white[0], line_white[1], line_white[2])
    glBegin(GL_LINES)
    for edge in line_edges:
        for vertex in edge:
            glVertex3fv(vertices_2[vertex])
    glEnd()



def main():

    A = np.array([[1,0,0],[0,1,0],[0,0,1]])
    dt = 0.0625
    B = np.array([[dt,0,0],[0,dt,0],[0,0,dt]])

    H = np.array([[1,0,0],[0,1,0],[0,0,1]])
    #过程噪声
    Q = np.diag([0.1, 0.1, 0.1])    
    #测量噪声
    R_stable = np.diag([4e-5, 3e-5, 2e-5])
    R_move = np.diag([1e-1, 1e-1, 1e-3])

    R = R_stable
    # 估计误差协方差
    P = np.eye(3)

    x = np.zeros((3, 1))  # 状态向量 [角度_X, 角度_Y, 角度_Z]
    z = np.zeros((3, 1))  # 观测向量 [角度_X, 角度_Y, 角度_Z]

    pygame.init()
    display = (800, 600)
    pygame.display.set_mode(display, DOUBLEBUF | OPENGL)

    gluPerspective(45, (display[0] / display[1]), 0.1, 50.0)
    glTranslatef(0.0, 0.0, -10)

    # Connect to the serial port
    ser = serial.Serial('COM7', 115200)  # Replace 'COM3' with your serial port and baud rate

    rawFrame = []
    time = 0
    times = 100
    x_list = [0]
    x_or_list = []
    y_or_list = []
    z_or_list = []
    x_or = 0
    y_or = 0
    z_or = 0

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()

        # Read gyroscope measurements from the serial port

        byte  = ser.read(1)        
        rawFrame += byte 

        if rawFrame[-2:]==[13, 10]:
            #print(rawFrame)  
            if len(rawFrame) == 14:

                (x_gyro, y_gyro, z_gyro, x_acc, y_acc, z_acc) = struct.unpack('>hhhhhh', bytes(rawFrame[:-2]))                         
                # debug info
                output = 'gyr_x={0:<6} gyr_y={1:<6} gyr_z={2:<6} acc_x={3:<6} acc_y={4:<6} acc_z={5:<6}'.format(
                    x_gyro,
                    y_gyro,
                    z_gyro,
                    x_acc,
                    y_acc,
                    z_acc
                )

            rawFrame = []

            GYRO_RESOLUATION_1 = 32.8

            gyro_reso = GYRO_RESOLUATION_1

            #acc_reso = 415
            DATA_INTERVAL = 0.0625

            #xyz在时间间隔内的角速度
            x_gyro = float(x_gyro)/float(gyro_reso)
            y_gyro = float(y_gyro)/float(gyro_reso)
            z_gyro = -float(z_gyro)/float(gyro_reso)

            #x_or = x_or + (x_gyro-0.01)*DATA_INTERVAL/180*3.14
            x_or = x_or + (x_gyro)*DATA_INTERVAL/180*3.14
            y_or = y_or + y_gyro*DATA_INTERVAL/180*3.14
            z_or = z_or + z_gyro*DATA_INTERVAL/180*3.14

            #将角速度作为控制变量

            u = np.array([[x_gyro],[y_gyro],[z_gyro]]) 

            x = np.dot(A, x) + np.dot(B, u)  # 状态预测
            P_pred = np.dot(np.dot(A, P), A.T) + Q  # 估计误差协方差预测 

            # 更新步骤
            x_acc = float(x_acc)/float(4096)
            y_acc = float(y_acc)/float(4096)
            z_acc = float(z_acc)/float(4096)

            roll = (math.atan2(float(y_acc),float(z_acc)))
            pitch = (-math.atan2(float(x_acc),((float(y_acc)**2 + float(z_acc)**2))**(0.5)))

            z = np.array([[roll+0.06],[pitch+0.01],[z_or]])  # 加速度计数据作为观测向量
            #z = np.array([[roll],[pitch],[0]])  # 加速度计数据作为观测向量

            y = z - np.dot(H, x)  # 观测残差

            S = np.dot(np.dot(H, P_pred), H.T) + R  # 观测残差协方差
            K = np.dot(np.dot(P_pred, H.T), np.linalg.inv(S))  # 卡尔曼增益
            x = x + np.dot(K, y)  # 状态更新
            x_list.append(x[0][0])
            y_list.append(x[1][0])
            z_list.append(x[2][0])

            x_or_list.append(x_or)
            y_or_list.append(y_or)
            z_or_list.append(z_or)
            time = time + 1


            P = np.dot((np.eye(3) - np.dot(K, H)), P_pred)  # 估计误差协方差更新

            #print(np.dot(K, y)[0])

            new_xtheta = x[0][0]
            new_ytheta = x[1][0]
            new_ztheta = x[2][0]
            print('--------------------')
            print('new_xtheta:',new_xtheta)
            print('new_ytheta:',new_ytheta)
            print('new_ztheta:',new_ztheta)




            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            draw_cube_A(vertices_1, new_xtheta, new_ytheta, new_ztheta)

            draw_cube_B(vertices_1, x_or, y_or, z_or)
            pygame.display.flip()
            pygame.time.wait(10)
        if time == times:
            break

    plt.figure(1)
    plt
    plt.plot([i for i in range(times+1)],x_list, '-.', label = 'filter')
    plt.plot([i for i in range(times)],x_or_list, '-*', label = 'original')
    plt.title('KF vs original performance at x')
    plt.legend()
    plt.grid()
    plt.show()
    plt.figure(2)
    plt.plot([i for i in range(times)],y_list, '-.', label = 'filter')
    plt.plot([i for i in range(times)],y_or_list, '-*', label = 'original')
    plt.title('KF vs original performance at y')
    plt.legend()
    plt.grid()
    plt.show()
    plt.figure(3)
    plt.plot([i for i in range(times)],z_list, '-.', label = 'filter')
    plt.plot([i for i in range(times)],z_or_list, '-*', label = 'original')
    plt.title('KF vs original performance at z')
    plt.legend()
    plt.grid()
    plt.show()
    plt.legend()
    plt.grid()
    plt.show()
    # Close the serial port when finished
    ser.close()

if __name__ == '__main__':
    main()