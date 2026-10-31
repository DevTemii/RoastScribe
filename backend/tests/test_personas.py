from app.config import settings
from app.plugins import load_personas


def test_every_persona_file_is_valid():
    files = list(settings.personas_dir.glob("*.json"))
    assert files
    assert len(load_personas()) == len(files)


def test_core_personas_present():
    assert {"cynical_vc", "gordon_ramsay", "senior_architect", "gen_z_founder"} <= set(
        load_personas()
    )
