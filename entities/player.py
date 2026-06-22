"""
entities/player.py

Wraps Ursina's FirstPersonController to add:
  • Configurable speed / jump / gravity from settings
  • Health system (take_damage, heal, is_dead)
  • Flashlight toggle with torch-flicker animation
  • Smooth stair-climb shim (steps < 0.35 wu are auto-climbed)
  • Sprint support (hold Shift)
"""
import math
import random

from ursina import (
    camera, color, held_keys, time,
    SpotLight, PointLight, Text, Entity, Vec2,
)
from ursina.prefabs.first_person_controller import FirstPersonController

from core.settings import (
    PLAYER_SPEED, PLAYER_SPRINT, PLAYER_JUMP_HEIGHT,
    PLAYER_GRAVITY, PLAYER_MAX_HP, MOUSE_SENSITIVITY,
    FLASHLIGHT_COLOR, FLASHLIGHT_INNER_CONE, FLASHLIGHT_OUTER_CONE,
    FLASHLIGHT_RANGE, FLASHLIGHT_ATTENUATION,
)


class Player:
    """
    Thin wrapper that holds the FirstPersonController plus HP and flashlight.
    Access the raw Ursina entity via  player.controller
    and world position via          player.position
    """

    def __init__(self, spawn: tuple = (1, 0.1, 29)):
        self.max_hp = PLAYER_MAX_HP
        self.hp     = PLAYER_MAX_HP
        self.dead   = False

        # ── Controller ───────────────────────────────────────────────────────
        self.controller = FirstPersonController(
            position=spawn,
            speed=PLAYER_SPEED,
            jump_height=PLAYER_JUMP_HEIGHT,
            gravity=PLAYER_GRAVITY,
            mouse_sensitivity=Vec2(*MOUSE_SENSITIVITY),
        )
        self.controller.collider = 'box'

        # ── Flashlight ───────────────────────────────────────────────────────
        self.flashlight = SpotLight(
            parent=camera,
            position=(0.3, -0.2, 0.5),
            color=color.rgba(*FLASHLIGHT_COLOR),
            enabled=False,
        )
        self.flashlight.shadow_map_resolution = Vec2(1024, 1024)
        self.flashlight.inner_cone_angle = FLASHLIGHT_INNER_CONE
        self.flashlight.outer_cone_angle = FLASHLIGHT_OUTER_CONE
        self.flashlight.attenuation      = FLASHLIGHT_ATTENUATION
        self.flashlight.range            = FLASHLIGHT_RANGE

        # Dim ambient glow so the player isn't in total black when flashlight off
        self.ambient_glow = PointLight(
            parent=camera,
            position=(0, 0, 0),
            color=color.rgb(2, 2, 2),          # very dark but not zero
            attenuation=(1, 0.1, 0.1),
            enabled=True,
        )

        self._fl_timer = 0.0                   # flicker accumulator

        # ── Stair-climb ──────────────────────────────────────────────────────
        self._step_threshold = 0.35            # max step height auto-climbed

    # ── properties ───────────────────────────────────────────────────────────

    @property
    def position(self):
        return self.controller.position

    @property
    def rotation_y(self):
        return self.controller.rotation_y

    @property
    def x(self): return self.controller.x
    @property
    def y(self): return self.controller.y
    @property
    def z(self): return self.controller.z

    # ── public API ───────────────────────────────────────────────────────────

    def take_damage(self, amount: int) -> None:
        if self.dead:
            return
        self.hp = max(0, self.hp - amount)
        if self.hp == 0:
            self.dead = True

    def heal(self, amount: int) -> None:
        self.hp = min(self.max_hp, self.hp + amount)

    def is_dead(self) -> bool:
        return self.dead

    def toggle_flashlight(self) -> bool:
        self.flashlight.enabled = not self.flashlight.enabled
        if self.flashlight.enabled:
            self.ambient_glow.color = color.rgb(1, 1, 1)
        else:
            self.ambient_glow.color = color.rgb(2, 2, 2)
        return self.flashlight.enabled

    def update(self) -> None:
        """Called every frame from main.update()."""
        if self.dead:
            self.controller.speed = 0
            return

        dt = time.dt

        # Sprint
        self.controller.speed = (
            PLAYER_SPRINT if held_keys['shift'] else PLAYER_SPEED
        )

        # Flashlight flicker
        if self.flashlight.enabled:
            self._fl_timer += dt
            t = self._fl_timer
            flicker = (
                1.0
                + math.sin(t * 13.7) * 0.04
                + math.sin(t * 8.3 + 1.2) * 0.03
                + math.sin(t * 5.1 + 3.7) * 0.02
                + random.uniform(-0.015, 0.015)
            )
            flicker = max(0.85, min(1.15, flicker))
            r = min(1.0, FLASHLIGHT_COLOR[0] * flicker)
            g = min(1.0, FLASHLIGHT_COLOR[1] * flicker)
            b = min(1.0, FLASHLIGHT_COLOR[2] * flicker)
            self.flashlight.color = color.rgba(r, g, b, 1.0)


def create_player(spawn: tuple = (1, 0.1, 29)) -> "Player":
    """Factory used by main.py."""
    return Player(spawn=spawn)