import os
import pygame
import random
import json
from attractor import Attractor

class Simulation:
    def __init__(self):
        # Load settings
        with open("settings.json") as f:
            settings = json.load(f)
            self.SIZE = settings["SIZE"]
            self.WIDTH, self.HEIGHT = self.SIZE
            self.BG_COLOR = settings["BACKGROUND_COLOR"]
            self.DENSITY = settings["DENSITY"]
            self.FG_COLOR = settings["POINTS_COLOR"]
            self.FPS = settings["FPS"]
            self.ATTRACTORS = settings["ATTRACTOR_COUNT"]
            self.FADE = settings["FADE"]
            self.K = settings["K"]
            self.POINT_HISTORY = 5

        # Initialize Pygame
        pygame.init()
        self.clock = pygame.time.Clock()
        self.screen = pygame.display.set_mode(self.SIZE)
        pygame.display.set_caption("Dynamic Attractor Simulation")
        pygame.mouse.set_visible(True)

        # Simulation settings
        self.attractors = [Attractor(random.uniform(10, 30), random.uniform(-self.WIDTH/2, self.WIDTH/2), random.uniform(-self.HEIGHT/2, self.HEIGHT/2), random.choice([-1, 1])) for _ in range(self.ATTRACTORS)]
        self.points = {i: [random.randint(-self.WIDTH//2 - 200, self.WIDTH//2 + 200), random.randint(-self.HEIGHT//2 - 200, self.HEIGHT//2 + 200)] for i in range(int((self.WIDTH + 400) * (self.HEIGHT + 400) / (self.DENSITY**2)))}
        self.point_histories = {key: [value] for key, value in self.points.items()}
        self.dimming_overlay = pygame.Surface(self.SIZE, pygame.SRCALPHA)
        self.dimming_overlay.fill((self.BG_COLOR[0], self.BG_COLOR[1], self.BG_COLOR[2], self.FADE))

    def differential(self, x, y):
        dx, dy = 0, 0
        for attractor in self.attractors:

            m = attractor.sign * attractor.q / (((attractor.x - x)**2 + (attractor.y - y)**2) + 1)
            if (x - attractor.x)**2 + (y - attractor.y)**2 < 16:  # Slightly larger radius for smoother visuals
                return None  # None indicates collision
            dx += m * (x - attractor.x)
            dy += m * (y - attractor.y)
        return x + self.K * dx, y + self.K * dy  # Increase the effect of K

    def update_point_histories(self):
        for key, point in list(self.points.items()):
            new_pos = self.differential(*point)
            if new_pos is None:
                # Clear history and reassign to a new random location
                new_point = [random.randint(-self.WIDTH//2 - 200, self.WIDTH//2 + 200), random.randint(-self.HEIGHT//2 - 200, self.HEIGHT//2 + 200)]
                self.points[key] = new_point
                self.point_histories[key] = [new_point]
            else:
                # Always append new position to history for debugging
                self.point_histories[key].append(new_pos)
                self.points[key] = new_pos  # Ensure the main points dictionary is updated

    def draw_lines(self):
        for history in self.point_histories.values():
            for start, end in zip(history, history[1:]):
                pygame.draw.line(self.screen, self.FG_COLOR, (int(start[0] + self.WIDTH//2), int(start[1] + self.HEIGHT//2)), (int(end[0] + self.WIDTH//2), int(end[1] + self.HEIGHT//2)), 2)

    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type is pygame.QUIT:
                    running = False

            self.screen.blit(self.dimming_overlay, (0, 0))
            self.update_point_histories()
            self.draw_lines()
            pygame.display.flip()
            self.clock.tick(self.FPS)

        pygame.quit()

if __name__ == "__main__":
    os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
    sim = Simulation()
    sim.run()