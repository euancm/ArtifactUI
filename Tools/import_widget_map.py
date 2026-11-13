import json
from pathlib import Path

import unreal


root = Path(unreal.Paths.project_dir()).resolve() / "Mods" / "ArtifactUI"
rows = json.loads((root / "Data" / "ArtifactLocalization.json").read_text(encoding="utf-8"))
if {row["Namespace"] for row in rows} != {"ST_S2BaseGameLocalization"}:
    raise RuntimeError("The widget's lookup namespace does not cover the generated mapping.")
aliases = {row["Name"]: row["LocalizationSID"] for row in rows}
if len(aliases) != len(rows):
    raise RuntimeError("The generated map contains duplicate class names.")
blueprint = unreal.load_asset("/ArtifactUI/GameLite/FPS_Game/UIRemaster/Inspect/W_InspectArtifactView")
if blueprint is None:
    raise RuntimeError("Cannot load the artifact widget.")
unreal.BlueprintEditorLibrary.compile_blueprint(blueprint)
defaults = unreal.get_default_object(unreal.BlueprintEditorLibrary.generated_class(blueprint))
defaults.set_editor_property("ArtifactLocalizationSIDs", aliases)
if dict(defaults.get_editor_property("ArtifactLocalizationSIDs")) != aliases:
    raise RuntimeError("The widget rejected the generated localization map.")
if not unreal.EditorAssetLibrary.save_loaded_asset(blueprint):
    raise RuntimeError("Cannot save the artifact widget.")
unreal.log(f"ArtifactUI imported {len(aliases)} class localization aliases.")
unreal.log("Check Compiler Results for compile errors.")
