"""
FPS Labyrinth – entry point
Run this file to start the game.
"""
from ursina import Ursina, window, color

from core.settings   import WINDOW_TITLE
from core.lighting   import setup_lighting
from core.fog        import setup_fog
from core.map_builder import build_world
from entities.player  import create_player
from entities.enemy   import EnemyManager
from systems.combat   import CombatSystem
from ui.hud           import HUD
from ui.minimap       import Minimap

# ── Engine ──────────────────────────────────────────────────────────────────
app = Ursina()
window.title          = WINDOW_TITLE
window.borderless     = False
window.exit_button.visible = False
window.fps_counter.enabled = True
window.color          = color.black

# ── World ────────────────────────────────────────────────────────────────────
setup_lighting()
setup_fog()
world_data = build_world()          # returns { "floors": [...], "stairs": [...], "exit": entity }

# ── Player ───────────────────────────────────────────────────────────────────
player = create_player(spawn=(1, 0.1, 29))   # (x, y, z) in world coords

# ── Enemies ──────────────────────────────────────────────────────────────────
enemy_manager = EnemyManager(player=player)
enemy_manager.spawn_enemies(world_data["spawn_points"])

# ── Combat ───────────────────────────────────────────────────────────────────
combat = CombatSystem(player=player, enemy_manager=enemy_manager)

# ── UI ───────────────────────────────────────────────────────────────────────
hud     = HUD(player=player, combat=combat)
minimap = Minimap(world_data["floor_grids"][0])  # show ground floor by default

# ── Global update / input forwarding ─────────────────────────────────────────
def update():
    combat.update()
    enemy_manager.update()
    hud.update()
    minimap.update(player)


def input(key):
    combat.input(key)
    hud.input(key)

    # Arrow-key → WASD aliases (preserved from original)
    _arrow = {
        "up arrow":       ("w", 1), "up arrow up":    ("w", 0),
        "down arrow":     ("s", 1), "down arrow up":  ("s", 0),
        "left arrow":     ("a", 1), "left arrow up":  ("a", 0),
        "right arrow":    ("d", 1), "right arrow up": ("d", 0),
    }
    if key in _arrow:
        k, v = _arrow[key]
        from ursina import held_keys
        held_keys[k] = v


app.run()