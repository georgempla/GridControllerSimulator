from idlelib.pyparse import trans

from utils.icons import draw_icons, draw_label

import pygame,math,json,os,sys

BG_DARK = (6,8,14)
GRID_COL = (255,255,255,8)
BORDER = (40,55,75)
TEXT = (220,220,220)
DIM = (70,85,100)
GOLD = (255,210,50)
TOOLBAR_BG = (12,16,26)
TOOLBAR_BRD = (40,55,75)
BTN_NORMAL = (25,38,60)
BTN_HOVER = (40,62,100)
BTN_ACTIVE = (50,100,160)
BTN_BRD = (80,130,200)

TOOLBAR_W = 180
DOT_SPACING = 40

NODE_TYPES = [
    {"id":"nuclear","label":"Nuclear","group":"generation"},
    {"id":"hydro","label":"Hydro","group":"generation"},
    {"id":"gas_ccgt","label":"Gas CCGT","group":"generation"},
    {"id":"gas_peaker","label":"Gas Peaker","group":"generation"},
    {"id":"wind","label":"Wind Farm","group":"generation"},
    {"id":"solar","label":"Solar Array","group":"generation"},
    {"id":"biomass","label":"Biomass","group":"generation"},
    {"id":"battery","label":"Battery","group":"storage"},
    {"id":"pumped_hydro","label":"Pumped Hydro","group":"storage"},
    {"id":"substation","label":"Substation","group":"substation"},
    {"id":"load","label":"Load Zone","group":"load"},
    {"id":"control_center","label":"Control Center","group":"control"},
    {"id":"backup_control_center","label":"Backup CC","group":"control"}
]

_NODE_COUNTERS = {}
def _next_node_id(type_id):
    prefix_map = {
        "nuclear": "GEN","hydro":"GEN","gas_ccgt":"GEN","gas_peaker":"GEN","wind":"GEN","solar":"GEN","biomass":"GEN","battery":"STG","pumped_hydro":"STG","substation":"SUB","load":"LOAD","backup_control_center":"CC","control_center":"CC"
    }
    prefix = prefix_map.get(type_id,"NODE")
    _NODE_COUNTERS[prefix] = _NODE_COUNTERS.get(prefix,0)+1

    return f"{prefix}-{_NODE_COUNTERS[prefix]:03d}"

def _default_node(type_id,wx,wy):
    type_map = {
        "nuclear": ("nuclear","pressurized_water_reactor","generation_nodes",1500,750,1500,2,14400),
        "hydro": ("hydro","run_of_river","generation_nodes",420,40,420,30,5),
        "gas_ccgt": ("combined_cycle gas","combined_cycle","generation_nodes",480,150,480,8,90),
        "gas_peaker": ("open_cycle gas", "open_cycle_gas_turbine","generation_nodes",200,0,200,20,10),
        "wind":("wind","onshore","generation_nodes",250,0,250,15,0),
        "solar": ("solar","utility_scale_pv","generation_nodes",80,0,80,0,0),
        "biomass": ("biomass","wood_waste_combustion","generation_nodes",55,15,55,3,240),
        "battery": ("battery","lithium_ion","storage_nodes",200,None,None,None,None),
        "pumped_hydro": ("pumped_hydro","closed_loop","storage_nodes",1200,None,None,None,None),
        "substation": ("transmission_substation","","substation_nodes",0,None,None,None,None),
        "load": ("residential", "","load_nodes",0,None,None,None,None),
        "control_center": ("EMS_SCADA", "", "control_nodes", 0, None, None, None, None),
        "backup_control_center":("backup_EMS","","control_nodes",0,None,None,None,None),
    }
    t = type_map[type_id]
    nid = _next_node_id(type_id)

    node = {
        "_collection":t[2],
        "id":nid,
        "name": f"New {type_id.replace('_',' ').title()}",
        "type":t[0],
        "subtype":t[1],
        "position":{"x":round(wx,1),"y":round(wy,1)},
        "status":"online",
        "installed_capacity_mw":t[3],
        "min_output_mw":t[4],
        "max_output_mw":t[5],
        "ramp_rate_mw_per_min":t[6],
        "startup_time_minutes":t[7],
        "fuel_type":t[0],
        "capacity_mwh": 200 if t[2] == "storage_nodes" else None,
        "max_charge_rate_mw": 100 if t[2] == "storage_nodes" else None,
        "max_discharge_rate_mw":100 if t[2] == "storage_nodes" else None,
        "round_trip_efficiency":0.88 if t[2] == "storage_nodes" else None,
        "state_of_charge_percent":60 if t[2] == "storage_nodes" else None,
        "peak_demand_mw":100 if t[2] == "load_nodes" else None,
        "average_demand_mw": 65 if t[2] == "load_nodes" else None,
        "demand_profile": "residential" if t[2] == "load_nodes" else None,
        "priority_class": 3 if t[2] == "load_nodes" else None,
        "interruptible_load_mw":10 if t[2] == "load_nodes" else None,
        "voltage_primary_kv": 500 if t[2] == "substation_nodes" else None,
        "voltage_secondary_kv": 138 if t[2] == "substation_nodes" else None,
        "transformer_count": 2 if t[2] == "substation_nodes" else None,
        "transformer_capacity_mva_each":600 if t[2] == "substation_nodes" else None,
        "n_minus_1_capable": True if t[2]=="substation_nodes" else None,
        "busbar_configuration": "double_busbar" if t[2] == "substation_nodes" else None,
    }
    if t[2] == "control_nodes":
        node["demand_mw"] = 90.0 if type_id == "control_center" else 60.0
        node["activation_time_minutes"] = 60 if type_id == "control_center" else 15
        node["_is_backup"] = (type_id == "backup_control_center")
    return node

_EDGE_COUNTER = 0
def _next_edge_id():
    global _EDGE_COUNTER
    _EDGE_COUNTER +=1
    return f"BL-{_EDGE_COUNTER}"
def _default_edge(from_id, to_id,voltage):
    limit_map = {500:900,138:400,25:150}
    imp_map = {500:0.012,138:0.028,25:0.05}
    return {
        "id": _next_edge_id(),
        "name": f"Line {from_id} to {to_id}",
        "from_node":from_id,
        "to_node":to_id,
        "voltage_kv": voltage,
        "thermal_limit_mw":limit_map.get(voltage,200),
        "impedance_pu": imp_map.get(voltage,0.05),
        "circuits": 1,
        "status": "online",
        "length_km":10,
    }
def _infer_voltage(node):
    col = node.get("_collection","")
    sub = node.get("subtype","")
    if node.get("type") in ("nuclear","hydro") or sub in ("pressurized_water_reactor","run_of_river"):
        return 138
    if col == "load_nodes":
        return 25
    if col == "storage_nodes":
        return 25
    return 138
def validate_map(nodes,edges):
    issues = []
    node_ids = {n["id"] for n in nodes}
    adj = {n["id"]:set() for n in nodes}
    for e in edges:
        if e["from_node"] in adj and e["to_node"] in adj:
            adj[e["from_node"]].add(e["to_node"])
            adj[e["to_node"]].add(e["from_node"])
    def reachable_from(start):
        visited,q = {start},[start]
        while q:
            cur = q.pop()
            for nb in adj.get(cur,[]):
                if nb not in visited:
                    visited.add(nb)
                    q.append(nb)
        return visited
    for n in nodes:
        if not adj[n["id"]]:
            issues.append({"id":n["id"], "message": "Isolated no connections", "severity":"error"})
    required = {
        "generation_nodes" : ["installed_capacity_mw","min_output_mw","max_output_mw"],
        "storage_nodes": ["capacity_mwh","max_charge_rate_mw","max_discharge_rate_mw"],
        "substation_nodes":["voltage_primary_kv","voltage_secondary_kv"],
        "load_nodes":["peak_demand_mw","demand_profile"]
    }
    for n in nodes:
        if n.get("_collection","") == "storage_nodes":
            print(n)
        for field in required.get(n.get("_collection",""),[]):
            if n.get(field) is None or n.get(field) == "":
                issues.append({"id": n["id"],"message":f"Missing field: {field}","severity":"error"})
    has_sub = any(n["_collection"] == "substation_nodes" for n in nodes)
    if not has_sub:
        issues.append({"id":None,"message":f"No substation add at least one","severity":"error"})
    has_gen = any(n["_collection"] == "generation_nodes" for n in nodes)
    if not has_gen:
        issues.append({"id":None,"message":"No generators on map","severity":"error"})
    has_sto = any(n["_collection"] == "storage_nodes" for n in nodes)
    if not has_sto:
        issues.append({"id": None, "message": "No storage on map", "severity": "error"})

    gen_ids = [n["id"] for n in nodes if n["_collection"] == "generation_nodes"]
    reachable = set()
    for gid in gen_ids:
        reachable |= reachable_from(gid)
    for n in nodes:
        if n["_collection"] == "load_nodes" and n["id"] not in reachable:
            issues.append({"id":n["id"], "message":"Load unreachable from any generator","severity":"warning"})
    for e in edges:
        if e["from_node"] not in node_ids:
            issues.append({"id":e["id"],"message":f"Dangling from_node {e['from_node']}","severity":"error"})
        if e["to_node"] not in node_ids:
            issues.append({"id":e["id"],"message":f"Dangling to_node {e['to_node']}","severity":"error"})
    main_css = [n for n in nodes if n.get("_collection") == "control_nodes" and not n.get("_is_backup")]
    if len(main_css) == 0:
        issues.append({"id":None,"message":"No Control Center, add one from toolbar","severity":"error"})
    if len(main_css) >1:
        issues.append({"id": None, "message": "Multiple Main Control Centers, only one allowed", "severity": "error"})
    backup_css = [n for n in nodes if n.get("_collection") == "control_nodes" and n.get("_is_backup")]
    if len(backup_css) == 0:
        issues.append({"id": None, "message": "No Backup Control Center, add one from toolbar", "severity": "error"})
    if len(backup_css) > 1:
        issues.append({"id": None, "message": "Multiple Backup Control Centers, only one allowed", "severity": "error"})
    for n in nodes:
        if n.get("_collection") == "control_nodes" and not adj[n["id"]]:
            issues.append({"id":n["id"],"message":f"{n['name']} is isolated","severity":"error"})
    return issues
def _cc_block(n,fallback_id,fallback_name,fallback_type,fallback_demand,fallback_activation):
    if n is None:
        return {
            "id":fallback_id,"name":fallback_name,
            "position":{"x":50,"y":50},
            "type":fallback_type,
            "systems":[],"scan_rate_seconds":4,
            "demand_mw":fallback_demand,
            "activation_time_minutes":fallback_activation,
        }
    pos = n.get("position",{"x":50,"y":50})
    return {
        "id": n.get("id",fallback_id), "name": n.get("name",fallback_name),
        "position": pos,
        "type": fallback_type,
        "systems": [], "scan_rate_seconds": 4,
        "demand_mw": n.get("demand_mw",fallback_demand),
        "activation_time_minutes": n.get("activation_time_minutes",fallback_activation),
    }
def export_map(nodes,edges,metadata):
    gen_nodes,sto_nodes,sub_nodes,load_nodes = [],[],[],[]
    cc_main = None
    cc_backup=None
    for n in nodes:
        clean = {k:v for k,v in n.items() if not k.startswith("_") and v is not None}
        col = n.get("_collection")
        if col == "generation_nodes":gen_nodes.append(clean)
        elif col == "storage_nodes": sto_nodes.append(clean)
        elif col == "substation_nodes":sub_nodes.append(clean)
        elif col == "load_nodes":load_nodes.append(clean)
        elif col == "control_nodes":
            if n.get("_is_backup"):
                cc_backup = clean
            else:
                cc_main = clean
    tx_lines,dist_lines = [],[]
    print(edges)
    for e in edges:
        clean = {k: v for k, v in e.items() if not k.startswith("_")}
        if e.get("voltage_kv",25)>=138:
            tx_lines.append(clean)
        else:
            dist_lines.append(clean)
    total_cap = sum(n.get("installed_capacity_mw",0) for n in gen_nodes)
    peak = sum(n.get("peak_demand_mw",0) for n in load_nodes)
    meta = {k:v for k,v in metadata.items() if not k.startswith("_")}
    meta["total_installed_capacity_mw"] = total_cap
    meta["peak_demand_mw"] = peak
    meta["description"]=f"Custom map: {meta.get('name','')}"
    default_profiles = {
        'residential':{"hourly_factors":[0.6]*24},
        'commercial': {"hourly_factors": [0.7] * 24},
        'industrial': {"hourly_factors": [0.9] * 24},
        'flat': {"hourly_factors": [1.0] * 24},
        'port_industrial': {"hourly_factors": [0.8] * 24},
        'airport': {"hourly_factors": [0.8] * 24},
        'mixed_residential_commercial': {"hourly_factors": [0.7] * 24}
    }
    seasonal = {
        s:{"residential_modifier":1.0,"commercial_modifier":1.0,"industrial_modifier":1.0}
        for s in ("winter","spring","summer","automn")
    }
    scada = {
        "control_center": _cc_block(cc_main,"CC-001","Control Center","EMS_SCADA",90.0,60),
        "backup_control_center":_cc_block(cc_backup,"CC-002","Backup Control Center","backup_EMS",60.0,15),
        "pmu_nodes":[],
    }
    return {
        "map_metadata":meta,
        "generation_nodes":gen_nodes,
        "storage_nodes":sto_nodes,
        "substation_nodes":sub_nodes,
        "load_nodes":load_nodes,
        "transmission_lines":tx_lines,
        "distribution_lines":dist_lines,
        "interconnects":[{
      "id": "IC-001",
      "name": "Main Interconnect",
      "from_node": "SUB-001",
      "type": "hvdc",
      "max_export_mw": 600,
      "max_import_mw": 400,
      "current_scheduled_flow_mw": 0,
      "current_flow_direction": "export",
      "ramp_rate_mw_per_min": 50,
      "contract_type": "renewable_export_agreement",
      "status": "online",
    }],
        "gas_infrastructure":[],
        "demand_profiles":default_profiles,
        "seasonal_modifiers":seasonal,
        "scada_and_monitoring":scada,
        "grid_challenges":[],
        "events":[],
    }
def save_map(nodes,edges,metadata,maps_dir="maps"):
    os.makedirs(maps_dir,exist_ok=True)
    data = export_map(nodes,edges,metadata)
    safe_name = metadata.get("name","custom").replace(" ","_").lower()
    filepath = resource_path(os.path.join(maps_dir,f"{safe_name}.json"))
    with open(filepath,"w") as f:
        json.dump(data,f,indent=2)
    return filepath
def resource_path(relative):
    if getattr(sys, '_MEIPASS', None):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, relative)
GROUP_COLOURS = {
    "generation":(50,120,80),
    "storage":(50,80,140),
    "substation":(80,80,80),
    "load":(120,60,40),
    "control":(100,60,140),
}
DEMAND_PROFILES = [
    "residential","commercial","industrial","flat",
    "port_industrial","airport","mixed_residentrial_commercial"
]

class MetadataPanel:
    W=300
    def __init__(self, metadata, screen_w,screen_h,fonts):
        self.meta = metadata
        self.fonts = fonts
        self.closed = False
        self._error = ""
        FIELDS = [
            ("name", "Map Name", "str"),
            ("city", "City", "str"),
            ("state","State","str"),
            ("climate","Climate","str"),
        ]
        self.inputs = []
        pad = 8
        row_h = 26
        h =30+len(FIELDS)*row_h+62
        self.x = screen_w //2 - self.W//2
        self.y= 50
        self.rect =pygame.Rect(self.x,self.y,self.W,h)
        iy=self.y+30
        for key,label,dtype in FIELDS:
            inp= _PanelInput(self.x+130,iy,self.W-138,str(metadata.get(key,"")),fonts["tiny"])
            self.inputs.append((key,dtype,label,inp))
            iy+=row_h
        self._profile_y = iy+4
        self._close_rect = pygame.Rect(self.x+self.W-26,self.y+4,22,18)
    def handle_event(self,event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self._close_rect.collidepoint(event.pos):
                self.closed = True
                return
            prof_rect = pygame.Rect(self.x+130,self._profile_y,self.W-138,18)
            if prof_rect.collidepoint(event.pos):
                cur = self.meta.get("_selected_profile","residential")
                idx = DEMAND_PROFILES.index(cur) if cur in DEMAND_PROFILES else 0
                self.meta["_selected_profile"] = DEMAND_PROFILES[(idx+1)%len(DEMAND_PROFILES)]
        for _,dtype,_,inp in self.inputs:
            inp.handle_event(event)
            if inp.commited:
                self_commit(inp,dtype)
                inp.commited = False
    def _commit(self,inp,dtype):
        for key,dt,_,i in self.inputs:
            if i is inp:
                try:
                    self.meta[key] = int(float(inp.value)) if dt=="int" else (float(inp.value) if d=="float" else inp.value)
                except ValueError:
                    self._error = "Bad value"
                return
    def draw(self,surface):
        bg = pygame.Surface((self.W,self.rect.h),pygame.SRCALPHA)
        bg.fill((10,14,24,245))
        surface.blit(bg,(self.x,self.y))
        pygame.draw.rect(surface,BTN_BRD,self.rect,1,border_radius=4)
        metadata_label = self.fonts["bold"].render("MAP METADATA",True,GOLD)
        surface.blit(metadata_label,(self.x+8,self.y+6))
        mouse = pygame.mouse.get_pos()
        xc = (120,40,40) if self._close_rect.collidepoint(mouse) else (80,30,30)
        pygame.draw.rect(surface,xc,self._close_rect,border_radius=2)
        x_label = self.fonts["tiny"].render("X",True,(220,100,100))
        surface.blit(x_label,(self._close_rect.centerx-x_label.get_width()//2,self._close_rect.centery-x_label.get_height()//2))
        pygame.draw.line(surface,BORDER,(self.x,self.y+24),(self.x+self.W,self.y+24),1)
        iy = self.y+30
        for key,dtype,label,inp in self.inputs:
            lbl = self.fonts["tiny"].render(label,True,DIM)
            surface.blit(lbl,(self.x+8,iy+2))
            inp.rect.y = iy
            inp.draw(surface)
            iy+=26
        self._profile_y = iy+4
        lbl2 = self.fonts["tiny"].render("Default Profile",True,DIM)
        surface.blit(lbl2,(self.x+8,self._profile_y+2))
        prof_rect = pygame.Rect(self.x+130,self._profile_y,self.W-138,18)
        pygame.draw.rect(surface,(25,38,60),prof_rect,border_radius=2)
        pygame.draw.rect(surface,BTN_BRD,prof_rect,1,border_radius=2)
        cur_prof = self.meta.get("_selected_profile","residential")
        prof_label = self.fonts["tiny"].render(cur_prof+" >",True,TEXT)
        surface.blit(prof_label,(prof_rect.x+4,prof_rect.centery-prof_label.get_height()//2))
class EdgePropertyPanel:
    W = 230
    FIELDS = [
        ("name", "Name", "str"),
        ("voltage_kv", "Voltage kV", "int"),
        ("thermal_limit_mw", "Thermal MW", "float"),
        ("impedance_pu", "Impedance pu", "float"),
        ("length_km", "Length km", "float"),
        ("circuits","Circuits","int"),
    ]
    def __init__(self,edge,screen_w,screen_h,fonts):
        self.edge = edge
        self.fonts = fonts
        self._error = ""
        self.inputs = []
        row_h = 26
        pad = 8
        height = 30 +len(self.FIELDS)*row_h+38
        self.x = screen_w-self.W-4
        self.y = max(4,screen_h//2)
        self.rect = pygame.Rect(self.x,self.y,self.W,height)
        iy = self.y +28
        for key,label,dtype in self.FIELDS:
            cur = edge.get(key,"")
            inp = _PanelInput(self.x+110,iy,self.W-118,str(cur) if cur is not None else "",fonts["tiny"])
            self.inputs.append((key,dtype,inp))
            iy += row_h
        bw = self.W -pad*2
        self.delete_rect = pygame.Rect(self.x+pad, iy+6,bw,22)
    def handle_event(self,event):
        for _,_,inp in self.inputs:
            inp.handle_event(event)
            if inp.commited:
                self._commit(inp)
                inp.commited = False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.delete_rect.collidepoint(event.pos):
                return "delete"
        return None
    def _commit(self,inp):
        for key, dtype, i in self.inputs:
            if i is inp:
                try:
                    self.edge[key] = float(inp.value) if dtype == "float" else (int(float(inp.value)) if dtype == "int" else inp.value)
                    self._error=""
                except ValueError:
                    self._error = f"Bad value for {key}"
                return
    def draw(self,surface):
        bg = pygame.Surface((self.W,self.rect.h),pygame.SRCALPHA)
        bg.fill((10,14,24,235))
        surface.blit(bg,(self.x,self.y))
        pygame.draw.rect(surface,(180,120,50),self.rect,1,border_radius=4)
        hdr = self.fonts["bold"].render("LINE PROPERTIES",True,(255,180,60))
        surface.blit(hdr, (self.x+8,self.y+6))
        pygame.draw.line(surface,BORDER,(self.x,self.y+22),(self.x+self.W,self.y+22),1)
        iy = self.y+28
        for (key,label,_),(_,_,inp) in zip(self.FIELDS,self.inputs):
            lbl = self.fonts["tiny"].render(label,True,DIM)
            surface.blit(lbl,(self.x+8,iy+4))
            inp.rect.x = self.x +110
            inp.rect.y = iy
            inp.draw(surface)
            iy +=26
            mouse = pygame.mouse.get_pos()
            bdg = (120,30,30) if self.delete_rect.collidepoint(mouse) else (80,20,20)
            pygame.draw.rect(surface,bdg,self.delete_rect,border_radius=3)
            pygame.draw.rect(surface,(180,60,60),self.delete_rect,1,border_radius=3)
            dl = self.fonts["tiny"].render("DELETE LINE",True,(220,100,100))
            surface.blit(dl,(self.delete_rect.centerx-dl.get_width()//2,self.delete_rect.centery-dl.get_height()//2))


class NodePropertyPanel:
    W = 240
    FIELDS = {
        "generation_nodes":[
            ("name","NAME","str"),
            ("installed_capacity_mw", "Capacity MW", "float"),
            ("min_output_mw", "Min MW", "float"),
            ("max_output_mw", "Max MW", "float"),
            ("ramp_rate_mw_per_min","Ramp MW/min","float"),
            ("startup_time_minutes","Startup min", "float"),
            ("voltage_kv", "Voltage kV", "float"),
        ],
        "storage_nodes": [
            ("name", "Name", "str"),
            ("capacity_mwh", "Capacity MWh", "float"),
            ("max_charge_rate_mw", "Max chg MW", "float"),
            ("max_discharge_rate_mw", "Max dis MW", "float"),
            ("round_trip_efficiency", "Efficiency", "float"),
        ],
        "substation_nodes": [
            ("name", "Name", "str"),
            ("voltage_primary_kv", "Primary kV", "float"),
            ("voltage_secondary_kv", "Secondary kV", "float"),
            ("transformer_count", "Xfmr count", "int"),
            ("transformer_capacity_mva_each", "Xfmr MVA", "float")
        ],
        "load_nodes": [
            ("name","Name","str"),
            ("peak_demand_mw", "Peak MW", "float"),
            ("average_demand_mw", " Average MW", "float"),
            ("priority_class", "Priority 0-3", "int"),
            ("interruptible_load_mw", "Interr. MW", "float"),
        ],
        "control_nodes":[
            ("name","Name","str"),
            ("demand_mw", "Demand MW","float"),
            ("activation_time_minutes","Startup min","int"),
        ]
    }
    def __init__(self,node,screen_w,screen_h,fonts):
        self.node = node
        self.screen_h = screen_h
        self.screen_w = screen_w
        self.fonts =fonts
        self.inputs = []
        self._error = ""

        col = node.get("_collection","generation_nodes")
        fields = self.FIELDS.get(col,[])
        row_h = 26
        pad = 8
        height = 30 + len(fields)*row_h + 48
        self.x = screen_w-self.W
        self.y = max(4,min(screen_h-height-4,80))
        self.rect= pygame.Rect(self.x,self.y,self.W,height)
        iy = self.y +28
        for key,label,dtype in fields:
            cur = node.get(key, "")
            inp = _PanelInput(
                x= self.x+110,
                y=iy,
                w=self.W-118,
                placeholder=str(cur) if cur is not None else "",
                font=fonts["tiny"]
            )
            self.inputs.append((key,dtype,inp))
            iy += row_h
        bw = self.W-pad*2
        self.delete_rect = pygame.Rect(self.x+pad,iy+6,bw,22)
    def handle_event(self,event):
        for _,_,inp in self.inputs:
            inp.handle_event(event)
            if inp.commited:
                self._commit(inp)
                inp.commited = False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.delete_rect.collidepoint(event.pos):
                return "delete"
        return None
    def _commit(self,inp):
        for key, dtype,i in self.inputs:
            if i is inp:
                try:
                    if dtype == "float":
                        self.node[key] = float(inp.value)
                    elif dtype == "int":
                        self.node[key] = int(float(inp.value))
                    else:
                        self.node[key] = inp.value
                    self._error = ""
                except ValueError:
                    self._error = f"Bad value for {key}"
                return
    def draw(self,surface):
        bg = pygame.Surface((self.W,self.rect.h),pygame.SRCALPHA)
        bg.fill((10,14,24,235))
        surface.blit(bg,(self.x,self.y))
        pygame.draw.rect(surface,BTN_BRD,self.rect,1,border_radius=4)
        name = self.node.get("name", "Node")[:26]
        hdr = self.fonts["bold"].render(name,True,GOLD)
        surface.blit(hdr,(self.x+8,self.y+6))
        pygame.draw.line(surface,BORDER,(self.x,self.y+22),(self.x+self.W,self.y+22),1)
        row_h=26
        iy=self.y+28
        col = self.node.get("_collection","generation_nodes")
        for (key,label,dtype),(_,_,inp) in zip(self.FIELDS.get(col,[]),self.inputs):
            lbl = self.fonts["tiny"].render(label,True,DIM)
            surface.blit(lbl,(self.x+8,iy+4))
            inp.rect.x = self.x +110
            inp.rect.y = iy
            inp.draw(surface)
            iy += row_h
        mouse=pygame.mouse.get_pos()
        bdg = (120,30,30) if self.delete_rect.collidepoint(mouse) else (80,20,20)
        pygame.draw.rect(surface,bdg,self.delete_rect,border_radius=3)
        pygame.draw.rect(surface,(180,60,60),self.delete_rect,1,border_radius=3)
        dl = self.fonts["tiny"].render("DELETE NODE",True,(220,100,100))
        surface.blit(dl,(self.delete_rect.centerx-dl.get_width()//2,self.delete_rect.centery-dl.get_height()//2))
        if self._error:
            el = self.fonts["tiny"].render(self._error,True,(255,80,80))
            surface.blit(el,(self.x+8,self.rect.bottom-14))
class _PanelInput:
    ALLOWED = set("qwertyuioplkjhgfdsazxcvbnmMNBVCXZLKJHGFDSAQWERTYUIOP"
                  "0123456789 ._-(),/")
    def __init__(self, x,y,w,placeholder,font):
        self.rect = pygame.Rect(x,y,w,18)
        self.placeholder = placeholder
        self.font = font
        self.value = placeholder
        self.active = False
        self.commited = False
    def handle_event(self,event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            was = self.active
            self.active = self.rect.collidepoint(event.pos)
            if self.active and not was:
                self.value = ""
        if not self.active:
            return
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                self.commited = True
                self.active = False
            elif event.key == pygame.K_BACKSPACE:
                self.value = self.value[:-1]
            elif event.unicode in self.ALLOWED:
                self.value += event.unicode
    def draw(self, surface):
        brd = (100,160,220) if self.active else (50,65,85)
        pygame.draw.rect(surface,(18,24,36),self.rect,border_radius=2)
        pygame.draw.rect(surface,brd,self.rect,1,border_radius=2)
        display = self.value if self.value else self.placeholder
        col = (220,220,220) if self.value else (70,90,110)
        txt = self.font.render(display,True,col)
        surface.blit(txt,(self.rect.x+4,self.rect.centery-txt.get_height()//2))
        if self.active and (pygame.time.get_ticks()//500) %2 == 0:
            cx = self.rect.x + 4 +txt.get_width()+1
            pygame.draw.line(surface,(220,220,220),(cx,self.rect.y+2),(cx,self.rect.bottom-2),1)
class BuilderCamera:
    CONSTANT_ZOOM = 8
    def __init__(self,offset_x=TOOLBAR_W,offset_y=0):
        self.pan_x = offset_x+80
        self.pan_y = 80
        self.zoom = 1.0
        self.offset_x = offset_x
        self._drag = False
        self._last = (0,0)
    def world_to_screen(self,wx,wy):
        sx = wx*self.zoom*self.CONSTANT_ZOOM+self.pan_x
        sy = wy*self.zoom*self.CONSTANT_ZOOM+self.pan_y
        return int(sx),int(sy)
    def screen_to_world(self,sx,sy):
        wx = (sx-self.pan_x)/self.zoom/self.CONSTANT_ZOOM
        wy = (sy-self.pan_y)/self.zoom/self.CONSTANT_ZOOM
        return wx,wy
    def _in_canvas(self,pos):
        return pos[0]>self.offset_x
    def handle_event(self,event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self._in_canvas(event.pos):
                self._drag = True
                self._last = event.pos
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self._drag = False
        elif event.type == pygame.MOUSEMOTION and self._drag:
            dx = event.pos[0]-self._last[0]
            dy = event.pos[1]-self._last[1]
            self.pan_x += dx
            self.pan_y += dy
            self._last = event.pos
        elif event.type == pygame.MOUSEWHEEL:
            if self._in_canvas(pygame.mouse.get_pos()):
                factor = 1.1 if event.y>0 else 0.9
                mx,my = pygame.mouse.get_pos()
                wx = (mx-self.pan_x)/self.zoom/self.CONSTANT_ZOOM
                wy = (my-self.pan_y)/self.zoom/self.CONSTANT_ZOOM
                self.zoom = max(0.3,min(6.0,self.zoom*factor))
                self.pan_x = mx-wx*self.zoom*self.CONSTANT_ZOOM
                self.pan_y = my-wy*self.zoom*self.CONSTANT_ZOOM

class ToolbarButton:
    H = 32
    GAP = 4

    def __init__(self,x,y,w,node_type,fonts):
        self.rect = pygame.Rect(x,y,w,self.H)
        self.node_type = node_type
        self.fonts = fonts
        self.hovered = False
        self.active = False

    def update(self,mouse):
        self.hovered = self.rect.collidepoint(mouse)
    def handle_click(self,pos):
        return self.rect.collidepoint(pos)
    def draw(self,surface):
        group = self.node_type["group"]
        grp_col = GROUP_COLOURS.get(group,(60,60,60))
        if self.active:
            bg = BTN_ACTIVE
            brd = BTN_BRD
        elif self.hovered:
            bg = BTN_HOVER
            brd = BTN_BRD
        else:
            bg = BTN_NORMAL
            brd = TOOLBAR_BRD

        pygame.draw.rect(surface,bg,self.rect,border_radius=3)
        pygame.draw.rect(surface,brd,self.rect,1,border_radius=3)
        stripe = pygame.Rect(self.rect.x+2,self.rect.y+4,3,self.H-8)
        pygame.draw.rect(surface,grp_col,stripe,border_radius=2)
        lbl = self.fonts["small"].render(self.node_type["label"],True,TEXT)
        surface.blit(lbl,(self.rect.x+12,self.rect.centery-lbl.get_height()//2))

class MapBuilder:
    def __init__(self,screen_w,screen_h):
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.done = False
        self.meta_panel = None
        self._issues = []
        self._show_issues = False
        self._validate_btn_rect = pygame.Rect(0,0,1,1)
        self._save_msg = ""
        self._save_msg_tick = 0
        self._export_btn_rect = pygame.Rect(0, 0, 1, 1)
        self.tick = 0
        self.fonts = {
            "title":pygame.font.SysFont("consolas",14,bold=True),
            "small":pygame.font.SysFont("consolas",11),
            "tiny":pygame.font.SysFont("consolas",10),
            "bold": pygame.font.SysFont("consolas",12,bold=True)
        }
        self.camera = BuilderCamera(offset_x=TOOLBAR_W)
        self.active_tool = None
        self._dot_surf = self._make_dot_surf(screen_w*3,screen_h*3)
        self.toolbar_buttons = []
        self._build_toolbar()
        bw,bh = 140,30
        self.back_rect = pygame.Rect(
            TOOLBAR_W//2-bw//2,
            screen_h-bh-12,
            bw,bh
        )
        self.nodes = []
        self.edges = []
        self.selected_node_id = None
        self.hovered_node_id = None
        self._pending_edge_from = None
        self.node_panel = None
        self.edge_panel = None
        self.metadata = {
            "name": "New Map",
            "city": "A City",
            "state":"Alaska",
            "climate":"subarctic",
            "version":"1.0.0",
            "_selected_profile":"residential"
        }




    @staticmethod
    def _make_dot_surf(w,h):
        surf = pygame.Surface((w,h),pygame.SRCALPHA)
        surf.fill((0,0,0,0))
        for x in range(0,w,DOT_SPACING):
            for y in range(0,h,DOT_SPACING):
                pygame.draw.circle(surf,(255,255,255,30),(x,y),1)
        return surf

    def _build_toolbar(self):
        self.toolbar_buttons.clear()
        x = 8
        y=60
        w = TOOLBAR_W-16
        last_group = None
        for nt in NODE_TYPES:
            if nt["group"] != last_group:
                y += 6
                last_group = nt["group"]
            btn = ToolbarButton(x,y,w,nt,self.fonts)
            self.toolbar_buttons.append(btn)
            y += ToolbarButton.H + ToolbarButton.GAP
        y +=12
        self._meta_btn_rect = pygame.Rect(x,y,w,26)
        vby = self._meta_btn_rect.bottom + 8
        self._validate_btn_rect = pygame.Rect(x, vby, w, 26)
        eby = self._validate_btn_rect.bottom+6
        self._export_btn_rect = pygame.Rect(x,eby,w,28)
    def handle_event(self,event):
        mouse = pygame.mouse.get_pos()
        if self.node_panel:
            result = self.node_panel.handle_event(event)
            if result == "delete":
                nid = self.node_panel.node["id"]
                self.nodes = [n for n in self.nodes if n["id"] != nid]
                self.edges = [e for e in self.edges
                              if e["from_node"] != nid and e["to_node"] != nid]
                self.node_panel = None
                return None
            if event.type == pygame.MOUSEBUTTONDOWN and self.node_panel.rect.collidepoint(event.pos):
                return None
        if self.edge_panel:
            result = self.edge_panel.handle_event(event)
            if result == "delete":
                eid = self.edge_panel.edge["id"]
                self.edges = [e for e in self.edges if e["id"] != eid]
                self.edge_panel = None
                return None
            if event.type == pygame.MOUSEBUTTONDOWN and self.edge_panel.rect.collidepoint(event.pos):
                return None
        if self.meta_panel and not self.meta_panel.closed:
            self.meta_panel.handle_event(event)
            if event.type == pygame.MOUSEBUTTONDOWN and self.meta_panel.rect.collidepoint(event.pos):
                return None
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.active_tool = None
            self._pending_edge_from = None
            self.selected_node_id = None
            for btn in self.toolbar_buttons:
                btn.active = False
            return None
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.back_rect.collidepoint(mouse):
                self.done = True
                return "back"
            if mouse[0] <= TOOLBAR_W:
                for btn in self.toolbar_buttons:
                    if btn.handle_click(mouse):
                        if self.active_tool == btn.node_type["id"]:
                            self.active_tool= None
                            btn.active = False
                        else:
                            self.active_tool = btn.node_type["id"]
                            for b in self.toolbar_buttons:
                                b.active = False
                            btn.active = True
                        return None
                if self._meta_btn_rect.collidepoint(mouse):
                    if self.meta_panel and not self.meta_panel.closed:
                        self.meta_panel.closed = True
                    else:
                        self.meta_panel = MetadataPanel(self.metadata,self.screen_w,self.screen_h,self.fonts)
                    return None
                if self._validate_btn_rect.collidepoint(mouse):
                    self._issues = validate_map(self.nodes,self.edges)
                    self._show_issues = not self._show_issues
                    return None
                if self._export_btn_rect.collidepoint(mouse):
                    issues = validate_map(self.nodes,self.edges)
                    errors = [i for i in issues if i["severity"] == "error"]
                    if errors:
                        self._save_msg = f"Fix {len(errors)} error(s) first"
                        self._save_msg_tick = self.tick
                    else:
                        path = save_map(self.nodes,self.edges,self.metadata,maps_dir="maps")
                        self._save_msg = f"Saved to {os.path.basename(path)}"
                        self._save_msg_tick = self.tick
                    return None

            else:
                wx,wy = self.camera.screen_to_world(*mouse)
                if self.active_tool:
                    node = _default_node(self.active_tool,wx,wy)
                    self.nodes.append(node)
                    return None
                else:
                    hit = self._node_at_screen(*mouse)
                    if hit:
                        if self._pending_edge_from is None:
                            self._pending_edge_from = hit["id"]
                            self.selected_node_id = hit["id"]
                        else:
                            if hit["id"] != self._pending_edge_from:
                                n_from = self._node_by_id(self._pending_edge_from)
                                n_to = hit
                                v = max(_infer_voltage(n_from),_infer_voltage(n_to))
                                self.edges.append(_default_edge(n_from["id"],n_to["id"],v))
                            self._pending_edge_from = None
                            self.selected_node_id = None
                    else:
                        self._pending_edge_from = None
                        self.selected_node_id = None
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
            if mouse[0] > TOOLBAR_W:
                hit = self._node_at_screen(*mouse)
                if hit:
                    self.node_panel = NodePropertyPanel(hit,self.screen_w,self.screen_h,self.fonts)

                else:
                    hit_edge = self._edge_at_screen(*mouse)
                    if hit_edge:
                        self.edge_panel = EdgePropertyPanel(hit_edge,self.screen_w,self.screen_h,self.fonts)
                    else:
                        self.edge_panel =None
                        self.node_panel = None

        self.camera.handle_event(event)
        return None
    def _node_by_id(self,nid):
        for n in self.nodes:
            if n["id"] == nid:
                return n
        return None
    def _node_screen_pos(self,node):
        pos = node.get("position",{})
        return self.camera.world_to_screen(pos.get("x",0),pos.get("y",0))
    def _node_at_screen(self,sx,sy,radius=18):
        best,best_d = None,float("inf")
        for n in self.nodes:
            nx,ny = self._node_screen_pos(n)
            d = math.hypot(sx-nx,sy-ny)
            if d <radius and d <best_d:
                best,best_d = n,d
        return best
    def _edge_at_screen(self,sx,sy,tol=8):
        best,best_d = None,float("inf")
        for e in self.edges:
            nf = self._node_by_id(e["from_node"])
            nt = self._node_by_id(e["to_node"])
            if not nf or not nt:
                continue
            x1,y1 = self._node_screen_pos(nf)
            x2,y2 = self._node_screen_pos(nt)
            abx,aby = x2-x1,y2-y1
            apx,apy= sx-x1,sy-y1
            ab2 = abx*abx+aby*aby
            if ab2 == 0:
                continue
            t=max(0.0,min(1.0,(apx*abx+apy*aby)/ab2))
            d = math.hypot(sx-(x1+t*abx),sy-(y1+t*aby))
            if d<tol and d<best_d:
                best,best_d=e,d
        return best

    def draw(self,surface):
        self.tick +=1
        mouse = pygame.mouse.get_pos()
        canvas_rect = pygame.Rect(TOOLBAR_W,0,self.screen_w-TOOLBAR_W,self.screen_h)
        surface.fill(BG_DARK)
        dot_ox = int(self.camera.pan_x)%DOT_SPACING-DOT_SPACING
        dot_oy = int(self.camera.pan_y)%DOT_SPACING-DOT_SPACING
        surface.blit(self._dot_surf,(TOOLBAR_W+dot_ox,dot_oy),
                     pygame.Rect(0,0,
                                 self.screen_w-TOOLBAR_W+DOT_SPACING,
                                 self.screen_h+DOT_SPACING))
        for n in self.nodes:
            sx,sy = self._node_screen_pos(n)
            icon_node = {
                "id": n["id"],
                "name": n["name"],
                "type": n.get("type",n["_collection"]),
                "subtype": n.get("type",""),
                "raw": n,
            }
            draw_icons(surface,icon_node,sx,sy,36)
            if self.camera.zoom>0.8:
                draw_label(surface,n["name"],sx,sy,self.fonts["tiny"],node_size=18)
            error_ids = {v["id"] for v in self._issues if v["severity"] == "error"}
            warning_ids = {v["id"] for v in self._issues if v["severity"] == "warning"}
            if n["id"] in error_ids:
                pygame.draw.circle(surface,(255,60,60),(sx,sy),24,2)
            elif n["id"] in warning_ids:
                pygame.draw.circle(surface,(255,200,50),(sx,sy),24,2)
            if n["id"] == self.selected_node_id:
                pygame.draw.circle(surface,(100,180,255),(sx,sy),22,2)
        LINE_STYLE = {
            500: ((255,255,255),3),
            138: ((180,180,180),2),
            25: ((80,80,80),1),
        }
        for e in self.edges:
            nf = self._node_by_id(e["from_node"])
            nt = self._node_by_id(e["to_node"])
            if not nf or not nt:
                continue
            x1,y1 = self._node_screen_pos(nf)
            x2,y2 = self._node_screen_pos(nt)
            col,w = LINE_STYLE.get(e["voltage_kv"],((80,80,80),1))
            pygame.draw.line(surface,col,(x1,y1),(x2,y2),w)
            if self.camera.zoom>1.2:
                mx,my = (x1+x2)//2,(y1+y2)//2
                lbl =self.fonts["tiny"].render(f"{e['voltage_kv']}kv", True, col)
                surface.blit(lbl,(mx-lbl.get_width()//2,my-8))
        if self._pending_edge_from:
            nf = self._node_by_id(self._pending_edge_from)
            if nf:
                x1,y1 = self._node_screen_pos(nf)
                mx,my =  pygame.mouse.get_pos()
                pygame.draw.line(surface,(80,150,255),(x1,y1),(mx,my),1)
                hint = self.fonts["tiny"].render("click second node | ESC cancel", True,(80,150,255))
                surface.blit(hint,(TOOLBAR_W+10,8))
        if self.node_panel:
            self.node_panel.draw(surface)
        if self.edge_panel:
            self.edge_panel.draw(surface)
        pygame.draw.line(surface,BORDER,(TOOLBAR_W,0),(TOOLBAR_W,self.screen_h),1)
        pygame.draw.rect(surface,TOOLBAR_BG,pygame.Rect(0,0,TOOLBAR_W,self.screen_h))
        pygame.draw.rect(surface,TOOLBAR_BRD,pygame.Rect(0,0,TOOLBAR_W,self.screen_h),1)
        title = self.fonts["title"].render("MAP BUILDER",True,GOLD)
        surface.blit(title,(TOOLBAR_W//2-title.get_width()//2,16))
        pygame.draw.line(surface,BORDER,(8,38),(TOOLBAR_W-8,38),1)
        for btn in self.toolbar_buttons:
            btn.update(mouse)
            btn.draw(surface)
        self._draw_group_labels(surface)
        brd = BTN_BRD if self.back_rect.collidepoint(mouse) else TOOLBAR_BRD
        bg = BTN_HOVER if self.back_rect.collidepoint(mouse) else BTN_NORMAL
        pygame.draw.rect(surface,bg,self.back_rect,border_radius=3)
        pygame.draw.rect(surface,brd,self.back_rect,1,border_radius=3)
        mhov = self._meta_btn_rect.collidepoint(mouse)
        mcol = BTN_HOVER if mhov else BTN_NORMAL
        pygame.draw.rect(surface,mcol,self._meta_btn_rect,border_radius=3)
        pygame.draw.rect(surface,BTN_BRD,self._meta_btn_rect,1,border_radius=3)
        menu_label = self.fonts["tiny"].render("Map Settings",True,GOLD)
        surface.blit(menu_label,(self._meta_btn_rect.x+8,self._meta_btn_rect.centery-menu_label.get_height()//2))
        err_count = sum(1 for v in self._issues if v["severity"] == "error")
        warn_count = sum(1 for v in self._issues if v["severity"] == "warning")
        if err_count:
            vc, vbrd = (100, 25, 25), (200, 60, 60)
        elif warn_count:
            vc, vbrd = (90, 70, 10), (220, 180, 50)
        else:
            vc, vbrd = BTN_NORMAL, BTN_BRD
        vhov = self._validate_btn_rect.collidepoint(pygame.mouse.get_pos())
        pygame.draw.rect(surface, BTN_HOVER if vhov else vc, self._validate_btn_rect, border_radius=3)
        pygame.draw.rect(surface, vbrd, self._validate_btn_rect, 1, border_radius=3)
        badge = f"E: {err_count}, W: {warn_count}" if (err_count or warn_count) else "Valid"
        vl = self.fonts["tiny"].render(f"Validate {badge}", True, TEXT)
        surface.blit(vl, (self._validate_btn_rect.x + 6, self._validate_btn_rect.centery - vl.get_height() // 2))
        ehov = self._export_btn_rect.collidepoint(mouse)
        pygame.draw.rect(surface,(30,90,40)if ehov else (20,65,30),self._export_btn_rect,border_radius=3)
        pygame.draw.rect(surface,(60,180,80),self._export_btn_rect,1,border_radius=3)
        el = self.fonts["small"].render("Export JSON",True,TEXT)
        surface.blit(el,(self._export_btn_rect.x+8,self._export_btn_rect.centery-el.get_height()//2))
        if self._save_msg and self.tick-self._save_msg_tick<180:
            ml = self.fonts["tiny"].render(self._save_msg,True,(80,220,100))
            surface.blit(ml,(self._export_btn_rect.x,self._export_btn_rect.bottom+4))
        if self._show_issues:
            self._draw_issues_panel(surface)
        if self.meta_panel and not self.meta_panel.closed:
            self.meta_panel.draw(surface)
        lbl = self.fonts["small"].render("Back",True,TEXT)
        surface.blit(lbl,(self.back_rect.centerx-lbl.get_width()//2,
                          self.back_rect.centery-lbl.get_height()//2))
        self._draw_status_bar(surface,mouse)
        if self.active_tool and mouse[0]>TOOLBAR_W:
            hint = self.fonts["tiny"].render(f"[{self.active_tool}] click to place | ESC to cancel",True,GOLD)
            surface.blit(hint,(TOOLBAR_W+10,8))
    def _draw_issues_panel(self,surface):
        if not self._issues:
            lines = [{"id":None,"message":"No issues found","severity":"ok"}]
        else:
            lines = self._issues
        W = 260
        row = 16
        h=28+len(lines)*row+8
        x = TOOLBAR_W+8
        y = 40
        bg = pygame.Surface((W,h),pygame.SRCALPHA)
        bg.fill((10,14,24,230))
        surface.blit(bg,(x,y))
        r = pygame.Rect(x,y,W,h)
        pygame.draw.rect(surface,BTN_BRD,r,1,border_radius=4)
        title_label = self.fonts["bold"].render("VALIDATION REPORT",True,GOLD)
        surface.blit(title_label,(x+8,y+6))
        pygame.draw.line(surface,BORDER,(x,y+22),(x+W,y+22),1)
        iy = y+26
        sev_cols = {"error":(255,80,80),"warning":(255,200,50),"ok":(80,200,120)}
        for issue in lines:
            col = sev_cols.get(issue["severity"],DIM)
            pygame.draw.circle(surface,col,(x+10,iy+6),4)
            msg = self.fonts["tiny"].render(issue["message"][:38],True,col)
            surface.blit(msg,(x+20,iy))
            iy += row


    def _draw_group_labels(self,surface):
        drawn = set()
        for btn in self.toolbar_buttons:
            g = btn.node_type["group"]
            if g in drawn:
                continue
            drawn.add(g)
            col = GROUP_COLOURS.get(g,DIM)
            lbl = self.fonts["tiny"].render(g.upper(),True,col)
            surface.blit(lbl,(btn.rect.x+8,btn.rect.y-10))
    def _draw_status_bar(self,surface,mouse):
        bar_h = 24
        bar_rect = pygame.Rect(TOOLBAR_W,self.screen_h-bar_h,self.screen_w-TOOLBAR_W,bar_h)
        pygame.draw.rect(surface,TOOLBAR_BG,bar_rect)
        pygame.draw.line(surface,BORDER,(TOOLBAR_W,self.screen_h-bar_h),(self.screen_w,self.screen_h-bar_h),1)
        if mouse[0]>TOOLBAR_W:
            wx,wy = self.camera.screen_to_world(*mouse)
            coord_text = f"x {wx:.1f} y {wy:.1f} zoom {self.camera.zoom:.2f}x"
        else:
            coord_text = f"zoom {self.camera.zoom:.2f}x"
        stat = f"nodes: {len(self.nodes)} edges: {len(self.edges)} {coord_text}"
        lbl = self.fonts["tiny"].render(stat,True,DIM)
        surface.blit(lbl, (TOOLBAR_W + 8, self.screen_h-bar_h+5))
