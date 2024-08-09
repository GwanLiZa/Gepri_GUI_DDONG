import subprocess
import pygame
import random
import numpy as np
import sys

colors = [
    (0, 0, 0),
    (120, 37, 179),
    (100, 179, 179),
    (80, 34, 22),
    (80, 134, 22),
    (180, 34, 22),
    (180, 34, 122),
]

class Figure:
    x = 0
    y = 0

    figures = [
        [[1, 5, 9, 13], [4, 5, 6, 7]],
        [[4, 5, 9, 10], [2, 6, 5, 9]],
        [[6, 7, 9, 10], [1, 5, 6, 10]],
        [[1, 2, 5, 9], [0, 4, 5, 6], [1, 5, 9, 8], [4, 5, 6, 10]],
        [[1, 2, 6, 10], [5, 6, 7, 9], [2, 6, 10, 11], [3, 5, 6, 7]],
        [[1, 4, 5, 6], [1, 4, 5, 9], [4, 5, 6, 9], [1, 5, 6, 9]],
        [[1, 2, 5, 6]],
    ]

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.type = random.randint(0, len(self.figures) - 1)
        self.color = random.randint(1, len(colors) - 1)
        self.rotation = 0

    def image(self):
        return self.figures[self.type][self.rotation]

    def rotate(self):
        self.rotation = (self.rotation + 1) % len(self.figures[self.type])

class Start:
    def __init__(self):
        pygame.init()
        self.width, self.height = 300, 600
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption('Gepri GUI (Start Program)')
        self.clock = pygame.time.Clock()
        self.zoom = 30
        self.game_over = False
        self.grid = np.zeros((20, 10), dtype=int) 
        self.figure = None
        self.score = 0
        self.lines_cleared = 0
        self.state = "start"
        self.level = 2
        self.x = 0
        self.y = 0
        self.line = 0
        self.new_figure()

    def new_figure(self):
        self.figure = Figure(3, 0)

    def intersects(self):
        for i in range(4):
            for j in range(4):
                if i * 4 + j in self.figure.image():
                    if (i + self.figure.y > len(self.grid) - 1 or
                            j + self.figure.x > len(self.grid[0]) - 1 or
                            j + self.figure.x < 0 or
                            self.grid[i + self.figure.y][j + self.figure.x] > 0):
                        return True
        return False

    def break_lines(self):
        for i in range(len(self.grid)):
            if all(self.grid[i, j] > 0 for j in range(len(self.grid[i]))):
                self.line += 1
                self.grid[1:i+1] = self.grid[0:i]
                self.grid[0] = np.zeros(len(self.grid[0]), dtype=int)

        self.score += self.line ** 2

    def go_down(self):
        self.figure.y += 1
        if self.intersects():
            self.figure.y -= 1
            self.freeze()

    def freeze(self):
        for i in range(4):
            for j in range(4):
                if i * 4 + j in self.figure.image():
                    self.grid[i + self.figure.y, j + self.figure.x] = self.figure.color
        self.break_lines()
        self.new_figure()
        if self.intersects():
            self.state = "gameover"
            self.game_over = True

    def go_side(self, dx):
        old_x = self.figure.x
        self.figure.x += dx
        if self.intersects():
            self.figure.x = old_x

    def rotate(self):
        old_rotation = self.figure.rotation
        self.figure.rotate()
        if self.intersects():
            self.figure.rotation = old_rotation

    def run(self):
        pressing_down = False
        counter = 0

        while not self.game_over:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP:
                        self.rotate()
                    if event.key == pygame.K_DOWN:
                        pressing_down = True
                    if event.key == pygame.K_LEFT:
                        self.go_side(-1)
                    if event.key == pygame.K_RIGHT:
                        self.go_side(1)
                    if event.key == pygame.K_SPACE:
                        self.go_down()
                    if event.key == pygame.K_ESCAPE:
                        self.__init__()

                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_DOWN:
                        pressing_down = False

            if self.figure is None:
                self.new_figure()

            counter += 1
            if counter > 100000:
                counter = 0

            if counter % (30 // self.level // 2) == 0 or pressing_down:
                if self.state == "start":
                    self.go_down()

            self.screen.fill((0, 0, 0)) 

            for i in range(len(self.grid)):
                for j in range(len(self.grid[i])):
                    pygame.draw.rect(self.screen, (128, 128, 128),
                                     [self.x + self.zoom * j, self.y + self.zoom * i, self.zoom, self.zoom], 1)
                    if self.grid[i][j] > 0:
                        pygame.draw.rect(self.screen, colors[self.grid[i][j]],
                                         [self.x + self.zoom * j + 1, self.y + self.zoom * i + 1, self.zoom - 2, self.zoom - 2])

            if self.figure is not None:
                for i in range(4):
                    for j in range(4):
                        p = i * 4 + j
                        if p in self.figure.image():
                            pygame.draw.rect(self.screen, colors[self.figure.color],
                                             [self.x + self.zoom * (j + self.figure.x) + 1,
                                              self.y + self.zoom * (i + self.figure.y) + 1,
                                              self.zoom - 2, self.zoom - 2])

            font = pygame.font.SysFont('Calibri', 25, True, False)
            font1 = pygame.font.SysFont('Calibri', 65, True, False)
            text = font.render(f"Score: {self.score}", True, (255, 255, 255))

            self.screen.blit(text, [20, 20])

            pygame.display.flip()
            self.clock.tick(30)

        pygame.quit()
        if self.line >= 10:   
            return
        else:
            sys.exit()

def main():
    start = Start()
    start.run()

if __name__ == '__main__':
    main()
    subprocess.run(["python", "src/main.py"])
