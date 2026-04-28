import pygame,math,json,os,sys

BG_DARK = (6,8,14)
BG_PANEL = (12,16,26)
BORDER = (40,55,75)
TEXT = (220,220,220)
DIM = (70,85,100)
GOLD = (255,210,50)
AVAILABLE=(30,60,100)
AVAIL_HOV= (45, 85, 140)
AVAIL_BRD = (80, 130, 200)
LOCKED = (18, 22, 30)
LOCK_BRD = (35, 42, 52)
LOCK_TEXT = (50, 62, 74)
GREEN= (30, 110, 50)
GREEN_HOV= (45, 160, 70)
RED = (110, 25, 25)
RED_HOV= (160, 35, 35)
ACCENT = (60, 130, 200)

CARD_H = 72
CARD_GAP = 8
SCROLL_STEP = 40

def _draw_grid(surface,w,h,spacing=48):
    s = pygame.Surface((w,h),pygame.SRCALPHA)
    for x in range(0,w,spacing):
        pygame.draw.line(s,(255,255,255,6),(x,0),(x,h))
    for y in range(0,h,spacing):
        pygame.draw.line(s,(255,255,255,6),(0,y),(w,y))
    surface.blit(s,(0,0))
def _panel(surface,rect,border_col=BORDER):
    bg = pygame.Surface((rect.w,rect.h),pygame.SRCALPHA)
    bg.fill((10,14,24,220))
    surface.blit(bg,rect.topleft)
    pygame.draw.rect(surface,border_col,rect,1,border_radius=4)

def _btn(surface,rect,label,font,hovered,col_n=AVAILABLE,col_h=AVAIL_HOV,brd=AVAIL_BRD):
    pygame.draw.rect(surface,col_h if hovered else col_n,rect,border_radius=4)
    pygame.draw.rect(surface,brd,rect,1,border_radius=4)
    lbl = font.render(label,True,TEXT)
    surface.blit(lbl,(rect.centerx-lbl.get_width()//2,rect.centery-lbl.get_height()//2))
def _scan_maps_folder(maps_dir):
    results = []
    if not os.path.isdir(maps_dir):
        return results
    for fname in sorted(os.listdir(maps_dir)):
        if not fname.endswith('.json'):
            continue
        fpath = os.path.join(maps_dir,fname)
        meta = _read_map_metadata(fname)
        meta['path'] = fpath
        meta['filename'] = fname
        results.append(meta)
    return results
def resource_path(relative):
    if getattr(sys, '_MEIPASS', None):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, relative)
def _read_map_metadata(path):
    try:
        if "maps" not in path and not os.path.isabs(path):
            path = resource_path("maps/"+path)
        with open(path,'r') as f:
            data = json.load(f)
        map_data = data.get('map_metadata',{})
        return {
            'name':map_data.get('name',os.path.basename(path)),
            'city':map_data.get('city','N/A'),
            'state':map_data.get('state','N/A'),
            'capacity':map_data.get('total_installed_capacity_mw','N/A'),
            'peak':map_data.get('peak_demand_mw','N/A'),
            'climate': map_data.get('climate','N/A'),
            'version':map_data.get('version','N/A'),
            'valid':True,
        }
    except Exception as e:
        print(e)
        return {
            'name':os.path.basename(path),
            'city':'N/A',
            'state':'N/A',
            'capacity':'N/A',
            'peak':'N/A',
            'climate':'N/A',
            'version':'N/A',
            'valid':False,
        }




class PathInputBox:
    ALLOWED = set(
        'qwertyuioplkjhgfdsazxcvbnmMNBVCXZLKJHGFDSAPOIUYTREWQ'
        '0123456789 ._-/\\:(){}[]~'
    )
    def __init__(self,rect,font,placeholder='Paste or type of path...'):
        self.rect = rect
        self.font = font
        self.placeholder = placeholder
        self.text = ''
        self.active = False
        self.error = ''
        self.valid_path=None
        self._cursor_vis = True
        self._cursor_t = 0
    def validate(self):
        self.error = ''
        self.valid_path = None
        p = self.text.strip()
        if not p:
            self.error = 'Path is empty'
            return False
        if not os.path.isfile(p):
            self.error = 'File not found'
        if not p.endswith('.json'):
            self.error = 'Must be a .json file'
        meta = _read_map_metadata(p)
        if not meta['valid']:
            self.error = 'JSON could not be parsed'
            return False
        self.valid_path = p
        return True
    def handle_event(self,event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button==1:
            self.active = self.rect.collidepoint(event.pos)
            self.error = ''
        if not self.active:
            return False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
                return True
            if event.key == pygame.K_RETURN:
                return 'submit'
            if event.key == pygame.K_ESCAPE:
                self.active= False
                return True
            if event.key == pygame.K_v and (pygame.key.get_mods() & pygame.KMOD_CTRL):
                try:
                    pasted = pygame.scrap.get(pygame.SCRAP_TEXT)
                    if pasted:
                        text = pasted.decode('utf-8',errors='ignore').replace('\x00','').strip()
                        self.text += text
                except Exception as e:
                    print(e)
                    pass
                return True
            if event.unicode in self.ALLOWED:
                self.text += event.unicode
                return True
        return False
    def draw(self,surface,tick):
        brd = (255,80,80) if self.error else (AVAIL_BRD if self.active else BORDER)
        pygame.draw.rect(surface,(14,20,32),self.rect,border_radius=3)
        pygame.draw.rect(surface,brd,self.rect,1,border_radius=3)
        display = self.text if self.text else self.placeholder
        col = TEXT if self.text else (60,80,100)
        max_w = self.rect.w-10
        surf = self.font.render(display,True,col)
        if surf.get_width()>max_w:
            while surf.get_width()>max_w and len(display)>0:
                display = display[1:]
                surf = self.font.render('...'+display,True,col)
        surface.blit(surf,(self.rect.x+5,self.rect.centery-surf.get_height()//2))
        if self.active and (tick//30)%2==0:
            cx = self.rect.x+5+surf.get_width()+2
            pygame.draw.line(surface,TEXT,(cx,self.rect.y+4),(cx,self.rect.bottom-4),1)
        if self.error:
            error_font = pygame.font.SysFont('consolas',10)
            error_label = error_font.render(self.error,True,(220,80,80))
            surface.blit(error_label,(self.rect.x,self.rect.bottom+3))

class MapCard:
    def __init__(self,meta,x,y,w,fonts):
        self.meta = meta
        self.rect = pygame.Rect(x,y,w,CARD_H)
        self.selected = False
        self.hovered = False
        self.fonts = fonts
    def collide(self,pos):
        return self.rect.collidepoint(pos)
    def draw(self,surface):
        self.hovered = self.rect.collidepoint(pygame.mouse.get_pos())
        valid = self.meta['valid']

        if self.selected:
            bg,brd = (20,55,100),AVAIL_BRD
        elif self.hovered and valid:
            bg,brd = AVAIL_HOV,AVAIL_BRD
        elif not valid:
            bg,brd = LOCKED,LOCK_BRD
        else:
            bg,brd = AVAILABLE,AVAIL_BRD

        pygame.draw.rect(surface,bg,self.rect,border_radius=5)
        pygame.draw.rect(surface,brd,self.rect,1,border_radius=5)

        bar_col = GOLD if self.selected else (brd if valid else LOCK_BRD)
        pygame.draw.rect(surface,bar_col,pygame.Rect(self.rect.x+4,self.rect.y+8,3,CARD_H-16),border_radius=2)

        name_col = TEXT if valid else LOCK_TEXT
        dim_col = DIM if valid else LOCK_TEXT
        item_font = self.fonts['item']
        desc_font = self.fonts['desc']
        tag_font = self.fonts['tag']

        name_label = item_font.render(self.meta['name'],True,name_col)
        surface.blit(name_label,(self.rect.x+16,self.rect.y+10))
        location = f"{self.meta['city']}, {self.meta['state']}"
        location_label = desc_font.render(location,True,dim_col)
        surface.blit(location_label,(self.rect.x+16,self.rect.y+30))
        cap = f"{self.meta['capacity']} MW installed - {self.meta['peak']} MW peak"
        cap_label = desc_font.render(cap,True,dim_col)
        surface.blit(cap_label,(self.rect.x+15,self.rect.y+46))
        rx = self.rect.right-10
        ver_label = tag_font.render(f"v{self.meta['version']}",True,(90,130,180) if valid else LOCK_TEXT)
        surface.blit(ver_label,(rx-ver_label.get_width(),self.rect.y+10))

        climate_col={
            'subarctic':(120,200,255),
            'arctic':(160,220,255),
            'temperate':(120,200,130),
        }.get(self.meta['climate'],(130,130,130))
        climate_label = tag_font.render(self.meta['climate'].upper(),True,climate_col if valid else LOCK_TEXT)
        surface.blit(climate_label,(rx-climate_label.get_width(),self.rect.y+28))
        if not valid:
            invalid_label = tag_font.render("INVALID JSON",True,(180,60,60))
            surface.blit(invalid_label,(rx-invalid_label.get_width(),self.rect.y+CARD_H-invalid_label.get_height()-8))
        elif self.selected:
            selected_label = tag_font.render("SELECTED",True,GOLD)
            surface.blit(selected_label,(rx-selected_label.get_width(),self.rect.y+CARD_H-selected_label.get_height()-8))

class CustomMapMenu:
    TABS = ['BUILTIN MAPS','EXTERNAL FILE','MAP CREATOR']

    def __init__(self,screen_w,screen_h,maps_dir='maps'):
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.maps_dir=maps_dir
        self.tick = 0
        self.tab = 0
        self.scroll_y=0
        self._max_scroll=0
        self.selected_builtin = None
        self.selected_ext_path = None
        self.vr = pygame.Rect(0,0,0,0)
        self._launch_builder = False

        self.fonts = {
            'title':pygame.font.SysFont('consolas',36,bold=True),
            'sub':pygame.font.SysFont('consolas',13),
            'label':pygame.font.SysFont('consolas',16,bold=True),
            'item': pygame.font.SysFont('consolas',13,bold=True),
            'desc':pygame.font.SysFont('consolas',11),
            'tag':pygame.font.SysFont('consolas',10,bold=True),
            'small':pygame.font.SysFont('consolas',11),
            'body':pygame.font.SysFont('consolas',12),
        }
        self._layout()
        self._load_builtin_cards()
        ix=self.content_rect.x+12
        iy=self.content_rect.y+60
        iw=self.content_rect.w-24
        self.path_input = PathInputBox(
            pygame.Rect(ix,iy,iw,30),
            self.fonts['body']
        )
        self._ext_meta = None
        self._ext_valid = False

    def _layout(self):
        cx = self.screen_w//2
        pw,ph=720,520
        self.panel_rect = pygame.Rect(cx-pw//2,100,pw,ph)
        tab_y=self.panel_rect.y+36
        tab_h = 30
        tab_w = pw//len(self.TABS)
        self.tab_rects = [
            pygame.Rect(self.panel_rect.x + i*tab_w,tab_y,tab_w,tab_h)
            for i in range(len(self.TABS))
        ]
        cont_y = tab_y +tab_h+4
        cont_h = self.panel_rect.bottom-cont_y-52
        self.content_rect = pygame.Rect(
            self.panel_rect.x+8,cont_y,
            pw-16,cont_h
        )
        by = self.panel_rect.bottom-42
        bw,bh=160,32
        self.back_rect = pygame.Rect(self.panel_rect.x+12,by,bw,bh)
        self.load_rect = pygame.Rect(self.panel_rect.right-bw-12,by,bw,bh)
        self.hint_rect = pygame.Rect(self.panel_rect.x+bw+24,by+8,self.panel_rect.w-2*bw-48,bh-16)

    def _load_builtin_cards(self):
        maps = _scan_maps_folder(self.maps_dir)
        cw = self.content_rect.w-8
        cx = 4
        self.cards: list[MapCard] = []
        for i,meta in enumerate(maps):
            y = i*(CARD_H+CARD_GAP)
            self.cards.append(MapCard(meta,cx,y,cw,self.fonts))
        total_h = max(self.content_rect.h,len(self.cards)*(CARD_H+CARD_GAP))
        self._max_scroll = max(0,total_h-self.content_rect.h)
        self._cards_surf = pygame.Surface(
            (self.content_rect.w,total_h),pygame.SRCALPHA
        )

    def handle_event(self,event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button==1:
            pos = event.pos
            if self.back_rect.collidepoint(pos):
                return 'back'
            if self.load_rect.collidepoint(pos):
                result = self._try_confirm()
                if result:
                    return ('load',result)
            for i,tr in enumerate(self.tab_rects):
                if tr.collidepoint(pos):
                    self.tab = i
                    self.scroll_y = 0
                    return None
            if self.tab == 0:
                cy_off = pos[1]-self.content_rect.y+self.scroll_y
                cx_off = pos[0]-self.content_rect.x
                for card in self.cards:
                    cr = pygame.Rect(card.rect.x,card.rect.y,card.rect.w,card.rect.h)
                    if cr.collidepoint(cx_off,cy_off) and card.meta['valid']:
                        for c in self.cards:
                            c.selected = False
                        card.selected = True
                        self.selected_builtin = card
                        return None
            if self.tab == 1:
                self.path_input.handle_event(event)
                if self.vr.collidepoint(event.pos):
                    self._validate_external()
                return None
            if self.tab == 2:
                if hasattr(self,'_builder_launch_rect') and self._builder_launch_rect.collidepoint(pos):
                    return 'open_builder'
        if self.tab == 0:
            if event.type == pygame.MOUSEWHEEL and self.content_rect.collidepoint(pygame.mouse.get_pos()):
                self.scroll_y = max(0,min(self._max_scroll, self.scroll_y - event.y*SCROLL_STEP))
        if self.tab ==1:
            result = self.path_input.handle_event(event)
            if result == 'submit':
                self._validate_external()
        return None
    def _validate_external(self):
        ok = self.path_input.validate()
        if ok:
            self._ext_valid = True
            self._ext_meta = _read_map_metadata(self.path_input.valid_path)
        else:
            self._ext_valid = False
            self._ext_meta = None
    def _try_confirm(self):
        if self.tab == 0 and self.selected_builtin:
            return self.selected_builtin.meta['path']
        if self.tab == 1:
            self._validate_external()
            if self._ext_valid:
                return self.path_input.valid_path
        return None
    def draw(self,surface):
        self.tick +=1
        cx = self.screen_w//2
        mouse = pygame.mouse.get_pos()
        surface.fill(BG_DARK)
        _draw_grid(surface,self.screen_w,self.screen_h)
        title = self.fonts['title'].render("CUSTOM MAP SUPPORT",True,TEXT)
        surface.blit(title,(cx-title.get_width()//2,28))
        pulse = 0.6 + 0.4 * abs(math.sin(self.tick*0.025))
        sub_col = tuple(int(c*pulse) for c in (100,140,180))
        sub = self.fonts['sub'].render("Load a grid, browse your files, or build one from scratch",True,sub_col)
        surface.blit(sub,(cx-sub.get_width()//2,72))
        _panel(surface,self.panel_rect,BORDER)
        pygame.draw.rect(surface,ACCENT,pygame.Rect(self.panel_rect.x,self.panel_rect.y+12,3,self.panel_rect.h-24),border_radius=2)
        pygame.draw.line(surface,BORDER,(self.panel_rect.x,self.panel_rect.y+32),(self.panel_rect.right,self.panel_rect.y+32),1)
        self._draw_tabs(surface,mouse)
        tab_bottom = self.tab_rects[0].bottom
        pygame.draw.line(surface,BORDER,(self.panel_rect.x,tab_bottom+2),(self.panel_rect.right,tab_bottom+2),1)
        old_clip = surface.get_clip()
        surface.set_clip(self.content_rect)
        if self.tab == 0: self._draw_builtin_tab(surface)
        elif self.tab==1: self._draw_external_tab(surface,mouse)
        elif self.tab==2: self._draw_creator_tab(surface)
        surface.set_clip(old_clip)
        if self.tab == 0 and self._max_scroll>0:
            self._draw_scrollbar(surface)
        pygame.draw.line(surface,BORDER,(self.panel_rect.x,self.load_rect.y-8),(self.panel_rect.right,self.load_rect.y-8),1)
        _btn(surface,self.back_rect, "BACK",self.fonts['small'],self.back_rect.collidepoint(mouse),col_n=(25,38,60),col_h=(40,62,100))
        can_load = self._can_load()
        load_col_n = GREEN if can_load else LOCKED
        load_col_h = GREEN_HOV if can_load else LOCKED
        load_brd = (60,180,80) if can_load else LOCK_BRD
        _btn(surface,self.load_rect,"LOAD MAP",self.fonts['small'],self.load_rect.collidepoint(mouse) and can_load, col_n=load_col_n,col_h=load_col_h,brd=load_brd)
        hint = self._hint_text()
        if hint:
            hint_label = self.fonts['desc'].render(hint,True,DIM)
            surface.blit(hint_label,(cx-hint_label.get_width()//2,self.load_rect.centery-hint_label.get_height()//2))
    def _can_load(self):
        if self.tab == 0:
            return self.selected_builtin is not None
        if self.tab == 1:
            return self._ext_valid
        return False
    def _hint_text(self):
        if self.tab == 0:
            if self.selected_builtin:
                return f"Selected: {self.selected_builtin.meta['name']}"
            return 'Select a map above to enable loading'
        if self.tab == 1:
            if self._ext_valid and self._ext_meta:
                return f"Valid map: {self._ext_valid}"
            return "Enter a file path and press Enter to validate"
        return "Map Creator now available"
    def _draw_tabs(self,surface,mouse):
        for i,(tr,label) in enumerate(zip(self.tab_rects,self.TABS)):
            active = (i==self.tab)
            hovered = tr.collidepoint(mouse) and not active
            bg = (20,45,85) if active else (AVAIL_HOV if hovered else BG_PANEL)
            brd = AVAIL_BRD if active else BORDER
            pygame.draw.rect(surface,bg,tr,border_radius=3)
            pygame.draw.rect(surface,brd,tr,1,border_radius=3)
            if active:
                pygame.draw.rect(surface,AVAIL_BRD,pygame.Rect(tr.x+4,tr.bottom-2,tr.w-8,2))
            col = TEXT if active else (DIM if not hovered else TEXT)
            lbl = self.fonts['tag'].render(label,True,col)
            surface.blit(lbl,(tr.centerx-lbl.get_width()//2,tr.centery-lbl.get_height()//2))
    def _draw_builtin_tab(self,surface):
        self._cards_surf.fill((0,0,0,0))
        for card in self.cards:
            card.draw(self._cards_surf)
        surface.blit(self._cards_surf,(self.content_rect.x,self.content_rect.y-self.scroll_y))
        if not self.cards:
            msg = self.fonts['body'].render(f'No .json files found in "{self.maps_dir}/"',True,DIM)
            surface.blit(msg,(self.content_rect.centerx-msg.get_width()//2,self.content_rect.y+40))
    def _draw_external_tab(self,surface,mouse):
        cr=self.content_rect
        f = self.fonts
        lines = [
            "Paste the full path to any compatible grid JSON file.",
            "The file must contain a map_metadata block.",
            "Press Enter to validate, the click LOAD MAP"
        ]
        ty = cr.y +14
        for line in lines:
            s = f['desc'].render(line,True,DIM)
            surface.blit(s,(cr.x+12,ty))
            ty += 16
        self.path_input.draw(surface,self.tick)
        self.vr = pygame.Rect(
            self.path_input.rect.right-90,
            self.path_input.rect.y,
            88,30
        )
        _btn(surface,self.vr,"VALIDATE",f['small'],
             self.vr.collidepoint(mouse),col_n=(30,60,110),col_h=(45,85,150))
        if self._ext_meta:
            ry = self.path_input.rect.bottom+24
            rr = pygame.Rect(cr.x+12,ry,cr.w-24,110)
            brd_col = (60,180,80) if self._ext_valid else (180,60,60)
            _panel(surface,rr,brd_col)
            pygame.draw.rect(surface,brd_col,pygame.Rect(rr.x,rr.y+6,3,rr.h-12),border_radius=2)
            rows = [
                ('Map name', self._ext_meta['name']),
                ('City', f"{self._ext_meta['city']}, {self._ext_meta['state']}"),
                ('Capacity', f"{self._ext_meta['capacity']} MW installed"),
                ('Peak load', f"{self._ext_meta['peak']} MW"),
                ('Climate', self._ext_meta['climate']),
                ('Version', self._ext_meta['version']),
            ]
            iy = rr.y+8
            for label,val in rows:
                ls = f['tag'].render(label,True,DIM)
                vs = f['desc'].render(val,True,TEXT)
                surface.blit(ls,(rr.x+10,iy))
                surface.blit(vs,(rr.x+110,iy))
                iy+=16
        elif self.path_input.error:
            ry = self.path_input.rect.bottom+28
            err = f['body'].render(f"{self.path_input.error}",True,(220,80,80))
            surface.blit(err,(cr.x+12,ry))
    def _draw_creator_tab(self,surface):
        cr = self.content_rect
        f = self.fonts
        s = pygame.Surface((cr.w,cr.h),pygame.SRCALPHA)
        cell = 32
        for gx in range(0,cr.w,cell):
            for gy in range(0,cr.h,cell):
                pygame.draw.rect(s,(40,60,90,60),
                                 pygame.Rect(gx+1,gy+1,cell-2,cell-2),
                                 border_radius=3)
        surface.blit(s,(cr.x,cr.y))
        lcx,lcy = cr.centerx,cr.centery-120
        """pygame.draw.rect(surface,(30,45,70),
                         pygame.Rect(lcx-22,lcy-4,44,32),
                         border_radius=4)
        pygame.draw.rect(surface,BORDER,
                         pygame.Rect(lcx-22,lcy-4,44,32),
                         1,border_radius=4)"""
        """ pygame.draw.arc(surface,BORDER,
                        pygame.Rect(lcx-14,lcy-22,28,28),
                        math.radians(0),math.radians(180),3)
        pygame.draw.circle(surface,AVAIL_BRD,(lcx,lcy+10),5)
        pygame.draw.rect(surface,AVAIL_BRD,
                         pygame.Rect(lcx-1,lcy+10,3,7))"""

        heading = f['label'].render("Map Creator",True,TEXT)
        surface.blit(heading,(cr.centerx-heading.get_width()//2,lcy+42))
        sub_lines = [
            "Design your own grid topology with a visual node editor.",
            "Place generators, substations, loads and draw transmission lines.",
            "Export as JSON and load immediately or share with the community"
        ]
        ty = lcy+68
        for line in sub_lines:
            ls= f['desc'].render(line,True,DIM)
            surface.blit(ls,(cr.centerx-ls.get_width()//2,ty))
            ty+=18
        pulse =0.5+0.5*abs(math.sin(self.tick*0.03))
        tag_col = tuple(int(c*pulse) for c in GOLD)
        tag_s = f['tag'].render("NOW AVAILABLE",True,tag_col)
        tr_rect = pygame.Rect(cr.centerx-tag_s.get_width()//2-8,
                              ty+6,
                              tag_s.get_width()+16,tag_s.get_height()+8)
        pygame.draw.rect(surface,(40,30,5),tr_rect,border_radius=3)
        pygame.draw.rect(surface,GOLD,tr_rect,1,border_radius=3)
        bw, bh = 160, 34
        launch_rect = pygame.Rect(cr.centerx - bw // 2, tr_rect.bottom+16,bw,bh)
        self._builder_launch_rect = launch_rect
        hovered = launch_rect.collidepoint(pygame.mouse.get_pos())
        _btn(surface,launch_rect, "LAUNCH BUILDER",self.fonts['small'],hovered,col_n=(30,80,40),col_h=(45,120,60),brd=(60,180,80))

        surface.blit(tag_s,(tr_rect.x+8,tr_rect.y+4))
    def _draw_scrollbar(self,surface):
        vp = self.content_rect
        sw = 4
        sx = vp.right-sw-2
        sh = vp.height
        frac = vp.height/(vp.height+self._max_scroll)
        thumb_h = max(20,int(sh*frac))
        thumb_y = vp.y + int((sh-thumb_h)*(self.scroll_y/self._max_scroll))
        pygame.draw.rect(surface,BORDER,(sx,vp.y,sw,sh),border_radius=2)
        pygame.draw.rect(surface,AVAIL_BRD,(sx,thumb_y,sw,thumb_h),border_radius=2)
