"""
entities/enemy.py

Implements the Enemy class and EnemyManager.

Enemy state machine
───────────────────
  PATROL   →  wanders between random nearby waypoints
  ALERT    →  heard/saw the player, turning to look
  CHASE    →  sprinting toward player (LoS confirmed)
  ATTACK   →  melee swing when within ENEMY_ATTACK_RANGE
  DEAD     →  frozen, removed after death animation

Line-of-Sight uses Ursina's raycast from the enemy's eye position toward
the player; if the ray hits the player entity before hitting a wall the
enemy "sees" the player.
"""
import random
import math

from ursina import (
    Entity, Vec3, color, raycast, distance,
    time, Sequence, Func, Wait, destroy,
)

from core.settings import (
    ENEMY_SPEED, ENEMY_SPRINT_SPEED,
    ENEMY_MAX_HP, ENEMY_ATTACK_RANGE,
    ENEMY_ATTACK_DAMAGE, ENEMY_ATTACK_COOLDOWN,
    ENEMY_SIGHT_RANGE, ENEMY_FOV_HALF,
    ENEMY_PATROL_WAIT, ENEMY_PATROL_DIST,
)


# ── State constants ───────────────────────────────────────────────────────────
PATROL = "patrol"
ALERT  = "alert"
CHASE  = "chase"
ATTACK = "attack"
DEAD   = "dead"


class Enemy(Entity):
    """
    A single enemy.  Inherits from Entity so it's automatically drawn and
    has a collider the player's hitscan can hit.
    """

    def __init__(self, position: Vec3, player, **kwargs):
        super().__init__(
            model='cube',
            color=color.orange,
            scale=Vec3(0.8, 1.8, 0.8),
            position=position,
            collider='box',
            **kwargs,
        )
        # Store the raw player reference (our Player wrapper)
        self._player = player

        # Health
        self.hp     = ENEMY_MAX_HP
        self.max_hp = ENEMY_MAX_HP

        # Simple head indicator – tiny red sphere on top of the body
        self._head = Entity(
            parent=self,
            model='sphere',
            color=color.red,
            scale=Vec3(0.55, 0.55, 0.55),
            position=(0, 0.65, 0),
        )

        # Eyes offset for LoS ray origin
        self._eye_offset = Vec3(0, 0.6, 0)

        # AI state
        self.state          = PATROL
        self._patrol_timer  = 0.0
        self._patrol_wait   = random.uniform(*ENEMY_PATROL_WAIT)
        self._waypoint      = None
        self._attack_timer  = 0.0
        self._alert_timer   = 0.0        # brief pause before chasing

        # Bob animation accumulator
        self._bob_t = random.uniform(0, math.pi * 2)

    # ── public ───────────────────────────────────────────────────────────────

    def take_damage(self, amount: int) -> None:
        if self.state == DEAD:
            return
        self.hp -= amount
        # Visual hit flash
        self.color = color.white
        Sequence(Wait(0.1), Func(self._restore_color)).start()
        if self.hp <= 0:
            self._die()

    def is_dead(self) -> bool:
        return self.state == DEAD

    # ── internal helpers ─────────────────────────────────────────────────────

    def _restore_color(self):
        if self.state != DEAD:
            self.color = color.orange

    def _die(self):
        self.state = DEAD
        self.color = color.dark_gray
        self._head.color = color.dark_gray
        # Crumple animation then destroy
        Sequence(
            Func(lambda: setattr(self, 'scale_y', 0.4)),
            Wait(1.2),
            Func(lambda: destroy(self)),
        ).start()

    def _eye_pos(self) -> Vec3:
        return self.position + self._eye_offset

    def _can_see_player(self) -> bool:
        """
        True when:
          1. Player is within ENEMY_SIGHT_RANGE.
          2. Player is inside the FOV cone (dot-product test).
          3. Raycast from eyes to player doesn't hit a wall first.
        """
        player_pos = self._player.position
        to_player  = player_pos - self._eye_pos()
        dist       = to_player.length()

        if dist > ENEMY_SIGHT_RANGE:
            return False

        # FOV cone check
        forward = Vec3(
            math.sin(math.radians(self.rotation_y)),
            0,
            math.cos(math.radians(self.rotation_y)),
        ).normalized()
        to_player_flat = Vec3(to_player.x, 0, to_player.z).normalized()
        dot = forward.dot(to_player_flat)
        if dot < math.cos(math.radians(ENEMY_FOV_HALF)):
            return False

        # Raycast obstruction check
        hit = raycast(
            origin=self._eye_pos(),
            direction=to_player.normalized(),
            distance=dist,
            ignore=[self],
        )
        # If ray hits nothing, or hits the player controller entity
        if not hit.hit:
            return True
        # Check if the hit entity belongs to the player
        if hasattr(hit.entity, 'is_player') and hit.entity.is_player:
            return True
        # If the hit distance is very close to player distance, it's the player
        if abs(hit.distance - dist) < 0.5:
            return True
        return False

    def _face_player(self) -> None:
        """Rotate enemy to face player (Y-axis only)."""
        dx = self._player.x - self.x
        dz = self._player.z - self.z
        target_y = math.degrees(math.atan2(dx, dz))
        self.rotation_y = target_y

    def _move_toward_player(self, speed: float, dt: float) -> None:
        """Translate toward player at given speed."""
        dx = self._player.x - self.x
        dz = self._player.z - self.z
        dist = math.sqrt(dx * dx + dz * dz)
        if dist < 0.01:
            return
        nx, nz = dx / dist, dz / dist
        self.x += nx * speed * dt
        self.z += nz * speed * dt

    def _choose_waypoint(self) -> Vec3:
        angle = random.uniform(0, math.pi * 2)
        dist  = random.uniform(1, ENEMY_PATROL_DIST)
        return Vec3(
            self.x + math.sin(angle) * dist,
            self.y,
            self.z + math.cos(angle) * dist,
        )

    def _patrol_step(self, dt: float) -> None:
        if self._waypoint is None:
            self._patrol_timer -= dt
            if self._patrol_timer <= 0:
                self._waypoint     = self._choose_waypoint()
                self._patrol_timer = 0

        if self._waypoint:
            dx = self._waypoint.x - self.x
            dz = self._waypoint.z - self.z
            dist = math.sqrt(dx * dx + dz * dz)
            if dist < 0.3:
                self._waypoint     = None
                self._patrol_timer = random.uniform(*ENEMY_PATROL_WAIT)
            else:
                speed = ENEMY_SPEED * 0.5
                self.x += (dx / dist) * speed * dt
                self.z += (dz / dist) * speed * dt
                self.rotation_y = math.degrees(math.atan2(dx, dz))

    # ── per-frame update ──────────────────────────────────────────────────────

    def update(self) -> None:
        if self.state == DEAD:
            return

        dt = time.dt

        # Bob animation (up/down oscillation when moving)
        self._bob_t += dt * 4
        self.y = self.y + math.sin(self._bob_t) * 0.003   # very subtle

        # Cooldown timers
        self._attack_timer = max(0.0, self._attack_timer - dt)

        # ── State machine ────────────────────────────────────────────────────
        if self.state == PATROL:
            self._patrol_step(dt)
            if self._can_see_player():
                self.state       = ALERT
                self._alert_timer = 0.4   # brief "oh no" pause

        elif self.state == ALERT:
            self._face_player()
            self._alert_timer -= dt
            if self._alert_timer <= 0:
                self.state = CHASE

        elif self.state == CHASE:
            self._face_player()
            dist_to_player = distance(self.position, self._player.position)
            if dist_to_player <= ENEMY_ATTACK_RANGE:
                self.state = ATTACK
            else:
                self._move_toward_player(ENEMY_SPRINT_SPEED, dt)
                # Give up if player is too far and not visible
                if (dist_to_player > ENEMY_SIGHT_RANGE * 1.5
                        and not self._can_see_player()):
                    self.state = PATROL

        elif self.state == ATTACK:
            self._face_player()
            dist_to_player = distance(self.position, self._player.position)
            if dist_to_player > ENEMY_ATTACK_RANGE:
                self.state = CHASE
            elif self._attack_timer <= 0:
                self._do_attack()
                self._attack_timer = ENEMY_ATTACK_COOLDOWN

    def _do_attack(self) -> None:
        """Lunge animation + deal damage."""
        # Lunge: move quickly toward player then snap back
        orig_pos = Vec3(self.position)
        dx = self._player.x - self.x
        dz = self._player.z - self.z
        dist = math.sqrt(dx * dx + dz * dz) or 1
        lunge = Vec3(self.x + (dx / dist) * 0.4, self.y, self.z + (dz / dist) * 0.4)

        Sequence(
            Func(lambda: setattr(self, 'position', lunge)),
            Wait(0.08),
            Func(lambda: setattr(self, 'position', orig_pos)),
        ).start()

        self._player.take_damage(ENEMY_ATTACK_DAMAGE)


# ── EnemyManager ─────────────────────────────────────────────────────────────

class EnemyManager:
    """Owns all enemy instances and forwards update calls."""

    def __init__(self, player):
        self._player  = player
        self._enemies: list[Enemy] = []

    def spawn_enemies(self, spawn_points: list) -> None:
        for pos in spawn_points:
            e = Enemy(position=pos, player=self._player)
            self._enemies.append(e)

    def update(self) -> None:
        for e in self._enemies:
            if not e.is_dead():
                e.update()

    def get_living(self) -> list:
        return [e for e in self._enemies if not e.is_dead()]

    def hit_enemy(self, entity, damage: int) -> bool:
        """
        Called by the combat system when a hitscan ray hits something.
        Returns True if the entity was an enemy and took damage.
        """
        for e in self._enemies:
            if e is entity or e._head is entity:
                e.take_damage(damage)
                return True
        return False