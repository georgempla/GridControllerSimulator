from itertools import count

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


def _panel (surface,x,y,w,h):
    bg = pygame.Surface((w,h),pygame.SRCALPHA)
    bg.fill(HUD_BG)

    surface.blit(bg,(x,y))
    pygame.draw.rect(surface,HUD_BORDER,pygame.Rect(x,y,w,h),1)
def _draw_arrow(surface,rect,color,count=2,thickness=2,padding=100):
    cy = rect.centery
    half_h = (rect.height//2)-padding

    chevron_w = 10
    spacing = 6
    total_w = count*chevron_w+(count-1)*spacing
    start_x = rect.centerx-total_w//2

    for i in range(count):
        tip_x = start_x +i*(chevron_w+spacing)+chevron_w
        tail_x = rect.centerx -total_w//2 +i*(chevron_w+spacing)
        pygame.draw.line(surface,color,(tail_x,cy-half_h),(tip_x,cy),thickness)
        pygame.draw.line(surface,color,(tip_x,cy),(tail_x,cy+half_h),thickness)

#So I don't really know how good this is, I am trying smt new with the design
class SandboxButton():
    def __init__(self,x,y,w,h,label,tag,oneclick,enabled):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.rect = pygame.Rect(x,y,w,h)
        self.highlight_rect = pygame.Rect(x-2,y-2,w+4,h+4)
        self.label = label
        self.tag = tag
        self.hover = False
        self.enabled = enabled
        self.oneclick = oneclick

    def handle_event(self,click,mouse_pos):
        self.hover = self.highlight_rect.collidepoint(*mouse_pos)
        if self.hover and click:
            if not self.oneclick:
                self.enabled = not self.enabled
            return self.oneclick,self.tag
        return False,None
    def draw(self,surface,font_small):
        pygame.draw.rect(surface,HUD_BORDER,self.highlight_rect,border_radius=3)
        pygame.draw.rect(surface,BTN_GREEN if self.enabled else (HUD_BG if not self.hover else HUD_DIM),self.rect,border_radius=3)
        label = font_small.render(self.label,True,HUD_TEXT)
        surface.blit(label,(self.x+(self.w - label.get_width())//2,self.y+(self.h-label.get_height())//2))
buttons = [
    {"label":"Disable game over", "tag":"nogameover","oneclick":False},
    {"label":"Trip all generatos :)", "tag":"tripallgens","oneclick":True},
    {"label":"Freeze frequency", "tag":"freezefreq","oneclick":False},
    {"label":"Freeze simulation","tag":"freeze","oneclick":False},
    {"label":"Initiate ship arrival","tag":"shipevent","oneclick":True},
    {"label":"Initiate cyberattack","tag":"cyberevent","oneclick":True},
    {"label":"Initiate Snowstorm","tag":"whiteoutevent","oneclick":True},
    {"label":"Trip all lines","tag":"tripalllines","oneclick":True},
    {"label":"Interrupt all events","tag":"stopevents","oneclick":True}
]
class SandboxMenu:
    def __init__(self,screen_w,screen_h):
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.h = screen_h//2.7
        self.w = screen_w//5
        self.x = screen_w
        self.y = (screen_h-self.h)//2
        self.panel_visible = False
        self.hover_rect_hover = False
        self.closing = False
        self.opening = False
        self.hover_rect = pygame.Rect(screen_w-screen_w//16,self.y*1.15,screen_w//16,self.h*0.8)
        self.enabled = {x["tag"]: False for x in buttons}
        self._make_buttons(self.x,self.y,self.w,self.h)
        
    def _make_buttons(self,start_x,start_y,menu_w,menu_h):
        self.buttons = []
        button_w = int(menu_w*0.8)
        button_x = start_x + menu_w//10
        button_h = 20
        padding = 10
        for i,button_info in enumerate(buttons):
            button_y = start_y + i*(button_h+padding) + button_h
            self.buttons.append(SandboxButton(button_x,button_y,button_w,button_h,button_info["label"],button_info["tag"],button_info["oneclick"],self.enabled[button_info["tag"]]))
    def handle_event(self,event,mouse_pos):

        if self.hover_rect.collidepoint(*mouse_pos):
            if self.panel_visible:
                if not self.hover_rect_hover:
                    self.closing = True
            else:
                if not self.hover_rect_hover:
                    self.opening = True
                    self.panel_visible = True
            self.hover_rect_hover = True
        else:
            self.hover_rect_hover = False
        click = False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            click = True
        for button in self.buttons:
            oneclick,tag = button.handle_event(click,mouse_pos)
            if tag:
                if not oneclick:
                    self.enabled[tag] = not self.enabled[tag]
                return tag


    def draw(self, surface,fonts):
        if self.closing:
            if self.x+2 >= self.screen_w:
                self.closing = False
                self.panel_visible = False
            else:
                self.x +=2
            self._make_buttons(self.x,self.y,self.w,self.h)
        elif self.opening:
            if self.x -2 <= self.screen_w-self.w:
                self.opening = False
                self.x = self.screen_w-self.w
            else:
                self.x -=2
            self._make_buttons(self.x,self.y,self.w,self.h)
        pygame.draw.rect(surface,HUD_BORDER,self.hover_rect,1)
        arrow_color = HUD_TEXT if self.hover_rect_hover else HUD_DIM
        _draw_arrow(surface,self.hover_rect,arrow_color)

        if self.panel_visible:
            _panel(surface,self.x,self.y,self.w,self.h)
            for button in self.buttons:
                button.draw(surface,fonts['small'])