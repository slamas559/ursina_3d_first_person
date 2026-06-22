"""
core/settings.py
All tuneable game constants in one place.
"""

# ── Window ───────────────────────────────────────────────────────────────────
WINDOW_TITLE = "3D FPS Labyrinth"

# ── Textures ─────────────────────────────────────────────────────────────────
FLOOR_TEX   = "assets/Tile/Tile_13-128x128.png"
WALL_TEX    = "assets/Bricks/Bricks_11-128x128.png"
CEILING_TEX = "assets/Roofs/Roofs_17-128x128.png"

# ── Geometry ─────────────────────────────────────────────────────────────────
WALL_HEIGHT  = 3.5     # world units per storey
FLOOR_OFFSET = 3.6     # vertical gap between floor 0 and floor 1 origin

# ── Player ────────────────────────────────────────────────────────────────────
PLAYER_SPEED       = 6
PLAYER_SPRINT      = 10
PLAYER_JUMP_HEIGHT = 1.8
PLAYER_GRAVITY     = 1.0
PLAYER_MAX_HP      = 100
MOUSE_SENSITIVITY  = (40, 40)

# ── Flashlight ────────────────────────────────────────────────────────────────
FLASHLIGHT_COLOR        = (1.0, 0.82, 0.5, 1.0)   # warm amber RGBA
FLASHLIGHT_INNER_CONE   = 10
FLASHLIGHT_OUTER_CONE   = 30
FLASHLIGHT_RANGE        = 15
FLASHLIGHT_ATTENUATION  = (1, 0.01, 0.005)

# ── Enemy AI ─────────────────────────────────────────────────────────────────
ENEMY_SPEED           = 3.5
ENEMY_SPRINT_SPEED    = 6.5
ENEMY_MAX_HP          = 50
ENEMY_ATTACK_RANGE    = 1.6      # world units
ENEMY_ATTACK_DAMAGE   = 10
ENEMY_ATTACK_COOLDOWN = 1.2      # seconds between hits
ENEMY_SIGHT_RANGE     = 16       # raycast distance for LoS check
ENEMY_FOV_HALF        = 60       # half field-of-view in degrees
ENEMY_PATROL_WAIT     = (1.5, 3.5)  # random idle pause range (secs)
ENEMY_PATROL_DIST     = 5        # max patrol step distance

# ── Weapon ────────────────────────────────────────────────────────────────────
WEAPON_DAMAGE         = 25
WEAPON_FIRE_RATE      = 0.18     # seconds between shots
WEAPON_RELOAD_TIME    = 1.8      # seconds
WEAPON_MAG_SIZE       = 12
WEAPON_MAX_AMMO       = 60
WEAPON_RANGE          = 50       # hitscan distance
WEAPON_RECOIL_AMOUNT  = 0.025    # y offset on fire
MUZZLE_FLASH_DURATION = 0.06     # seconds flash stays visible

# ── Fog ───────────────────────────────────────────────────────────────────────
FOG_COLOR   = (0, 0, 0)
FOG_DENSITY = 0.15