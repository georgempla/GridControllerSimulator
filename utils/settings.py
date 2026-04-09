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

#I might start commenting my code :)
#This is basically a copy of mainmenu to be consistent
class Toggle:
    def __init__(self,x,y,w,h,color,color_toggle,value1,value2,label,state):
        self.rect = pygame.Rect(x,y,w,h-12)
        self.border_rect = pygame.Rect(x - 2, y - 2, w + 4, h - 8)
        self.state = state
        self.toggle_rect_nact = pygame.Rect(x+2,y+2,w//2-4,h-16)
        self.toggle_rect_act = pygame.Rect(x + w//2 + 2, y + 2, w // 2 - 4, h - 16)
        self.label = label
        self.color = color
        self.color_toggle = color_toggle
        self.value1 = value1
        self.value2 = value2
        self.hovered = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        if (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.rect.collidepoint(event.pos)):
            self.state = not self.state
            return self.state
        return None

    def draw(self, surface, font, font_label):
        col_toggle = tuple(min(255, c + 40) for c in self.color_toggle) if self.hovered else self.color_toggle
        pygame.draw.rect(surface, self.color_toggle, self.border_rect,border_radius=3)

        pygame.draw.rect(surface, self.color, self.rect,  border_radius=3)

        if self.state:
            pygame.draw.rect(surface, col_toggle, self.toggle_rect_act, border_radius=6)
        else:
            pygame.draw.rect(surface, col_toggle, self.toggle_rect_nact, border_radius=6)
        lbl1 = font.render(self.value1, True, (220, 220, 220))
        lbl2 = font.render(self.value2, True, (220, 220, 220))
        bx, by =self.rect.midbottom
        surface.blit(lbl1, (bx - lbl1.get_width()-15, by + lbl1.get_height() // 2))
        surface.blit(lbl2, (bx+15, by + lbl2.get_height() // 2))
        lbl = font_label.render(self.label, True, (220, 220, 220))
        surface.blit(lbl, (self.rect.midleft[0] - lbl.get_width(), self.rect.midleft[1]-lbl.get_height()//2))
class Slider:
    def __init__(self,x,y,w,h,color,color_toggle,value1,value2,label,label_w,state):
        x -= label_w
        self.rect = pygame.Rect(x,y,w,h-12)
        self.border_rect = pygame.Rect(x - 2, y - 2, w + 4, h - 8)
        self.state = state
        self.toggle_rect_base =[state*w//100+x-int(state/100*(w//10-4)),y+2,w//10-4,h-16]
        self.label = label
        self.color = color
        self.color_toggle = color_toggle
        self.value1 = value1
        self.value2 = value2
        self.hovered = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        if self.hovered and pygame.mouse.get_pressed()[0]:

            self.state = (event.pos[0]-self.rect.x)*100//self.rect.width
            if self.state<3:
                self.state = 0
            elif self.state>97:
                self.state=100
            self.toggle_rect_base[0] = self.state*self.rect.width//100+self.rect.x-int(self.state/100*self.toggle_rect_base[3])
            return self.state
        return None

    def draw(self, surface, font, font_label):
        col_toggle = tuple(min(255, c + 40) for c in self.color_toggle) if self.hovered else self.color_toggle
        pygame.draw.rect(surface, self.color_toggle, self.border_rect,border_radius=3)

        pygame.draw.rect(surface, self.color, self.rect,  border_radius=3)

        toggle_rect = pygame.Rect(*self.toggle_rect_base)
        pygame.draw.rect(surface, col_toggle, toggle_rect, border_radius=6)

        lbl1 = font.render(self.value1, True, (220, 220, 220))
        lbl2 = font.render(self.value2, True, (220, 220, 220))
        lblstate = font.render(str(self.state), True, (220, 220, 220))
        bx, by =self.rect.midbottom
        blx,bly = self.rect.bottomleft
        surface.blit(lbl1, (blx - lbl1.get_width()//2, by + lbl1.get_height() // 2))
        surface.blit(lbl2, (blx + self.rect.width - lbl2.get_width()//2, by + lbl2.get_height() // 2))
        surface.blit(lblstate, (bx - lblstate.get_width()//2, by + lblstate.get_height() // 2))
        lbl = font_label.render(self.label, True, (220, 220, 220))
        surface.blit(lbl, (self.rect.midleft[0] - lbl.get_width(), self.rect.midleft[1]-lbl.get_height()//2))
class Button:
    def __init__(self,x,y,w,h,color,color_toggle,label,label_w,state):
        self.rect = pygame.Rect(x,y,w,h-12)
        self.border_rect = pygame.Rect(x-2, y-2, w+4, h - 8)
        self.state = state
        self.toggle_rect_nact = pygame.Rect(x+2,y+2,w//2-4,h-16)
        self.toggle_rect_act = pygame.Rect(x + w//2 + 2, y + 2, w // 2 - 4, h - 16)
        self.label = label
        self.color = color
        self.color_toggle = color_toggle
        self.hovered = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        if (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.rect.collidepoint(event.pos)):
            self.state = not self.state
            return self.state
        return None

    def draw(self, surface, font, font_label):
        col_toggle = tuple(min(255, c + 40) for c in self.color_toggle) if self.hovered else self.color_toggle
        pygame.draw.rect(surface, col_toggle, self.border_rect,border_radius=3)
        pygame.draw.rect(surface, self.color, self.rect,  border_radius=3)
        if self.state:
            pygame.draw.line(surface,col_toggle,(self.rect.x+2,self.rect.y),(self.rect.x+self.rect.width-4,self.rect.y+self.rect.height),6)
            pygame.draw.line(surface, col_toggle, (self.rect.x+self.rect.width -4, self.rect.y),(self.rect.x + 2, self.rect.y + self.rect.height), 6)
        lbl = font_label.render(self.label, True, (220, 220, 220))
        surface.blit(lbl, (self.rect.midleft[0] - lbl.get_width(), self.rect.midleft[1]-lbl.get_height()//2))

class Settings:
    BTN_W = 520
    BTN_H = 62
    BTN_GAP = 10

    def __init__(self, screen_w, screen_h, cur_settings):
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.cur_settings = cur_settings
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
        cx = self.screen_w // 2
        total_h = 266
        start_y = self.screen_h // 2 - total_h // 2 + 30

        self.fscreen_rect = Button(cx, start_y, 40, 52, BG_PANEL, AVAILABLE, "Fullscreen: ",108, self.cur_settings['fullscreen'])
        self.mode_rect = Toggle(cx,start_y+66,80,52,BG_PANEL,AVAILABLE,"50hz","60hz","Grid Frequency: ",self.cur_settings['freq'])
        self.music_rect = Slider(cx,start_y+132,400,52,BG_PANEL,AVAILABLE,"0","100","Music Volume: ",126,self.cur_settings['music'])
        self.calm_rect = Button(cx, start_y+198, 40, 52, BG_PANEL, AVAILABLE, "Calm Music Only: ",153, self.cur_settings['calm'])

        bw = 160
        bh = 36
        by = self.screen_h - bh - 18
        self.back_rect = pygame.Rect(cx-bw//2,by,bw,bh)

    def handle_event(self, event):
        value = self.mode_rect.handle_event(event)
        if value != None:
            self.cur_settings["freq"]=value
            return self.cur_settings,False
        value = self.music_rect.handle_event(event)
        if value != None:
            pygame.mixer.music.set_volume(value / 100)
            self.cur_settings["music"] = value
            return self.cur_settings,False
        value = self.fscreen_rect.handle_event(event)
        if value != None:
            self.cur_settings["fullscreen"] = value
            return self.cur_settings,False
        value = self.calm_rect.handle_event(event)
        if value != None:
            self.cur_settings["calm"] = value
            return self.cur_settings,True
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos
            if self.back_rect.collidepoint(pos):
                return 'back'
        return None

    def draw(self, surface):
        self.tick += 1
        cx = self.screen_w // 2
        surface.fill(BG_DARK)
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

        self.fscreen_rect.draw(surface,self.font_small,self.font_label)
        self.mode_rect.draw(surface,self.font_small,self.font_label)
        self.music_rect.draw(surface, self.font_small, self.font_label)
        self.calm_rect.draw(surface, self.font_small, self.font_label)
        self._draw_bottom_btn(surface, self.back_rect, "BACK", False, mouse)

        ver = self.font_small.render("v0.1.1-alpha", True, (35, 45, 58))
        surface.blit(ver, (self.screen_w - ver.get_width() - 8, self.screen_h - ver.get_height() - 6))

    def _draw_bottom_btn(self, surface, rect, label, locked, mouse, col_normal=(25, 40, 65),
                         col_hover=(40, 65, 105)):
        if locked:
            pygame.draw.rect(surface, LOCKED, rect, border_radius=4)
            pygame.draw.rect(surface, LOCK_BRD, rect, 1, border_radius=4)
            lbl = self.font_small.render(label, True, LOCK_TEXT)
        else:
            col = col_hover if rect.collidepoint(mouse) else col_normal
            pygame.draw.rect(surface, col, rect, border_radius=4)
            pygame.draw.rect(surface, AVAIL_BRD if not locked else LOCK_BRD, rect, 1, border_radius=4)
            lbl = self.font_small.render(label, True, TEXT)
        surface.blit(lbl, (rect.centerx - lbl.get_width() // 2, rect.centery - lbl.get_height() // 2))

    def _draw_grid(self, surface):
        spacing = 48
        alpha_surf = pygame.Surface((self.screen_w, self.screen_h), pygame.SRCALPHA)
        for x in range(0, self.screen_w, spacing):
            pygame.draw.line(alpha_surf, (255, 255, 255, 6), (x, 0), (x, self.screen_h))
        for y in range(0, self.screen_h, spacing):
            pygame.draw.line(alpha_surf, (255, 255, 255, 6), (0, y), (self.screen_w, y))
        surface.blit(alpha_surf, (0, 0))