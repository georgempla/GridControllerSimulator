from heapq import merge

import pygame
import math

HUD_BG = (15,20,30,200)
HUD_BORDER = (60,80,100)
HUD_TEXT = (220,220,220)
HUD_DIM = (100,120,140)
SURPLUS_COL = (80,200,120)
DEFICIT_COL = (255, 80 ,50)
NEUTRAL_COL = (60, 80, 100)

FREQ_THRESHOLDS = [
    (60.2, 'normal', (80,200,120), None),
    (59.8, 'normal', (80,200,120), None),
    (59.5, 'warning', (255,200,50), 'Amber - generation deficiency'),
    (59.2, 'alert', (255,120,30), 'Red - dispatch generation now'),
    (58.8, 'emergency', (255,60,40), 'UFLS Stage 1 - shed class 3 loads'),
    (58.4, 'severe', (255,30,30), 'UFLS Stage 2 - shed class 2 loads'),
    (-1, 'collapse', (200,0,200), 'GRID COLLAPSE IMMINENT')
]

FREQ_STATUS_LABELS = {
    'normal': 'NOMINAL',
    'warning': 'WARNING',
    'alert': 'ALERT',
    'emergency': 'EMERGENCY',
    'severe': 'SEVERE EMERGENCY',
    'collapse': 'GRID COLLAPSE'
}

def wrap_value(text, max_width, font):
    if font.size(text)[0]<=max_width:
        return [text]
    words = text.replace("/", "/ ").split(" ")
    lines = []
    current = ''
    for word in words:
        test = (current+" "+word).strip()
        if font.size(test)[0] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines if lines else [text]
def get_freq_state(hz):
    if hz > 60.2:
        return ('warning', (255,200,50), 'High frequency - excess generation')
    for threshold, status, colour, alarm in FREQ_THRESHOLDS:
        if hz > threshold:
            return (status, colour, alarm)

def get_freq_alarms(hz):
    status,col,alarm_text = get_freq_state(hz)
    if status == 'normal' or alarm_text is None:
        return []
    severity_map = {
        'warning':'warning',
        'alert': 'warning',
        'emergency': 'critical',
        'severe':'critical',
        'collapse':'critical'
    }
    return [{
        'text': alarm_text,
        'severity': severity_map.get(status,'info'),
        'source': 'frequency'
    }]

def _panel (surface, x,y,w,h):
    bg = pygame.Surface((w,h), pygame.SRCALPHA)
    bg.fill(HUD_BG)

    surface.blit(bg, (x,y))
    pygame.draw.rect(surface,HUD_BORDER,pygame.Rect(x,y,w,h),1)

def draw_frequency_gauge(surface, fonts, hz, screen_w, tick=0):
    W,H = 200,120
    cx = screen_w//2
    x = cx - W//2
    y = 10

    status, col, alarm_text = get_freq_state(hz)

    if status in ('emergency', 'severe', 'collapse'):
        flash_alpha = 120 + int(80 * math.sin(tick * 0.2))
        bg = pygame.Surface((W, H), pygame.SRCALPHA)
        bg.fill((80,0,0, flash_alpha))
        surface.blit(bg, (x,y))

    _panel(surface, x,y, W,H)
    pygame.draw.rect(surface,col, pygame.Rect(x,y,W,H), 1)
    title = fonts['tiny'].render("GRID FREQUENCY",True,HUD_DIM)
    surface.blit(title, (cx - title.get_width() // 2, y+5))

    arc_cx = cx
    arc_cy = y + H - 36
    radius = 55
    ARC_START = 210
    ARC_END = 330
    arc_range = ARC_END - ARC_START
    freq_min = 58.0
    freq_max = 62.0

    BAND_COLOURS = [
        (60.2,62.0,(255,200,50)),
        (59.8, 60.2, (80,200,120)),
        (59.5, 59.8, (255,200,50)),
        (59.2, 59.5, (255,120,40)),
        (58.8, 59.2, (255,60,40)),
        (58.4,58.8, (255,30,30)),
        (58.0,58.4, (200, 0, 200)),
    ]
    for band_min, band_max, band_col in BAND_COLOURS:
        pts = []
        start_t = (max(band_min, freq_min)-freq_min)/(freq_max-freq_min)
        end_t = (min(band_max, freq_max)-freq_min)/(freq_max-freq_min)
        for t in range(int(start_t*100), int(end_t*100)+ 1):
            deg = ARC_START + (t/100) * arc_range
            rad = math.radians(deg)
            pts.append(
                (
                    arc_cx+radius * math.cos((rad)),
                    arc_cy + radius * math.sin(rad)
                )
            )
        if len(pts) >=2:
            pygame.draw.lines(surface,band_col,False,pts,6)

        ticks = {58.0:8,58.5:8,59.0:8, 59.5:5, 60.0:10, 60.5:5, 61.0:8, 61.5:8,62:8}
        for freq_val, tick_len in ticks.items():
            t = (freq_val -freq_min)/(freq_max-freq_min)
            deg = ARC_START + t * arc_range
            rad = math.radians(deg)
            ox = arc_cx + radius * math.cos(rad)
            oy = arc_cy + radius * math.sin(rad)
            ix = arc_cx +(radius-tick_len)*math.cos(rad)
            iy = arc_cy +(radius-tick_len)*math.sin(rad)
            pygame.draw.line(surface, HUD_DIM, (int(ox), int(oy)), (int(ix), int(iy)), 2)

        hz_clamped = max(freq_min, min(freq_max, hz))
        t = (hz_clamped - freq_min)/(freq_max-freq_min)
        needle_deg = ARC_START + t*arc_range
        needle_rad = math.radians(needle_deg)
        tip_x = arc_cx + (radius-6) * math.cos(needle_rad)
        tip_y = arc_cy + (radius-6) * math.sin(needle_rad)
        pygame.draw.line(surface,col,(arc_cx,arc_cy),(int(tip_x),int(tip_y)), 2)
        pygame.draw.circle(surface,col,(arc_cx,arc_cy), 4)

        dig_surf = fonts['med_bold'].render(f"{hz:.3f} Hz", True,col)
        surface.blit(dig_surf, (cx-dig_surf.get_width() // 2, y+H - 30))

        status_text = FREQ_STATUS_LABELS.get(status, '')

        if status in ('emergency', 'severe', 'collapse'):
            if (tick//15)%2 == 0:
                st_surf = fonts['small_bold'].render(status_text, True,col)
                surface.blit(st_surf, (cx-st_surf.get_width()//2, y+H-16))
        else:
            st_surf = fonts['small_bold'].render(status_text,True,col)
            surface.blit(st_surf,(cx-st_surf.get_width()//2, y+H-16))

GRACE = 10
def draw_gen_load_bat(surface, fonts, gen_mw, load_mw,screen_w, screen_h):
    W,H = 400,54
    x = screen_w//2 - W//2
    y = screen_h-H-10
    _panel(surface,x,y,W,H)

    title = fonts['tiny'].render('GENERATION VS LOAD', True, HUD_DIM)
    surface.blit(title, (x+W//2 - title.get_width()//2, y +5))

    bar_x = x+10
    bar_y = y+20
    bar_w = W-20
    bar_h = 16
    centere = bar_x+bar_w//2

    pygame.draw.rect(surface, (30,35,45), pygame.Rect(bar_x,bar_y,bar_w,bar_h))

    max_mw = 500
    delta = gen_mw-load_mw
    half = bar_w//2
    fill_px = int(abs(delta)/max_mw*half)
    fill_px= min(fill_px,half)

    if abs(delta)<GRACE:
        delta = 0
        gen_mw = load_mw
    if delta>0:
        col = SURPLUS_COL
        pygame.draw.rect(surface,col,pygame.Rect(centere-fill_px,bar_y,fill_px,bar_h))
    elif delta<0:
        col = DEFICIT_COL
        pygame.draw.rect(surface,col,pygame.Rect(centere,bar_y,fill_px,bar_h))

    pygame.draw.line(surface,HUD_TEXT,(centere,bar_y-2), (centere,bar_y+bar_h+2),2)
    gen_lbl = fonts['small'].render(f"GEN {gen_mw:.0f} MW", True,SURPLUS_COL)
    load_lbl = fonts['small'].render(f"{load_mw:.0f} MW LOAD", True,DEFICIT_COL)
    surface.blit(gen_lbl,(bar_x,bar_y+bar_h+4))
    surface.blit(load_lbl, (bar_x+bar_w-load_lbl.get_width(), bar_y+bar_h+4))

    sign = '+' if delta >=0 else ''
    delta_col = SURPLUS_COL if delta>=0 else DEFICIT_COL
    delta_lbl = fonts['small_bold'].render(f"{sign}{delta:.0f} MW", True, delta_col)
    surface.blit(delta_lbl,(centere-delta_lbl.get_width()//2,bar_y+bar_h+4))

SPEED_STEPS = [1,5,30,60]
def draw_status_panel(surface,fonts,game_state,time_multiplier=1.0):
    W,H = 200,150
    x,y = 10,10
    _panel(surface,x,y,W,H)

    season_col = {
        'winter': (150,200,255),
        'spring': (150,255,150),
        'summer': (255,230,100),
        'autumn': (255,160,80),
    }

    hour = game_state.get('hour', 0)
    am_pm = 'AM' if hour<12 else 'PM'
    hour_12 = hour%12 or 12
    season = game_state.get('season','winter').capitalize()
    s_col = season_col.get(season.lower(), HUD_TEXT)
    rows = [
        ('Time', f"{hour_12:02d}:{int(game_state.get('minute')):02d} {am_pm}", HUD_TEXT),
        ('Season', season,s_col),
        ('Day', f"{game_state.get("day", 1)}", HUD_TEXT),
        ('Online', f"{game_state.get("gen_online", 0)} / {game_state.get('gen_total', 0)} units", HUD_TEXT),
        ('Capacity', f"{game_state.get("total_capacity_mw", 0):.0f} MW", HUD_TEXT)
    ]
    for i, (label,value,col) in enumerate(rows):
        ry = y+12+i*17
        surface.blit(fonts['tiny'].render(label,True,HUD_DIM),(x+8,ry))
        surface.blit(fonts['small'].render(value,True,col),(x+90,ry))
        
    score = game_state.get('score',0)
    score_col = (255,210,50)
    pygame.draw.line(surface,HUD_BORDER,(x,y+98),(x+W,y+98),1)
    surface.blit(fonts['tiny'].render('SCORE',True,HUD_DIM), (x+8,y+102))
    score_surf = fonts['small_bold'].render(f"{score:,}", True, score_col)
    surface.blit(score_surf,(x+W-score_surf.get_width()-8,y+102))
        
    pygame.draw.line(surface,HUD_BORDER,(x,y+114),(x+W,y+114),1)
    surface.blit(fonts['tiny'].render('SIM SPEED', True, HUD_DIM),(x+8,y+118))
    
    btn_w=38
    btn_h=16
    btn_y = y+131
    speed_rects = {}
    for i, speed in enumerate(SPEED_STEPS):
        bx = x+4+i*(btn_w+3)
        rect=pygame.Rect(bx,btn_y,btn_w,btn_h)
        active = (time_multiplier == speed)
        bg_col = (40,80,140) if active else (25,35,50)
        brd_col = (100,160,220) if active else HUD_BORDER
        pygame.draw.rect(surface,bg_col,rect,border_radius=2)
        pygame.draw.rect(surface,brd_col,rect,1,border_radius=2)
        lbl_col=(220,220,220) if active else HUD_DIM
        lbl =fonts['tiny'].render(f"{speed}x", True, lbl_col)
        surface.blit(lbl,(rect.centerx-lbl.get_width()//2,
                          rect.centery-lbl.get_height()//2))
        speed_rects[speed] = rect
    return speed_rects

def wrap_value(text, max_width, font):
    if font.size(text)[0]<=max_width:
        return [text]
    words = text.replace("/", "/ ").split(" ")
    lines = []
    current = ''
    for word in words:
        test = (current+" "+word).strip()
        if font.size(test)[0] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines if lines else [text]
def draw_alarms_panel(surface,fonts, alarms,export_mw,screen_w):
    #text, severity(warning, critical,info)
    W = 220
    x = screen_w-W-10
    y=10

    alarm_font = fonts['tiny']
    text_max_w = W-30
    max_visible = 5

    visible_alarms = alarms[-max_visible:]
    wrapped_alarms = []
    for alarm in visible_alarms:
        lines = wrap_value(alarm.get('text',''), text_max_w,alarm_font)
        wrapped_alarms.append((alarm,lines))

    total_lines = sum(len(lines) for _,lines in wrapped_alarms)
    H = 34 + max(1,total_lines) * 16+8
    _panel(surface,x,y,W,H)



    sev_cols = {
        'info':(100,180,255),
        'warning':(255,200,50),
        'critical':(255,80,50)
    }
    title = fonts['tiny'].render('INTERCONNECT', True,HUD_DIM)
    surface.blit(title,(x+8,y+6))

    if export_mw>=0:
        flow_text = f"EXPORT {export_mw:.0f} MW"
        flow_col = (100,200,255)
    else:
        flow_text = f"IMPORT {abs(export_mw):.0f}"
        flow_col = (255,160,80)

    flow_surd = fonts['small_bold'].render(flow_text,True,flow_col)
    surface.blit(flow_surd, (x+W-flow_surd.get_width()-8,y+5))

    pygame.draw.line(surface,HUD_BORDER, (x,y+18),(x+W,y+18),1)

    alarm_title = fonts['tiny'].render("ACTIVE ALARMS", True, HUD_DIM)
    surface.blit(alarm_title, (x+8,y+22))

    clear_rect = pygame.Rect(x+W-42, y +20,36,13)
    mouse_pos = pygame.mouse.get_pos()
    clear_hovered = clear_rect.collidepoint(mouse_pos)
    clear_col = (80,60,60) if clear_hovered else(50,40,40)
    pygame.draw.rect(surface,clear_col,clear_rect,border_radius=2)
    pygame.draw.rect(surface,(120,60,60), clear_rect, 1,border_radius=2)
    clr_lbl = fonts['tiny'].render("CLEAR", True, (200,120,120))
    surface.blit(clr_lbl, (clear_rect.centerx- clr_lbl.get_width()//2, clear_rect.centery-clr_lbl.get_height()//2))
    pygame.draw.line(surface,HUD_BORDER,(x,y+34), (x+W, y +34), 1)

    if not alarms:
        no_alarms=fonts['small'].render("All systems nominal", True,(80,200,120))
        surface.blit(no_alarms, (x+8, y +40))
    else:
        ay = y+40
        for alarm,lines in wrapped_alarms:
            col = sev_cols.get(alarm.get('severity','info'), HUD_TEXT)
            pygame.draw.circle(surface,col,(x+12,ay+6),4)
            for i, line in enumerate(lines):
                surface.blit(alarm_font.render(line,True,col),(x+22,ay +i*16))
            ay += len(lines)*16+2
    return clear_rect

def build_hud_fonts():
    return {
        'tiny': pygame.font.SysFont('consolas',10),
        'small': pygame.font.SysFont('consolas', 11),
        'small_bold': pygame.font.SysFont('consolas',11,bold=True),
        'med_bold': pygame.font.SysFont('consolas',13,bold=True)
    }

def draw_hud(surface, fonts,data, screen_w, screen_h):
    freq_alarms = get_freq_alarms(data.get('hz',60.0))

    merged = [a for a in data.get('alarms') if a.get('source') != 'frequency']
    merged = freq_alarms + merged
    draw_frequency_gauge(surface,fonts,data.get("hz",60),screen_w,data.get("tick", 0))
    speed_rects = draw_status_panel(surface,fonts,data.get("game_state"),data.get("time_multiplier"))
    draw_gen_load_bat(surface,fonts,data.get("gen_mw"),data.get("load_mw"),screen_w,screen_h)
    clear_rect = draw_alarms_panel(surface,fonts,merged,data.get("export_mw"),screen_w)
    return {'clear_rect':clear_rect,'speed_rects':speed_rects}
