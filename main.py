from attractor import Attractor
import colorsys
import pygame
import random
import math
import json
import os

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
            self.FG_COLOR = settings["POINTS_COLOR"]
            self.TRACE_COLOR = settings["TRACE_COLOR"]
            self.EXPIRED_TRACE_COLOR = settings["EXPIRED_TRACE_COLOR"]
            self.JULY_MODE = settings["JULY_MODE"]
            self.DENSITY = settings["DENSITY"]
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
            self.TRACE_RADIUS = settings["TRACE_RADIUS"]
            self.SHOW_FPS = settings["SHOW_FPS"]
            self.SYSTEM_FONT_SIZE = settings["SYSTEM_FONT_SIZE"]

        # Initialize Pygame
        pygame.init()
        self.clock = pygame.time.Clock()
        if self.FULLSCREEN:
            self.screen = pygame.display.set_mode(self.SIZE , pygame.FULLSCREEN)
        else:
            self.screen = pygame.display.set_mode(self.SIZE)
        pygame.display.set_caption("Dynamic Attractor Simulation")
        pygame.mouse.set_visible(True)

        # Simulation settings
        self.attractors = [Attractor(random.uniform(10, 30), random.uniform(-self.WIDTH/2, self.WIDTH/2), random.uniform(-self.HEIGHT/2, self.HEIGHT/2), random.choice([-1, 1])) for _ in range(self.ATTRACTORS)]
        self.attractors = []
        self.attractors.append(Attractor(20, -100, 100, -1))
        self.attractors.append(Attractor(20, -100, -100, -1))
        self.attractors.append(Attractor(20, -100, 0, 1))
        self.attractors.append(Attractor(20, 100, 0, -1))
        self.attractors.append(Attractor(20, 100, 100, 1))
        self.attractors.append(Attractor(20, 100, -100, 1))
        self.points = {i: [random.randint(-(self.WIDTH + self.PADDING[0])//2, (self.WIDTH + self.PADDING[0])//2), random.randint(-(self.HEIGHT + self.PADDING[1])//2, (self.HEIGHT + self.PADDING[1])//2)] for i in range(int((self.WIDTH + self.PADDING[0]) * (self.HEIGHT + self.PADDING[1]) / (self.DENSITY**2)))}
        self.point_histories = {key: [value] for key, value in self.points.items()}
        self.dimming_overlay = pygame.Surface(self.SIZE, pygame.SRCALPHA)
        self.dimming_overlay.fill((self.BG_COLOR[0], self.BG_COLOR[1], self.BG_COLOR[2], self.FADE))
        self.traced_points = []
        self.potential_points = []
        self.deleted_traced_points = []
        self.deleted_potential_points = []

        self.current_fps = 0
        self.will_remove = []
        self.will_stop_tracing = []
        self.will_stop_tracing_potential = []

        # Font
        self.font = pygame.font.SysFont(u"Noto Sans Mono", self.SYSTEM_FONT_SIZE)
        self.fps_rect = pygame.Rect(0, 0, 50, 50)

    def differential(self, x: float, y: float) -> list[float]:
        dx, dy = 0, 0

        for attractor in self.attractors:
            distance_squared = (x - attractor.x)**2 + (y - attractor.y)**2
            if distance_squared == 0:
                return None, None
            if distance_squared < self.REMOVAL_RADIUS**2:
                if attractor.sign == -1:
                    return 'collided', (attractor.x - x, attractor.y - y)  # Point is within the removal radius of an attractor, might as well count it in the middle to remove artifacts
            m = attractor.sign * attractor.q / (distance_squared + 1)
            dx += m * (x - attractor.x)
            dy += m * (y - attractor.y)

        return 'ok', (self.K * dx, self.K * dy)

    def update_point_histories(self) -> None:
        self.to_remove = self.will_remove
        self.to_stop_tracing = self.will_stop_tracing
        self.to_stop_tracing_potential = self.will_stop_tracing_potential
        self.will_remove = []
        self.will_stop_tracing = []
        self.will_stop_tracing_potential = []
        

        # Remove old traces
        for point in self.to_stop_tracing:
            self.deleted_traced_points.append(point)
            self.traced_points.remove(point)

        for point in self.to_stop_tracing_potential:
            self.deleted_potential_points.append(point)
            self.potential_points.remove(point)

        # Remove the marked points
        for key in self.to_remove:
            if self.RESPAWN:
                # Respown disappeared points
                self.points[key] = [random.randint((-self.WIDTH - self.PADDING[0])//2, (self.WIDTH + self.PADDING[0])//2), random.randint((-self.HEIGHT - self.PADDING[1])//2, (self.HEIGHT + self.PADDING[1])//2)]
                self.point_histories[key] = [(random.randint((-self.WIDTH - self.PADDING[0])//2, (self.WIDTH + self.PADDING[0])//2), random.randint((-self.HEIGHT - self.PADDING[1])//2, (self.HEIGHT + self.PADDING[1])//2)), (random.randint((-self.WIDTH - self.PADDING[0])//2, (self.WIDTH + self.PADDING[0])//2), random.randint((-self.HEIGHT - self.PADDING[1])//2, (self.HEIGHT + self.PADDING[1])//2))]
                self.point_histories[key].pop(0)
                self.point_histories[key].pop(0)
            else:
                del self.points[key]
                del self.point_histories[key]

        for key, point in list(self.points.items()):
            result, d = self.differential(*point)
            if d is None:
                self.will_remove.append(key)
                continue
            new_pos = point[0] + d[0], point[1] + d[1]
            if (self.LIMIT_DISTANCE and ((abs(new_pos[0]) > self.WIDTH/2 + self.MARGIN[0]) or (abs(new_pos[1]) > self.HEIGHT/2 + self.MARGIN[1]))):
                # Mark the point for removal
                self.will_remove.append(key)
            else:
                if result == 'collided':
                    self.will_remove.append(key)
                # Append new position to history, ensuring history does not exceed specified length
                if len(self.point_histories[key]) >= self.POINT_HISTORY:
                    self.point_histories[key].pop(0)  # Remove the oldest position
                self.point_histories[key].append(new_pos)
                self.points[key] = new_pos  # Update the main points dictionary
        
        # Potential lines
        for point in self.potential_points:
            result, d = self.differential(*point[-1])
            dx = d[1]
            dy = -d[0]
            new_pos = point[-1][0] + dx, point[-1][1] + dy
            if (new_pos is None) or (self.LIMIT_DISTANCE and ((abs(new_pos[0]) > self.WIDTH/2 + self.MARGIN[0]) or (abs(new_pos[1]) > self.HEIGHT/2 + self.MARGIN[1]))):
                self.to_stop_tracing.append(point)
            else:
                self.potential_points[self.potential_points.index(point)].append(new_pos)
                if result == 'collided':
                    self.will_stop_tracing_potential.append(point)
                    self.will_stop_tracing_potential[-1].append(new_pos) 

        # Traced point
        for point in self.traced_points:
            result, (dx, dy) = self.differential(*point[-1])
            new_pos = point[-1][0] + dx, point[-1][1] + dy
            if (new_pos is None) or (self.LIMIT_DISTANCE and ((abs(new_pos[0]) > self.WIDTH/2 + self.MARGIN[0]) or (abs(new_pos[1]) > self.HEIGHT/2 + self.MARGIN[1]))):
                self.to_stop_tracing.append(point)
            else:
                self.traced_points[self.traced_points.index(point)].append(new_pos)
                if result == 'collided':
                    self.will_stop_tracing.append(point)
                    self.will_stop_tracing[-1].append(new_pos)
                    
    def get_angle(self, start: list[float], end: list[float]) -> float:
        distance = math.sqrt((start[0] - end[0])**2 + (start[1] - end[1])**2)
        if distance == 0:
            return 0

        if end[0] > start[0]:
            a = 1 + (end[1] - start[1]) / distance
        else:
            a = 3 - (end[1] - start[1]) / distance

        return a/4

    def float_to_rgb_hue(self, value: float) -> list[int]:
        HUE = [value, 0.5, 1]
        return [255*i for i in colorsys.hls_to_rgb(*HUE)]

    def draw_lines(self) -> None:
        for history in self.point_histories.values():
            for start, end in zip(history, history[1:]):
                if self.JULY_MODE:
                    pygame.draw.line(self.screen, self.float_to_rgb_hue(self.get_angle(start, end)), (int(start[0] + self.WIDTH//2), int(start[1] + self.HEIGHT//2)), (int(end[0] + self.WIDTH//2), int(end[1] + self.HEIGHT//2)), self.POINT_RADIUS)
                else:
                    pygame.draw.line(self.screen, self.FG_COLOR, (int(start[0] + self.WIDTH//2), int(start[1] + self.HEIGHT//2)), (int(end[0] + self.WIDTH//2), int(end[1] + self.HEIGHT//2)), self.POINT_RADIUS)
        for point in self.traced_points:
            for i, _ in enumerate(point[1:]):
                pygame.draw.line(self.screen, self.TRACE_COLOR, (int(point[i][0] + self.WIDTH//2), int(point[i][1] + self.HEIGHT//2)), (int(point[i+1][0] + self.WIDTH//2), int(point[i+1][1] + self.HEIGHT//2)), self.TRACE_RADIUS) # TODO: add simulation settings

        for point in self.potential_points:
            for i, _ in enumerate(point[1:]):
                pygame.draw.line(self.screen, self.TRACE_COLOR, (int(point[i][0] + self.WIDTH//2), int(point[i][1] + self.HEIGHT//2)), (int(point[i+1][0] + self.WIDTH//2), int(point[i+1][1] + self.HEIGHT//2)), self.TRACE_RADIUS) # TODO: add simulation settings


        for point in self.deleted_traced_points:
            for i, _ in enumerate(point[1:]):
                pygame.draw.line(self.screen, self.EXPIRED_TRACE_COLOR, (int(point[i][0] + self.WIDTH//2), int(point[i][1] + self.HEIGHT//2)), (int(point[i+1][0] + self.WIDTH//2), int(point[i+1][1] + self.HEIGHT//2)), self.TRACE_RADIUS) # TODO: add simulation settings

    def run(self) -> None:
        self.screen.fill(self.BG_COLOR)

        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    coors = pygame.mouse.get_pos()
                    if event.button == 1: # left click
                        self.traced_points.append([(coors[0]-self.WIDTH//2, coors[1]-self.HEIGHT//2)])
                    elif event.button == 3: # right click
                        self.potential_points.append([(coors[0]-self.WIDTH//2, coors[1]-self.HEIGHT//2)])


            self.screen.blit(self.dimming_overlay, (0, 0))
            self.update_point_histories()
            self.draw_lines()

            if self.SHOW_FPS:
                text = self.font.render(str(round(self.current_fps)).encode("utf-8"), True, [0, 255, 0])
                self.fps_rect = text.get_rect()
                temp_surface = pygame.Surface((self.fps_rect.width, self.fps_rect.height))
                temp_surface.fill((0, 0, 0))
                temp_surface.blit(text, (0, 0))
                self.screen.blit(temp_surface, (self.WIDTH-self.fps_rect.width, 0))

            pygame.display.flip()
            
            self.clock.tick(self.FPS)
            self.current_fps = self.clock.get_fps()

        pygame.quit()

if __name__ == "__main__":
    os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
    sim = Simulation()
    sim.run()