"""
core/fog.py
Applies Panda3D exponential density fog to swallow distant geometry and sell
the darkness atmosphere.
"""
from core.settings import FOG_COLOR, FOG_DENSITY


def setup_fog():
    try:
        from panda3d.core import Fog
        from direct.showbase.ShowBase import ShowBase
        import builtins

        base: ShowBase = builtins.base          # Ursina exposes the ShowBase as `base`
        fog = Fog("dungeon_fog")
        fog.setColor(*FOG_COLOR)
        fog.setExpDensity(FOG_DENSITY)
        base.render.setFog(fog)
    except Exception as exc:
        print(f"[fog] Fog setup skipped: {exc}")