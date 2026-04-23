import pygame

HUD_BG = (15,20,30,200)
HUD_BORDER = (60,80,100)
HUD_TEXT = (220,220,220)
HUD_DIM = (100,120,140)
SURPLUS_COL = (80,200,120)
DEFICIT_COL = (255,80,50)
NEUTRAL_COL = (60,80,100)
GRAY_SURPLUS_COL = (168,168,168)
GRAY_DEFICIT_COL = (142,142,142)
GRAY_NEUTRAL_COL = (74,74,74)
BTN_GREEN = (20,110,40)
def _panel(surface,x,y,w,h):
    bg = pygame.Surface((w,h),pygame.SRCALPHA)
    bg.fill(HUD_BG)
    surface.blit(bg,(x,y))
    pygame.draw.rect(surface,HUD_BORDER,pygame.Rect(x,y,w,h),1)
def wrap_value(text, max_width, font):
    if font.size(text)[0]<=max_width:
        return [text]
    words = text.replace("/", "/ ").split(" ")
    lines = []
    current = ''
    for word in words:
        test = (current+" "+word).strip()
        if font.size(test)[0] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines if lines else [text]

#I thought I should probably build a notification class that I use for achievments and giving proper music credits
class Notification:
    def __init__(self,screenw,screenh,image_path,message,type,len,author=None,name=None):
        self.screenw = screenw
        self.screenh = screenh
        self.cooldown = 0
        self.image = pygame.image.load(image_path).convert_alpha()

        self.w = screenw//4
        self.h = screenh//7
        self.y = self.screenh//7 +(self.h+self.screenh//100)*len
        self.len = len
        self.x = -self.w
        self.title_font = pygame.font.SysFont("consolas",15,True)
        self.body_font = pygame.font.SysFont("consolas",12)
        self.author_label = None
        self.labels=[]
        self.image_edge = self.w//100+int(self.h*0.8)

        if type == "music":
            self.title_label = self.title_font.render("Now playing:",True,HUD_TEXT)
            self.author_label = self.body_font.render(f"-By {author}",True,HUD_TEXT)
            self.body_label = self.body_font.render(message, True, HUD_TEXT)

        elif type == "ach":
            self.title_label = self.title_font.render("Achievment obtained:", True, HUD_TEXT)
            text1,text2 = message.split("\n")
            self.body_label = self.body_font.render(text1,True,HUD_TEXT)
            texts = wrap_value(text2,self.w-self.image_edge-6,self.body_font)
            for text in texts:
                self.labels.append(self.body_font.render(text,True,HUD_TEXT))


        self.image = pygame.transform.scale(self.image,(int(self.h*0.8),int(self.h*0.8)))
        self.opening = True
        self.closing = False
        self.build_notification()
    def build_notification(self):
        self.image_pos = (self.x+self.w//100,self.y+self.h//10)
        self.rect = pygame.Rect(self.x,self.y,self.w,self.h)
        self.image_edge = self.w//100+int(self.h*0.8)

        self.title_pos = ((self.w - self.image_edge - self.title_label.get_width()) // 2 + self.x + self.image_edge,
                          self.y + self.h // 10)
        self.body_pos = ((self.w - self.image_edge - self.body_label.get_width()) // 2 + self.x + self.image_edge,
                         self.h // (3 if self.labels else 2) + self.y)
        if self.labels:
            self.labels_final = []
            for i,label in enumerate(self.labels):
                self.labels_final.append([label,(self.x +self.image_edge+6,
                             self.h // 3 + self.y + (i+1)*(label.get_height()+6))])

        if self.author_label:
            self.author_pos = ((self.w-self.image_edge-self.author_label.get_width())//2+self.x+self.image_edge,self.body_pos[1]+self.body_label.get_height()+self.h//10)

    def update_index(self):
        self.len -=1
        self.y = self.screenh//7 +(self.h+self.screenh//100)*self.len
        self.build_notification()

    def draw(self,surface,tick):
        step = 7.5 if tick else 1.5
        if self.opening:
            if self.x+step>=self.screenw//100:
                self.x = self.screenw//100
                self.opening = False
                self.cooldown = 100 if tick else 1000
            else:
                self.x += step
            self.build_notification()
        elif self.closing:
            if self.x-step<= -self.w:
                self.x = -self.w
                self.closing = False
                return True
            else:
                self.x -= step
            self.build_notification()

        elif self.cooldown<=0:
            self.closing = True
        else:
            self.cooldown -=1

        _panel(surface,self.x,self.y,self.w,self.h)
        surface.blit(self.image,self.image_pos)
        surface.blit(self.title_label,self.title_pos)
        surface.blit(self.body_label, self.body_pos)

        if self.labels:
            for label,pos in self.labels_final:
                surface.blit(label,pos)

        if self.author_label:
            surface.blit(self.author_label,self.author_pos) #Time to give authors some proper credit right?