from functools import total_ordering

import numpy as np
import random
import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from pygame.event import set_keyboard_grab

INERTIA_CONSTANTS = {
    'nuclear': 6.0,
    'pressurized_water_reactor': 6.0,
    'hydro':4.0,
    'run_of_river': 4.0,
    'gas':5.0,
    'combined_cycle': 5.0,
    'open_cycle_gas_turbine':3.0,
    'biomass':4.0,
    'wood_waste_combustion':4.0,
    'wind':0.0,
    'solar':0.0,
    'battery':0.0
}

@dataclass
class GeneratorState:
    id:str
    name:str
    gen_type:str
    installed_capacity_mw:float
    min_output_mw: float
    max_output_mw:float
    ramp_rate_mw_per_min:float
    startup_time_minutes:float
    fuel_type:str
    efficiency_percent:float
    carbon_kg_per_mwh:float
    availability_factor:float
    forced_outage_rate:float
    seasonal_derating:dict
    node_id: str

    status: str = 'online' #online, standby, tripped, starting
    current_output_mw: float = 0.0
    setpoint_mw: float = 0.0
    operator_setpoint_mw:float=0.0
    startup_timer: float = 0.0
    outage_timer: float = 0.0

    @property
    def inertia_constant(self):
        return INERTIA_CONSTANTS.get(self.gen_type, INERTIA_CONSTANTS.get(self.fuel_type, 3.0))
    def effective_max_mw(self, season):
        derating = self.seasonal_derating.get(season, 1.0)
        return self.installed_capacity_mw*self.availability_factor*derating

@dataclass
class LineState:
    id:str
    name:str
    from_node:str
    to_node:str
    voltage_kv: float
    thermal_limit_mw: float
    impedance_pu: float
    circuits: int
    status:str = 'online'
    flow_mw: float = 0.0
    overload_timer: float = 0.0 # seconds above limit

@dataclass
class LoadState:
    id:str
    name:str
    node_id:str
    peak_demand_mw:float
    average_demand_mw:float
    demand_profile:str
    priority_class:int
    interruprible_load_mw: float
    backup_generation_mw:float
    voltage_sensitivity: str

    current_demand_mw: float = 0.0
    shed_mw: float = 0.0 #amount currently shed by UFLS or controller
    on_backup: bool = False
    interruption_cooldown: float=0.0

@dataclass
class StorageState:
    id: str
    name: str
    node_id: str
    capacity_mwh: float
    max_charge_rate_mw: float
    max_discharge_rate_mw: float
    round_trip_efficiency: float
    min_soc_pecent: float
    max_soc_percent: float
    response_time_seconds: float
    storage_type: str

    current_energy_mwh: float = 0.0
    charge_rate_mw: float = 0.0 # + chanrging, - discharging
    setpoint_mw:float = 0.0
    status: str = 'online'

    @property
    def soc_percent(self):
        return (self.current_energy_mwh/self.capacity_mwh)*100
    @property
    def can_charge(self):
        return self.soc_percent<self.max_soc_percent
    @property
    def can_discharge(self):
        return self.soc_percent>self.min_soc_pecent

#ENGINE
class SimulationEngine:
    TICK_SECONDS = 1.0
    F_NOMINAL = 60.0
    INERTIA_MULTIPLIER=1

    UFLS_STAGES = [
        (50,3,'UFLS Stage 1 - shedding class 3 loads'),
        (50,2,'UFLS Stage 2 - shedding class 2 loads')
    ]
    UFLS_RESTORE = {
        3:61.2,
        2:61.3
    }
    COLLAPSE_HZ = 58.4

    def __init__(self, grid_data:dict):
        self.data = grid_data
        self.time_multiplier = 1.0
        self.sim_time_min = 300.0
        self.frequency_hz =60.0
        self.alarms: List[dict] = []
        self.game_over = False
        self.game_over_reason = ''
        self.hvdc_flow_mw = 150.0 #+ export
        self.hvdc_setpoint_mw = 150.0
        self._ufls_cooldown = 0.0
        self.wind_speed_ms=8.0
        self.cloud_cover = 0.3
        self.sim_day = 0
        self.score = 0.0
        self._score_display = 0

        self.generators: Dict[str, GeneratorState] = {}
        self.lines: Dict[str, LineState] = {}
        self.loads: Dict[str, LoadState] = {}
        self.storage: Dict[str, StorageState] = {}
        self.node_ids: List[str] = []

        self._build_state(grid_data)
        self._build_bus_index()
        self._build_b_matrix()

        for g in self.generators.values():
            if g.status == 'online':
                g.current_output_mw = g.min_output_mw
                g.setpoint_mw = g.min_output_mw
            elif g.status == 'standby':
                g.current_output_mw = 0.0
                g.setpoint_mw = 0.0

        for s_data in grid_data['storage_nodes']:
            sid = s_data['id']
            if sid in self.storage:
                soc = s_data.get('state_of_charge_percent', 50)/100
                self.storage[sid].current_energy_mwh = (soc*self.storage[sid].capacity_mwh)


    def _build_state(self, data):
        for g in data['generation_nodes']:
            pos = g.get('position')
            if pos is None:
                continue
            gs = GeneratorState(
                id = g['id'],
                name = g['name'],
                gen_type = g.get('subtype', g.get('type')),
                installed_capacity_mw=g['installed_capacity_mw'],
                min_output_mw=g.get('min_output_mw', 0),
                max_output_mw=g['max_output_mw'],
                ramp_rate_mw_per_min = g.get('ramp_rate_mw_per_min', 5)*60,
                startup_time_minutes= g.get('startup_time_minutes', 60),
                fuel_type=g.get('fuel_type', 'unknown'),
                efficiency_percent=g.get('efficiency_percent',40),
                carbon_kg_per_mwh=g.get("carbon_kg_per_mwh",0),
                availability_factor=g.get("availability_factor",0.95),
                forced_outage_rate=g.get("forced_outage_rate",0.02),
                seasonal_derating=g.get("seasonal_derating", {}),
                node_id= g['id'],
                status = g.get('status', 'online'),
                current_output_mw=0.0,
                setpoint_mw=0.0,
                operator_setpoint_mw=0.0
            )
            self.generators[g['id']] = gs
        for s in data['storage_nodes']:
            pos = s.get('position')
            if pos is None:
                continue
            ss = StorageState(
                id = s['id'],
                name = s['name'],
                node_id=s['id'],
                capacity_mwh=s['capacity_mwh'],
                max_charge_rate_mw=s['max_charge_rate_mw'],
                max_discharge_rate_mw=s['max_discharge_rate_mw'],
                round_trip_efficiency=s['round_trip_efficiency'],
                min_soc_pecent=s.get('min_soc_percent',10),
                max_soc_percent=s.get('max_soc_percent',95),
                response_time_seconds=s.get('response_time_seconds', 1),
                storage_type=s.get('type','battery'),
                status=s.get('status','online')
            )
            self.storage[s['id']]=ss

        for line in (data['transmission_lines'] + data['distribution_lines']):
            ls = LineState(
                id=line['id'],
                name=line['name'],
                from_node=line['from_node'],
                to_node=line['to_node'],
                voltage_kv=line['voltage_kv'],
                thermal_limit_mw=line['thermal_limit_mw'],
                impedance_pu=line.get('impedance_pu',0.85),
                circuits=line.get('circuits', 1),
                status=line.get('status','online')
            )
            self.lines[line['id']] = ls

        for load in data['load_nodes']:
            pos = load.get('position')
            if pos is None:
                continue
            ld = LoadState(
                id = load['id'],
                name=load['name'],
                node_id=load['id'],
                peak_demand_mw=load['peak_demand_mw'],
                average_demand_mw=load['average_demand_mw'],
                demand_profile=load.get('demand_profile','flat'),
                priority_class=load.get('priority_class', 3),
                interruprible_load_mw=load.get('interruptible_load_mw', 0),
                backup_generation_mw=load.get('backup_generation_mw',0),
                voltage_sensitivity=load.get('voltage_sensitivity','medium'),
                current_demand_mw=load.get('average_demand_mw',0)
            )
            self.loads[load['id']] =ld
    def _build_bus_index(self):
        ids = set()
        for sub in self.data['substation_nodes']:
            ids.add(sub['id'])
        for gid in self.generators:
            ids.add(gid)
        for sid in self.storage:
            ids.add(sid)
        for lid in self.loads:
            ids.add(lid)
        self.node_ids = sorted(ids)
        self.bus_index = {nid:i for i, nid in enumerate(self.node_ids)}
        self.n_buses = len(self.node_ids)
    def _build_b_matrix(self):
        # Build DC power flow susceptance matrix B
        #B[i][i] = sum of susceptances of all lines at bus i
        #B[i][j] = -susceptance of line between i and j
        #Susceptance = 1 / impedance_pu

        n = self.n_buses
        B = np.zeros((n,n))
        for line in self.lines.values():
            if line.status != 'online':
                continue
            fi = self.bus_index.get(line.from_node)
            ti = self.bus_index.get(line.to_node)
            if fi is None or ti is None:
                continue
            b = 1.0/line.impedance_pu
            B[fi][fi] += b
            B[ti][ti] += b
            B[fi][ti] -= b
            B[ti][fi] -= b
        self.B_full = B
    def _solve_dc_power_flow(self):
        # Solve dc powerflow using reduced B matrix (SUB-001 as slack) dict{line_id:flow_mw}
        slack_id = 'SUB-001'
        slack_idx = self.bus_index.get(slack_id,0)

        P = np.zeros(self.n_buses)

        for g in self.generators.values():
            idx = self.bus_index.get(g.node_id)
            if idx is not None and g.status == 'online':
                P[idx] += g.current_output_mw
        for s in self.storage.values():
            idx = self.bus_index.get(s.node_id)
            if idx is not None and s.status == 'online':
                P[idx] -= s.charge_rate_mw
        for load in self.loads.values():
            idx = self.bus_index.get(load.node_id)
            if idx is not None:
                net_demand = load.current_demand_mw - load.shed_mw
                P[idx] -= max(0.0, net_demand)
        hvdc_idx = self.bus_index.get('SUB-009')
        if hvdc_idx is not None:
            P[hvdc_idx] -= self.hvdc_flow_mw

        mask = [i for i in range(self.n_buses) if i != slack_idx]
        B_red = self.B_full[np.ix_(mask,mask)]
        P_red = P[mask]

        try:
            theta_red = np.linalg.solve(B_red,P_red)
        except np.linalg.LinAlgError:
            return {}

        theta = np.zeros(self.n_buses)
        for i,val in zip(mask, theta_red):
            theta[i] = val

        flows= {}
        for line in self.lines.values():
            if line.status != 'online':
                flows[line.id] = 0.0
                continue
            fi = self.bus_index.get(line.from_node)
            ti = self.bus_index.get(line.to_node)
            if fi is None or ti is None:
                flows[line.id] = 0.0
                continue
            b = 1.0/ line.impedance_pu
            flows[line.id] = b*(theta[fi]-theta[ti])
        return flows

    def _tick_time(self, dt_seconds):
        self.sim_time_min += dt_seconds/60.0
        if self.sim_time_min >= 1440:
            self.sim_time_min -= 1440
            self.sim_day +=1

    @property
    def current_hour(self):
        return int((self.sim_time_min/60)%24)
    @property
    def current_season(self):
        day = self.sim_day %365
        if day <80 or day >=355: return 'winter'
        if day <172: return 'spring'
        if day <264: return 'summer'
        return 'autumn'

    def _tick_demand(self):
        profiles = self.data['demand_profiles']
        season_modifiers = self.data['seasonal_modifiers']
        season = self.current_season
        s_mod = season_modifiers.get(season, {})
        total_hours = self.sim_time_min/60.0
        current_hour = int(total_hours)%24
        next_hour = (current_hour+1)%24
        hour_progress = total_hours%1.0

        for load in self.loads.values():
            profile = profiles.get(load.demand_profile, profiles['flat'])
            factors = profile['hourly_factors']
            hourly_factor = (factors[current_hour]*(1.0-hour_progress)+ factors[next_hour]*hour_progress)
            if load.demand_profile == 'residential':
                seasonal = s_mod.get('residential_modifier', 1.0)
            elif load.demand_profile in ('industrial','port_industrial'):
                seasonal = s_mod.get('industrial_modifier', 1.0)
            else:
                seasonal = s_mod.get('commercial_modifier', 1.0)

            noise = random.gauss(0,0.005)
            load.current_demand_mw = load.peak_demand_mw * hourly_factor * seasonal*(1+noise)
            load.current_demand_mw = max(0.0, load.current_demand_mw)
            if load.interruption_cooldown >0:
                load.interruption_cooldown -=1/60.0
    def _tick_weather(self,dt_seconds):
        mean_wind = 9.0
        theta = 0.1
        sigma = 0.5
        dt_min = dt_seconds/60.0
        self.wind_speed_ms +=(
            theta*(mean_wind-self.wind_speed_ms)*dt_min+sigma*random.gauss(0,1)*math.sqrt(dt_min)
        )
        self.wind_speed_ms = max(0.0,self.wind_speed_ms)
        self.cloud_cover += random.gauss(0,0.01)*dt_min
        self.cloud_cover = max(0.0,min(1.0,self.cloud_cover))
    def _calc_wind_output(self, g:GeneratorState):
        v = self.wind_speed_ms
        cut_in = 3.5
        cut_out = 25.0
        rated_spd = 12.0
        if v < cut_in or v >= cut_out:
            return 0.0
        if v<rated_spd:
            return g.installed_capacity_mw*(v/rated_spd)**3
        return g.installed_capacity_mw
    def _calc_solar_output(self,g:GeneratorState):
        season = self.current_season
        hour = (self.sim_time_min/60.0)%24
        derating = g.seasonal_derating.get(season,0.1)
        sunrise,sunset = 6,20
        if hour<sunrise or hour>=sunset:
            return 0.0
        daylight_frac = math.sin(math.pi*(hour-sunrise)/(sunset-sunrise))
        return (g.installed_capacity_mw*derating*daylight_frac*(1.0-self.cloud_cover*0.8))
    def _tick_dispatch(self, dt_seconds):
        dt_min = dt_seconds/60.0
        season = self.current_season
        for g in self.generators.values():
            
            if g.status == 'tripped':
                g.current_output_mw=0.0
                if g.outage_timer>=0: 
                    g.outage_timer -= dt_min
                    if g.outage_timer<=0:
                        g.status = 'standby'
                        self._add_alarm(f"{g.name} restored to standby", "info")
                continue
            if g.status == 'starting':
                g.startup_timer -= dt_min
                if g.startup_timer<=0:
                    g.status = 'online'
                    self._add_alarm(f"{g.name} is now online", 'info')
            if g.status == 'tripping':
                g.current_output_mw -= g.ramp_rate_mw_per_min*dt_min*5
                if g.current_output_mw <=0.0:
                    g.current_output_mw=0.0
                    g.status = 'tripped'
                    g.outage_timer=0.0
                    self._add_alarm(f"{g.name} offline",'warning')
            if g.status != 'online':
                
                continue
            if g.fuel_type == 'wind':
                g.current_output_mw = self._calc_wind_output(g)
                g.setpoint_mw = g.current_output_mw
                continue
            if g.fuel_type == 'solar':
                g.current_output_mw = self._calc_solar_output(g)
                g.setpoint_mw = g.current_output_mw
                continue
            eff_max = g.effective_max_mw(season)
            freq_error = self.frequency_hz-self.F_NOMINAL
            if g.inertia_constant>40 and abs(freq_error)>0.05:
                DROOP_R=0.02
                headroom = eff_max-g.current_output_mw
                droop_offset = -(freq_error/self.F_NOMINAL)*(1.0/DROOP_R)*eff_max
                droop_offset = max(-g.operator_setpoint_mw+g.min_output_mw,min(eff_max-g.operator_setpoint_mw,droop_offset))
                g.setpoint_mw = g.operator_setpoint_mw+droop_offset
            else:
                g.setpoint_mw = g.operator_setpoint_mw
            target = max(g.min_output_mw,min(eff_max, g.setpoint_mw))

            delta = target-g.current_output_mw
            max_delta= g.ramp_rate_mw_per_min *dt_min
            g.current_output_mw += math.copysign(min(abs(delta), max_delta), delta)

    def _tick_storage(self, dt_seconds):
        dt_hours = dt_seconds/3600.0
        for s in self.storage.values():
            if s.status != 'online':
                continue
            ramp_rate_mw_per_sec = s.max_charge_rate_mw/s.response_time_seconds
            delta = s.setpoint_mw-s.charge_rate_mw
            max_step=ramp_rate_mw_per_sec*dt_seconds
            s.charge_rate_mw += math.copysign(min(abs(delta),max_step),delta)
            rate = s.charge_rate_mw
            if rate >0:
                if not s.can_charge:
                    s.charge_rate_mw = 0
                    s.setpoint_mw = 9
                    continue
                max_rate = min(s.max_charge_rate_mw, (s.max_soc_percent-s.soc_percent)/100 *s.capacity_mwh/dt_hours)
                actual = min(rate,max_rate)
                s.current_energy_mwh += (actual*dt_hours*s.round_trip_efficiency)
            elif rate<0:
                if not s.can_discharge:
                    s.charge_rate_mw = 0
                    s.setpoint_mw = 0
                    continue
                max_rate = min(s.max_discharge_rate_mw,(s.soc_percent-s.min_soc_pecent)/100*s.capacity_mwh/dt_hours)
                actual = min(abs(rate),max_rate)
                s.current_energy_mwh -= (actual*dt_hours/s.round_trip_efficiency)
            s.current_energy_mwh = max(0.0, min(s.capacity_mwh, s.current_energy_mwh))
    def _tick_hvdc(self,dt_seconds):
        ic = self.data['interconnects'][0]
        ramp_per_sec = ic['ramp_rate_mw_per_min']/60.0
        delta = self.hvdc_setpoint_mw-self.hvdc_flow_mw
        max_step = ramp_per_sec*dt_seconds
        self.hvdc_flow_mw += math.copysign(min(abs(delta),max_step),delta)
    def _tick_power_flow(self):
        flows = self._solve_dc_power_flow()
        for lid, flow in flows.items():
            if lid in self.lines:
                self.lines[lid].flow_mw = flow
    def _tick_frequency(self,dt_seconds):
        #swing equation to calculate frequency
        total_gen = sum(g.current_output_mw for g in self.generators.values() if g.status =='online' or g.status == 'tripping')
        for s in self.storage.values():
            if s.status =='online':
                total_gen -= s.charge_rate_mw
        total_gen -= self.hvdc_flow_mw
        total_load = sum(max(0.0, l.current_demand_mw-l.shed_mw)for l in self.loads.values())
        imbalance = total_gen - total_load

        total_inertia = sum(g.inertia_constant*g.installed_capacity_mw for g in self.generators.values() if g.status == 'online' and g.inertia_constant>0)*self.INERTIA_MULTIPLIER
        if total_inertia <1.0:
            total_inertia=1.0
        if abs(imbalance)<10:
            self.frequency_hz += (self.F_NOMINAL - self.frequency_hz) * 0.01 * dt_seconds
        else:
            df_dt = (imbalance/(2*total_inertia)) *self.F_NOMINAL
            self.frequency_hz += df_dt*dt_seconds
            self.frequency_hz = max(57.0,min(63.0,self.frequency_hz))
        if self.frequency_hz <=59.5:
            self.time_multiplier = 1
    def _tick_protection(self,dt_seconds):
        for line in self.lines.values():
            if line.status != 'online':
                continue
            loading = abs(line.flow_mw)/line.thermal_limit_mw
            if loading >1.0:
                line.overload_timer += dt_seconds
                relay_time = max(0.1,2.0-(loading-1.0)*10)
                if line.overload_timer >= relay_time:
                    self._trip_line()
            if loading > 0.8:
                self._add_alarm(
                    f"{line.name} {loading*100:.0f}% loaded",
                    'warning' if loading<0.95 else 'critical'
                )
            else:
                line.overload_timer = 0.0
    def _trip_line(self, line: LineState):
        line.status = 'tripped'
        line.flow_mw = 0.0
        line.overload_timer = 0.0
        self._add_alarm(f"LINE TRIP: {line.name}", 'critical')
        self._build_b_matrix()
    def _check_cascade(self):
        changed = True
        iterations = 0
        while changed and iterations<20:
            changed = False
            iterations +=1
            flows = self._solve_dc_power_flow()
            for lid, flow in flows.items():
                line = self.lines.get(lid)
                if abs(flow)>line.thermal_limit_mw*1.0:
                    self._trip_line(line)
                    changed = True
                    break
    def _tick_ufls(self):
        #Auto Load shed (HAS BEEN DEACTIVATED FOR MAKING GAMEPLAY TOO EASY)
        shed_occured = False
        for threshold_hz, priority_class, alarm_text in self.UFLS_STAGES:
            if self.frequency_hz< threshold_hz:
                self._add_alarm(alarm_text,'critical')
                self._ufls_cooldown = 30.0
                shed_occured = True
                for load in self.loads.values():
                    if load.priority_class == 0:
                        continue
                    if load.priority_class < priority_class:
                        continue
                    unshed = load.current_demand_mw-load.shed_mw
                    if unshed>0:
                        load.shed_mw = min(load.current_demand_mw,load.shed_mw+20.0)
        if not shed_occured and self._ufls_cooldown <= 0:
            if self.frequency_hz> self.UFLS_RESTORE[3]:
                for load in self.loads.values():
                    if load.priority_class ==3 and load.shed_mw>0:
                        load.shed_mw = max(0.0,load.shed_mw-1.0)
            if self.frequency_hz > self.UFLS_RESTORE[2]:
                for load in self.loads.values():
                    if load.priority_class ==2 and load.shed_mw > 0:
                        load.shed_mw = max(0.0, load.shed_mw - 1.0)

        """for threshold_hz, priority_class, alarm_text in self.UFLS_STAGES:

            if self.frequency_hz<threshold_hz:
                for load in self.loads.values():
                    print(load.interruprible_load_mw)
                    if (load.priority_class>=priority_class and load.shed_mw<load.current_demand_mw and load.interruprible_load_mw>0):
                        shed_amount = min(load.interruprible_load_mw,load.current_demand_mw-load.shed_mw)

                        load.shed_mw += shed_amount
                        self._add_alarm(alarm_text,'critical')
                        self._add_alarm(f"Shedding {shed_amount:.0f}MW at {load.name}", 'critical')
                        break

        if self.frequency_hz>59.8:
            for load in self.loads.values():
                if load.id == "LOAD-002":
                    print(load.shed_mw>0, load.priority_class>=3, load.shed_mw, load.priority_class)
                if load.shed_mw>0 and load.priority_class<=3:
                    load.shed_mw = max(0.0,load.shed_mw-1.0)"""
        if self.frequency_hz<self.COLLAPSE_HZ:
            self.game_over=True
            self.game_over_reason = "Grid collapse - frequency below 58.4 Hz"
    def _tick_events(self, dt_seconds):
        ticks_per_hour = 3600/dt_seconds
        for g in self.generators.values():
            if g.status != 'online':
                continue
            rate = g.forced_outage_rate/(8760*ticks_per_hour)
            if random.random()<rate:
                g.status = 'tripping'
                g.setpoint_mw = 0.0
                g.outage_timer = random.uniform(240,2880)
                self._add_alarm(f"FORCED OUTAGE: {g.name}", 'critical')

    def _add_alarm(self, text:str,severity:str):
        for alarm in self.alarms[-5:]:
            if alarm['text'] == text:
                return
        self.alarms.append({'text':text,'severity':severity,'time':self.sim_time_min})
        if len(self.alarms) >50:
            self.alarms = self.alarms[-50:]
            
    def _tick_score(self,dt_seconds):
        hz_error = abs(self.frequency_hz-self.F_NOMINAL)
        if hz_error<0.1:
            freq_score = 1.0
        elif hz_error<0.3:
            freq_score = 0.6
        elif hz_error<0.5:
            freq_score = 0.2
        else:
            freq_score = 0.0
            
        ic = self.data['interconnects'][0]
        max_export = ic['max_export_mw']
        export_score = self.hvdc_flow_mw/max_export
        
        tick_score = (freq_score*0.7+export_score*0.3)*dt_seconds
        self.score = max(0.0,self.score+tick_score)


    def set_generator_setpoint(self, gen_id:str, mw:float):
        g = self.generators.get(gen_id)
        if not g:
            return
        if g.status == 'standby' and mw>0:
            g.status = 'starting'
            g.startup_timer = g.startup_time_minutes
            g.operator_setpoint_mw = mw
            self._add_alarm(f"{g.name} starting up",'info')
        elif g.status == 'online':
            g.setpoint_mw = mw
            g.operator_setpoint_mw = mw

    def trip_generator(self, gen_id:str):
        g = self.generators.get(gen_id)
        if g and g.status == 'online':
            g.status = 'tripping'
            g.setpoint_mw = 0.0
            self._add_alarm(f"{g.name} manually tripped",'warning')

    def set_storage_rate(self,storage_id:str,rate_mw:float):
        s=self.storage.get(storage_id)
        if not s:
            return
        if rate_mw>0:
            s.setpoint_mw = min(rate_mw, s.max_charge_rate_mw)
        else:
            s.setpoint_mw = max(rate_mw, -s.max_discharge_rate_mw)
    def set_hvdc_flow(self,mw):
        ic = self.data['interconnects'][0]
        self.hvdc_setpoint_mw = max(-ic['max_import_mw'],min(ic['max_export_mw'],mw))

    def reset_shed_load(self,load_id:str):
        load = self.loads.get(load_id)
        if load and load.priority_class>0:
            load.shed_mw=0.0

    def tick(self, real_dt_seconds:float):
        #call every frame, real time converted to ticks with time_multiplier
        if self.game_over:
            return
        sim_dt = real_dt_seconds *self.time_multiplier
        self._ufls_cooldown = max(0.0,self._ufls_cooldown-sim_dt)
        self._tick_time(sim_dt)
        self._tick_demand()
        self._tick_weather(sim_dt)
        self._tick_dispatch(sim_dt)
        self._tick_storage(sim_dt)
        self._tick_hvdc(sim_dt)
        self._tick_power_flow()
        self._tick_protection(sim_dt)
        self._check_cascade()
        self._tick_frequency(sim_dt)
        self._tick_ufls()
        self._tick_events(sim_dt)
        self._tick_score(sim_dt)

    def hud_data(self) -> dict:
        total_gen = sum(
            g.current_output_mw for g in self.generators.values()
        )
        total_load = sum(
            max(0.0, l.current_demand_mw-l.shed_mw) for l in self.loads.values()
        )
        for s in self.storage.values():
            if s.charge_rate_mw >= 0:
                total_load += s.charge_rate_mw
            else:
                total_gen -= s.charge_rate_mw
        gen_online = sum(
            1 for g in self.generators.values() if g.status == 'online'
        )
        if self.hvdc_flow_mw >=0:
            total_load += self.hvdc_flow_mw
        else:
            total_gen += self.hvdc_flow_mw
        return { 
            'hz':self.frequency_hz,
            'gen_mw':total_gen,
            'load_mw':total_load,
            'export_mw':self.hvdc_flow_mw,
            'alarms':self.alarms[-10:],
            'time_multiplier':self.time_multiplier,
            'game_over': self.game_over,
            'game_over_reason':self.game_over_reason,
            'game_state':{
                'minute':self.sim_time_min%60,
                'hour': self.current_hour,
                'season':self.current_season,
                'day':int(self.sim_time_min/(60*24))+1,
                'score': int(self.score),
                'gen_online':gen_online,
                'gen_total': len(self.generators),
                'total_capacity_mw': sum(
                    g.effective_max_mw(self.current_season) for g in self.generators.values() if g.status == 'online'
                )
            }
        }