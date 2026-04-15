from importlib.resources import read_text
from os import truncate
from time import process_time
from tkinter.ttk import Label

import pygame, math


COLOURS = {
    'nuclear':      (255, 220,  50),
    'hydro':        ( 50, 150, 255),
    'wind':         (100, 230, 255),
    'solar':        (255, 255,  80),
    'gas':          (255, 140,   0),
    'gas_dim':      (180,  90,   0),
    'biomass':      ( 80, 200, 100),
    'battery':      (150, 255, 100),
    'pumped_hydro': ( 50, 100, 255),
    'substation':   (200, 200, 200),
    'load_0':       (255,  50,  50),   #critical
    'load_1':       (255, 140,  50),   #essential
    'load_2':       (255, 210,  50),   #industrial
    'load_3':       (180, 180, 180),   #residential
}

def truncate_label(text, max_chars =18):
    if len(text)> max_chars:
        return text[:max_chars-1]+"..."
    return text

def get_label_rect(text,x,y,font,node_size=14):
    text = truncate_label(text)
    lw,lh = font.size(text)
    pad=3
    return pygame.Rect(
        x-lw//2-pad,
        y+node_size+2,
        lw+pad*2,
        lh+pad
    )

def find_label_position(text,x,y,font,label_rects,node_size=14):
    for offset in range(0,40,8):
        rect = get_label_rect(text,x,y+offset,font,node_size)
        if not any(rect.colliderect(r)for r in label_rects):
            return y+offset,rect
    return y+40,get_label_rect(text,x,y+40,font,node_size)

def _polygon(surface, colour, cx,cy,points, width=0):
    translated = [(cx+px, cy+py) for px, py in points]
    pygame.draw.polygon(surface,colour,translated,width)

def _circle(surface, colour, cx, cy, r, width=0):
    pygame.draw.circle(surface, colour, (cx,cy), r, width)

def _rect(surface, colour, cx, cy, w, h, width=0):
    r = pygame.Rect(cx - w//2, cy - h//2, w, h)
    pygame.draw.rect(surface, colour, r, width)

def _line(surface, colour, cx, cy, x1, y1 , x2, y2, width = 1):
    pygame.draw.line(surface, colour, (cx+x1, cy+y1), (cx+x2, cy+y2), width)



def draw_nuclear(surface, x, y , size):
    c = COLOURS['nuclear']
    r = size//2
    for angle in (0,60,120):
        pts = []
        for t in range(0, 361, 20):
            ex = (r*0.9) * math.cos(math.radians(t))
            ey = (r * 0.4) * math.sin(math.radians(t))
            rx = ex* math.cos(angle) - ey * math.sin(angle)
            ry = ex* math.sin(angle) + ey * math.cos(angle)
            pts.append((x+rx, y +ry))
        if len(pts) >=2:
            pygame.draw.lines(surface,c,True,pts,1)
    _circle(surface, c, x, y, max(2, size//6))
    
def draw_hydro(surface, x,y,size):
    c = COLOURS['hydro']
    h = size//2
    w = int(size *0.4)
    
    _line(surface,c,x,y,0,-h,h//3,2)
    
    _polygon(surface, c, x, y+h//3, [(-w,0),(w,0),(0,h//2)])

def draw_wind(surface, x,y,size):
    c = COLOURS['wind']
    r = size//2
    for i in range(3):
        angle = math.radians(i*120 - 90)
        tip_x = int(r* math.cos(angle))
        tip_y = int(r*math.sin(angle))
        
        perp = math.radians(i*120-90+80)
        base_x = int(r*0.25 * math.cos(perp))
        base_y = int(r*0.25*math.sin(perp))
        pts = [(0,0),(base_x,base_y), (tip_x, tip_y)]
        _polygon(surface,c,x,y,pts)
    
    _circle(surface, (30,30,30), x,y, max(2,size//7))
    _circle(surface, c, x ,y, max(2,size//7),1)
def draw_solar(surface, x, y, size):
    c = COLOURS['solar']
    r = size//2
    inner = max(2,size//5)
    _circle(surface,c,x,y,inner)
    for i in range(8):
        angle = math.radians(i*45)
        x1 = int((inner+2)*math.cos(angle))
        y1 = int((inner+2)*math.sin(angle))
        x2 = int(r*math.cos(angle))
        y2 = int(r*math.sin(angle))
        _line(surface,c,x,y,x1,y1,x2,y2,2)

def draw_gas_ccgt(surface,x,y,size):
    c = COLOURS['gas']
    r = size//2
    pts = [
        (0,-r),
        (r//2,-r//4),
        (r//3,r//2),
        (0,r//3),
        (-r//3,r//2),
        (-r//2, -r//4)
    ]
    _polygon(surface,c,x,y,pts)
    inner = [(p[0]//2,p[1]//2) for p in pts]
    _polygon(surface, (255,100,100),x,y,inner)

def draw_gas_peaker(surface,x,y,size):
    c =COLOURS['gas_dim']
    r = size//2
    pts = [
        (0,-r),
        (r//2,-r//4),
        (r//3,r//2),
        (0,r//3),
        (-r//3,r//2),
        (-r//2, -r//4)
    ]
    _polygon(surface,c,x,y,pts,width=0)
    _polygon(surface,(255,255,255),x,y,pts,width=1)

def draw_biomass(surface,x,y,size):
    c = COLOURS['biomass']
    r = size//2
    pts = []
    for i in range(6):
        angle = math.radians(i*60-30)
        pts.append((int(r*math.cos(angle)),int(r*math.sin(angle))))
    _polygon(surface,c,x,y,pts,width=2)
    _line(surface,c,x,y,0,-r+3,0,r-3,1)
    
def draw_battery(surface,x,y,size):
    c = COLOURS['battery']
    w,h = size, int(size*1.3)
    
    _rect(surface,c,x,y+size//8,w,h,width=2)
    nub_w= max(3,size//3)
    _rect(surface, c ,x ,y-h//2+size//8-2,nub_w,4)
    _line(surface,c,x,y,0,-size//4,0,size//4,2)
    
def draw_pumped_hydro(surface,x,y,size):
    c = COLOURS['pumped_hydro']
    r = size//2
    _circle(surface,c,x,y,r,2)
    ar = r-3
    aw = max(2,size//5)
    _line(surface,c,x,y,0,0,0,-ar,2)
    _polygon(surface,c,x,y-ar,[(-aw,aw),(aw,aw),(0,0)])
    
    _line(surface,c,x,y,0,0,0,ar,2)
    _polygon(surface,c,x,y+ar,[(-aw,-aw),(aw,-aw),(0,0)])

def draw_substation(surface, x,y,size):
    c = COLOURS['substation']
    _rect(surface,c,x,y,size,size,width=2)
    _circle(surface,c,x,y,max(2,size//6))

def draw_label(surface, text, x, y, font, node_size=14):
    label = font.render(text,True,(220,220,220))
    lw,lh = label.get_size()
    pad = 3
    bg_rect = pygame.Rect(x-lw//2-pad, y+node_size+ 2, lw + pad*2, lh+ pad)
    
    bg = pygame.Surface((bg_rect.width,bg_rect.height), pygame.SRCALPHA)
    bg.fill((0,0,0,160))
    surface.blit(bg,bg_rect.topleft)
    surface.blit(label, (x-lw//2, y+node_size+2+pad//2))

def draw_load(surface, x, y, size, node):
    """Route to the correct load icon based on type and name."""
    load_type = node.get('raw', {}).get('type', 'residential')
    name = node.get('name', '').lower()

    if 'hospital' in name or 'medical' in name:
        draw_load_hospital(surface, x, y, size)
    elif 'airport' in name:
        draw_load_airport(surface, x, y, size)
    elif load_type == 'residential':
        draw_load_residential(surface, x, y, size)
    elif load_type == 'industrial':
        draw_load_industrial(surface, x, y, size)
    elif load_type == 'commercial':
        draw_load_commercial(surface, x, y, size)
    elif load_type == 'mixed':
        draw_load_mixed(surface, x, y, size)
    else:
        draw_load_residential(surface, x, y, size)


def draw_load_residential(surface, x, y, size):
    """Classic house — square body + triangular roof."""
    c = COLOURS['load_3']
    w = int(size * 0.85)
    h = int(size * 0.7)
    body_top = y + size // 6
    # Body
    _rect(surface, c, x, body_top + h // 2, w, h, width=2)
    # Roof
    _polygon(surface, c, x, body_top,
             [(-w // 2 - 1, 0), (w // 2 + 1, 0), (0, -int(size * 0.4))],
             width=2)
    # Door
    door_w = max(2, w // 4)
    door_h = max(3, h // 3)
    _rect(surface, c, x, body_top + h - door_h // 2, door_w, door_h, width=1)


def draw_load_industrial(surface, x, y, size):
    """Factory — wide flat building + two chimneys with smoke dots."""
    c = COLOURS['load_2']
    w = size
    h = int(size * 0.55)
    body_top = y + size // 5
    # Main body
    _rect(surface, c, x, body_top + h // 2, w, h, width=2)
    # Left chimney
    ch_w = max(2, size // 6)
    ch_h = int(size * 0.5)
    _rect(surface, c, x - size // 3,
          body_top - ch_h // 2, ch_w, ch_h, width=2)
    # Right chimney
    _rect(surface, c, x + size // 6,
          body_top - ch_h // 2, ch_w, ch_h, width=2)
    # Smoke dots above chimneys
    _circle(surface, c, x - size // 3, body_top - ch_h - 3,
            max(1, size // 8), 1)
    _circle(surface, c, x + size // 6, body_top - ch_h - 3,
            max(1, size // 8), 1)


def draw_load_commercial(surface, x, y, size):
    """Office tower — tall narrow rectangle + grid of windows."""
    c = COLOURS['load_1']
    w = int(size * 0.6)
    h = size
    # Tower body
    _rect(surface, c, x, y, w, h, width=2)
    # 2x3 window grid
    for row in range(3):
        for col in range(2):
            wx = x - w // 4 + col * (w // 2)
            wy = y - h // 3 + row * (h // 3)
            win_size = max(2, size // 7)
            _rect(surface, c, wx, wy, win_size, win_size, width=1)


def draw_load_hospital(surface, x, y, size):
    """Hospital — square building + bold red cross on face."""
    c = COLOURS['load_0']
    w = int(size * 0.9)
    # Building
    _rect(surface, c, x, y, w, w, width=2)
    # Cross (filled for visibility)
    arm = max(2, size // 5)
    span = int(size * 0.35)
    # Horizontal bar
    _rect(surface, c, x, y, span * 2, arm)
    # Vertical bar
    _rect(surface, c, x, y, arm, span * 2)


def draw_load_airport(surface, x, y, size):
    """Airport — simple aircraft silhouette (top-down view)."""
    c = COLOURS['load_0']
    r = size // 2
    # Fuselage
    _polygon(surface, c, x, y, [
        (0,       -r),          # nose
        ( r // 5,  0),
        (0,        r * 2 // 3), # tail
        (-r // 5,  0),
    ])
    # Wings
    _polygon(surface, c, x, y, [
        (-r,       r // 5),
        ( r,       r // 5),
        ( r // 4,  r // 2),
        (-r // 4,  r // 2),
    ])
    # Tail fins
    _polygon(surface, c, x, y, [
        (-r // 3,  r * 2 // 3),
        ( r // 3,  r * 2 // 3),
        ( r // 5,  r),
        (-r // 5,  r),
    ])


def draw_load_mixed(surface, x, y, size):
    """Mixed zone — small house next to small office block."""
    c = COLOURS['load_3']
    half = size // 2

    # Left: mini house
    hw = int(half * 0.75)
    hh = int(half * 0.55)
    hx = x - half // 2
    hy = y + size // 8
    _rect(surface, c, hx, hy + hh // 2, hw, hh, width=2)
    _polygon(surface, c, hx, hy,
             [(-hw // 2, 0), (hw // 2, 0), (0, -int(half * 0.35))],
             width=2)

    # Right: mini office tower
    tw = int(half * 0.5)
    th = int(half * 0.9)
    tx = x + half // 2
    _rect(surface, COLOURS['load_1'], tx, y, tw, th, width=2)
def draw_control_center(surface,x,y,size):
    c=(100,200,255)
    r=size//2
    _rect(surface,c,x,y+size//8,size,int(size*0.6),width=2)
    sw = max(2,size//5)
    sh = max(2,size//6)
    for i in range(3):
        mx = x-size//3+i*(size//3)
        _rect(surface,c,mx,y,sw,sh,width=1)
    _line(surface,c,x,y,0,-r,0,-int(r*0.35),1)
    _line(surface,c,x,y,-size//5,-r+2,size//5,-r+2)
def draw_backup_control_center(surface,x,y,size):
    c = (60,120,160)
    r=size//2
    _rect(surface,c,x,y+size//8,size,int(size*0.6),width=2)
    sw = max(3,size//3)
    sh=max(2,size//6)
    _rect(surface,c,x,y,sw,sh,width=1)
    _circle(surface,(255,180,40),x+size//3,y-size//5,max(2,size//8))
    _line(surface,c,x,y,0,-r,0,-int(r*0.5),1)

def draw_icons(surface, node,x, y, size):
    subtype = node.get('subtype','')
    t = node.get('type','')

    if 'nuclear' in subtype: draw_nuclear(surface,x,y,size)
    elif 'pumped_hydro' in subtype: draw_pumped_hydro(surface, x, y, size)
    elif 'hydro' in subtype: draw_hydro(surface,x,y,size)
    elif 'wind' in subtype: draw_wind(surface,x,y,size)
    elif 'solar' in subtype: draw_solar(surface,x,y,size)
    elif 'combined_cycle' in subtype: draw_gas_ccgt(surface,x,y,size)
    elif 'open_cycle' in subtype: draw_gas_peaker(surface,x,y,size)
    elif 'biomass' in subtype: draw_biomass(surface,x,y,size)
    elif 'battery' in subtype: draw_battery(surface, x, y, size//2)
    elif 'EMS_SCADA' == t:draw_control_center(surface, x, y, size)
    elif 'backup_EMS' ==t:draw_backup_control_center(surface,x,y,size)
    elif 'load_nodes' in t:draw_load(surface, x, y, size//1.5, node)
    else: draw_substation(surface, x,y,size//1.5)
