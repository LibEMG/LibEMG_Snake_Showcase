import pygame
import random
import socket
from pygame.locals import *

class SnakeGame:
    def __init__(self):
        random.seed(0)
        self.width = 500
        self.height = 500
        
        # Pygame Setup:
        pygame.init()
        self.window = pygame.display.set_mode([self.width, self.height])
        pygame.display.set_caption('Pygame (Snake) EMG Demo')
        self.clock = pygame.time.Clock()

        # Game Variables:
        self.running = True 
        self.score = 0
        self.movement = 20
        self.snake_head = [40,40]
        self.snake_body = []
        self.target = [None, None]
        self.generate_target()
        self.previous_key_presses = []

        # Colors
        self.snake_green = (5, 255, 0)
        self.head_blue = (0, 133, 255)
        self.red = (255, 0, 0)

        # Socket for reading EMG
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) 
        self.sock.bind(('127.0.0.1', 12346))

    def generate_target(self):
        x = random.randrange(20, self.width-20) 
        y = random.randrange(20, self.height-20) 
        self.target[0] = x - x % self.movement
        self.target[1] = y - y % self.movement
    
    def handle_emg(self):
        data, _ = self.sock.recvfrom(1024)
        data = str(data.decode("utf-8"))
        if data:
            input_class = float(data.split(' ')[0])
            # 0 = Hand Closed = down
            if input_class == 0:
                self.previous_key_presses.append("down")
            # 1 = Hand Open
            elif input_class == 1:
                self.previous_key_presses.append("up")
            # 3 = Extension 
            elif input_class == 3:
                self.previous_key_presses.append("right")
            # 4 = Flexion
            elif input_class == 4:
                self.previous_key_presses.append("left")
            else:
                return
            
            self.move_snake()

    def handle_movement(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False 
                
            # Listen for key presses:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    self.previous_key_presses.append("left")
                elif event.key == pygame.K_RIGHT:
                    self.previous_key_presses.append("right")
                elif event.key == pygame.K_UP:
                    self.previous_key_presses.append("up")
                elif event.key == pygame.K_DOWN:
                    self.previous_key_presses.append("down")
                else:
                    return 

                self.move_snake()
    
    def move_snake(self):    
        # Move head 
        self.move(self.previous_key_presses[-1], self.snake_head)
        # Move the snake body 
        for i in range(0, len(self.snake_body)):
            self.move(self.previous_key_presses[-(2+i)], self.snake_body[i])

    def move(self, direction, block):
        block_temp = block.copy()
        if direction == "left":
            block_temp[0] -= self.movement
        elif direction == "right":
            block_temp[0] += self.movement
        elif direction == "up":
            block_temp[1] -= 20
        elif direction == "down":
            block_temp[1] += 20
        
        # Check boundaries
        if (block_temp[0] > 0 and block_temp[0] < self.width and block_temp[1] > 0 and block_temp[1] < self.height):
            block[0] = block_temp[0]
            block[1] = block_temp[1]

    def grow_snake(self):
        x = self.snake_head[0]
        y = self.snake_head[1]
        idx = -1

        if len(self.snake_body) > 0:
            x = self.snake_body[-1][0]
            y = self.snake_body[-1][1]
            idx = -(1 + len(self.snake_body))

        if self.previous_key_presses[idx] == "left":
            x += self.movement
        elif self.previous_key_presses[idx] == "right":
            x -= self.movement
        elif self.previous_key_presses[idx] == "up":
            y += 20
        elif self.previous_key_presses[idx] == "down":
            y -= 20
        self.snake_body.append([x,y])

    def run_game(self):
        while self.running: 
            # Fill the background with black
            self.window.fill((233, 233, 233))

            # Listen for movement events
            self.handle_movement()
            self.handle_emg()

            # Check for collision between snake and head
            snake = Rect(self.snake_head[0], self.snake_head[1], 20, 20)
            target = Rect(self.target[0], self.target[1], 20, 20)
            if pygame.Rect.colliderect(snake, target):
                self.generate_target()
                self.grow_snake()
                self.score += 1

            # Draw Snake
            pygame.draw.rect(self.window, self.head_blue, snake, border_radius=2)
            for b in self.snake_body:
                pygame.draw.rect(self.window, self.snake_green, [b[0], b[1], 20, 20],  border_radius=2)

            # Draw Target 
            pygame.draw.rect(self.window, self.red, target)

            # Score label
            myfont = pygame.font.SysFont("arial bold", 30)
            label = myfont.render("Score: " + str(self.score), 1, (0,0,0))
            self.window.blit(label, (self.width - 100, 10))

            pygame.display.update()
            self.clock.tick(30)

        pygame.quit()