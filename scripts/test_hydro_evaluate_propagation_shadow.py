"""Offline prospective matching: archival timing, identity, QC and deduplication."""
import copy
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import tempfile
import unittest

from hydro_evaluate_propagation_shadow import digest, evaluate
from hydro_propagation_model import CONTRACT, MODEL_VERSION


class PropagationShadowEvaluationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.observations = self.root / "observations"
        (self.observations / "raw").mkdir(parents=True)
        self.reference = datetime(2026, 9, 23, tzinfo=timezone.utc)
        self.as_of = self.reference + timedelta(hours=10)
        self.issue = {
            "schema": "radar-propagation-shadow/v1", "mode": "shadow", "publishable": False,
            "station": "86510000", "status": "calculated", "contract": CONTRACT,
            "modelVersion": MODEL_VERSION, "modelSha256": "a" * 64,
            "referenceAt": self.reference.isoformat(),
            "generatedAt": (self.reference + timedelta(minutes=15)).isoformat(),
            "observation": {"timestamp": self.reference.isoformat(), "level": 8},
            "points": [{"nominalLeadHours": lead,
                        "timestamp": (self.reference + timedelta(hours=lead)).isoformat(),
                        "level": 8 + lead / 10, "realLeadHours": 99} for lead in range(1, 7)],
        }
        self.entries = []
        self.add_issue(self.issue)
        self.write_observations()

    def add_issue(self, issue, archived_minutes=20):
        path = self.root / f"issue-{len(self.entries)}.json"
        path.write_text(json.dumps(issue))
        entry = {"issue": path.name, "issueSha256": digest(path),
                 "archivedAt": (self.reference + timedelta(minutes=archived_minutes)).isoformat(),
                 "evidenceReceiptKey": "projection/receipts/01234567-89ab-cdef-0123-456789abcdef.json",
                 "archiveSha256": "b" * 64}
        self.entries.append(entry)
        return entry

    def write_observations(self, leads=range(1, 7), quality="Dado aprovado", station="86510000", received=None):
        path = self.observations / "raw" / "ana-86510000-fresh.xml"
        body = "<root>" + "".join(
            f"<DadosHidrometereologicos><CodEstacao>{station}</CodEstacao>"
            f"<DataHora>{(self.reference + timedelta(hours=lead)).isoformat()}</DataHora>"
            f"<NivelFinal>{800 + lead * 10}</NivelFinal><CQ_NivelFinal>{quality}</CQ_NivelFinal>"
            "</DadosHidrometereologicos>" for lead in leads) + "</root>"
        path.write_text(body)
        manifest = [{"file": path.name, "sha256": digest(path),
                     "collected_at": (received or self.as_of).isoformat()}]
        (self.observations / "collection-manifest.json").write_text(json.dumps(manifest))

    def run_evaluation(self, as_of=None):
        path = self.root / "issues.json"
        path.write_text(json.dumps(self.entries))
        at = as_of or self.as_of
        return evaluate(path, self.observations, at.isoformat(), now=self.as_of.isoformat())

    def test_exact_pairs_and_conservative_real_leads(self):
        result = self.run_evaluation()
        self.assertEqual(result["summary"]["verifiedPairs"], 6)
        self.assertEqual(result["summary"]["hitsWithin50cm"], 6)
        self.assertEqual(result["summary"]["mae_m"], 0)
        self.assertAlmostEqual(result["records"][0]["realLeadHours"], 2 / 3)
        self.assertEqual(result["realLeadBands"]["[0,1)"]["verifiedPairs"], 1)
        self.assertFalse(result["trained"])
        self.assertFalse(result["accuracyGoalAchieved"])

    def test_first_archival_issue_is_selected_without_consulting_truth(self):
        early = copy.deepcopy(self.issue)
        for point in early["points"]:
            point["level"] += 2
        self.entries.clear()
        self.add_issue(early, archived_minutes=20)
        self.add_issue(self.issue, archived_minutes=30)
        self.entries.reverse()
        result = self.run_evaluation()
        self.assertEqual(result["counts"]["duplicatePoints"], 6)
        self.assertEqual(result["summary"]["verifiedPairs"], 6)
        self.assertEqual(result["summary"]["hitsWithin50cm"], 0)
        self.assertAlmostEqual(result["summary"]["mae_m"], 2)

    def test_distinct_model_hashes_are_separate_forecasts(self):
        other = copy.deepcopy(self.issue)
        other["modelSha256"] = "c" * 64
        self.add_issue(other)
        result = self.run_evaluation()
        self.assertEqual(result["counts"]["duplicatePoints"], 0)
        self.assertEqual(result["summary"]["verifiedPairs"], 12)
        self.assertEqual(set(result["byModelSha256"]), {"a" * 64, "c" * 64})
        self.assertEqual(result["byModelSha256"]["a" * 64]["summary"]["verifiedPairs"], 6)

    def test_generated_early_but_archived_after_target_is_expired(self):
        self.entries[0]["archivedAt"] = (self.reference + timedelta(hours=2)).isoformat()
        result = self.run_evaluation()
        self.assertEqual(result["counts"]["expiredBeforeArchivePoints"], 2)
        self.assertEqual(result["summary"]["verifiedPairs"], 4)

    def test_missing_proof_and_future_or_pre_generation_archive_are_rejected(self):
        for key, value in (("archiveSha256", None), ("evidenceReceiptKey", None),
                           ("archivedAt", (self.as_of + timedelta(seconds=1)).isoformat()),
                           ("archivedAt", self.reference.isoformat())):
            original = self.entries[0][key]
            self.entries[0][key] = value
            result = self.run_evaluation()
            self.assertEqual(result["counts"]["malformedIssues"], 1)
            self.assertEqual(result["summary"]["verifiedPairs"], 0)
            self.entries[0][key] = original

    def test_naive_archival_timestamp_is_rejected(self):
        self.entries[0]["archivedAt"] = "2026-09-23T00:20:00"
        self.assertEqual(self.run_evaluation()["counts"]["malformedIssues"], 1)

    def test_tampered_issue_is_rejected(self):
        (self.root / self.entries[0]["issue"]).write_text(json.dumps({**self.issue, "publishable": True}))
        self.assertEqual(self.run_evaluation()["counts"]["malformedIssues"], 1)

    def test_station_contract_or_target_time_mismatch_is_rejected(self):
        for changed in (
            {**self.issue, "station": "86720000"},
            {**self.issue, "contract": "other-model"},
            {**self.issue, "points": [{**point, "timestamp": self.reference.isoformat()} for point in self.issue["points"]]},
        ):
            self.entries.clear()
            self.add_issue(changed)
            self.assertEqual(self.run_evaluation()["counts"]["malformedIssues"], 1)

    def test_partial_suffix_cannot_select_only_good_targets(self):
        self.entries.clear()
        self.add_issue({**self.issue, "points": self.issue["points"][1:]})
        self.assertEqual(self.run_evaluation()["counts"]["malformedIssues"], 1)

    def test_malformed_json_shapes_are_counted_without_crashing(self):
        for body in ([1, 2], {**self.issue, "points": [2]}):
            self.entries.clear()
            self.add_issue(body)
            self.assertEqual(self.run_evaluation()["counts"]["malformedIssues"], 1)

    def test_missing_truth_is_never_interpolated_or_counted_as_hit(self):
        self.write_observations(leads=[1.25, 2, 3, 4, 5, 6])
        result = self.run_evaluation()
        self.assertEqual(result["summary"]["unobserved"], 1)
        self.assertEqual(result["summary"]["verifiedPairs"], 5)
        self.assertEqual(result["summary"]["hitsWithin50cm"], 5)
        self.assertEqual(result["summary"]["hitRateVerified"], 1)
        self.assertEqual(result["summary"]["hitRateMatureOpportunities"], 5 / 6)

    def test_nonapproved_or_future_received_truth_is_not_accepted(self):
        self.write_observations(quality="Dado suspeito")
        result = self.run_evaluation()
        self.assertEqual(result["summary"]["unobserved"], 6)
        self.assertIsNone(result["summary"]["hitRateVerified"])
        self.write_observations(received=self.as_of + timedelta(seconds=1))
        result = self.run_evaluation()
        self.assertEqual(result["summary"]["verifiedPairs"], 0)
        self.assertIn("after", result["observations"]["reason"])

    def test_tampered_observation_body_fails_closed(self):
        path = self.observations / "raw" / "ana-86510000-fresh.xml"
        path.write_text(path.read_text() + "\n")
        with self.assertRaisesRegex(ValueError, "checksum"):
            self.run_evaluation()

    def test_wrong_truth_station_fails_closed(self):
        self.write_observations(station="86720000")
        with self.assertRaisesRegex(ValueError, "station"):
            self.run_evaluation()

    def test_future_targets_remain_pending_without_invented_accuracy(self):
        early = self.reference + timedelta(minutes=30)
        self.write_observations(leads=[0], received=early)
        result = self.run_evaluation(as_of=early)
        self.assertEqual(result["summary"]["future"], 6)
        self.assertEqual(result["summary"]["verifiedPairs"], 0)
        self.assertIsNone(result["summary"]["mae_m"])
        self.assertIsNone(result["summary"]["hitRateVerified"])

    def test_unavailable_attempt_is_accounted_separately(self):
        self.entries.clear()
        self.add_issue({**self.issue, "status": "unavailable", "points": [], "reason": "missing flow"})
        result = self.run_evaluation()
        self.assertEqual(result["counts"]["unavailableIssues"], 1)
        self.assertEqual(result["counts"]["malformedIssues"], 0)
        self.assertEqual(result["summary"]["opportunities"], 0)


if __name__ == "__main__":
    unittest.main()
