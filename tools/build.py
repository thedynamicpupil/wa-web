#!/usr/bin/env python3
"""Build through the kit driver and stage the WA-only web app."""
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KIT_BUILD = ROOT / "kit" / "tools" / "build.py"


def load_kit_build():
    spec = importlib.util.spec_from_file_location("wa_kit_build", KIT_BUILD)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def stage_web(game_dir, build_root, preset, cfg):
    """Use the WA player after linking; the pinned kit has no generic launcher."""
    from serve_web import stage

    site = Path(build_root) / "web" / "site"
    stage(Path(build_root) / preset / "recomp", site, repack=False)
    return site


def main(argv=None):
    kit_build = load_kit_build()
    kit_build.web_site = stage_web
    sys.argv = [str(KIT_BUILD), "--game-dir", str(ROOT),
                *(sys.argv[1:] if argv is None else argv)]
    return kit_build.main()


if __name__ == "__main__":
    raise SystemExit(main())
