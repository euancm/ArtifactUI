ArtifactUI localization compatibility

The inspection widget extracts the class identifier between BP_ and the
last _C from the discovered artifact actor's class display name.
ArtifactLocalizationSIDs maps that class identifier to the item's
LocalizationSID, or to its SID when no localization override is present.
The map is generated from installed base game and Cost of Hope DLC data.

Both localized fields use ST_S2BaseGameLocalization. Flare Time is present
in that namespace: AArtifactCNPPShard maps to DLC01_AArtifactCNPPShard.
Its Blueprint name is not its localization identifier.

Name and description are shown only when the map entry and the respective
live localization lookup succeed. Missing text is blank, not a previous
artifact's text. The name, description, and ID start blank and are cleared
on Construct and in PreCloseUpdateView, preserving the inherited handlers.
The ID displays the extracted class identifier.

Some prototypes use the same Blueprint class. Where one lacks a complete
name/description pair and another is localized, the widget displays the
localized artifact's text for both; it cannot distinguish them by class.
The known affected quest prototypes and their displayed ordinary artifacts:
SQ13_Soul (Soul), QuestArtifactCrystalThorn (Crystal Thorn),
DLC01_SQ13_ArtifactPeace (Moonlight), PQuestArtifactScraper and its fake
variant (Eye). These are prototype IDs, not verified in-game names.
Different localized texts sharing a class are rejected during generation.

This is an installed-content compatibility map, not automatic support for
future DLC or third-party artifacts. The existing inspection activation
and actor/component discovery are unchanged.

Regenerating the map

Extract the installed game's English Game.locres and base/DLC
ItemPrototypes.cfg.bin files locally with Zone Kit's UnrealPak.
Run with Python 3.10 or later:

  python Tools\generate_localization_map.py --locres "<Game.locres>" --prototypes "<base ItemPrototypes.cfg.bin>" "<DLC ItemPrototypes.cfg.bin>" --output Data\ArtifactLocalization.json

The generator copies identifiers only, not game translations. It warns
about prototypes without a matching name/description pair. A localized
prototype sharing their class still supplies that class's text.
Ambiguous namespaces and conflicting class mappings are errors.
If namespaces change, update the widget lookups before importing new data.
Run the following in the Zone Kit Python console to import the generated
Name and LocalizationSID values, compile and save:

  exec(open(r"X:\STALKER2ZoneKit\Stalker2\Mods\ArtifactUI\Tools\import_widget_map.py").read())

Validation

  python -B -m unittest discover -s Tests -v

In the Zone Kit Python console:

  exec(open(r"X:\STALKER2ZoneKit\Stalker2\Mods\ArtifactUI\Tools\verify_widget.py").read())

This requests compilation and compares its map with the generated data.
Check Compiler Results separately: this Zone Kit build does not expose
the Blueprint's compile-status property to Python.
In-game tests verified Hypercube and Flickering Flare using the class
lookup. Test Weird Ball and other affected artifacts after importing
and packaging the generated map.

Packaging with this Zone Kit installation

  X:\STALKER2ZoneKit\Engine\Build\BatchFiles\RunUAT.bat GSCCookModOverrideContent -Project=X:\STALKER2ZoneKit\Stalker2\Stalker2.uproject -PluginPath=X:\STALKER2ZoneKit\Stalker2\Mods\ArtifactUI\ArtifactUI.uplugin -UnrealExe=X:\STALKER2ZoneKit\Stalker2\Binaries\Win64\Stalker2ModEditor-Win64-Shipping-Cmd.exe -TargetPlatform=Win64 -CustomConfig=ModCookOverrideContent -nocompile -nocompileuat

The UnrealExe argument is required: the default UnrealEditor-Cmd.exe
does not exist in this distribution. Do not pass -skipcook when building
changed widget content.

The three package files (.pak, .ucas, .utoc) are produced under:
  X:\STALKER2ZoneKit\Stalker2\SavedMods\Staged\ArtifactUI\Windows\OverrideContent\Windows\Stalker2\Mods\ArtifactUI\Content\Paks\Windows

Keep all three files together. Avoid loading an older ArtifactUI package
alongside the new version. Test an ordinary artifact, a Weird artifact,
Flare Time, and switching between them before publishing.
