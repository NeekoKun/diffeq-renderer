import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"

from attractor import Attractor
import logging
import pygame
import random
import time
import tqdm
import json
import cv2

start_time = time.time()

with open("settings.json") as f:
    logging.debug("Loading application settings...")
    settings = json.load(f)

    SIZE = settings["SIZE"]
    WIDTH = SIZE[0]
    HEIGHT = SIZE[1]
    PADDING = settings["PADDING"]
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
    FRAMES_DIR = settings["TEMP_OUTPUT"]
    KEEP_FRAMES = settings["KEEP_FRAMES"]

    for i in settings:
        logging.info(i+":", settings[i])
    
    logging.debug("Settings loaded succesfully")

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
points_count = int((WIDTH + PADDING[0]*2) * ( HEIGHT + PADDING[1]*2 ) / (DENSITY**2))

points = [[random.randint(int(-WIDTH/2 - PADDING[0]), int(WIDTH/2 + PADDING[0])), random.randint(int(-HEIGHT/2 - PADDING[1]), int(HEIGHT/2 + PADDING[1]))] for _ in range(points_count)]

running = True

screen.fill(BG_COLOR)

# Thank you reddit
dimming_overlay: pygame.Surface = pygame.Surface(SIZE, pygame.SRCALPHA).convert_alpha()
dimming_overlay.fill(pygame.Color(BG_COLOR[0], BG_COLOR[1], BG_COLOR[2], FADE))

################
## MATH STUFF ##
################

def differential(x, y) -> list[int]:
    logging.info("Starting differential equation at", x, y)
    dx = dy = 0

    for i in attractors:
        m = i.sign * i.q / ((i.x - x)*(i.x - x) + (i.y - y)*(i.y - y))
        dx += m * (x - i.x)
        dy += m * (y - i.y)

        if abs(x - i.x) < 3 and abs(y - i.y) < 3:
            logging.debug("Point at", x, y, "collided with attractor at", i.x, i.y)
            return i.x, i.y

    logging.info("Equation returned", dx, dy)
    return x + K * dx, y + K * dy

def dim():
    screen.blit(dimming_overlay, (0, 0))

def eval_diff():
    for i, p in enumerate(points):
        screen.set_at((round(p[0] + WIDTH/2), round(p[1] + HEIGHT/2)), FG_COLOR)
        try:
            points[i] = differential(p[0], p[1])
        except ZeroDivisionError:
            logging.debug("Removed point", p[0], p[1], "upon collision")
            points.remove(p)


###############
## MAIN LOOP ##
###############

if not RENDER:
    logging.debug("Application not set to render: frames will not be saved")

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    dim()

    eval_diff()

    clock.tick(FPS)

    pygame.display.flip()

    # Rendering to video
    if RENDER:
        pygame.image.save(screen, f"{FRAMES_DIR}/frame_{counter}.png")

    if (counter >= FRAMES) and (FRAMES != 0):
        logging.debug(f"Target frames rendered at {time.time() - start_time}")
        running = False

    counter += 1
    logging.info("Frame", counter, "rendered")

logging.debug(f"Terminating pygame at {time.time() - start_time}")
pygame.quit()

###############
## RENDERING ##
###############

if RENDER:
    logging.debug("Compressing frames to video...")
    # Collecting the individual frames
    image_files = [f"frame_{i}.png" for i in range(counter)]

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    video_writer = cv2.VideoWriter(OUTPUT, fourcc, FPS, SIZE)

    for image_file in tqdm.tqdm(image_files):
        image_path = os.path.join(FRAMES_DIR, image_file)
        image = cv2.imread(image_path)
        video_writer.write(image)

    video_writer.release()
    logging.debug("Rendering completed succesfully")

    if not KEEP_FRAMES:
        logging.debug("Deleting frame images")
        for i in tqdm.tqdm(image_files):
            os.remove(os.path.join(FRAMES_DIR, i))
        logging.debug("Frames deleted succesfully")

logging.debug("Program quitting")
