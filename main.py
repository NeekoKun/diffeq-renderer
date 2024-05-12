import os
import pygame
import random
import json
from attractor import Attractor

class Simulation:
    def __init__(self) -> None:
        # Load settings
        with open("settings.json") as f:
            settings = json.load(f)
            self.SIZE = settings["SIZE"]
            self.WIDTH, self.HEIGHT = self.SIZE
            self.PADDING = settings["PADDING"]
            self.MARGIN = settings["MARGIN"]
            self.BG_COLOR = settings["BACKGROUND_COLOR"]
            self.DENSITY = settings["DENSITY"]
            self.FG_COLOR = settings["POINTS_COLOR"]
            self.FPS = settings["FPS"]
            self.ATTRACTORS = settings["ATTRACTOR_COUNT"]
            self.FADE = settings["FADE"]
            self.K = settings["K"]
            self.POINT_HISTORY = settings["POINT_HISTORY"]
            self.REMOVAL_RADIUS = settings["REMOVAL_RADIUS"]
            self.POINT_RADIUS = settings["POINT_RADIUS"]
            self.RESPAWN = settings["RESPAWN_POINTS"]
            self.LIMIT_DISTANCE = settings["LIMIT_DISTANCE"]
            self.FULLSCREEN = settings["FULLSCREEN"]

        # Initialize Pygame
        pygame.init()
        self.clock = pygame.time.Clock()
        if self.FULLSCREEN:
            self.screen = pygame.display.set_mode(self.SIZE, pygame.FULLSCREEN)
        else:
            self.screen = pygame.display.set_mode(self.SIZE)
        pygame.display.set_caption("Dynamic Attractor Simulation")
        pygame.mouse.set_visible(True)

        # Simulation settings
        self.attractors = [Attractor(random.uniform(10, 30), random.uniform(-self.WIDTH/2, self.WIDTH/2), random.uniform(-self.HEIGHT/2, self.HEIGHT/2), random.choice([-1, 1])) for _ in range(self.ATTRACTORS)]
        self.points = {i: [random.randint((-self.WIDTH - self.PADDING[0])//2, (self.WIDTH + self.PADDING[0])//2), random.randint((-self.HEIGHT - self.PADDING[1])//2, (self.HEIGHT + self.PADDING[1])//2)] for i in range(int((self.WIDTH + self.PADDING[0]) * (self.HEIGHT + self.PADDING[1]) / (self.DENSITY**2)))}
        self.point_histories = {key: [value] for key, value in self.points.items()}
        self.dimming_overlay = pygame.Surface(self.SIZE, pygame.SRCALPHA)
        self.dimming_overlay.fill((self.BG_COLOR[0], self.BG_COLOR[1], self.BG_COLOR[2], self.FADE))

    def differential(self, x: float, y: float) -> list[float]:
        dx, dy = 0, 0

        for attractor in self.attractors:
            distance_squared = (x - attractor.x)**2 + (y - attractor.y)**2
            if distance_squared == 0:
                return None
            if distance_squared < self.REMOVAL_RADIUS**2:
                if attractor.sign == -1:
                    return attractor.x, attractor.y  # Point is within the removal radius of an attractor, might as well count it in the middle to remove artifacts
                if attractor.sign == 1:
                    continue                         # Dumb physics thing for which a point inside a sphere doesn't feel any force to a particular direction
            m = attractor.sign * attractor.q / (distance_squared + 1)
            dx += m * (x - attractor.x)
            dy += m * (y - attractor.y)

        return x + self.K * dx, y + self.K * dy

    def update_point_histories(self) -> None:
        to_remove = []
        for key, point in list(self.points.items()):
            new_pos = self.differential(*point)
            if (new_pos is None) or (self.LIMIT_DISTANCE and ((abs(new_pos[0]) > self.WIDTH/2 + self.MARGIN[0]) or (abs(new_pos[1]) > self.HEIGHT/2 + self.MARGIN[1]))):
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
            if self.RESPAWN:
                # Respown disappeared points
                self.points[key] = [random.randint((-self.WIDTH - self.PADDING[0])//2, (self.WIDTH + self.PADDING[0])//2), random.randint((-self.HEIGHT - self.PADDING[1])//2, (self.HEIGHT + self.PADDING[1])//2)]
                self.point_histories[key] = [(random.randint((-self.WIDTH - self.PADDING[0])//2, (self.WIDTH + self.PADDING[0])//2), random.randint((-self.HEIGHT - self.PADDING[1])//2, (self.HEIGHT + self.PADDING[1])//2)), (random.randint((-self.WIDTH - self.PADDING[0])//2, (self.WIDTH + self.PADDING[0])//2), random.randint((-self.HEIGHT - self.PADDING[1])//2, (self.HEIGHT + self.PADDING[1])//2))]
                self.point_histories[key].pop(0)
                self.point_histories[key].pop(0)
            else:
                del self.points[key]
                del self.point_histories[key]


    def draw_lines(self) -> None:
        for history in self.point_histories.values():
            for start, end in zip(history, history[1:]):
                pygame.draw.line(self.screen, self.FG_COLOR, (int(start[0] + self.WIDTH//2), int(start[1] + self.HEIGHT//2)), (int(end[0] + self.WIDTH//2), int(end[1] + self.HEIGHT//2)), self.POINT_RADIUS)

    def run(self) -> None:
        self.screen.fill(self.BG_COLOR)

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