import pygame.mouse
from pygame import MOUSEBUTTONDOWN, MOUSEBUTTONUP, MOUSEMOTION, MOUSEWHEEL


class Camera():
    CONSTANT_ZOOM = 8
    def __init__(self):
        self.pan_x = 200
        self.pan_y =0
        self.zoom = 1
        self.dragging = False
        self.last_mouse = (0,0)

    def zoom_at(self, mouse_x, mouse_y, factor):
        wx = (mouse_x - self.pan_x)/ self.zoom
        wy = (mouse_y - self.pan_y)/ self.zoom

        self.zoom *= factor
        self.zoom = max(0.5, min(5.0,self.zoom))

        self.pan_x = mouse_x - wx * self.zoom
        self.pan_y = mouse_y - wy * self.zoom

    def handle_event(self,event):
        if event.type == MOUSEBUTTONDOWN and event.button == 1:
            self.dragging = True
            self.last_mouse = event.pos
        elif event.type == MOUSEBUTTONUP and event.button == 1:
            self.dragging = False
        if event.type == MOUSEMOTION and self.dragging:
            dx = event.pos[0] - self.last_mouse[0]
            dy = event.pos[1] - self.last_mouse[1]
            self.pan_x += dx
            self.pan_y += dy
            self.last_mouse = event.pos
        elif event.type == MOUSEWHEEL:
            factor = 1.1 if event.y > 0 else 0.9
            self.zoom_at(*pygame.mouse.get_pos(), factor)
    
    def world_to_screen(self, wx,wy):
        sx = wx * self.zoom * self.CONSTANT_ZOOM + self.pan_x
        sy = wy * self.zoom * self.CONSTANT_ZOOM + self.pan_y
        return (int(sx), int(sy))
    
    def screen_to_world(self,wx,wy):
        wx = (wx - self.pan_x) / self.zoom / self.CONSTANT_ZOOM
        wy = (wy - self.pan_y) / self.zoom / self.CONSTANT_ZOOM
        return (wx, wy)