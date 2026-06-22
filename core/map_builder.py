"""
core/map_builder.py

Reads ALL_FLOORS from map_data.py and instantiates the world geometry:
  • Textured floor / ceiling quads per storey
  • Wall cubes for every '1' cell
  • Stair ramps for every 'S' cell (connects floor N → floor N+1)
  • Exit portal on the cell marked 'X'
  • Returns a structured dict consumed by main.py

Coordinate conventions
──────────────────────
  Grid  (row, col)   → World  x=col, z=(rows-1-row)
  Floor index f      → World  y_base = f * FLOOR_OFFSET
"""
from ursina import Entity, Vec3, color, PointLight, Mesh

from core.settings import (
    WALL_TEX, FLOOR_TEX, CEILING_TEX,
    WALL_HEIGHT, FLOOR_OFFSET,
)
from core.map_data import ALL_FLOORS


# ── helpers ──────────────────────────────────────────────────────────────────

def _grid_to_world_x(col: int) -> float:
    return float(col)


def _grid_to_world_z(row: int, rows: int) -> float:
    return float((rows - 1) - row)


# ── geometry builders ─────────────────────────────────────────────────────────

def _build_floor_slab(grid, floor_idx: int) -> None:
    """Spawn a single textured quad covering the entire floor."""
    rows = len(grid)
    cols = len(grid[0])
    y_base = floor_idx * FLOOR_OFFSET

    floor_ent = Entity(
        model='quad', rotation_x=90,
        texture=FLOOR_TEX,
        color=color.white,
        scale=(cols, rows),
        position=(cols / 2 - 0.5, y_base, rows / 2 - 0.5),
        collider='box',
    )
    floor_ent.texture_scale = (cols, rows)

    ceiling_ent = Entity(
        model='quad', rotation_x=-90,
        texture=CEILING_TEX,
        color=color.white,
        scale=(cols, rows),
        position=(cols / 2 - 0.5, y_base + WALL_HEIGHT, rows / 2 - 0.5),
    )
    ceiling_ent.texture_scale = (cols, rows)


def _build_walls(grid, floor_idx: int) -> None:
    """Spawn one wall cube per '1' cell."""
    rows = len(grid)
    y_base = floor_idx * FLOOR_OFFSET

    for row_i, row in enumerate(grid):
        for col_i, cell in enumerate(row):
            if cell == 1:
                Entity(
                    model='cube',
                    texture=WALL_TEX,
                    color=color.white,
                    scale=Vec3(1, WALL_HEIGHT, 1),
                    position=Vec3(
                        _grid_to_world_x(col_i),
                        y_base + WALL_HEIGHT / 2,
                        _grid_to_world_z(row_i, rows),
                    ),
                    collider='box',
                )


def _build_stair(col: int, row: int, rows: int,
                 floor_idx: int, stair_list: list) -> None:
    """
    Build a ramp (series of thin step cubes) going from floor_idx up to
    floor_idx+1.  The ramp occupies the 'S' cell and the cell above it.

    Each step is a thin box that rises 0.25 world units; the player can
    walk up them smoothly (they act like a gentle slope in practice because
    the player's collision sphere rolls over low steps).
    """
    x = _grid_to_world_x(col)
    z = _grid_to_world_z(row, rows)
    y_base = floor_idx * FLOOR_OFFSET

    steps = 14           # number of discrete steps
    total_h = FLOOR_OFFSET
    step_h  = total_h / steps
    step_d  = 0.9 / steps   # depth per step along z

    for i in range(steps):
        step = Entity(
            model='cube',
            color=color.gray,
            scale=Vec3(0.9, step_h, step_d),
            position=Vec3(x, y_base + i * step_h + step_h / 2,
                          z - 0.45 + i * step_d),
            collider='box',
        )
        stair_list.append(step)

    # Invisible landing platform at the top so the player can stand on it
    Entity(
        model='cube', color=color.clear,
        scale=Vec3(1, 0.1, 1),
        position=Vec3(x, y_base + total_h + 0.05, z),
        collider='box',
    )


def _build_exit_portal(col: int, row: int, rows: int, floor_idx: int) -> Entity:
    """Spawn the glowing red exit portal and its PointLight."""
    x = _grid_to_world_x(col)
    z = _grid_to_world_z(row, rows)
    y_base = floor_idx * FLOOR_OFFSET

    portal = Entity(
        model='cube',
        color=color.red,
        scale=(1, 2, 0.2),
        position=Vec3(x, y_base + 1, z),
        collider='box',
    )
    PointLight(
        parent=portal,
        color=color.red,
        attenuation=(1, 0.05, 0.01),
    )
    return portal


def _scan_specials(grid, floor_idx: int, rows: int,
                   spawn_points: list, stair_list: list) -> Entity | None:
    """
    Walk the grid once and handle S / E / X cells.
    Returns the exit Entity if found, else None.
    """
    exit_entity = None
    for row_i, row in enumerate(grid):
        for col_i, cell in enumerate(row):
            if cell == 'S':
                _build_stair(col_i, row_i, rows, floor_idx, stair_list)

            elif cell == 'E':
                x = _grid_to_world_x(col_i)
                z = _grid_to_world_z(row_i, rows)
                y_base = floor_idx * FLOOR_OFFSET
                spawn_points.append(Vec3(x, y_base + 1, z))

            elif cell == 'X':
                exit_entity = _build_exit_portal(col_i, row_i, rows, floor_idx)

    return exit_entity


# ── public API ────────────────────────────────────────────────────────────────

def build_world() -> dict:
    """
    Build all floors and return a data dict for use by main.py:

    {
        "floor_grids"  : list[grid]         – raw 2-D arrays (for minimap),
        "floors"       : list[int]           – floor indices built,
        "stairs"       : list[Entity]        – stair step entities,
        "spawn_points" : list[Vec3]          – enemy spawn world positions,
        "exit"         : Entity              – the win-condition portal,
    }
    """
    stairs       = []
    spawn_points = []
    exit_entity  = None
    floor_grids  = []

    for floor_idx, grid in enumerate(ALL_FLOORS):
        rows = len(grid)
        floor_grids.append(grid)

        _build_floor_slab(grid, floor_idx)
        _build_walls(grid, floor_idx)

        found_exit = _scan_specials(grid, floor_idx, rows, spawn_points, stairs)
        if found_exit:
            exit_entity = found_exit

    return {
        "floor_grids"  : floor_grids,
        "floors"       : list(range(len(ALL_FLOORS))),
        "stairs"       : stairs,
        "spawn_points" : spawn_points,
        "exit"         : exit_entity,
    }