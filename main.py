from math import acosh
import os,sys
import pygame
from pygame import MOUSEBUTTONDOWN
from utils import camera as cam_module
from utils import map_renderer
from utils.game_over import GameOverScreen
from utils.main_menu import MainMenu
from utils.tutorial import TutorialStep, TutorialManager
from utils.disclaimer import DisclaimerScreen

def resource_path(relative):
    base = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, relative)

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

def make_game(map,with_tutorial=False):
    global cam_module,map_renderer
    camera = cam_module.Camera()
    nodes, lines,data = map_renderer.load_grid(resource_path(map))
    tutorial = None
    if with_tutorial:
        node_map = {n['id']: n for n in nodes}
        tutorial = TutorialManager(SCREEN_WIDTH,SCREEN_HEIGHT,node_map,camera)
    oakridge = map_renderer.MapRenderer(nodes,lines,data, camera, font, font_bold, SCREEN_WIDTH,SCREEN_HEIGHT,tutorial=tutorial)

    return camera,oakridge

STATE = 'disclaimer'
menu = MainMenu(SCREEN_WIDTH,SCREEN_HEIGHT)
camera,oakridge = None,None
game_over_screen = None
disclaimer = DisclaimerScreen(SCREEN_WIDTH,SCREEN_HEIGHT)
clock = pygame.time.Clock()
run = True



while run:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
        elif STATE == 'disclaimer':
            disclaimer.handle_event(event)
            if disclaimer.done:
                STATE = 'menu'
        elif STATE == 'menu':
            action = menu.handle_event(event)
            if action == 'simulation':
                camera,oakridge = make_game("maps/oakridge_grid.json")
                STATE = 'game'
            elif action == 'tutorial':
                camera, oakridge = make_game("maps/oakridge_grid.json",True)
                STATE = 'game'
            elif action == 'quit':
                run = False
        elif STATE == 'game':
            if oakridge.map_click(event):
                continue
            camera.handle_event(event)
        elif STATE == 'game_over':
            result = game_over_screen.handle_event(event)
            if result == 'restart':
                camera,oakridge = make_game("maps/oakridge_grid.json")
                game_over_screen = None
                STATE = 'game'
            elif result == 'menu':
                game_over_screen = None
                camera = None
                oakridge = None
                STATE = 'menu'

    screen.fill((10,10,10))
    if STATE == 'disclaimer':
        disclaimer.draw(screen)
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
    elif STATE == 'game_over':
        oakridge.draw(screen)
        game_over_screen.draw(screen)
        clock.tick(60)

    elif STATE == 'menu':
        menu.draw(screen)
        clock.tick(60)

    pygame.display.flip()