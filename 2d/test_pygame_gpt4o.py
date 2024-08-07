import pygame
import serial
import re
import math

# 初始化 Pygame
pygame.init()

# 设置窗口大小
window_length = 800
window_height = 600
window_size = (window_length, window_height)
screen = pygame.display.set_mode(window_size)
pygame.display.set_caption("2D lighthouse visualizer")

# 设置串口
serial_port = "COM15"  # 根据实际情况修改
baud_rate = 38400

try:
    ser = serial.Serial(serial_port, baud_rate)
except serial.SerialException as e:
    print(f"无法打开串口 {serial_port}: {e}")
    pygame.quit()
    exit(1)

# 1 cm = 37.7952755906 pixels (assuming 96 DPI)
dpi = 96
cm_size = dpi / 2.54
mm_size = cm_size / 10

# 圆形初始位置
circle_pos = [100, 100]
circle_radius = 20

# 创建背景图像
background_size = (3600, 3600)  # 有时候想想，多大才算大呀？
background = pygame.Surface(background_size)

# 绘制白色背景
background.fill((255, 255, 255))

# 网格颜色
cm_grid_color = (139, 0, 0)  # 深红色
mm_grid_color = (211, 211, 211)  # 浅灰色

# 设置字体
font = pygame.font.SysFont(None, 36)
small_font = pygame.font.SysFont(None, 18)

# 绘制1mm网格到背景
for x in range(0, background_size[0], int(mm_size)):
    pygame.draw.line(background, mm_grid_color, (x, 0), (x, background_size[1]))
for y in range(0, background_size[1], int(mm_size)):
    pygame.draw.line(background, mm_grid_color, (0, y), (background_size[0], y))

# 绘制1cm网格到背景
for x in range(0, background_size[0], int(cm_size)):
    pygame.draw.line(background, cm_grid_color, (x, 0), (x, background_size[1]))
for y in range(0, background_size[1], int(cm_size)):
    pygame.draw.line(background, cm_grid_color, (0, y), (background_size[0], y))

# 绘制X和Y坐标轴
axis_color = (0, 0, 0)  # 黑色
axis_num_color = (110, 152, 88)
# # Y轴
# pygame.draw.line(
#     background,
#     axis_color,
#     (background_size[0] // 2, 0),
#     (background_size[0] // 2, background_size[1]),
#     2,
# )
# # X轴
# pygame.draw.line(
#     background,
#     axis_color,
#     (0, background_size[1] // 2),
#     (background_size[0], background_size[1] // 2),
#     2,
# )

# 在坐标轴上标注刻度
for i in range(0, background_size[0], int(cm_size)):
    if i != background_size[0] // 2:
        pygame.draw.line(
            background,
            axis_color,
            (i, background_size[1] // 2 - 5),
            (i, background_size[1] // 2 + 5),
        )
        label = small_font.render(
            str((i - background_size[0] // 2) // int(cm_size)), True, axis_num_color
        )
        background.blit(
            label, (i - label.get_width() // 2, background_size[1] // 2 + 10)
        )

for i in range(0, background_size[1], int(cm_size)):
    if i != background_size[1] // 2:
        pygame.draw.line(
            background,
            axis_color,
            (background_size[0] // 2 - 5, i),
            (background_size[0] // 2 + 5, i),
        )
        label = small_font.render(
            str((background_size[1] // 2 - i) // int(cm_size)), True, axis_num_color
        )
        background.blit(
            label, (background_size[0] // 2 + 10, i - label.get_height() // 2)
        )

# 设置初始缩放比例和偏移量
scale = 1.0
offset = [0, 0]
dragging = False
last_mouse_pos = (0, 0)

# 正则表达式匹配 "A_X: 50, A_Y: 200, B_X: 100, B_Y: 150"
pattern = re.compile(r"A_X:\s*(\d+),\s*A_Y:\s*(\d+),\s*B_X:\s*(\d+),\s*B_Y:\s*(\d+)")

# 计算实际位置需要的参数
lighthouse_height = 550  # 单位mm
lighthouse_freq = 120  # 120Hz for sync light
lighthouse_period = 1 / lighthouse_freq  # 120Hz~=0.00833s
lighthouse_angular_velocity = 2 * math.pi * lighthouse_freq
resolution = 10000000  # @10M,1s= 10,000,000 ticks


# 当前版本的角度计算方法是一种更易理解的形式，即时间/周期*pi。
# 获得角度后，根据简单的三角函数方法就能计算得到相应的X，Y相对坐标。
def get_position(time_x, time_y, height_lh, resolution):

    time_motor_ax = time_x / resolution  # seconds
    time_motor_ay = time_y / resolution
    theta_ax = time_motor_ax / lighthouse_period * math.pi  # now in radians
    theta_ay = time_motor_ay / lighthouse_period * math.pi
    max_side_x = height_lh / math.sin(theta_ax)
    max_side_y = height_lh / math.sin(theta_ay)
    x_p = max_side_x * math.cos(theta_ax)
    y_p = max_side_y * math.cos(theta_ay)
    return x_p, y_p


# 主循环
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # 左键按下，开始拖动
                dragging = True
                last_mouse_pos = event.pos
            elif event.button == 4:  # 滚轮向上，放大
                scale *= 1.1
            elif event.button == 5:  # 滚轮向下，缩小
                scale *= 0.9
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:  # 左键松开，停止拖动
                dragging = False
        elif event.type == pygame.MOUSEMOTION:
            if dragging:
                mouse_pos = event.pos
                dx = mouse_pos[0] - last_mouse_pos[0]
                dy = mouse_pos[1] - last_mouse_pos[1]
                offset[0] += dx
                offset[1] += dy
                last_mouse_pos = mouse_pos

    # 从串口读取数据
    if ser.in_waiting > 0:
        try:
            line = ser.readline().decode("utf-8").strip()
            print(f"Received line: {line}")  # 打印接收到的行
            match = pattern.match(line)
            if match:
                time_motor_ax = int(match.group(1))  # convert ticks(@10M) to seconds(s)
                time_motor_ay = int(match.group(2))  # convert ticks(@10M) to seconds(s)
                circle_pos[0], circle_pos[1] = get_position(
                    time_motor_ax, time_motor_ay, lighthouse_height, resolution
                )
                circle_pos[0] = round(window_length + circle_pos[0], 3)
                circle_pos[1] = round(window_height + circle_pos[1], 3)

                print(
                    f"Updated circle position to: {circle_pos}"
                )  # 打印更新后的圆形位置
            else:
                print("No match found for the line")  # 如果没有匹配成功
        except Exception as e:
            print(f"读取串口数据时出错: {e}")

    # 缩放背景图像
    scaled_background = pygame.transform.smoothscale(
        background, (int(background_size[0] * scale), int(background_size[1] * scale))
    )

    # 计算偏移后的位置
    offset_x = offset[0]
    offset_y = offset[1]

    # 绘制背景图像
    # screen.blit(background, (0, 0))
    screen.fill((255, 255, 255))  # 清屏
    screen.blit(scaled_background, (offset_x, offset_y))

    # 绘制贴靠右边框和下边框的坐标轴刻度
    for i in range(0, window_size[0], int(cm_size)):
        # 计算实际坐标
        real_x = (i - offset_x) / scale / cm_size
        pygame.draw.line(
            screen, axis_color, (i, window_size[1] - 5), (i, window_size[1] + 5)
        )
        label = small_font.render(f"{real_x:.1f}", True, axis_color)
        screen.blit(label, (i - label.get_width() // 2, window_size[1] - 20))

    for i in range(0, window_size[1], int(cm_size)):
        # 计算实际坐标
        real_y = (i - offset_y) / scale / cm_size
        pygame.draw.line(
            screen, axis_color, (window_size[0] - 5, i), (window_size[0] + 5, i)
        )
        label = small_font.render(f"{real_y:.1f}", True, axis_color)
        screen.blit(label, (window_size[0] - 50, i - label.get_height() // 2))

    # 计算圆形在缩放和偏移后的位置
    scaled_circle_pos = [
        offset_x + circle_pos[0] * scale * mm_size,
        offset_y + circle_pos[1] * scale * mm_size,
    ]

    # 绘制黑色圆形
    # pygame.draw.circle(screen, (0, 0, 0), circle_pos, circle_radius)
    pygame.draw.circle(
        screen,
        (0, 0, 0),
        (int(scaled_circle_pos[0]), int(scaled_circle_pos[1])),
        int(circle_radius * scale),
    )

    # 创建文本表面
    coord_text = font.render(
        f"X: {circle_pos[0]}, Y: {circle_pos[1]} (mm)", True, (0, 0, 0)
    )

    # 获取文本表面的矩形
    text_rect = coord_text.get_rect()

    # 将矩形位置设置为窗口左上角
    text_rect.topleft = (10, 10)

    # 绘制文本
    screen.blit(coord_text, text_rect)

    # 更新显示
    pygame.display.flip()

    # 控制帧率
    pygame.time.Clock().tick(60)

# 关闭串口和 Pygame
ser.close()
pygame.quit()
