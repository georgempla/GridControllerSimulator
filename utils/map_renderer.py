import json
import math
import time
from audioop import reverse
from xml.sax import parse

from pygame import MOUSEBUTTONDOWN
from utils.icons import draw_icons, draw_label
from utils.infopanels import InfoPanel
from utils.hud import draw_hud, build_hud_fonts
from utils.simulationEngine import SimulationEngine
import pygame.draw


def load_grid(filepath):
    with open(filepath) as f:
        data = json.load(f)

    nodes = []
    data['hz'] = 58.0
    data['tick'] = 0
    data['gen_mw'] = 500
    data['load_mw'] = 550
    data['game_state'] = {'hour':18, 'season':'winter','day':1,'gen_online':5,'gen_total':len(data['generation_nodes']),'total_capacity_mw':2800}
    data['export_mw'] = 100
    data['alarms']=[
        {'text':'GEN-004 wind ramp event', 'severity':'warning'},
        {'text': 'SUB-005 N-1 risk', 'severity':'critical'}
    ]
    for collection in ['generation_nodes','storage_nodes','substation_nodes', 'load_nodes']:
        for node in data[collection]:
            pos = node.get('position')
            if pos is None:
                continue
            subtype = node.get('type') or node.get("subtype")

            if subtype == "gas":
                subtype = node.get("subtype")

            nodes.append({
                'id': node['id'],
                'name': node['name'],
                'type': collection,
                'subtype': subtype,
                'x': pos['x'],
                'y':pos['y'],
                'raw': node
            })
    lines = (data['transmission_lines'] + 
             data['distribution_lines'])
    return nodes,lines,data



class MapRenderer:
    ICON_THRESHOLD = 0.8
    LABEL_THRESHOLD = 1
    
    def __init__(self,nodes, lines, data, camera, font,font_bold, screen_w, screen_h,tutorial=None):
        self.font = font
        self.font_bold = font_bold
        self.nodes = nodes
        self.lines = lines
        self.data = data
        self.camera = camera
        self.panels = []
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.last_tick = time.time()
        self.hud_fonts = build_hud_fonts()
        self.SimulationEngine = SimulationEngine(data)
        self.node_map = {n['id']: n for n in nodes}
        self.tutorial = tutorial
        if self.tutorial:
            self.tutorial.set_engine(self.SimulationEngine)
            self.tutorial.node_map = self.node_map
    
    def draw(self,surface):

        self.draw_lines(surface)
        self.draw_nodes(surface)
        for p in self.panels:
            p.draw(surface)
        """if time.time() -self.last_tick>0.05:
            self.data['tick'] += 1
            self.data['hz'] = 59 + math.cos(math.radians(self.data['tick']))
            self.data['load_mw'] = 500 + 450*math.cos(math.radians(self.data['tick']*2))
            self.last_tick = time.time()"""
        dt_seconds = time.time() - self.last_tick
        if dt_seconds >=0.1:
            self.SimulationEngine.tick(dt_seconds)
            for p in self.panels:
                p.update_rows()
            self.last_tick = time.time()
        self.rects = draw_hud(surface, self.hud_fonts, self.SimulationEngine.hud_data(),self.screen_w, self.screen_h)
        if self.tutorial and not self.tutorial.done:
            self.tutorial.draw(surface)
    def draw_lines(self,surface):
        LINE_STYLES = {
            500: {'color' : (255,255,255), 'width':3},
            138: {'color': (180,180,180), 'width':2},
            25: {'color':(80,80,80), 'width':1}
        }
        for line in self.lines:
            from_node = self.node_map.get(line["from_node"])
            to_node = self.node_map.get(line['to_node'])
            if not from_node or not to_node:
                continue

            sx1, sy1 = self.camera.world_to_screen(from_node['x'], from_node['y'])
            sx2, sy2 = self.camera.world_to_screen(to_node['x'], to_node['y'])
            
            style = LINE_STYLES.get(line['voltage_kv'], LINE_STYLES[25])
            pygame.draw.line(surface,style['color'], (sx1,sy1),(sx2,sy2),style['width'])

    def get_clicked_node(self, mouse_pos):
        wx,wy = self.camera.screen_to_world(*mouse_pos)
        hit_radius = 3 / self.camera.zoom
        for node in self.nodes:
            dx = node['x'] - wx
            dy = node['y'] - wy

            if math.sqrt(dx*dx + dy*dy)<hit_radius:
                return node
        return None

    def draw_nodes(self, surface):
        for node in self.nodes:
            sx,sy = self.camera.world_to_screen(node['x'],node['y'])
            if self.camera.zoom < self.ICON_THRESHOLD:
                pygame.draw.circle(surface,(255,100,100), (sx,sy), 6)
            else:
                draw_icons(surface,node,sx,sy,40)
                if self.camera.zoom > self.LABEL_THRESHOLD:
                    draw_label(surface,node['name'],sx,sy,self.font)

    def map_click(self, event):
        if self.tutorial and not self.tutorial.done:
            consumed = self.tutorial.handle_event(event)
            if consumed:
                return True
        consumed = any(p.handle_event(event) for p in reversed(self.panels))
        if consumed:
            return True
        if event.type == MOUSEBUTTONDOWN and event.button == 1: 
            if self.rects["clear_rect"].collidepoint(event.pos):
                self.SimulationEngine.alarms.clear()
                return True
            for speed,rect in self.rects['speed_rects'].items():
                if rect.collidepoint(event.pos):
                    self.SimulationEngine.time_multiplier = speed
                    return True
            clicked = self.get_clicked_node(event.pos)

            if clicked:
                if self.tutorial:
                    self.tutorial.notify_node_clicked(clicked['id'])
                if clicked['id'] == 'SUB-009':
                    self.panels.append(InfoPanel.make_hvdc_panel(*event.pos,self.screen_w,self.screen_h,self.font,self.font_bold,self.SimulationEngine))
                else:
                    self.panels.append(InfoPanel(clicked, *event.pos,self.screen_w,self.screen_h,self.font,self.font_bold, self.SimulationEngine))
            else:
                if self.panels:
                    self.panels.pop()
                else:
                    self.camera.handle_event(event)
        else:
            self.camera.handle_event(event)
