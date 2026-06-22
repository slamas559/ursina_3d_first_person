"""
core/lighting.py
Sets up the global lighting environment (pure darkness + ambient near-zero).
Individual torches / portal glows are created by the entities that own them.
"""
from ursina import AmbientLight, color


def setup_lighting():
    """
    Install the bare-minimum ambient light (essentially 0) so the engine does
    not fall back to its default white ambient.  The flashlight SpotLight and
    per-entity PointLights are the only real light sources in the scene.
    """
    AmbientLight(color=color.rgb(0, 0, 0))   # pure black – no ambient at all