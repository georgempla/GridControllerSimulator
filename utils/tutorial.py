from random import gauss

import pygame
import math
from dataclasses import dataclass,field
from typing import Optional,Callable,Tuple,List

from select import select

OVERPLAY_COL = (0,0,0,160)
PANEL_BG = (10,14,22,230)
PANEL_BORDER = (80,130,200)
TEXT = (220,220,220)
DIM = (100,120,140)
GOLD = (255,210,50)
BTN_NEXT = (30,80,140)
BTN_HOV = (45,110,180)
BTN_SKIP = (35,40,48)
BTN_SKIP_HOV = (55,62,72)
HIGHLIGHT_COL = (80,150,255,60)
HIGHLIGHT_BRD = (80,150,255)
GATE_COL = (255,180,40)

@dataclass
class ScreenHighlight:
    rect:pygame.Rect


@dataclass
class NodeHighlight:
    node_id:str
    radius:int=38
@dataclass
class PanelHighlight:
    node_id:str
    backup:NodeHighlight=None

@dataclass
class TutorialStep:
    title:str
    body:str
    highlight:Optional[object] = None
    gate:Optional[Callable] = None
    gate_hint: str=''
    pan:[int,int]=None
    close:str=None

def _hud_freq_rect(sw):
    W,H = 200,120
    return pygame.Rect(sw//2-W//2,10,W,H)
def _hud_status_rect():
    return pygame.Rect(10,10,200,148)
def _hud_genload_rect(sw,sh):
    W,H = 400,54
    return pygame.Rect(sw//2-W//2,sh-H-10,W,H)
def _hud_alarms_rect(sw):
    return pygame.Rect(sw-230,10,220,220)

def build_steps(screen_w,screen_h,node_map,freq):
    def gate_click_node(node_id):
        def _gate(engine,event):
            return getattr(engine, '_tutorial_clicked_node',None) == node_id
        return _gate
    def gate_setpoint_changed(gen_id):
        def _gate(engine,event):
            g = engine.generators.get(gen_id)
            return g is not None and g.setpoint_mw > g.min_output_mw
        return _gate
    def gate_storage_commanded():
        def _gate(engine,event):
            return any(abs(s.setpoint_mw)>0 for s in engine.storage.values())
        return _gate
    steps =[
        TutorialStep(
            title="Welcome to Grid Controller Simulator",
            body=f"""You are the system operator for the Oakridge,Alaska
power grid, a 1,500MW nuclear-based system serving
a city of 100,000 people.\n
Your job: to keep the lights on while maintaining a frequency
of {int(freq)}hz and honour your export contract to the southern grid.\n
This is a tutorial to teach you the interface.
Click next to begin.
            """
        ),
        TutorialStep(
            title="The Map",
            body="""The map is your main source of information on the grid.\n
Lines are color-coded by voltage:
    White  - 500 kV transmission (nuclear backbone)
    Grey   - 138 kV subtransmission
    Dark   - 25 kV distribution\n
The icons represent generators, substations, storage,
and load zones. Zoom using scroll and pan by dragging."""
        ),
        TutorialStep(
            title="Camera Controls",
            body="""
Scroll wheel   - zoom in / out
Left drag      - pan the map\n
Zoom is centred on your cursor position, so aim
at a node before zooming to bring it into focus.\n
At low zoom, nodes collapse to coloured dots
to avoid clutter. Zoom in to see full icons and labels.
            """
        ),
        TutorialStep(
            title="Frequency Gauge",
            body=f"""
The gauge at the top centre is your primary instrument.\n
{freq} Hz  - nominal, all is well
{freq-0.5} Hz  - warning, generation deficit
{freq-0.7} Hz  - alert, dispatch now
{freq-1.2} Hz  - emergency, load shedding begins
{freq-1.6} Hz  - grid collapse, game over\n
Frequency falls when load exceeds generation,
and rises when generation exceeds load.
""",
            highlight=ScreenHighlight(_hud_freq_rect(screen_w))
        ),
        TutorialStep(
            title="Generation vs Load Bar",
            body="""
The bar at the bottom centre shows the real time
balance between total generation and total demand.\n
Green left of centre  - surplus (frequency rises)
Red right of centre   - deficit (frequency falls)\n
A small grace band (10 MW) is shown as balanced.
Your job is to keep the indicator close to centre."
            """,

        highlight = ScreenHighlight(_hud_genload_rect(screen_w, screen_h)),
    ),
        TutorialStep(
            title="Status Panel",
            body="""
The top left panel shows the grid state at a glance:\n
Time     - simulated time of day
Season   - affects demand a renewable output
Day      - days gone by since start
Online   - amount of generators currently online
Capacity - total available MW accross your online units
Score    - your currect score\n
Speed buttons let you accelerate simulation time.
""",
            highlight=ScreenHighlight(_hud_status_rect()),

        ),
        TutorialStep(
            title="Alarms Panel",
            body="""
The top right panel shows active system alarms.
    Blue dot   - informational
    Amber dot  - warning (line loading, low frequency)
    Red dot    - critical (forced outage, major failures)
Alarms are time-ordered, newest at the bottom.
Press CLEAR to dismiss acknowledged alarms.\n
The HVDC interconnect flow is shown at the top
of this panel - positive is export.
""",
            highlight=ScreenHighlight(_hud_alarms_rect(screen_w)),
        ),

        TutorialStep(
            title="Clicking a Node",
            body="""
Every node on the map is clickable.
Clicking opens a live Info Panel with real-time data
and control buttons for that facility.\n
Click the Oakridge Nuclear Power Station to continue.
(It's the large node in the lower left of the map.)
""",
            highlight=NodeHighlight('GEN-001', radius=45),
            gate=gate_click_node('GEN-001'),
            gate_hint="Click the nuclear plant on the map to continue",
            pan=[-70,-250],
        ),

        TutorialStep(
            title="The Info Panel",
            body="""
The Info Panel shows live data for the selected node:\n
Status      - online / standby / tripped / starting
Output      - current MW being generated right now
Setpoint    - target the unit is ramping toward
Min / Max   - operating range
Ramp Rate   - MW per minute this unit can change\n
The nuclear plant ramps at only 2 MW/min so plan ahead.
Click elsewhere to dismiss the panel.
""",
            highlight=PanelHighlight('GEN-001',NodeHighlight('GEN-001',radius=45)),

        ),

        TutorialStep(
            title="Setting a Generator Setpoint",
            body="""
To change a generator's output, type a MW value
in the text field on its Info Panel and press Enter.\n
The unit will ramp toward that setpoint at its
physical ramp rate, it won't get there instantly.\n
Try changing the CCGT setpoint (GEN-003) now.
It ramps at 8 MW/min, so changes are visible quickly.
""",
            highlight=PanelHighlight('GEN-003',NodeHighlight('GEN-003',radius=40)),
            gate=gate_setpoint_changed('GEN-003'),
            gate_hint="Open GEN-003 and enter a new setpoint to continue",
            pan=[-222,-266],
            close='GEN-001',
        ),

        TutorialStep(
            title="Trip & Restart",
            body="""
The TRIP button immediately begins ramping a generator
to zero and takes it offline.\n
Once tripped, the RESTART button sends it back to
minimum output - or starts the startup timer for
units with long startup times (Plan ahead).\n
The two peaker plants (GEN-006, GEN-007) start in
standby - you must restart them before they can
contribute to the grid.
""",

        highlight = PanelHighlight('GEN-003', NodeHighlight('GEN-003', radius=40)),
        ),
    TutorialStep(
            title="Storage, Battery & Pumped Hydro",
            body="""
There are two storage assets on the Oakridge grid:\n
Battery (STG-001) 200 MWh, responds in 0.2 seconds
Pumped Hydro (STG-002) 1200 MWh, responds in 30 seconds\n
Use MAX DIS to discharge into the grid, MAX CHG to absorb
surplus, or enter a specific MW rate manually.\n
Try commanding storage now.
""",
            highlight=PanelHighlight('STG-001',NodeHighlight('STG-001', radius=38)),
            gate=gate_storage_commanded(),
            gate_hint="Command a storage unit to charge or discharge",
            close="GEN-003",
            pan=[-440,70]
        ),

        TutorialStep(
            title="HVDC Interconnect",
            body="""
Click the Export Interconnect Substation (SUB-009)
in the far east of the map to open the HVDC panel.\n
Positive MW = export to Southern Alaska (earns score)
Negative MW = import from Southern Alaska (emergency)\n
The link ramps at 50 MW/min, reversing from full
export to full import takes nearly 20 minutes.
Plan import requests before you actually need them.
""",
            highlight=PanelHighlight('SUB-009',NodeHighlight('SUB-009', radius=40)),
            close='STG-001',
            pan=[-638,0],
        ),

        TutorialStep(
            title="Load Priority Classes",
            body="""
Not all customers are equal. When shedding is needed,
loads are cut in this order:\n
Class 3  - Residential (shed first)
Class 2  - Industrial (interruptible contracts)
Class 1  - CBD / commercial (only in extremis)
Class 0  - Hospital, Airport (NEVER shed)\n
Losing a Class 0 load is always a failure condition
regardless of frequency. Protect them above all else.
""",
            close='SUB-009',
            pan=[230, 0],
        ),

        TutorialStep(
            title="You're Ready",
            body="""
That covers the Oakridge interface.\n
A few things to watch for in your first session:
    Winter evening peaks can hit 2,300 MW
    The gas pipeline is a single point of failure
    SUB-005 has no N-1 redundancy
    Wind ramp events can drop 250 MW in minutes
Good luck, Operator.
Press Finish to start your shift.
            """,
        ),
    ]
    return steps

class TutorialManager:
    PANEL_W = 440
    PANEL_H = 280

    def __init__(self,screen_w,screen_h,node_map,camera,freq):
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.node_map = node_map
        self.camera = camera
        self.steps = build_steps(screen_w,screen_h,node_map,freq)
        self.index = 0
        self.done = False
        self.tick = 0
        self._last_event = None

        self.font_title = pygame.font.SysFont('consolas',14,bold=True)
        self.font_body = pygame.font.SysFont('consolas', 12)
        self.font_small = pygame.font.SysFont('consolas', 11)

        self._layout_panel()

    def _layout_panel(self):
        cx = self.screen_w//2
        cy = self.screen_h//2

        self.px = cx-self.PANEL_W//2
        self.py = self.screen_h-self.PANEL_H-90
        self.panel_rect = pygame.Rect(self.px,self.py,self.PANEL_W,self.PANEL_H)

        bw,bh = 100,28
        by = self.py+self.PANEL_H-bh-10
        self.next_rect = pygame.Rect(self.px+self.PANEL_W-bw-10,by,bw,bh)
        self.skip_rect = pygame.Rect(self.px+10,by,80,bh)

    @property
    def current_step(self) -> TutorialStep:
        return self.steps[self.index]
    def _advance(self,panels):
        if self.index<len(self.steps)-1:
            self.index +=1
            if self.steps[self.index].pan:
                px,py= self.steps[self.index].pan
                self.camera.pan_x = px
                self.camera.pan_y = py
            if self.steps[self.index].close:
                for i,p in enumerate(panels):
                    if p.node.get('id') == self.steps[self.index].close:
                        panels.pop(i)
                        break

        else:
            self.done = True
    def notify_node_clicked(self,node_id:str):
        if hasattr(self,'_engine'):
            self._engine._tutorial_clicked_node = node_id

    def set_engine(self,engine):
        self._engine = engine

    def handle_event(self,event,panels):
        if self.done:
            return False
        self._last_event = event
        step = self.current_step
        mouse = pygame.mouse.get_pos()

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.skip_rect.collidepoint(mouse):
                self.done = True
                return True
            if self.next_rect.collidepoint(mouse):
                gate_passed = step.gate is None or step.gate(self._engine, None)
                if gate_passed:
                    self._advance(panels)
                    return True
        if step.gate and step.gate(self._engine,event):
            self._advance(panels)
            return False
        return False

    def draw(self,surface,panels):
        if self.done:
            return
        self.tick +=1
        step = self.current_step
        mouse = pygame.mouse.get_pos()
        is_last = self.index == len(self.steps)-1

        overlay = pygame.Surface((self.screen_w,self.screen_h),pygame.SRCALPHA)
        overlay.fill(OVERPLAY_COL)

        h1 = step.highlight
        if h1 is not None:
            if isinstance(h1,ScreenHighlight):
                self._cut_rect(overlay,h1.rect)
            elif isinstance(h1,NodeHighlight):
                node = self.node_map.get(h1.node_id)
                if node:
                    sx,sy = self.camera.world_to_screen(node['x'],node['y'])
                    self._cut_circle(overlay,sx,sy,h1.radius)
            elif isinstance(h1,PanelHighlight):
                found = False
                for panel in panels:
                    if panel.node.get('id') == h1.node_id:
                        found = True
                        self._cut_rect(overlay,panel.rect)
                if not found:
                    node = self.node_map.get(h1.node_id)
                    if node:
                        sx, sy = self.camera.world_to_screen(node['x'], node['y'])
                        self._cut_circle(overlay, sx, sy, h1.backup.radius)
        panel_cutout = self.panel_rect.inflate(6,6)
        self._cut_rect(overlay,panel_cutout)

        surface.blit(overlay,(0,0))

        if h1 is not None:
            pulse = 0.6+0.4*abs(math.sin(self.tick*0.05))
            brd_alpha = int(255*pulse)
            bed_col = (*HIGHLIGHT_BRD, brd_alpha)
            if isinstance(h1, ScreenHighlight):
                pygame.draw.rect(surface,HIGHLIGHT_BRD,h1.rect.inflate(4,4),2,border_radius=4)
            elif isinstance(h1,NodeHighlight):
                node = self.node_map.get(h1.node_id)
                if node:
                    sx,sy = self.camera.world_to_screen(node['x'],node['y'])
                    pygame.draw.circle(surface,HIGHLIGHT_BRD,(sx,sy),h1.radius,2)
                    inner_r = int(h1.radius*0.6+h1.radius*0.15*math.sin(self.tick*0.08))
                    inner_surf = pygame.Surface((self.screen_w,self.screen_h),pygame.SRCALPHA)
                    pygame.draw.circle(inner_surf,(*HIGHLIGHT_BRD,60),(sx,sy),inner_r,2)
                    surface.blit(inner_surf,(0,0))
            elif isinstance(h1,PanelHighlight):
                if not found:
                    node = self.node_map.get(h1.node_id)
                    if node:
                        sx, sy = self.camera.world_to_screen(node['x'], node['y'])
                        pygame.draw.circle(surface, HIGHLIGHT_BRD, (sx, sy), h1.backup.radius, 2)
                        inner_r = int(h1.backup.radius * 0.6 + h1.backup.radius * 0.15 * math.sin(self.tick * 0.08))
                        inner_surf = pygame.Surface((self.screen_w, self.screen_h), pygame.SRCALPHA)
                        pygame.draw.circle(inner_surf, (*HIGHLIGHT_BRD, 60), (sx, sy), inner_r, 2)
                        surface.blit(inner_surf, (0, 0))

        bg = pygame.Surface((self.PANEL_W,self.PANEL_H),pygame.SRCALPHA)
        bg.fill(PANEL_BG)
        surface.blit(bg,(self.px,self.py))
        pygame.draw.rect(surface,PANEL_BORDER,self.panel_rect,1,border_radius=4)

        counter = self.font_title.render(f"Step {self.index+1} of {len(self.steps)}", True, DIM)
        surface.blit(counter,(self.px+10,self.py+8))
        bar_w = self.PANEL_W-20
        prog = (self.index+1)/len(self.steps)
        pygame.draw.rect(surface,(25,35,50),pygame.Rect(self.px+10,self.py+22,bar_w,3))
        pygame.draw.rect(surface,PANEL_BORDER,pygame.Rect(self.px+10,self.py+22,int(bar_w*prog),3))

        title = self.font_title.render(step.title,True,GOLD)
        surface.blit(title,(self.px+10,self.py+32))

        pygame.draw.line(surface,(40,55,75),(self.px+10,self.py+52),(self.px+self.PANEL_W-10,self.py+52),1)

        ty = self.py+58
        for line in step.body.split('\n'):
            rendered = self.font_body.render(line,True,TEXT)
            surface.blit(rendered,(self.px+10,ty))
            ty+=17

        by = self.py + self.PANEL_H-28-10
        gate_passed = step.gate is None or step.gate(self._engine,None)
        if step.gate is not None and not gate_passed:
            hint = self.font_small.render(step.gate_hint,True,GATE_COL)
            surface.blit(hint,(self.px+self.PANEL_W-hint.get_width()-2,by+6))
        else:
            label = "Finish" if is_last else "Next"
            col = BTN_HOV if self.next_rect.collidepoint(mouse) else BTN_NEXT
            pygame.draw.rect(surface,col,self.next_rect,border_radius=3)
            pygame.draw.rect(surface,PANEL_BORDER,self.next_rect,1,border_radius=3)
            lbl = self.font_small.render(label,True,TEXT)
            surface.blit(lbl, (self.next_rect.centerx-lbl.get_width()//2,self.next_rect.centery-lbl.get_height()//2))

        skip_col = BTN_SKIP_HOV if self.skip_rect.collidepoint(mouse) else BTN_SKIP
        pygame.draw.rect(surface,skip_col,self.skip_rect,border_radius=3)
        pygame.draw.rect(surface,(50,60,72),self.skip_rect,1,border_radius=3)
        sk = self.font_small.render("Skip all",True,DIM)
        surface.blit(sk,(self.skip_rect.centerx-sk.get_width()//2,self.skip_rect.centery-sk.get_height()//2))

    def _cut_rect(self,overlay,rect):
        pygame.draw.rect(overlay,(0,0,0,0),rect)

    def _cut_circle(self, overlay,cx,cy,r):
        pygame.draw.circle(overlay,(0,0,0,0),(cx,cy),r)