from wsgiref.validate import check_environ

import pygame
import math

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

MENU_ITEMS =[
    {
        'id':'simulation',
        'label':'Realistic Simulation',
        'sub': 'Oakridge, Alaska - A full physics grid',
        'tag':'AVAILABLE',
        'locked':False
    },
    {
        'id':'sandbox',
        'label':'Sandbox Mode',
        'sub': 'Unlimited resources with no failure conditions',
        'tag':'COMING SOON',
        'locked':True
    },
    {
        'id': 'campaign',
        'label': 'Campaign Mode',
        'sub': 'Structured missions across multiple grids',
        'tag': 'COMING SOON',
        'locked': True
    },
    {
        'id': 'scenarios',
        'label': 'Custom Scenarions',
        'sub': 'Scripted crisis events and operator challenges',
        'tag': 'COMING SOON',
        'locked': True
    },
    {
        'id':'custom_map',
        'label':'Custom Map Support',
        'sub': 'Load your own grid JSON',
        'tag':'COMING SOON',
        'locked':True
    },
    {
        'id':'market',
        'label':'Energy Market',
        'sub': 'Explore maps made by other players',
        'tag':'MAYBE',
        'locked':True
    },
    {
        'id':'achievements',
        'label':'Achievements',
        'sub': 'Track records and unlock bonuses',
        'tag':'COMING SOON',
        'locked':True
    }
]

TAG_COLS = {
    'AVAILABLE':(50,180,80),
    'COMING SOON':(80,80,80),
    'MAYBE': (120,80,20)
}

class MainMenu:
    BTN_W = 520
    BTN_H = 62
    BTN_GAP = 10

    def __init__(self, screen_w, screen_h):
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.tick = 0

        self.font_title = pygame.font.SysFont('consolas',42,bold=True)
        self.font_sub = pygame.font.SysFont('consolas', 13)
        self.font_label = pygame.font.SysFont('consolas', 16, bold=True)
        self.font_item = pygame.font.SysFont('consolas', 13, bold=True)
        self.font_desc = pygame.font.SysFont('consolas', 11)
        self.font_tag = pygame.font.SysFont('consolas', 10, bold=True)
        self.font_small = pygame.font.SysFont('consolas', 11)

        self._layout()

    def _layout(self):
        cx = self.screen_w//2
        total_h = len(MENU_ITEMS)*(self.BTN_H+self.BTN_GAP)-self.BTN_GAP
        start_y = self.screen_h//2-total_h//2+30

        self.items_rects = {}
        for i,item in enumerate(MENU_ITEMS):
            y = start_y+i*(self.BTN_H+self.BTN_GAP)
            self.items_rects[item['id']] = pygame.Rect(
                cx-self.BTN_W//2,y,self.BTN_W,self.BTN_H
            )

        bw=160
        bh=36
        by = self.screen_h-bh-18
        self.tutorial_rect = pygame.Rect(cx-bw//2,by,bw,bh)
        self.settings_rect = pygame.Rect(cx-bw-170,by,bw,bh)
        self.quit_rect = pygame.Rect(cx+170,by,bw,bh)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos
            for item in MENU_ITEMS:
                if not item['locked'] and self.items_rects[item['id']].collidepoint(pos):
                    return item['id']
            if self.tutorial_rect.collidepoint(pos):
                return 'tutorial'
            if self.settings_rect.collidepoint(pos):
                return 'settings'
            if self.quit_rect.collidepoint(pos):
                return 'quit'
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            return 'quit'
        return None

    def draw(self,surface):
        self.tick +=1
        cx = self.screen_w //2
        surface.fill(BG_DARK)
        self._draw_grid(surface)
        title = self.font_title.render("GRID CONTROLLER SIMULATOR",True,TEXT)
        surface.blit(title,(cx-title.get_width()//2,28))

        pulse = 0.6+0.4*abs(math.sin(self.tick*0.025))
        sub_col=tuple(int(c*pulse)for c in (100,140,180))
        sub = self.font_sub.render(
            "The Interactive Experience", True, sub_col
        )
        surface.blit(sub,(cx-sub.get_width()//2,80))
        pygame.draw.line(surface,BORDER,(cx-300,102),(cx+300,102),1)
        mouse = pygame.mouse.get_pos()
        for item in MENU_ITEMS:
            self._draw_item(surface,item,self.items_rects[item['id']],mouse)

        self._draw_bottom_btn(surface, self.tutorial_rect,"TUTORIAL",False,mouse)
        self._draw_bottom_btn(surface, self.settings_rect,"SETTINGS",False,mouse)
        self._draw_bottom_btn(surface, self.quit_rect, "QUIT",False,mouse)

        ver = self.font_small.render("v0.1.1-alpha",True,(35,45,58))
        surface.blit(ver,(self.screen_w-ver.get_width()-8,self.screen_h-ver.get_height()-6))

    def _draw_item(self,surface,item,rect,mouse):
        locked = item['locked']
        hovered=(not locked)and rect.collidepoint(mouse)
        if locked:
            bg = LOCKED
            brd = LOCK_BRD
        elif hovered:
            bg = AVAIL_HOV
            brd = AVAIL_BRD
        else:
            bg = AVAILABLE
            brd = AVAIL_BRD

        pygame.draw.rect(surface,bg,rect,border_radius=4)
        pygame.draw.rect(surface,brd,rect,1,border_radius=4)

        if not locked:
            bar = pygame.Rect(rect.x,rect.y+8,3,rect.h-16)
            pygame.draw.rect(surface,AVAIL_BRD,bar,border_radius=2)

        label_col = LOCK_TEXT if locked else TEXT
        desc_col = (40,50,62) if locked else DIM

        label = self.font_item.render(item['label'],True,label_col)
        desc = self.font_desc.render(item['sub'],True,desc_col)
        surface.blit(label,(rect.x+18,rect.y+12))
        surface.blit(desc,(rect.x+18,rect.y+34))

        tag = item['tag']
        tag_col = TAG_COLS.get(tag,(80,80,80))
        tag_sf = self.font_tag.render(tag,True,tag_col)
        tw = tag_sf.get_width()+10
        tag_rect = pygame.Rect(rect.right-tw-12,rect.centery-9,tw,18)
        tag_bg = (*tag_col[:3],) if not locked else(25,30,40)
        pygame.draw.rect(surface,tag_col,tag_rect,1,border_radius=3)
        pygame.draw.rect(surface,tag_col,tag_rect,1,border_radius=3)
        surface.blit(tag_sf, (tag_rect.x+5,tag_rect.centery-tag_sf.get_height()//2))

        if locked:
            lk = self.font_tag.render("LOCKED",True,LOCK_BRD)
            surface.blit(lk,(rect.x+rect.w//2-lk.get_width()//2,rect.centery-lk.get_height()//2))

    def _draw_bottom_btn(self,surface,rect,label,locked,mouse,col_normal = (25,40,65),col_hover=(40,65,105)):
        if locked:
            pygame.draw.rect(surface,LOCKED,rect,border_radius=4)
            pygame.draw.rect(surface,LOCK_BRD,rect,1,border_radius=4)
            lbl = self.font_small.render(label,True,LOCK_TEXT)
        else:
            col = col_hover if rect.collidepoint(mouse) else col_normal
            pygame.draw.rect(surface,col,rect,border_radius=4)
            pygame.draw.rect(surface,AVAIL_BRD if not locked else LOCK_BRD,rect,1,border_radius=4)
            lbl = self.font_small.render(label,True,TEXT)
        surface.blit(lbl,(rect.centerx-lbl.get_width()//2,rect.centery-lbl.get_height()//2))

    def _draw_grid(self,surface):
        spacing = 48
        alpha_surf = pygame.Surface((self.screen_w,self.screen_h),pygame.SRCALPHA)
        for x in range(0,self.screen_w,spacing):
            pygame.draw.line(alpha_surf,(255,255,255,6),(x,0),(x,self.screen_h))
        for y in range(0, self.screen_h, spacing):
            pygame.draw.line(alpha_surf, (255, 255, 255, 6), (0, y), (self.screen_w, y))
        surface.blit(alpha_surf,(0,0))

