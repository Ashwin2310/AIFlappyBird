import pygame
import neat
import time
import os
import random
import visualize
import pickle
pygame.font.init()

WIN_WIDTH = 500 #constants (hence capital)
WIN_HEIGHT = 800

GEN = 0

BIRD_IMGS = [pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird1.png"))), pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird2.png"))),pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird3.png")))]
PIPE_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "pipe.png")))
BASE_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "base.png")))
BG_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bg.png")))

STAT_FONT = pygame.font.SysFont("comicsans", 50)

class Bird ():
    IMGS = BIRD_IMGS #Referenced using self.IMGS
    MAX_ROTATION = 25 #bird tilt going up or down
    ROT_VEL = 20 #How much rotation per frame
    ANIMATION_TIME = 5 # How long each birds animation

    def __init__(self,x,y):
        self.x = x #starting positions
        self.y = y
        self.tilt = 0 #flat till movement starts
        self.tick_count = 0 #jumping and falling
        self.vel = 0 #not moving in the beginning
        self.height = self.y
        self.img_count = 0 #for bird animation
        self.img = self.IMGS[0] #IMGS[0] is bird1.png. This will change based on animation frame

    def jump (self): #movement of the bird
        #MOVING RIGHT AND DOWN IS POSITIVE ON X and Y AXIS. LEFT AND UP IS NEGATIVE ON THE CO-ORDINATE SYSTEM
        self.vel = -10.5 #co-ordinate system starts at 0,0 which is the top left of pygame window.
        self.tick_count = 0 #keeps track of last jump
        self.height = self.y

    def move(self):
        self.tick_count += 1 #change in frame from last jump
        d = self.vel * self.tick_count + 1.5 * self.tick_count**2 #Creates the projectile

        if d >= 16:#terminal velocity
            d = 16
        if d < 0: #Moving upwards, then jump more
            d -= 2

        self.y = self.y + d #shows movement slowly up or down

        if d < 0 or self.y + self.height + 50: #If the bird is on an upward projectile, continue to show bird going up
            if self.tilt < self.MAX_ROTATION:
                self.tilt = self.MAX_ROTATION

        else:#tilting bird downwards
            if self.tilt > -90:
                self.tilt -= self.ROT_VEL #shows a nosedive


    def draw(self,win): #win shows window
        self.img_count += 1

        if self.img_count < self.ANIMATION_TIME: #ANIMATION_TIME STARTS AT <5
            self.img = self.IMGS[0]
        elif self.img_count < self.ANIMATION_TIME*2:#<10
            self.img = self.IMGS[1]
        elif self.img_count < self.ANIMATION_TIME * 3:#<15
            self.img = self.IMGS[2]
        elif self.img_count < self.ANIMATION_TIME*4:#<20 goes back to reseting to starting position
            self.img = self.IMGS[1]
        elif self.img_count < self.ANIMATION_TIME*4 + 1:
            self.img = self.IMGS[0]
            self.img_count = 0

        if self.tilt <= -80:
            self.img = self.IMGS[1]
            self.img_count = self.ANIMATION_TIME*2

        #How to rotate an image around the center

        rotated_image = pygame.transform.rotate(self.img, self.tilt)#rotates around the left hand corner
        new_rect = rotated_image.get_rect(center=self.img.get_rect(topleft = (self.x,self.y)).center)
        win.blit(rotated_image,new_rect.topleft)#blits(draws) the rotated image

    def get_mask (self): #collision detection
        return pygame.mask.from_surface(self.img)

class Pipe:
#NOTE THE BIRD DOESN'T MOVE. ALL THE OTHER OBJECTS MOVE TOWARDS THE BIRD
    GAP = 200 #spaces between pipes
    VEL = 5

    def __init__(self,x): #Only using x because tube height is randomized
        self.x = x
        self.height = 0

        self.top = 0
        self.bottom = 0
        self.PIPE_TOP = pygame.transform.flip (PIPE_IMG, False, True) #This flips the bottom pipe picture which is already available in imgs
        self.PIPE_BOTTOM = PIPE_IMG

        self.passed = False
        self.set_height()

    #This method creates the top and bottom pipe randomly
    def set_height (self):
        self.height = random.randrange(40,450)
        self.top = self.height - self.PIPE_TOP.get_height()
        self.bottom = self.height + self.GAP

    def move(self):
        self.x -= self.VEL

    def draw(self,win):
        win.blit (self.PIPE_TOP, (self.x,self.top))
        win.blit (self.PIPE_BOTTOM, (self.x,self.bottom))

    #collision detection - box drawn around pipe and bird. Checks if the rectangles collide with each other. Masking shows where the exact pixels are within a rectangle
    def collide(self,bird):
        bird_mask = bird.get_mask()
        top_mask = pygame.mask.from_surface(self.PIPE_TOP)
        bottom_mask = pygame.mask.from_surface(self.PIPE_BOTTOM)

    #offset shows how far the pixels are from each other
        top_offset = (self.x - bird.x, self.top - round(bird.y))
        bottom_offset = (self.x - bird.x, self.bottom - round(bird.y))

        b_point = bird_mask.overlap(bottom_mask,bottom_offset) #returns NONE if there is no collision (b_point = bottom point)
        t_point = bird_mask.overlap (top_mask, top_offset)

        if t_point or b_point: #if they are not NONE
            return True #collision is true, here we can make the bird die, pause game...
        return False

class Base():#the base image in the folder is small, the image needs to move forward and then repeat itself
    VEL = 5#same as pipe, so they move in unison
    WIDTH = BASE_IMG.get_width()
    IMG = BASE_IMG

    def __init__(self,y):
        self.y = y
        self.x1 = 0
        self.x2 = self.WIDTH

    def move (self):
        self.x1 -= self.VEL
        self.x2 -= self.VEL

#The two same images move together, when the first one moves so far to the left that it is invisible, it is recycled by moving to the right of the second block
        if self.x1 + self.WIDTH < 0:
            self.x1 = self.x2 + self.WIDTH

        if self.x2 + self.WIDTH < 0:
            self.x2 = self.x1 + self.WIDTH

    def draw(self,win):
        win.blit(self.IMG,(self.x1, self.y))
        win.blit(self.IMG,(self.x2, self.y))


#NOTE: SHIFT + TAB ALLOWS MOVEMENT OF A BLOCK OF CODE FROM RIGHT TO LEFT TAB SPACES
def draw_window(win,birds,pipes,base,score,gen): #Draw background image and then the bird on top of it
    win.blit (BG_IMG,(0,0))
    for pipe in pipes:
        pipe.draw(win)

    text = STAT_FONT.render("Score: "+ str(score),1,(255,255,255))
    win.blit(text, (WIN_WIDTH - 10 - text.get_width(), 10)) #score will always be displayed how ever big

    text = STAT_FONT.render("Gen: " + str(gen), 1, (255, 255, 255))
    win.blit(text, (10,10))

    base.draw(win)
    for bird in birds:
        bird.draw(win)
        pygame.display.update()


def main(genomes,config): #This is our fitness function
    global GEN
    GEN += 1
    birds = []  # starting position
    nets = [] #Neural networks, the genomes need to be tracked
    ge = []
    #Three empty lists so each position can correspond to one bird

    for _,g in genomes: #Genomes is a tuple that contains a id and genome object
        net = neat.nn.FeedForwardNetwork.create(g,config) #Neural network created given the config file and the genomes
        nets.append(net)
        birds.append(Bird(230,350))
        g.fitness = 0
        ge.append(g) #append genome to the list

    base = Base(730) #height is 800
    pipes = [Pipe(600)]
    win = pygame.display.set_mode((WIN_WIDTH,WIN_HEIGHT))
    clock = pygame.time.Clock()
    score = 0
    run = True  # used to end game/start
    while run:
        clock.tick(30)# 30 FPS
        for event in pygame.event.get():  # tracks events. Ex: user clicks the screen
            if event.type == pygame.QUIT:  # quit the game (the red X on top of the window)
                run = False
                pygame.quit()
                quit()  # quits the program

        #When the neural network checks the genomes, we got to account for their present pipes. There will be atmost 2 pipes on the screen
        pipe_ind = 0
        if len(birds) > 0: #if there are 2 pipes
            if len(pipes) > 1 and birds[0].x > pipes[0].x + pipes[0].PIPE_TOP.get_width(): #If pipe 1 is crossed
                pipe_ind = 1 # check the second pipe
        else:#If no birds left, quit game
            run = False
            break

        for x, bird in enumerate (birds):
            bird.move()
            ge[x].fitness += 0.1 #This for loop runs 30 times a second so it gains 1 fitness point everytime it stays alive
            output = nets[x].activate((bird.y,abs(bird.y - pipes[pipe_ind].height), abs(bird.y-pipes[pipe_ind].bottom)))

            if output[0] > 0.5: #Output neurons in a list
                bird.jump()

        rem = [] #empty list which removes pipes
        add_pipe = False
        for pipe in pipes:
            for x, bird in enumerate(birds): #So that the position the list can be described
                if pipe.collide(bird): #when the bird collides with the pipe, actions to be done..
                    ge[x].fitness -= 1 #When bird hits the pipe, its fitness score is decreased
                    birds.pop(x) #get rid of bird object, the genome and the NN
                    nets.pop(x)
                    ge.pop(x)

                if not pipe.passed and pipe.x < bird.x: #checks if the bird has crossed the pipe, needs to generate a new pipe
                    pipe.passed = True
                    add_pipe = True

            if pipe.x + pipe.PIPE_TOP.get_width() < 0:  # Checks if the pipe is completely off the screen
                # pipe needs to be removed
                rem.append(pipe)  # cannot directly be removed as this is done in a for loop, hence rem empty list

            pipe.move()

        if add_pipe:
            score += 1 #gets a point when bird crosses a pipe
            for g in ge:
                g.fitness += 5 #Gains 5 points if it crosses the pipe
            pipes.append(Pipe(600))

        for r in rem:
            pipes.remove(r)

        for x, bird in enumerate(birds):
            if bird.y + bird.img.get_height() >= 730 or bird.y < 0:
                birds.pop(x)
                nets.pop(x)
                ge.pop (x)

        base.move()
        draw_window(win,birds,pipes,base,score,GEN)

def run(config_path):
    #doesn't need the starting part of NEAT-config because that is essential
    config = neat.config.Config (neat.DefaultGenome, neat.DefaultReproduction, neat.DefaultSpeciesSet, neat.DefaultStagnation, config_path)

#population
    p = neat.Population(config)
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)

    winner = p.run(main,50) #will be running 50 fitness functions

if __name__ == "__main__":
    local_dir = os.path.dirname(__file__) #NEAT uses this to get path to configuration file
    config_path = os.path.join (local_dir, "NEAT-config.txt") #Finding the path to the file
    run(config_path)


