import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"

from attractor import Attractor
import threading as thr
import pygame
import random
import tqdm
import json
import cv2

with open("settings.json") as f:
    settings = json.load(f)

    SIZE = settings["SIZE"]
    WIDTH = SIZE[0]
    HEIGHT = SIZE[1]
    BG_COLOR = settings["BACKGROUND_COLOR"]
    DENSITY = settings["DENSITY"]
    FG_COLOR = settings["POINTS_COLOR"]
    FPS = settings["FPS"]
    ATTRACTORS = settings["ATTRACTOR_COUNT"]
    FADE = settings["FADE"]
    K = settings["K"]
    RENDER = settings["RENDER"]
    OUTPUT = settings["OUTPUT"]
    FRAMES = settings["FRAMES"]

##############
## SETTINGS ##
##############

# Pygame settings
clock = pygame.time.Clock()
screen = pygame.display.set_mode(SIZE)
pygame.display.init()
pygame.mouse.set_visible(True)
counter = 0

# Simulation settings
attractors = [Attractor(random.uniform(10, 30), random.uniform(-WIDTH/2, WIDTH/2), random.uniform(-HEIGHT/2, HEIGHT/2), random.choice([-1, 1])) for _ in range(ATTRACTORS)]
points_count = int((WIDTH + 400) * ( HEIGHT + 400 ) / (DENSITY**2))

def differential(x, y) -> list[int]:

    dx = dy = 0

    for i in attractors:
        m = i.sign * i.q / ((i.x - x)*(i.x - x) + (i.y - y)*(i.y - y))
        dx += m * (x - i.x)
        dy += m * (y - i.y)

        if abs(x - i.x) < 3 and abs(y - i.y) < 3:
            return i.x, i.y

    return x + K * dx, y + K * dy

points = [[random.randint(int(-WIDTH/2 - 200), int(WIDTH/2 + 200)), random.randint(int(-HEIGHT/2 - 200), int(HEIGHT/2 + 200))] for _ in range(points_count)]

running = True

screen.fill(BG_COLOR)

def dim():
    for x in range(WIDTH):
        for y in range(HEIGHT):
            col = screen.get_at((x, y))
            ncol = max(col[0] - FADE, BG_COLOR[0]), max(col[1] - FADE, BG_COLOR[1]), max(col[2] - FADE, BG_COLOR[2])
            screen.set_at((x, y), ncol)

def eval_diff():
    for i, p in enumerate(points):
        screen.set_at((round(p[0] + WIDTH/2), round(p[1] + HEIGHT/2)), FG_COLOR)
        try:
            points[i] = differential(p[0], p[1])
        except ZeroDivisionError:
            points.remove(p)


while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.fill(pygame.Color(0, 0, 0, a=10))

    dimth = thr.Thread(target=dim)
    diffth = thr.Thread(target=eval_diff)
    
    if FADE != 0:
        dimth.start()
    diffth.start()

    if FADE != 0:
        dimth.join()
    diffth.join()

    pygame.display.flip()

    # Rendering to video
    if RENDER:
        pygame.image.save(screen, "frames/frame_"+str(counter)+".png")

    if (counter >= FRAMES) and (FRAMES != 0):
        running = False
    counter += 1
    print("Frame:", counter)

pygame.quit()

if RENDER:
    # Collecting the individual frames
    image_files = ["frame_"+str(i)+".png" for i in range(counter)]

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    video_writer = cv2.VideoWriter(OUTPUT, fourcc, FPS, SIZE)

    for image_file in tqdm.tqdm(image_files):
        image_path = os.path.join("frames", image_file)
        image = cv2.imread(image_path)
        video_writer.write(image)

    video_writer.release()
