import pygame
import math

BG = (8,10,16)
RED = (200,40,40)
DIM_RED = (120,30,30)
GOLD = (255,210,50)
TEXT = (220,220,220)
DIM = (100,120,140)
BTN_W,BTN_H = 180,40

class GameOverScreen:
    def __init__(self,screen_w,screen_h,reason,score):
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.reason = reason
        self.score = score
        self.tick =0

        self.font_huge = pygame.font.SysFont('consolas',52,bold=True)
        self.font_large = pygame.font.SysFont('consolas',22,bold=True)
        self.font_med = pygame.font.SysFont('consolas',14)
        self.font_small = pygame.font.SysFont('consolas',12)

        cx = screen_w//2
        cy = screen_h//2
        self.restart_rect = pygame.Rect(cx-BTN_W-20,cy+80,BTN_W,BTN_H)
        self.menu_rect = pygame.Rect(cx+20,cy+80,BTN_W,BTN_H)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.restart_rect.collidepoint(event.pos):
                return 'restart'
            if self.menu_rect.collidepoint(event.pos):
                return 'menu'
        if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
            return 'restart'
        return None

    def draw(self,surface):
        self.tick+=1
        cx,cy = self.screen_w//2, self.screen_h//2

        surface.fill(BG)
        pulse = 0.55+0.08*math.sin(self.tick*0.04)
        vingette = pygame.Surface((self.screen_w,self.screen_h),pygame.SRCALPHA)
        for r in range(min(self.screen_w,self.screen_h)//2,0,-4):
            alpha = max(0,int((1-r/(min(self.screen_w,self.screen_h))/2))*160*pulse)
            pygame.draw.circle(vingette,(80,0,0,alpha),(cx,cy),r)
        surface.blit(vingette,(0,0))

        if (self.tick//20)%2 == 0:
            header = self.font_huge.render("GRID COLLAPSE", True,RED)
            surface.blit(header,(cx-header.get_width()//2,cy-160))

        pygame.draw.line(surface,DIM_RED,(cx-300,cy-100), (cx+300,cy-100),1)

        reason_surf = self.font_med.render("FAILURE REASON",True,DIM)
        surface.blit(reason_surf,(cx-reason_surf.get_width()//2,cy-90))
        reason_val = self.font_large.render(self.reason,True,TEXT)
        surface.blit(reason_val,(cx-reason_val.get_width()//2,cy-62))

        pygame.draw.line(surface,DIM_RED,(cx-300,cy-20),(cx+300,cy-20),1)
        score_lbl = self.font_med.render("FINAL SCORE",True,DIM)
        surface.blit(score_lbl,(cx-score_lbl.get_width()//2,cy-10))
        score_val = self.font_huge.render(f"{self.score:,}", True, GOLD)
        surface.blit(score_val,(cx-score_val.get_width()//2,cy+14))
        
        mouse = pygame.mouse.get_pos()
        self._draw_button(surface,self.restart_rect, "RESTART [R]", (40,100,50),(60,160,80),mouse)
        self._draw_button(surface,self.menu_rect, "MAIN MENU", (40,50,100),(60,80,160), mouse)
        
        hint = self.font_small.render("R to restart", True,DIM)
        surface.blit(hint,(cx-hint.get_width()//2,cy+136))
        
    def _draw_button(self,surface,rect,label,col_normal,col_hover,mouse):
        col = col_hover if rect.collidepoint(mouse) else col_normal
        pygame.draw.rect(surface,col,rect,border_radius=4)
        pygame.draw.rect(surface,True,rect,1,border_radius=4)
        lbl = self.font_med.render(label,True,TEXT)
        surface.blit(lbl,(rect.centerx-lbl.get_width()//2, rect.centery-lbl.get_height()//2))