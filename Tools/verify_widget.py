import json
from pathlib import Path

import unreal


root = Path(unreal.Paths.project_dir()).resolve() / "Mods" / "ArtifactUI"
rows = json.loads((root / "Data" / "ArtifactLocalization.json").read_text(encoding="utf-8"))
if {row["Namespace"] for row in rows} != {"ST_S2BaseGameLocalization"}:
    raise RuntimeError("The widget's lookup namespace does not cover the generated mapping.")
blueprint = unreal.load_asset("/ArtifactUI/GameLite/FPS_Game/UIRemaster/Inspect/W_InspectArtifactView")
if blueprint is None:
    raise RuntimeError("Cannot load the artifact widget.")
unreal.BlueprintEditorLibrary.compile_blueprint(blueprint)
defaults = unreal.get_default_object(unreal.BlueprintEditorLibrary.generated_class(blueprint))
actual = dict(defaults.get_editor_property("ArtifactLocalizationSIDs"))
expected = {row["Name"]: row["LocalizationSID"] for row in rows}
if actual != expected:
    raise RuntimeError("The saved widget's localization map differs from the generated mapping.")
if not unreal.EditorAssetLibrary.save_loaded_asset(blueprint):
    raise RuntimeError("Cannot save the compiled artifact widget.")
unreal.log(f"ArtifactUI map verification passed: {len(actual)} localization aliases.")
unreal.log("Check Compiler Results for compile errors; compile status is protected in this Zone Kit build.")
