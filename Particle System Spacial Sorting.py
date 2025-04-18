import pygame
import random
import math
pygame.init()

#Create window
maxx = 1580
maxy = 810
screen = pygame.display.set_mode((maxx, maxy))
pygame.display.set_caption('Pygame Base Template Minimum') #Change window title
oldScreen = pygame.Surface((maxx,maxy))
oldScreen.fill((255,255,255))
simTime = 0

#Global variables
font = pygame.font.SysFont(None, 24)
gravity = pygame.Vector2(0,1.98)
trails = False
arrangement = "spiral" # or "pool", "grid", "spiral". "cluster" is default
numLoops = 0

def generateFacedCircle(color, radius):
    circleOut = pygame.Surface((radius*2-1,radius*2-1))
    circleOut = circleOut.convert_alpha()
    for x in range(round(radius*2-1)):
        for y in range(round(radius*2-1)):
            fade = (1.0 - (math.dist((x,y),(radius, radius)) / radius))
            fade = min(1.0,max(0.0,fade))
            fade = fade**2*255
            circleOut.set_at((x,y), (color[0],color[1],color[2],fade))
    return circleOut

def clamp(val, low, high):
    if val < low:
        return low
    elif val > high:
        return high
    return val

def rotateVec(vector, degrees):
    radians = math.radians(degrees)
    x, y = vector
    vector.x = x * math.cos(radians) - y * math.sin(radians)
    vector.y = x * math.sin(radians) + y * math.cos(radians)
    
def lengthSquared(vec2):
    return vec2.x * vec2.x + vec2.y * vec2.y
    
class particle:
    drag = 0.000001
    useBoarders = True
    boarders = (0,0,maxx, maxy)
    
    def __init__(self, color, x, y, size):
        self.color = color
        self.pos = pygame.Vector2(x,y)
        self.oldPos = pygame.Vector2(x,y)
        self.vel = pygame.Vector2(0,0)
        self.accAccum = pygame.Vector2(0,0)
        self.acc = pygame.Vector2(0,0)
        self.size = size
        self.mass = 1

    def isTouching(self,other):
        towardVec = (other.pos - self.pos)
        return lengthSquared(towardVec) <= (self.size/2+other.size/2)**2

    def getDrag(self):
        if self.vel.x != 0 and self.vel.y != 0:
            dragAmnt = particle.drag * lengthSquared(self.vel)
            dragForce = -self.vel.normalize() * dragAmnt
            #if math.isnan(dragForce[0]) or math.isnan(dragForce[1]):
            #    error
            return dragForce
        return pygame.Vector2(0,0)
        
    def getForceTowards(self, target, strength = 1, falloff = -1):
        towardVec = (target - self.pos)
        distStrengthMult = 1
        if towardVec.x != 0 and towardVec.y != 0:
            if falloff >= 0:
                dist = towardVec.length()
                distStrengthMult = clamp((falloff - dist) / falloff, 0,1)
            return towardVec.normalize() * distStrengthMult * strength / self.mass
        return pygame.Vector2(random.random()*2-1,random.random()*2-1)

    def applyForce(self, force):
        self.accAccum += force

    #Returns boolean for if any force was applied
    def applyForceTowards(self, target, strength = 1, falloff = -1):
        self.applyForce(self.getForceTowards(target, strength, falloff))

    def applyBoarders(self):
        hit = False
        if self.pos.x < particle.boarders[0]:
            self.pos.x = particle.boarders[0]
            self.vel.x = abs(self.vel.x)
            hit = True
        elif self.pos.x > particle.boarders[0] + particle.boarders[2]:
            self.pos.x = particle.boarders[0] + particle.boarders[2]
            self.vel.x = -abs(self.vel.x)
            hit = True
        if self.pos.y < particle.boarders[1]:
            self.pos.y = particle.boarders[1]
            self.vel.y = abs(self.vel.y)
            hit = True
        elif self.pos.y > particle.boarders[1] + particle.boarders[3]:
            self.pos.y = particle.boarders[1] + particle.boarders[3]
            self.vel.y = -abs(self.vel.y)
            hit = True

        if hit:
            rotateVec(self.vel,random.uniform(-15,15))

    def arrest(self):
        self.acc = pygame.Vector2(0,0)
        self.accAccum = pygame.Vector2(0,0)
        self.vel = pygame.Vector2(0,0)

    def resetPos(self, newPos):
        self.arrest()
        self.pos = pygame.Vector2(newPos)
        self.oldPos = pygame.Vector2(newPos)
        
    def updatePhysics(self, deltaTime):
        #Drag
        self.applyForce(self.getDrag())
        #!!!!!!
        #Drag becomes NaN, or causes velocity to become NaN which causes drag to become NaN - not sure which one is the problem.
        #!!!!!!
        
        #Apply accumulated accelleration to accelleration
        self.acc = self.accAccum
        #Set velocity and position based on accelleration
        self.vel += self.acc * deltaTime
        #if self.vel.length() < particle.drag:
        #    self.vel = pygame.Vector2(0,0)
        if lengthSquared(self.vel) > 100000000: #100000000 is 10000**2
            self.vel = self.vel.normalize() * 10000
        #Now that the forces have taken effect, clear them
        self.accAccum = pygame.Vector2(0,0)
        
    def updatePosition(self, deltaTime):
        self.pos += (self.vel * deltaTime + self.acc * 0.5 * (deltaTime*deltaTime)) / 1000
        #Bound particles within screen
        if particle.useBoarders:
            self.applyBoarders()
        
    def draw(self, screen, trail = False):
        #(the 0.3s make it not jiggle as much because it doesn't get stuck between pixels)
        if trail:
            off = (self.size+1) % 2 / 2 + 0.5
            pygame.draw.line(screen, self.color, self.pos+pygame.Vector2(0.3-off,0.3-off), self.oldPos+pygame.Vector2(0.3-off,0.3-off), self.size-(self.size % 2==1))
        pygame.draw.circle(screen, self.color, self.pos+pygame.Vector2(0.3,0.3), self.size/2)
        #pygame.draw.circle(screen, self.color, self.oldPos+pygame.Vector2(0.3,0.3), self.size/2)
        #Save old position
        self.oldPos = self.pos.copy()
        
    #def updatePost(self):
    #   Save old position
    #   self.oldPos = self.pos.copy()
        
class particleSystem:
    xSize = 1
    ySize = 1
    particleSize = 10
    
    def __init__(self, color,x,y, size=10,numParticles=50):
        self.particles = []
        particleSystem.particleSize = size+1
        theColor = None
        if color != -1:
            theColor = color
        for i in range(numParticles):
            if color == -1:
                theColor =(random.randrange(255), random.randrange(255), random.randrange(255))
            self.particles.append(particle(theColor,x+random.random(),y+random.random(),self.particleSize))
        particleSystem.xSize = math.ceil(maxx / (self.particleSize)) + 1 #The +1 allows for ones at the far edge of the screen
        particleSystem.ySize = math.ceil(maxy / (self.particleSize)) + 1
        self.hitColors = False

    def setArrangement(self, arrngName):
        if len(self.particles) <= 0:
            return
        if arrngName == "pool":
            self.particles[0].resetPos((particle.boarders[0] + particle.boarders[2]/4, particle.boarders[1] + particle.boarders[3]/2))
            startingBallPos = pygame.Vector2(particle.boarders[0] + particle.boarders[2]/3*2, particle.boarders[1] + particle.boarders[3]/2)
            ballDiam = self.particles[0].size
            layerHeight = math.sin(60*3.14159/180)*ballDiam
            row,num = 0,0
            for i in range(1, len(self.particles)):                
                height = row%2*-ballDiam/2+num%2*(num+1)/2*ballDiam+(num+1)%2*num/2*-ballDiam
                self.particles[i].resetPos(startingBallPos + (layerHeight * row, height))
                num+=1
                if num > row:
                    row+=1
                    num = 0
        elif arrngName == "grid":
            squareSize = int(math.sqrt(len(self.particles)))
            boundsCenter = pygame.Vector2(particle.boarders[0] +particle.boarders[2]/2,particle.boarders[1] +particle.boarders[3]/2)
            ballDiam = self.particles[0].size
            startCorner = boundsCenter - (squareSize/2*ballDiam, squareSize/2*ballDiam)
            row, col = 0,0
            for aParticle in self.particles:
                aParticle.resetPos(startCorner + (row*ballDiam, col * ballDiam))
                row+=1
                if row > squareSize:
                    col+=1
                    row = 0
        elif arrngName == "spiral":
            boundsCenter = pygame.Vector2(particle.boarders[0] +particle.boarders[2]/2,particle.boarders[1] +particle.boarders[3]/2)
            ballDiam = self.particles[0].size
            angle = 0
            radius = ballDiam
            oldRadius = radius
            spacing = ballDiam *1.1
            for aParticle in self.particles:
                aParticle.resetPos(boundsCenter - (math.sin(angle*3.14159/180)*radius,math.cos(angle*3.14159/180)*radius))
                oldRadius = radius
                radius += (spacing**2/6.5)/radius
                angleDeriv = (radius**2 + oldRadius**2 - spacing**2) / (2*radius*oldRadius)
                if angleDeriv > 1:
                    angleDeriv = 1
                angle += math.acos(angleDeriv) * (180/3.14159)
        else: #Cluster/point
            boundsCenter = pygame.Vector2(particle.boarders[0] +particle.boarders[2]/2,particle.boarders[1] +particle.boarders[3]/2)
            for aParticle in self.particles:
                #aParticle.resetPos(boundsCenter + (random.random()-0.5,random.random()-0.5))
                aParticle.resetPos(boundsCenter)# + ((random.random()*2-1)*particleSystem.particleSize,(random.random()*2-1)*particleSystem.particleSize))
        
    def applyForce(self, force):
        for aParticle in self.particles:
            aParticle.applyForce(force)

    def applyForceTowards(self, target, strength = 1, falloff = -1):
        for aParticle in self.particles:
            aParticle.applyForceTowards(target, strength, falloff)

    def getLoc(theParticle):
        return (math.floor(theParticle.pos.x/particleSystem.particleSize),math.floor(theParticle.pos.y/particleSystem.particleSize))
    
    def update(self, deltaTime):
        #global numLoops
        #numLoops = 0
        #Apply repulsive force between particles
        #Sort particle indicies spacially
        spacialArray = [[[] for j in range(particleSystem.xSize)] for i in range(particleSystem.ySize)]
        for i in range(len(self.particles)):
            #numLoops += 1
            #Calculate own grid square coordinates
            myLoc = particleSystem.getLoc(self.particles[i])
            if myLoc[0] >= 0 and myLoc[0] <= particleSystem.xSize and myLoc[1] >= 0 and myLoc[1] <= particleSystem.ySize:
                spacialArray[myLoc[1]][myLoc[0]].append(i)
        #For every particle, check and apply collisions to it's nearby ones             
        for aParticle in self.particles:            
            #Calculate own grid square coordinates
            myLoc = particleSystem.getLoc(aParticle)
            if self.hitColors:
                aParticle.color = (0,255,0)
                gotHit = False
            #Check the 9 grid spaces around this particle for any nearby IDs
            collisions = 0
            evaluationMade = True
            i = 0
            consecutiveNos = 0
            #Go through all nearby IDs in rotating order
            while evaluationMade and consecutiveNos < 10 and collisions < 9 and i < 30: #check max 30 collisions, max 10 consecutive "no"s.
                evaluationMade = False
                for x in range(max(0,myLoc[0]-1), min(particleSystem.xSize,myLoc[0]+2)):
                    for y in range(max(0,myLoc[1]-1), min(particleSystem.ySize,myLoc[1]+2)):
                        if len(spacialArray[y][x]) > i:
                            index = spacialArray[y][x][i]                            
                            if aParticle != self.particles[index]:
                                evaluationMade = True
                                consecutiveNos += 1
                                #numLoops += 1
                                gotHit = True
                                if aParticle.isTouching(self.particles[index]):
                                    aParticle.applyForceTowards(self.particles[index].pos, -1, self.particles[index].size)
                                    collisions += 1
                                    consecutiveNos = 0
                                if collisions >= 9:
                                    break
                    if collisions >= 9:
                        break
                i += 1
            aParticle.updatePhysics(deltaTime)
            #Color stuff
            if self.hitColors and gotHit:
                aParticle.color = (255,0,0)
        #Update positions from completed velocities
        for aParticle in self.particles:
            #numLoops += 1
            aParticle.updatePosition(deltaTime)
                                                        
    def draw(self, screen, trails=False):
        for aParticle in self.particles:
            aParticle.draw(screen, trails)

    #def updatePost(self):
    #    for aParticle in self.particles:
    #        aParticle.updatePost()


#pS = particleSystem(-1, maxx / 2, maxy / 2, 3, 1000)
#pS.hitColors = True

pS = particleSystem(-1, maxx / 2, maxy / 2, 10, 200)

pS.setArrangement(arrangement)
repulsionRadius = 100
transparentCircle = pygame.Surface((repulsionRadius*2,repulsionRadius*2))
transparentCircle = transparentCircle.convert_alpha()
transparentCircle.fill((0,0,0,0))
pygame.draw.circle(transparentCircle, (240, 240, 240, 100), (repulsionRadius,repulsionRadius), repulsionRadius)
fadedCircle = generateFacedCircle((255,255,255), repulsionRadius * 0.9)
useGravity = False

#Main loop
simTime = pygame.time.get_ticks()
running = True
while running:
    #Delta time
    newTime = pygame.time.get_ticks()
    deltaTime = newTime - simTime
    simTime = newTime
    
    #Input
    mPos = pygame.Vector2(pygame.mouse.get_pos()) #Get mouse position
    keys = pygame.key.get_pressed()

    #Attractive force
    if pygame.mouse.get_pressed()[0]:
        pS.applyForceTowards(mPos, 5)
    #Repulsive force from mouse
    if pygame.mouse.get_pressed()[2]:    
        pS.applyForceTowards(mPos, -15, repulsionRadius)

    #Event loop
    for event in pygame.event.get():
        if event.type == pygame.QUIT: #Detect x button clicked
            running = False
        #if event.type == pygame.MOUSEBUTTONDOWN:
            #if event.button == pygame.BUTTON_RIGHT:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_c:
                oldScreen.fill((255,255,255))
            if event.key == pygame.K_SPACE:
                trails = not trails
            if event.key == pygame.K_r:
                pS.setArrangement(arrangement)
            if event.key == pygame.K_g:
                useGravity = not useGravity

    #Update
    if useGravity:
        pS.applyForce(gravity)
    pS.update(deltaTime)
    
    #Draw things
    #draw the old screen on the screen
    screen.blit(oldScreen,(0,0))

    if pygame.mouse.get_pressed()[2]:
        screen.blit(fadedCircle, mPos-(fadedCircle.get_width()/2,fadedCircle.get_height()/2))
    
    pS.draw(screen,trails)
        
    if trails:
        #Take a picture of the screen - things drawn before this
        #point leave a trail when trails is turned on
        oldScreen.blit(screen,(0,0))
    #Anything drawn after this point will never leave a trail
    if pygame.mouse.get_pressed()[2]:
        screen.blit(transparentCircle, mPos-(repulsionRadius,repulsionRadius))
    #pS.draw(screen)
    
    #pS.updatePost()
    textImg = font.render(str(deltaTime), True, (0,0,0))
    screen.blit(textImg,(0,0))
    #textImg = font.render(str(numLoops), True, (0,0,0))
    #screen.blit(textImg,(50,0))
    
    pygame.display.flip() #View.Update()
    
#End of program, close window
pygame.quit()
