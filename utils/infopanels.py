
import pygame
from pygame.draw import lines


def calculate_panel_pos(node_sx,node_sy, panel_w,panel_h, screen_w,screen_h, margin=12):
    x = node_sx + margin
    if x +panel_w > screen_w:
        x = node_sx - panel_w - margin

    y = node_sy
    if y+panel_h > screen_h:
        y = screen_h - panel_h - margin

    return max(0,x), max(0,y)
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

class Button:
    def __init__(self,label,x,y,w,h,color,callback):
        self.label = label
        self.rect = pygame.Rect(x,y,w,h)
        self.color =color
        self.callback = callback
        self.hovered = False
    def handle_event(self,event):
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        if (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.rect.collidepoint(event.pos)):
            self.callback()
            return True
        return False
    def draw(self,surface,font):
        col = tuple(min(255,c+40) for c in self.color) if self.hovered else self.color
        pygame.draw.rect(surface,col,self.rect,1,border_radius=3)
        lbl = font.render(self.label,True,(220,220,220))
        surface.blit(lbl,(self.rect.centerx-lbl.get_width()//2,self.rect.centery-lbl.get_height()//2))

class TextInput:
    ALLOWED = set('0123456789.-')
    def __init__(self,x,y,w,h,placeholder,callback,font):
        self.rect = pygame.Rect(x,y,w,h)
        self.placeholder = placeholder
        self.callback = callback
        self.font = font
        self.text = ''
        self.active = False
        self.error = False

    def handle_event(self,event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.active= self.rect.collidepoint(event.pos)
            self.error = False
            return self.active
        if not self.active:
            return False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                try:
                    self.callback(float(self.text))
                    self.text = ''
                    self.active = False
                except ValueError:
                    self.error = True
                return True
            elif event.key == pygame.K_BACKSPACE:
                self.text=self.text[:-1]
                return True
            elif event.unicode in self.ALLOWED:
                self.text += event.unicode
                return True
        return False
    def draw(self,surface):
        border = (255,80,80) if self.error\
            else (100,160,220) if self.active\
            else (60,80,100)
        pygame.draw.rect(surface,(20,28,40),self.rect,border_radius=3)
        pygame.draw.rect(surface,border,self.rect,1,border_radius=3)
        display = self.text if self.text else self.placeholder
        col = (220,220,220) if self.text else (80,100,120)
        txt = self.font.render(display,True,col)
        surface.blit(txt,(self.rect.x+5,self.rect.centery-txt.get_height()//2))

        if self.active and (pygame.time.get_ticks()//500)%2 == 0:
            cx = self.rect.x+5+txt.get_width()+1
            pygame.draw.line(surface,(220,220,220),(cx,self.rect.y+3),(cx,self.rect.bottom-3),1)

BTN_RED = (140,30,30)
BTN_GREEN = (30,110,50)
BTN_BLUE = (30,80,140)
BTN_ORANGE = (140,80,20)
BTN_DIM = (50,60,70)

class InfoPanel:
    PANEL_W = 250
    def __init__(self, node, sx,sy, screen_w, screen_h,font,bold_font,engine):
        self.font_bold = bold_font
        self.font = font
        if type(node) == dict:
            self.node = node
        else:
            self.node = {"name":node.name,"id":node.id}
        self.engine = engine
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.w = self.PANEL_W
        self.update_toggle = False

        self.buttons:list[Button] = []
        self.text_inputs:list[TextInput]=[]

        self.rows = self.build_rows(self.node)
        self._layout(sx,sy)

    def _layout(self,sx,sy):
        row_h = 24+len(self.rows)*18+8
        ctrl_h = self._controls_heights()
        self.h = row_h+ctrl_h
        self.x,self.y = calculate_panel_pos(sx,sy,self.w,self.h,self.screen_w,self.screen_h)
        self.rect = pygame.Rect(self.x,self.y,self.w,self.h)
        self._build_controls(self.x,self.y+row_h)

    def _controls_heights(self):
        t = self.node.get('type','')
        if t == 'generation_nodes':return 80
        if t == 'storage_nodes': return 64
        if t == 'load_nodes': return 44
        if t == 'hdvc': return 40
        if t == 'EMS_SCADA': return 38
        if t == '':return 30
        return 0


    def build_rows(self, node):
        raw = node.get('raw', {})
        t = node.get('type', '')
        if t == "generation_nodes": return self.gen_rows(raw)
        elif t == "storage_nodes": return self.storage_rows(raw)
        elif t == "substation_nodes": return self.sub_rows(raw)
        elif t == "load_nodes": return self.load_rows(raw)
        elif t == "EMS_SCADA" or t=="backup_EMS": return self.control_rows(raw)
        elif t == '':
            return self.line_rows(self.node)
        return []

    def gen_rows(self, raw):
        live = self.engine.generators.get(raw['id'])
        rows= [
            ('Status', (live.status.upper() if live else raw.get('status', 'N/A').upper())),
            ('Output', f"{live.current_output_mw:.1f} MW" if live else 'N/A'),
            ('Setpoint', f"{live.setpoint_mw:.1f} MW" if live else 'N/A'),
            ('Rated', f"{raw.get('installed_capacity_mw', '-')} MW"),
            ('Min/Max', f"{raw.get('min_output_mw', 'N/A')} - {raw.get('max_output_mw', 'N/A')} MW"),
            ('Ramp Rate', f"{raw.get('ramp_rate_mw_per_min', 'N/A')} MW/min"),
            ('Fuel', raw.get('fuel_type', 'N/A')),
            ('Carbon', f"{raw.get('carbon_kg_per_mwh', 'N/A')} kg/MWh"),
            ('Operator', raw.get('operator', 'N/A')),
        ]
        if live.startup_at !=0:
            rows.append(('Startup at',f"{live.startup_at//60}:{live.startup_at%60:02d}"))
            if self.update_toggle:
                self.update_toggle = False
        return rows
    def storage_rows(self, raw):
        live = self.engine.storage.get(raw['id'])
        soc = f"{live.soc_percent:.1f}%" if live else f"{raw.get('state_of_charge_percent', 'N/A')}%"
        rate = live.charge_rate_mw if live else 0
        rate_str = (f"{rate:.1f} MW charging" if rate > 0
                    else f"{abs(rate):.1f} MW discharging" if rate < 0
        else "idle")
        return [
            ('Status', live.status.upper() if live else raw.get('status', 'N/A').upper()),
            ('SOC', soc),
            ('Flow', rate_str),
            ('Capacity', f"{raw.get('capacity_mwh', 'N/A')} MWh"),
            ('Charge max', f"{raw.get('max_charge_rate_mw', 'N/A')} MW"),
            ('Dis. max', f"{raw.get('max_discharge_rate_mw', 'N/A')} MW"),
            ('Efficiency', f"{int(raw.get('round_trip_efficiency', 0) * 100)}%"),
            ('Response', f"{raw.get('response_time_seconds', 'N/A')}s"),
        ]

    def load_rows(self, raw):
        live = self.engine.loads.get(raw['id'])
        status = 'DISCONNECTED' if (live and live.current_demand_mw == 0) else 'ENERGISED'
        demand = f"{live.current_demand_mw:.1f} MW" if live else 'N/A'
        shed = f"{live.shed_mw:.1f} MW" if (live and live.shed_mw > 0) else 'None'
        backup = raw.get('backup_generation_mw')
        rows = [
            ('Status', status),
            ('Demand now', demand),
            ('Shed', shed),
            ('Peak demand', f"{raw.get('peak_demand_mw', 'N/A')} MW"),
            ('Avg demand', f"{raw.get('average_demand_mw', 'N/A')} MW"),
            ('Priority', f"Class {raw.get('priority_class', 'N/A')}"),
            ('Interruptible', f"{raw.get('interruptible_load_mw', 0)} MW"),
        ]
        if backup:
            on_bkp = ' (ACTIVE)' if (live and live.on_backup) else ''
            rows.append(('Backup gen',
                         f"{backup} MW ({raw.get('backup_type', 'N/A')}){on_bkp}"))
        return rows
    def sub_rows(self, raw):
        s = self.engine.substations.get(raw.get('id'))
        return [
            ("Status", s.status.upper()),
            ("Primary", f"{s.voltage_primary_kv} kV"),
            ("Secondary", f"{s.voltage_secondary_kv} kV"),
            ("Xfmrs", f"{s.transformer_count} x {s.transformer_capacity_mva_each} MVA"),
            ("N-1", 'YES' if s.n_minus_1_capable else 'NO'),
            ('Busbar', s.busbar_configuration.replace("_", " "))
        ]
    def get_node_name(self,id):
        if id[:3] == 'GEN':
            return self.engine.generators.get(id).name
        elif id[:3] == 'STG':
            return self.engine.storage.get(id).name
        elif id[:3] == 'SUB':
            if id == "SUB-009":
                return "Oakridge-Southern Alaska HVDC Interconnect"
            return self.engine.substations.get(id).name
        elif id[:3] == 'LOA':
            return self.engine.loads.get(id).name
        elif id=='CC-001':
            return self.engine.control_center.name
        elif id=='CC-002':
            return self.engine.backup_control_center.name

    def line_rows(self,raw):
        line = self.engine.lines.get(raw.get('id'))
        return [
            ("Status", line.status.upper()),
            ("From", f"{self.get_node_name(line.from_node)}"),
            ("To", f"{self.get_node_name(line.to_node)}"),
            ("Voltage", f"{line.voltage_kv} kV"),
            ("Thermal Limit",  f"{line.thermal_limit_mw} MW" ),
            ("Load", f"{int(abs(line.flow_mw)/line.thermal_limit_mw*100)} %"),
            ('Circuit', str(line.circuits))
        ]
    def control_rows(self,raw):
        main = False
        if raw.get("type") == "EMS_SCADA":
            control_center = self.engine.control_center
            main  = True
        elif raw.get("type") == "backup_EMS":
            control_center = self.engine.backup_control_center
        rows = [
            ("Status",control_center.status.upper()),
            ("Current Draw", f"{control_center.current_demand} MW"),
            ("Operational Draw",f"{control_center.demand_mw} MW"),
            ("Startup time",f"{control_center.activation_time} Minutes")
        ]
        if control_center.activate_at !=0:
            rows.append(("Activation at", f"{control_center.activate_at//60}:{int(control_center.activate_at%60):02d}"))
        if main:
            rows.append(("Backup Control",self.engine.backup_control_center.name))
        elif self.engine.cyberattack and control_center.status == "operational":
            rows.append(("Cyberattack","Active"))
            rows.append(("End at",f"{self.engine.cyberattack_end_at//60}:{self.engine.cyberattack_end_at%60:02d}"))
        return rows

    def _build_controls(self,px,py,update=False):
        self.buttons.clear()
        if not update or not self.update_toggle:
            self.text_inputs.clear()
        t = self.node.get('type','')
        raw = self.node.get('raw',{})
        nid = raw.get('id','')

        if t == 'generation_nodes':
            self._build_gen_controls(px,py,nid,raw,update)
        elif t == 'storage_nodes':
            self._build_storage_controls(px,py,nid,update)
        elif t == 'load_nodes':
            self._build_load_controls(px,py,nid,raw,update)
        elif t == 'EMS_SCADA':
            self._build_control_controls(px,py,nid,raw)
        elif t == '':
            self._build_line_controls(px, py, self.node.get('id'), self.node, update)

    def _build_line_controls(self, px, py, nid, raw, update):
        pad = 8
        bw = (self.w-pad*3)//2

        live = self.engine.lines.get(nid)
        is_online = live and live.status == 'online'
        is_standby = live and live.status == 'tripped'
        self.buttons.append(Button(
            'Restore',
            px+pad*2+bw, py+4, bw, 22,
            BTN_GREEN if is_standby else BTN_DIM,
            (lambda _id=nid: self.engine.restore_line(_id))
            if is_standby else lambda: None
        ))
        self.buttons.append(Button(
            'TRIP',
            px + pad, py + 4, bw, 22,
            BTN_RED if is_online else BTN_DIM,
            (lambda _line=live: self.engine._trip_line(_line))
            if is_online else lambda: None
        ))
    def _build_control_controls(self,px,py,nid,raw):
        pad =8
        bw = (self.w-pad*3)//2
        control_center = self.engine.control_center
        self.buttons.append(Button(
            "Start up",
            px+pad,py+4,bw,22,
            BTN_GREEN if (control_center.status == "operational" and self.engine.backup_control_center.activate_at ==0 and self.engine.backup_control_center.status != "operational") or (control_center.status=="standby" and self.engine.force_switch_started) else BTN_DIM,
            (lambda : self.engine._init_control_switch(control_center.status=="standby" and self.engine.force_switch_started)) if (control_center.status == "operational" and self.engine.backup_control_center.activate_at ==0 and self.engine.backup_control_center.status != "operational") or (control_center.status=="standby" and self.engine.force_switch_started)else lambda: None
        ))
        self.buttons.append(Button(
            "Transfer",
            px+pad*2+bw,py+4,bw,22,
            BTN_ORANGE if control_center.status == "operational" and self.engine.backup_control_center.status == "operational" else BTN_DIM,
            (lambda: self.engine._swich_control() if control_center.status == "operational" and self.engine.backup_control_center.status == "operational" else lambda: None)
        ))
    def _build_gen_controls(self,px,py,nid,raw,update):
        pad = 8
        bw = (self.w-pad*3)//2
        live = self.engine.generators.get(nid)
        if not update or not self.update_toggle:

            self.text_inputs.append(TextInput(
                px+pad,py+6,self.w-pad*2,22,
                f"Set MW ({raw.get('min_output_mw',0)}-{raw.get('max_output_mw',0)})",
                lambda mw,_id=nid:self.engine.set_generator_setpoint(_id,mw),self.font
            ))
            self.update_toggle = True
        is_online = live and live.status == 'online'
        is_standby = live and live.status == 'standby'

        self.buttons.append(Button(
            'TRIP',
            px+pad,py+34,bw,22,
            BTN_RED if is_online else BTN_DIM,
            (lambda  _id=nid:self.engine.trip_generator(_id))
            if is_online else lambda:None
        ))  
        
        self.buttons.append(Button(
            'Restart',
            px+pad*2+bw,py+34,bw,22,
            BTN_GREEN if is_standby else BTN_DIM,
            (lambda _id=nid:self.engine.set_generator_setpoint(_id,self.engine.generators[_id].min_output_mw+0.1))
            if is_standby else lambda:None
        ))

    def _build_storage_controls(self,px,py,nid,update):
        pad = 8
        bw = (self.w-pad*4)//3
        if not update:

            self.text_inputs.append(TextInput(
                px+pad,py+6,self.w -pad *2,22,
                'MW: + charge / - discharge',
                lambda mw, _id=nid: self.engine.set_storage_rate(_id,mw),
                self.font
            ))

        self.buttons.append(Button(
            'IDLE',
            px+pad,py+34,bw,22,
            BTN_BLUE,
            lambda _id=nid:self.engine.set_storage_rate(_id,0)
        ))
        self.buttons.append(Button(
            'MAX CHG',
            px+pad*2+bw,py+34,bw,22,
            BTN_GREEN,
            lambda _id=nid: self.engine.set_storage_rate(_id,self.engine.storage[_id].max_charge_rate_mw)
        ))
        self.buttons.append(Button(
            'MAX DIS',
            px+pad*3+bw*2,py+34,bw,22,
            BTN_ORANGE,
            lambda _id=nid:self.engine.set_storage_rate(_id,-self.engine.storage[_id].max_discharge_rate_mw)
        ))
    def _test_ship(self):
        self.engine.test_ship = True
    def _build_load_controls(self,px,py,nid,raw,update):
        pad=8
        bw = (self.w-pad*3)//2
        live = self.engine.loads.get(nid)
        priority = raw.get('priority_class',3)
        can_shed = (live and priority>0
                    and live.interruprible_load_mw>0
                    and live.shed_mw<live.current_demand_mw)
        can_restore = live and live.shed_mw>0

        self.buttons.append(Button(
            'SHED LOAD',
            px+pad,py+8,bw,22,
            BTN_ORANGE if can_shed else BTN_DIM,
            (lambda _id=nid:self._shed_load(_id))
            #(lambda _id=nid: self._test_ship())
            if can_shed else lambda:None
        ))
        self.buttons.append(Button(
            'RESTORE',
            px+pad*2 + bw,py+8,bw,22,
            BTN_GREEN if can_restore else BTN_DIM,
            (lambda _id=nid: self.engine.reset_shed_load(_id))
            if can_restore else lambda: None
        ))

    def _shed_load(self,load_id):
        load = self.engine.loads.get(load_id)
        if load:
            shed = min(load.interruprible_load_mw,load.current_demand_mw-load.shed_mw)
            load.shed_mw = shed

    @classmethod
    def make_hvdc_panel(cls,sx,sy,screen_w,screen_h,font,bold_font,engine):
        fake_node = {
            'id':'SUB-009',
            'name':'HDVC Interconnector Control',
            'type':'hdvc',
            'raw':{'id':'SUB-009'}
        }
        panel = cls.__new__(cls)
        panel.font=font
        panel.font_bold = bold_font
        panel.node = fake_node
        panel.engine = engine
        panel.screen_w = screen_w
        panel._is_hvdc = True
        panel.screen_h = screen_h
        panel.w = cls.PANEL_W
        panel.buttons =[]
        panel.text_inputs = []

        ic = engine.data['interconnects'][0]
        panel.rows=[
            ('Flow now', f"{engine.hvdc_flow_mw:.1f} MW"),
            ('Direction', 'EXPORT' if engine.hvdc_flow_mw >= 0 else 'IMPORT'),
            ('Max export', f"{ic['max_export_mw']} MW"),
            ('Max import', f"{ic['max_import_mw']} MW"),
            ('Ramp rate', f"{ic['ramp_rate_mw_per_min']} MW/min"),
            ('Status', ic['status'].upper())
        ]
        row_h = 25+len(panel.rows)*18+8
        ctrl_h = 36
        pad = 8
        panel.x,panel.y = calculate_panel_pos(sx,sy,panel.w,row_h +ctrl_h,screen_w,screen_h)

        panel.text_inputs.append(TextInput(
            panel.x + pad, panel.y + row_h + 6,
            panel.w - pad * 2, 22,
            f"MW + export / - import",
            lambda mw: engine.set_hvdc_flow(mw),
            font
        ))
        panel.h = row_h +ctrl_h
        panel.rect = pygame.Rect(panel.x,panel.y,panel.w,panel.h)
        

        return panel
    def update_rows(self):
        if getattr(self,'_is_hvdc',False):
            ic = self.engine.data['interconnects'][0]
            self.rows = [
                ('Flow now', f"{self.engine.hvdc_flow_mw:.1f} MW"),
                ('Direction', 'EXPORT' if self.engine.hvdc_flow_mw >= 0 else 'IMPORT'),
                ('Max export', f"{ic['max_export_mw']} MW"),
                ('Max import', f"{ic['max_import_mw']} MW"),
                ('Ramp rate', f"{ic['ramp_rate_mw_per_min']} MW/min"),
                ('Status', ic['status'].upper())
            ]
            return 
        self.rows = self.build_rows(self.node)
        row_h = 24+18*sum(
            len(wrap_value(v,self.w-110-8, self.font))
            for _,v in self.rows)+8
        self._build_controls(self.x, self.y + row_h,True)

    def handle_event(self,event):

        for ti in self.text_inputs:
            if ti.handle_event(event):
                return True
        for btn in self.buttons:
            if btn.handle_event(event):
                self.update_rows()
                return True
        if event.type == pygame.MOUSEBUTTONDOWN and event.button ==1:
            return self.rect.collidepoint(event.pos)
        return False
    
    def handle_click(self, pos):
        return self.rect.collidepoint(pos)

    def draw(self,surface,alpha=255):
        value_max_width = self.w-110-8
        wrapped_rows = []
        for label, value in self.rows:
            lines = wrap_value(value, value_max_width,self.font)
            wrapped_rows.append((label,lines))
        total_lines = sum(len(lines) for _, lines in wrapped_rows)
        row_h = 24 + total_lines*18 + 8
        ctrl_h = self._controls_heights()
        self.h = row_h+ctrl_h
        self.rect = pygame.Rect(self.x, self.y,self.w,self.h)
        bg = pygame.Surface((self.w,self.h), pygame.SRCALPHA)
        bg.fill((15,20,30,alpha))
        surface.blit(bg, (self.x, self.y))
        border_col = (100,140,180) if alpha==255 else(50,70,90)
        pygame.draw.rect(surface,border_col,self.rect,1)

        name = self.node['name']
        if len(name) >28:
            name = name[:27]+"..."
        header = self.font_bold.render(name, True, (220,220,220))
        surface.blit(header, (self.x + 8, self.y + 6))
        pygame.draw.line(surface,border_col, (self.x,self.y+22), (self.x+self.w, self.y+22), 1)
        ry = self.y+28
        for label,lines in wrapped_rows:
            lab_surf = self.font.render(label, True, (120,140,160))
            surface.blit(lab_surf, (self.x+8, ry))
            for i,line in enumerate(lines):
                val_surf = self.font.render(line, True, (220, 220, 220))
                surface.blit(val_surf, (self.x + 110, ry + i * 18))
            ry += len(lines) * 18
            
        if ctrl_h > 0:
            div_y = self.y+row_h-2
            pygame.draw.line(surface,border_col,(self.x,div_y), (self.x+self.w,div_y),1)
            
        for btn in self.buttons:
            btn.draw(surface,self.font)
        for ti in self.text_inputs:
            ti.draw(surface)
        #old rows code
        """for i, (label,value) in enumerate(self.rows):
            ry = self.y +28 +i*18
            lab_surf = self.font.render(label, True, (120,140,160))
            val_surf = self.font.render(value, True, (220,220,220))
            surface.blit(lab_surf, (self.x+8, ry))
            surface.blit(val_surf, (self.x+110, ry))"""

