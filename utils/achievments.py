import pygame,math,json

BG_DARK = (6, 8, 14)
BG_PANEL = (12, 16, 26)
BORDER = (40, 55, 75)
TEXT = (220, 220, 220)
DIM = (70, 85, 100)
GOLD = (255, 210, 50)
AVAILABLE = (30, 60, 100)
AVAIL_HOV = (45, 85, 140)
AVAIL_BRD = (80, 130, 200)
LOCKED = (18, 22, 30)
LOCK_BRD = (35, 42, 52)
LOCK_TEXT = (50, 62, 74)
RED_BTN = (100, 25, 25)
RED_HOV = (140, 35, 35)



TAG_COLORS={
    'basic':(60,120,80),
    'danger':(120,40,40),
    'chaos':(100,50,120),
    'control':(40,80,130),
    'advanced':(100,90,30),
    'green':(30,110,60),
}

CARD_H = 72
CARD_GAP=8
SCROLL_STEP=40

class AchievementsMenu:
    def __init__(self, screenw,screenh,achievements_path):
        self.screenw = screenw
        self.screenh = screenh
        with open(achievements_path,'r') as file:
            self.ACHIEVEMENTS = json.load(file)
        self.tick = 0
        self.scroll_y=0
        self.font_title = pygame.font.SysFont('consolas', 42, bold=True)
        self.font_sub = pygame.font.SysFont('consolas', 13)
        self.font_label = pygame.font.SysFont('consolas', 16, bold=True)
        self.font_item = pygame.font.SysFont('consolas', 13, bold=True)
        self.font_desc = pygame.font.SysFont('consolas', 11)
        self.font_tag = pygame.font.SysFont('consolas', 10, bold=True)
        self.font_small = pygame.font.SysFont('consolas', 11)
        self.build_screen()
        self._rebuild_vieport()
    def build_screen(self):
        cx = self.screenw//2
        bw = 160
        bh=36
        by = self.screenh-bh-18
        vpx=cx-340
        vpy=116
        vpw=680
        vph=by-vpy-10
        self.viewport=pygame.Rect(vpx,vpy,vpw,vph)
        self.back_rect=pygame.Rect(cx-bw//2,by,bw,bh)
    def _rebuild_vieport(self):
        cw = self.viewport.width
        n=len(self.ACHIEVEMENTS)
        total_h=max(self.viewport.height,n*(CARD_H+CARD_GAP)-CARD_GAP)
        self.content_surf=pygame.Surface((cw,total_h),pygame.SRCALPHA)
        self.content_surf.fill((0,0,0,0))
        self._max_scroll=max(0,total_h-self.viewport.height)
        for i,ach in self.ACHIEVEMENTS.items():
            y = (int(i)-1)*(CARD_H+CARD_GAP)
            self._draw_ach(self.content_surf,ach,0,y,cw)
    def handle_event(self,event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.back_rect.collidepoint(event.pos):
                return "back"
            if event.button==4 and self.viewport.collidepoint(event.pos):
                self.scroll_y=max(0,self.scroll_y-SCROLL_STEP)
            if event.button==5 and self.viewport.collidepoint(event.pos):
                self.scroll_y=min(self._max_scroll,self.scroll_y)
        if event.type == pygame.MOUSEWHEEL and self.viewport.collidepoint(pygame.mouse.get_pos()):
            self.scroll_y -= event.y*SCROLL_STEP
            self.scroll_y = max(0,min(self._max_scroll,self.scroll_y))
    def draw(self,surface):
        self.tick+=1
        surface.fill(BG_DARK)
        cx = self.screenw//2
        self._draw_grid(surface)
        title = self.font_title.render("GRID CONTROLLER SIMULATOR", True, TEXT)
        surface.blit(title, (cx - title.get_width() // 2, 28))

        pulse = 0.6 + 0.4 * abs(math.sin(self.tick * 0.025))
        sub_col = tuple(int(c * pulse) for c in (100, 140, 180))
        sub = self.font_sub.render(
            "The Interactive Experience", True, sub_col
        )
        surface.blit(sub, (cx - sub.get_width() // 2, 80))
        pygame.draw.line(surface, BORDER, (cx - 300, 102), (cx + 300, 102), 1)
        mouse = pygame.mouse.get_pos()
        self._draw_bottom_btn(surface,self.back_rect,"Back",mouse)
        pygame.draw.rect(surface,BG_PANEL,self.viewport,border_radius=6)
        old_clip = surface.get_clip()
        surface.set_clip(self.viewport)
        surface.blit(self.content_surf,(self.viewport.x,self.viewport.y-self.scroll_y))
        surface.set_clip(old_clip)
        pygame.draw.rect(surface,BORDER,self.viewport,1,border_radius=6)
        self._draw_scrollbar(surface)

    def _draw_bottom_btn(self,surface,rect,label,mouse,col_n=(25,40,65),col_hover=(40,65,105)):
        col= col_hover if rect.collidepoint(mouse) else col_n
        pygame.draw.rect(surface,col,rect,border_radius=4)
        pygame.draw.rect(surface,AVAIL_BRD,rect,1,border_radius=4)
        lbl=self.font_small.render(label,True,TEXT)
        surface.blit(lbl,(rect.centerx-lbl.get_width()//2,rect.centery-lbl.get_height()//2))
    def _draw_ach(self,surface,ach,x,y,w):
        unlocked = ach["unlocked"]
        bg = AVAILABLE if unlocked else LOCKED
        brd= AVAIL_BRD if unlocked else LOCK_BRD
        rect = pygame.Rect(x,y,w,CARD_H)
        pygame.draw.rect(surface,bg,rect,border_radius=6)
        pygame.draw.rect(surface,brd,rect,1,border_radius=6)
        bar_col=GOLD if unlocked else LOCK_BRD
        pygame.draw.rect(surface,bar_col,(x+4,y+8,3,CARD_H-16),border_radius=2)
        iconx,icony=x+20,y+CARD_H//2
        if unlocked:
            self._draw_star(surface,iconx,icony,12,GOLD)
        else:
            lk=self.font_item.render("[X]",True,LOCK_TEXT)
            surface.blit(lk,(iconx-lk.get_width()//2,icony-lk.get_height()//2))
        name_col=TEXT if unlocked else LOCK_TEXT
        name_s=self.font_item.render(ach["name"],True,name_col)
        surface.blit(name_s,(x+46,y+12))
        desc_col=DIM if unlocked else LOCK_TEXT
        desc_s= self.font_desc.render(ach["desc"],True,desc_col)
        surface.blit(desc_s,(x+46,y+34))

        tag_text = ach['tag']
        if tag_text:
            tag_col = TAG_COLORS.get(tag_text,(60,60,60)) if unlocked else (30,36,44)
            ts = self.font_tag.render(tag_text,True,TEXT if unlocked else LOCK_TEXT)
            tw,th=ts.get_size()
            pad=5
            pill = pygame.Rect(x+w-tw-pad*2-10,y+10,tw+pad*2,th+pad)
            pygame.draw.rect(surface,tag_col,pill,border_radius=3)
            surface.blit(ts,(pill.x+pad,pill.y+pad//2))

        if unlocked:
            ul = self.font_tag.render("UNLOCKED",True,(80,180,80))
            surface.blit(ul,(x+w-ul.get_width()-10,y+CARD_H-ul.get_height()-10))
    @staticmethod
    def _draw_star(surface,cx,cy,r,col):
        pts=[]
        for i in range(10):
            angle=math.radians(-90+i*36)
            radius = r if i%2==0 else r*0.45
            pts.append((cx+radius*math.cos(angle),cy+radius*math.sin(angle)))
        pygame.draw.polygon(surface,col,pts)
    def _draw_scrollbar(self,surface):
        if self._max_scroll<=0:
            return
        vp = self.viewport
        sw = 4
        sx = vp.right-sw-4
        sh=vp.height

        visible_frac=vp.height/(vp.height+self._max_scroll)
        thumb_h = max(24,int(sh*visible_frac))
        thumb_y = vp.y+int((sh-thumb_h)*(self.scroll_y/self._max_scroll))

        pygame.draw.rect(surface,BORDER,(sx,vp.y,sw,sh),border_radius=2)
        pygame.draw.rect(surface,AVAIL_BRD,(sx,thumb_y,sw,thumb_h),border_radius=2)
    def _draw_grid(self, surface):
        spacing = 48
        alphasurf = pygame.Surface((self.screenw,self.screenh),pygame.SRCALPHA)
        for x in range(0,self.screenw,spacing):
            pygame.draw.line(alphasurf,(255,255,255,6),(x,0),(x,self.screenh))
        for y in range(0,self.screenh,spacing):
            pygame.draw.line(alphasurf,(255,255,255,6),(0,y),(self.screenw,y))
        surface.blit(alphasurf,(0,0))