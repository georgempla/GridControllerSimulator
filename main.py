from math import acosh
import os,sys
import pygame
from numpy.random import random
from pygame import MOUSEBUTTONDOWN, KEYDOWN, MOUSEWHEEL
from utils import camera as cam_module
from utils import map_renderer
from utils.game_over import GameOverScreen
from utils.main_menu import MainMenu
from utils.tutorial import TutorialStep, TutorialManager
from utils.disclaimer import DisclaimerScreen
from utils.settings import Settings
from utils.sandbox_menu import SandboxMenu
from utils.notification import Notification
from utils.achievments import AchievementsMenu
from utils.custom_map_selector import CustomMapMenu
from utils.map_builder import MapBuilder

#welcome to the game:)
def resource_path(relative):
    base = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, relative)
if sys.platform == "win32":
    os.environ["SDL_AUDIODRIVER"] = "directsound"
elif sys.platform == "linux":
    os.environ["SDL_AUDIODRIVER"] = "pulseaudio"
try:
    pygame.mixer.pre_init(44100, -16, 2, 512)
    pygame.mixer.init()
    AUDIO_ENABLED = True
except pygame.error as e:
    print(f"Audio unavailable: {e}")
    AUDIO_DISABLED = False
pygame.init()

SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
pygame.font.init()

font_bold  = pygame.font.SysFont('consolas', 11, bold=True)
font = pygame.font.SysFont("consolas",10)


screen = pygame.display.set_mode((SCREEN_WIDTH,SCREEN_HEIGHT))
pygame.display.set_caption("Grid Controller Simulator")
icon = pygame.image.load(resource_path("assets/grid_controller.png"))
pygame.display.set_icon(icon)
pygame.scrap.init()


def make_game(map,cur_settings,with_tutorial=False,with_sandbox=False):
    global cam_module,map_renderer,restart_with_sandbox
    camera = cam_module.Camera()
    nodes, lines,data = map_renderer.load_grid(map if os.path.isabs(map) else resource_path(map))
    tutorial = None
    sandbox = None
    restart_with_sandbox = with_sandbox
    if with_tutorial:
        node_map = {n['id']: n for n in nodes}
        tutorial = TutorialManager(SCREEN_WIDTH,SCREEN_HEIGHT,node_map,camera,60.0 if cur_settings['freq'] else 50.0)
    if with_sandbox:
        sandbox = SandboxMenu(SCREEN_WIDTH,SCREEN_HEIGHT)
    oakridge = map_renderer.MapRenderer(nodes,lines,data, camera, font, font_bold, SCREEN_WIDTH,SCREEN_HEIGHT,60.0 if cur_settings['freq'] else 50.0, ach_path,tutorial=tutorial,sandbox=sandbox)

    return camera,oakridge
def play_track(index):
    global cur_settings
    if not AUDIO_ENABLED:
        return
    if cur_settings['calm'] and len(TRACKS) == 4:
        TRACKS.pop(-1)
        index = index%3
    elif not cur_settings['calm'] and len(TRACKS) == 3:
        TRACKS.append(resource_path('assets/alert.ogg'))
    pygame.mixer.music.load(TRACKS[index][0])
    notification_stack.append(Notification(SCREEN_WIDTH,SCREEN_HEIGHT,resource_path("assets/record.png"),TRACKS[index][1],"music",len(notification_stack),author=TRACKS[index][2]))
    pygame.mixer.music.set_volume(cur_settings['music']/100)
    pygame.mixer.music.set_endevent(MUSIC_END)
    pygame.mixer.music.play(fade_ms=150)
def next_track():
    global current_track
    current_track = (current_track+1)%len(TRACKS)
def prev_track():
    global current_track
    current_track=(current_track-1)*len(TRACKS)
    play_track(current_track)
def random_track():
    global current_track
    current_track=random.randint(0,len(TRACKS)-1)
    play_track(current_track)
TRACKS = [
    [resource_path('assets/ambient1.ogg'),"Cylinder Five", "Kevin MacLeod"],
    [resource_path('assets/ambient2.ogg'),"Ossuary 6 - Air", "Kevin MacLeod"],
    [resource_path('assets/ambient3.ogg'), "Echoes of Time", "Kevin MacLeod"],
    [resource_path('assets/alert.ogg'),"Volatile Reaction", "Kevin MacLeod"]
]

current_track=0
STATE = 'disclaimer'
cur_settings = {'fullscreen':False,'freq':True,'music':0,'calm':False}
fullscreen = False
menu = MainMenu(SCREEN_WIDTH,SCREEN_HEIGHT)
camera,oakridge = None,None
game_over_screen = None
restart_with_sandbox = False
achievements = None
settings_menu = Settings(SCREEN_WIDTH,SCREEN_HEIGHT,cur_settings)
disclaimer = DisclaimerScreen(SCREEN_WIDTH,SCREEN_HEIGHT)
clock = pygame.time.Clock()
run = True
MUSIC_END = pygame.USEREVENT+1
pygame.mixer.music.set_endevent(MUSIC_END)
notification_stack = []
ach_path = resource_path("data/ACHIEVEMENTS.json")
custom_map_menu = None

play_track(current_track)


while run:
    if AUDIO_ENABLED and not pygame.mixer.music.get_busy():
        next_track()
        play_track(current_track)

    for event in pygame.event.get():
        #print(event.type==MOUSEBUTTONDOWN and event.button == 5)
        if event.type == pygame.QUIT:
            run = False
        elif event.type == MUSIC_END:
            next_track()
        elif event.type == KEYDOWN and event.key == pygame.K_RIGHT:
            next_track()
            play_track(current_track)
        elif STATE == 'disclaimer':
            disclaimer.handle_event(event)
            if disclaimer.done:
                STATE = 'menu'
        elif STATE == 'menu':
            action = menu.handle_event(event)
            if action == 'simulation':
                camera,oakridge = make_game("maps/oakridge_grid.json",cur_settings)
                STATE = 'game'
            elif action == 'sandbox':
                camera,oakridge = make_game("maps/oakridge_grid.json",cur_settings,with_sandbox=True)
                STATE = 'game'
            elif action == 'tutorial':
                camera, oakridge = make_game("maps/oakridge_grid.json",cur_settings,True)
                STATE = 'game'
            elif action == 'achievements':
                STATE = 'achievements'
                achievements = AchievementsMenu(SCREEN_WIDTH,SCREEN_HEIGHT,ach_path)
            elif action == 'settings':
                STATE = 'settings'
            elif action == 'custom_map':
                custom_map_menu = CustomMapMenu(SCREEN_WIDTH,SCREEN_HEIGHT,maps_dir=resource_path('maps'))
                STATE='custom_map'
            elif action == 'quit':
                run = False
        elif STATE == 'game':
            if oakridge.map_click(event):
                continue
            camera.handle_event(event)
        elif STATE == 'settings':
            result = settings_menu.handle_event(event)
            if result == 'back':
                STATE = 'menu'
            elif result != None:
                cur_settings = result[0]
                if result[1]:
                    play_track(current_track)
                elif cur_settings['fullscreen'] != fullscreen:
                    fullscreen = not fullscreen
                    if cur_settings['fullscreen']:
                        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT),pygame.FULLSCREEN)
                    else:
                        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        elif STATE == 'game_over':
            result = game_over_screen.handle_event(event)
            if result == 'restart':
                camera,oakridge = make_game("maps/oakridge_grid.json",cur_settings,with_sandbox=restart_with_sandbox)
                game_over_screen = None
                STATE = 'game'
            elif result == 'menu':
                game_over_screen = None
                camera = None
                oakridge = None
                STATE = 'menu'
        elif STATE == "achievements":
            result = achievements.handle_event(event)
            if result == "back":
                STATE = 'menu'
        elif STATE == 'custom_map':
            result = custom_map_menu.handle_event(event)
            if result == 'back':
                STATE = 'menu'
            elif isinstance(result,tuple) and result[0] == 'load':
                camera,oakridge = make_game(result[1],cur_settings)
                STATE = 'game'
            elif isinstance(result,str) and result == 'open_builder':
                map_builder = MapBuilder(SCREEN_WIDTH,SCREEN_HEIGHT)
                STATE = 'map_builder'
        elif STATE == 'map_builder':
            result = map_builder.handle_event(event)
            if result == 'back':
                custom_map_menu = CustomMapMenu(SCREEN_WIDTH,SCREEN_HEIGHT,maps_dir=resource_path('maps'))
                STATE = 'custom_map'
    screen.fill((10,10,10))
    if STATE == 'disclaimer':
        disclaimer.draw(screen)
        clock.tick(60)

    elif STATE == 'game':
        oakridge.draw(screen)
        hud = oakridge.SimulationEngine.hud_data()
        if hud.get('game_over'):
            game_over_screen = GameOverScreen(
                SCREEN_WIDTH,SCREEN_HEIGHT,
                hud.get('game_over_reason', 'Uknown failure'),
                hud.get('game_state',{}).get('score',0)
            )
            STATE = 'game_over'
        for notif in oakridge.SimulationEngine.notifications:
            if notif[0] == 0:
                notification_stack.append(Notification(SCREEN_WIDTH,SCREEN_HEIGHT,resource_path("assets/ach.png"),notif[1],"ach",len(notification_stack)))
        oakridge.SimulationEngine.notifications = []

    elif STATE == 'game_over':
        oakridge.draw(screen)
        game_over_screen.draw(screen)
        clock.tick(60)
    elif STATE == 'settings':
        settings_menu.draw(screen)
        clock.tick(60)
    elif STATE == 'menu':
        menu.draw(screen)
        clock.tick(60)
    elif STATE == 'achievements':
        achievements.draw(screen)
    elif STATE == 'custom_map':
        custom_map_menu.draw(screen)
        clock.tick(60)
    elif STATE == 'map_builder':
        map_builder.draw(screen)
        clock.tick(60)
    for i,notification in enumerate(notification_stack):
        consumed = notification.draw(screen, STATE!="game")

        if consumed:
            notification_stack.pop(i)
            for v,notification2 in enumerate(notification_stack):
                if v>=i:
                    notification2.update_index()

    pygame.display.flip()