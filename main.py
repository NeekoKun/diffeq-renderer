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
            self.POINT_HISTORY = 2
            self.REMOVAL_RADIUS = 16

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
            distance_squared = (x - attractor.x)**2 + (y - attractor.y)**2
            if distance_squared < self.REMOVAL_RADIUS**2:
                return None  # Point is within the removal radius of an attractor
            m = attractor.sign * attractor.q / (distance_squared + 1)
            dx += m * (x - attractor.x)
            dy += m * (y - attractor.y)
        return x + self.K * dx, y + self.K * dy

    def update_point_histories(self):
        to_remove = []
        for key, point in list(self.points.items()):
            new_pos = self.differential(*point)
            if new_pos is None:
                # Mark the point for removal
                to_remove.append(key)
            else:
                # Append new position to history, ensuring history does not exceed specified length
                if len(self.point_histories[key]) >= self.POINT_HISTORY:
                    self.point_histories[key].pop(0)  # Remove the oldest position
                self.point_histories[key].append(new_pos)
                self.points[key] = new_pos  # Update the main points dictionary

        # Remove the marked points
        for key in to_remove:
            del self.points[key]
            del self.point_histories[key]

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