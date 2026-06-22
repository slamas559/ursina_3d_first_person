import math
import random
from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
from ursina.shaders import lit_with_shadows_shader

# Initialize the engine window
app = Ursina()

# Window configuration settings
window.title = "3D First Person Labyrinth"
window.borderless = False
window.exit_button.visible = False
window.fps_counter.enabled = True
window.color = color.black  # True black backdrop

# --- CRITICAL FIX: Remove default shader assignment ---
# Don't set default shader globally - we'll apply it where needed
# Entity.default_shader = lit_with_shadows_shader

# --- LIGHTING SYSTEM ---
# 1. COMPLETELY REMOVE THE DUMMY SUN - it's causing light bleed
# The shadow shader doesn't actually need a DirectionalLight if we handle it differently

# 2. AMBIENT LIGHT - SET TO COMPLETE ZERO
# This is CRITICAL - even a tiny amount of ambient light will make everything visible
AmbientLight(color=color.rgb(0, 0, 0))  # PURE BLACK - no ambient light at all

# 3. Instead, we'll use a very faint point light far away to simulate "moonlight" if needed
# But we want COMPLETE darkness, so we'll skip it

# Thicker, darker fog to swallow distant geometry
try:
    from panda3d.core import Fog
    dungeon_fog = Fog("dungeon_fog")
    dungeon_fog.setColor(0, 0, 0)  # Pitch black fog
    dungeon_fog.setExpDensity(0.15)  # Dense fog so light dies faster
    base.render.setFog(dungeon_fog)
except Exception as fog_error:
    print(f"Fog effect skipped: {fog_error}")
    
# --- TEXTURE CONFIGURATION CONFIGS ---
FLOOR_TEX   = "assets/Tile/Tile_13-128x128.png"
WALL_TEX    = "assets/Bricks/Bricks_11-128x128.png"
CEILING_TEX = "assets/Roofs/Roofs_17-128x128.png"

# --- STRUCTURAL LAYOUT MAP ---
MAP_GRID = [
 [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
 [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1],
 [1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1],
 [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
 [1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
 [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 1, 1, 1, 1, 1],
 [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
 [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
 [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 ,0 ,1 ,0 ,0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1],
 [1 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
 [1 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,1 ,0 ,0 ,0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
 [1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
 [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1],
 [1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1],
 [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
 [1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
 [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1],
 [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
 [1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
 [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 ,0 ,1 ,0 ,0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1],
 [1 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
 [1 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,1 ,0 ,0 ,0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
 [1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
 [1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1],
 [1, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1],
 [1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
 [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 1, 1, 1, 1, 1, 0, 0, 1, 1, 1, 1, 0, 0, 1],
 [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1],
 [1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1],
 [1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1],
 [1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0 ,0 ,1 ,0 ,0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 1],
 [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
]

grid_rows = len(MAP_GRID)
grid_cols = len(MAP_GRID[0])

# --- ENVIRONMENT BUILDERS ---
def build_map():
    # Create floor without shader first (just basic textured)
    floor = Entity(
        model='quad', rotation_x=90, color=color.white,
        texture=FLOOR_TEX,
        scale=(grid_cols, grid_rows),
        position=(grid_cols / 2 - 0.5, 0, grid_rows / 2 - 0.5),
        collider='box'
    )
    floor.texture_scale = (grid_cols, grid_rows)

    ceiling = Entity(
        model='quad', rotation_x=-90, color=color.white,
        texture=CEILING_TEX,
        scale=(grid_cols, grid_rows),
        position=(grid_cols / 2 - 0.5, 3.5, grid_rows / 2 - 0.5)
    )
    ceiling.texture_scale = (grid_cols, grid_rows)

    for z in range(grid_rows):
        for x in range(grid_cols):
            if MAP_GRID[z][x] == 1:
                wall_block = Entity(
                    model='cube', color=color.white, texture=WALL_TEX,
                    scale=Vec3(1, 3.5, 1),
                    position=Vec3(x, 3.5 / 2, (grid_rows - 1) - z),
                    collider='box'
                )
                wall_block.texture_scale = (1, 3.5)

build_map()

# --- THE GOAL (MAKING IT INTERESTING) ---
# A glowing red portal at the other end of the map
exit_portal = Entity(
    model='cube',
    color=color.red,
    scale=(1, 2, 1),
    position=(28, 1, (grid_rows - 1) - 1),
    collider='box'
)

# A light source for the portal to make it glow ominously in the dark
portal_glow = PointLight(
    parent=exit_portal, 
    color=color.red, 
    attenuation=(1, 0.05, 0.01)
)

win_text = Text(
    text="YOU ESCAPED!",
    position=(0, 0),
    origin=(0, 0),
    scale=3,
    color=color.lime,
    enabled=False
)

# --- INITIALIZE FIRST PERSON PLAYER ---
player = FirstPersonController(
    position=(1, 0.1, (grid_rows - 1) - 1),
    speed=6, jump_height=1.2, mouse_sensitivity=Vec2(40, 40)
)
player.collider = 'box'

# --- CRITICAL: FLASHLIGHT SYSTEM WITH TRUE DARKNESS ---
# This flashlight will be the ONLY light source in the maze

# Create the spotlight - this is the main light
flashlight = SpotLight(
    parent=camera,
    position=(0.3, -0.2, 0.5),  # Position relative to camera
    color=color.rgba(1.0, 0.82, 0.5, 1.0),  # Warm amber light
    enabled=False  # Start with flashlight off
)

# CRITICAL SETTINGS FOR PROPER SPOTLIGHT BEHAVIOR
flashlight.shadow_map_resolution = Vec2(1024, 1024)
flashlight.inner_cone_angle = 10  # Narrow inner cone for focused light
flashlight.outer_cone_angle = 30  # Wider outer cone for soft edges
flashlight.attenuation = (1, 0.01, 0.005)  # Light falloff
flashlight.range = 15  # How far the light reaches

# Add a second, dimmer light for the ambient glow around the player
# This simulates light bouncing off walls but is VERY dim
ambient_glow = PointLight(
    parent=camera,
    position=(0, 0, 0),
    color=color.rgb(0.02, 0.02, 0.02),  # Almost black
    attenuation=(1, 0.1, 0.1),
    enabled=True
)

flashlight_timer = 0 

# UI indicator
flashlight_ui = Text(
    text="FLASHLIGHT: OFF [F]",
    position=(-0.85, -0.42), 
    scale=1.5, 
    color=color.red
)

# --- 2D MINI-MAP DISPLAY SYSTEM ---
minimap_bg = Entity(
    parent=camera.ui, model='quad', color=color.Color(0, 0, 0, 0.75),
    scale=(0.25, 0.25), position=(0.73, 0.35)
)

pixel_scale_w = 1.0 / grid_cols
pixel_scale_h = 1.0 / grid_rows

for z in range(grid_rows):
    for x in range(grid_cols):
        if MAP_GRID[z][x] == 1:
            Entity(
                parent=minimap_bg, model='quad', color=color.cyan,
                scale=(pixel_scale_w, pixel_scale_h),
                position=(-0.5 + (x * pixel_scale_w) + (pixel_scale_w / 2), 0.5 - (z * pixel_scale_h) - (pixel_scale_h / 2))
            )

arrow_mesh = Mesh(vertices=[Vec3(0, 0.6, 0), Vec3(-0.45, -0.4, 0), Vec3(0.45, -0.4, 0)], mode='triangle')
minimap_player = Entity(
    parent=minimap_bg, model=arrow_mesh, color=color.magenta,
    scale=(pixel_scale_w * 3, pixel_scale_h * 3), z=-0.01 
)

# --- ENGINE FRAME REPETITION UPDATES ---
game_won = False

def update():
    global flashlight_timer, game_won
    if game_won:
        return  # Stop updating game logic if won

    dt = time.dt

    # --- SPRINT MODIFIER ---
    player.speed = 10 if held_keys['shift'] else 6

    # --- WIN CONDITION CHECK ---
    if distance(player.position, exit_portal.position) < 1.5:
        win_text.enabled = True
        game_won = True
        player.speed = 0

    # --- UPDATE MINI-MAP CURSOR ---
    array_z = (grid_rows - 1) - player.z
    array_x = player.x

    minimap_player.x = -0.5 + (array_x / grid_cols)
    minimap_player.y =  0.5 - (array_z / grid_rows)
    minimap_player.rotation_z = player.rotation_y 

    # --- TORCH FLICKER EFFECT ---
    if flashlight.enabled:
        flashlight_timer += dt
        # Create natural flicker with multiple sine waves
        flicker = 1.0 + math.sin(flashlight_timer * 13.7) * 0.04 + \
                         math.sin(flashlight_timer * 8.3 + 1.2) * 0.03 + \
                         math.sin(flashlight_timer * 5.1 + 3.7) * 0.02 + \
                         random.uniform(-0.015, 0.015)
        
        # Clamp flicker to reasonable range
        flicker = max(0.85, min(1.15, flicker))
        
        # Apply flicker to flashlight color
        r = min(1.0, max(0.0, 1.0 * flicker))
        g = min(1.0, max(0.0, 0.82 * flicker))
        b = min(1.0, max(0.0, 0.5 * flicker))
        flashlight.color = color.rgba(r, g, b, 1.0)

# --- SYSTEM GLOBAL CONTROLLER CAPTURES ---
def input(key):
    if key == 'escape':
        mouse.locked = not mouse.locked

    # --- TOGGLE FLASHLIGHT WITH 'F' KEY ---
    if key == 'f' and not game_won:
        flashlight.enabled = not flashlight.enabled
        flashlight_ui.text = f"FLASHLIGHT: {'ON' if flashlight.enabled else 'OFF'} [F]"
        flashlight_ui.color = color.lime if flashlight.enabled else color.red
        
        # When flashlight turns on, reduce the ambient glow slightly for contrast
        if flashlight.enabled:
            ambient_glow.color = color.rgb(0.01, 0.01, 0.01)
        else:
            ambient_glow.color = color.rgb(0.02, 0.02, 0.02)

    # --- ARROW KEY MOVEMENT ---
    if key == 'up arrow': held_keys['w'] = 1
    elif key == 'up arrow up': held_keys['w'] = 0

    if key == 'down arrow': held_keys['s'] = 1
    elif key == 'down arrow up': held_keys['s'] = 0

    if key == 'left arrow': held_keys['a'] = 1
    elif key == 'left arrow up': held_keys['a'] = 0

    if key == 'right arrow': held_keys['d'] = 1
    elif key == 'right arrow up': held_keys['d'] = 0

app.run()