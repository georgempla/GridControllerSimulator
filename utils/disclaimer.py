import pygame
import math

BG = (6, 8, 14)
BORDER = (50, 70, 100)
TEXT = (220, 220, 220)
DIM = (80, 100, 120)
GOLD = (255, 210, 50)
RED = (200, 60, 60)
BTN_COL = (30, 60, 110)
BTN_HOV = (45, 85, 150)

LINES = [
    ("GRID CONTROLLER SIMULATOR", GOLD, 'large'),
    ("Early Access Alpha - v0.1.2", DIM, 'med'),
    ("", None, 'gap'),
    ("This software is unfinished and under active development.", TEXT, 'small'),
    ("You will encounter bugs, missing features, and placeholder content.", TEXT, 'small'),
    ("This public alpha is to test the simulation and receive feedback.", TEXT, 'small'),
    ("", None, 'gap'),
    ("The electrical grid model is a fictional representation of a", DIM, 'small'),
    ("fictional city. Any resemblance to real infrastructure is coincidental.", DIM, 'small'),
    ("", None, 'gap'),
    ("Please take into account the complicated math behind the simulation while voting", DIM, 'small')
]

class DisclaimerScreen:
    def __init__(self,screen_w,screen_h):
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.tick = 0
        self.done = False

        self.font_large = pygame.font.SysFont('consolas', 26, bold=True)
        self.font_med = pygame.font.SysFont('consolas', 14)
        self.font_small = pygame.font.SysFont('consolas', 12)
        self.font_btn = pygame.font.SysFont('consolas', 13, bold=True)
        self.font_dim = pygame.font.SysFont('consolas', 10)
        PW, PH = 620, 380
        self.px = screen_w//2 - PW//2
        self.py = screen_h//2 - PH//2
        self.panel_rect = pygame.Rect(self.px, self.py, PW, PH)
        bw, bh = 200, 38
        self.btn_rect = pygame.Rect(
            screen_w//2 - bw//2,
            self.py + PH - bh - 16,
            bw, bh
        )

    def handle_event(self,event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.btn_rect.collidepoint(event.pos):
                self.done = True
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN,pygame.K_SPACE):
            self.done = True

    def draw(self, surface):
        self.tick +=1
        surface.fill(BG)

        grid_surf = pygame.Surface((self.screen_w,self.screen_h),pygame.SRCALPHA)
        for x in range(0, self.screen_w, 48):
            pygame.draw.line(grid_surf, (255, 255, 255, 5), (x, 0), (x, self.screen_h))
        for y in range(0, self.screen_h, 48):
            pygame.draw.line(grid_surf, (255, 255, 255, 5), (0, y), (self.screen_w, y))
        surface.blit(grid_surf, (0, 0))

        bg = pygame.Surface((self.panel_rect.w,self.panel_rect.h), pygame.SRCALPHA)
        bg.fill((10,14,24,230))
        surface.blit(bg,(self.px,self.py))
        pygame.draw.rect(surface,BORDER,self.panel_rect,1,border_radius=6)

        pygame.draw.rect(surface,(60,110,180),pygame.Rect(self.px,self.py+12,3,self.panel_rect.h-24),border_radius=2)

        ty = self.py + 22
        cx = self.screen_w//2
        for text,col,size in LINES:
            if size == 'gap':
                ty +=8
                continue
            if size == 'large':
                surf = self.font_large.render(text,True,col)
            elif size == 'med':
                surf = self.font_med.render(text,True,col)
            else:
                surf = self.font_small.render(text,True,col)
            surface.blit(surf,(cx-surf.get_width()//2,ty))
            ty += surf.get_height()+4

        div_y = self.btn_rect.y-12
        pygame.draw.line(surface,BORDER,(self.px+20,div_y),(self.px+self.panel_rect.w-20,div_y),1)

        mouse = pygame.mouse.get_pos()
        col = BTN_HOV if self.btn_rect.collidepoint(mouse) else BTN_COL
        pygame.draw.rect(surface,col,self.btn_rect,border_radius=4)
        lbl = self.font_btn.render("I Understand",True,TEXT)
        surface.blit(lbl,(self.btn_rect.centerx-lbl.get_width()//2,self.btn_rect.centery-lbl.get_height()//2))

        pulse = 0.4 + 0.3 * abs(math.sin(self.tick * 0.03))
        hint_col = tuple(int(c*pulse) for c in DIM)
        hint = self.font_dim.render("Press Enter or Space to continue", True,hint_col)
        surface.blit(hint,(cx-hint.get_width()//2,self.py+self.panel_rect.h+8))
