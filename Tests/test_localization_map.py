import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "Tools"))

from generate_localization_map import build_rows


def artifact(sid, class_name, localization_sid=None):
    fields = {
        "SID": sid,
        "Type": "EItemType::Artifact",
        "Blueprint": f"Blueprint'/Game/Artifacts/BP_{class_name}.BP_{class_name}'",
    }
    if localization_sid is not None:
        fields["LocalizationSID"] = localization_sid
    return fields


def localized(sid, namespace="BaseNamespace"):
    return {
        f"sid_items_{sid}_name": {namespace},
        f"sid_items_{sid}_description": {namespace},
    }


class LocalizationMapTests(unittest.TestCase):
    def test_blueprint_class_maps_to_explicit_localization_sid(self):
        rows = build_rows(
            [artifact("AArtifactCNPPShard", "AArtifact_CNPP_BigShard", "DLC01_AArtifactCNPPShard")],
            localized("DLC01_AArtifactCNPPShard"),
        )
        self.assertEqual(rows, [{
            "Name": "AArtifact_CNPP_BigShard",
            "Namespace": "BaseNamespace",
            "LocalizationSID": "DLC01_AArtifactCNPPShard",
        }])

    def test_templates_and_other_item_types_are_excluded(self):
        weapon = artifact("Weapon", "Weapon")
        weapon["Type"] = "EItemType::Weapon"
        self.assertEqual(build_rows([artifact("TemplateArtifact", "Template"), weapon], {}), [])

    def test_shared_class_with_same_localization_is_deduplicated(self):
        rows = build_rows(
            [artifact("Ball", "AArtifactBall"), artifact("Ball_Fake", "AArtifactBall", "Ball")],
            localized("Ball"),
        )
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["Name"], "AArtifactBall")

    def test_shared_class_prefers_localized_artifact(self):
        with self.assertWarnsRegex(UserWarning, "without complete localized text"):
            rows = build_rows(
                [artifact("QuestSoul", "EArtifactSoul"), artifact("Soul", "EArtifactSoul")],
                localized("Soul"),
            )
        self.assertEqual(rows[0]["LocalizationSID"], "Soul")

    def test_shared_class_with_different_localized_text_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Conflicting artifact class"):
            build_rows(
                [artifact("One", "SameClass"), artifact("Two", "SameClass")],
                localized("One") | localized("Two"),
            )

    def test_missing_description_is_reported(self):
        with self.assertWarnsRegex(UserWarning, "without complete localized text"):
            rows = build_rows(
                [artifact("TestArtifact", "TestArtifact")],
                {"sid_items_TestArtifact_name": {"BaseNamespace"}},
            )
        self.assertEqual(rows, [])

    def test_ambiguous_namespaces_are_reported(self):
        with self.assertRaisesRegex(ValueError, "2 matching namespaces"):
            build_rows(
                [artifact("TestArtifact", "TestArtifact")],
                {
                    "sid_items_TestArtifact_name": {"BaseNamespace", "DLCNamespace"},
                    "sid_items_TestArtifact_description": {"BaseNamespace", "DLCNamespace"},
                },
            )

    def test_invalid_blueprint_is_rejected(self):
        fields = artifact("TestArtifact", "TestArtifact")
        fields["Blueprint"] = "BP_TestArtifact"
        with self.assertRaisesRegex(ValueError, "unsupported artifact Blueprint path"):
            build_rows([fields], localized("TestArtifact"))


if __name__ == "__main__":
    unittest.main()
