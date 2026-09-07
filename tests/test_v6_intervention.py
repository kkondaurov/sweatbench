"""Prevent intervention accounting drift and accidental baseline pooling."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1] / 'evaluation/results/v6'
spec = importlib.util.spec_from_file_location('build_intervention', ROOT / 'build_intervention.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


class InterventionDataTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((ROOT / 'intervention-runs.json').read_text())

    def validate(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            (path / 'accepted-runs.json').write_bytes((ROOT / 'accepted-runs.json').read_bytes())
            (path / 'intervention-runs.json').write_text(json.dumps(self.data))
            with patch.object(builder, 'ROOT', path):
                return builder.validated_data()

    def test_audited_release(self):
        self.assertEqual(len(self.validate()['runs']), 6)

    def test_sol_rates_are_not_astra_rates(self):
        self.data['models']['sol']['rates_per_million'] = self.data['models']['astra']['rates_per_million']
        with self.assertRaises(AssertionError):
            self.validate()

    def test_sol_failure_is_preserved(self):
        run = self.validate()['runs'][4]
        self.assertEqual((run['core'], run['maintenance'], run['scenarios_final']), (38, 8, 92))
        self.assertEqual(sum(f['status'] == 'failed' for f in run['final_families']), 3)
        self.data['runs'][4]['core'] = 39
        with self.assertRaises(AssertionError):
            self.validate()

    def test_missing_sol_baseline_is_rejected(self):
        self.data['baseline_ids'].remove('sol-medium-01')
        with self.assertRaises(AssertionError):
            self.validate()

    def test_baseline_group_must_match_model_and_effort(self):
        self.data['runs'][4]['baseline_group'] = 'astra-medium'
        with self.assertRaises(AssertionError):
            self.validate()

    def test_duplicate_failed_family_is_rejected(self):
        self.data['runs'][4]['final_families'][0] = self.data['runs'][4]['final_families'][1]
        with self.assertRaises(AssertionError):
            self.validate()

    def test_family_definition_must_match_frozen_benchmark(self):
        self.data['runs'][4]['final_families'][0]['id'] = 'invented-check'
        with self.assertRaises(AssertionError):
            self.validate()

    def test_wrong_cost_is_rejected(self):
        self.data['runs'][0]['cost'] += 1
        with self.assertRaises(AssertionError):
            self.validate()

    def test_reasoning_is_not_billed_twice(self):
        self.data['runs'][0]['milestones'][0]['cost'] += 0.01
        with self.assertRaises(AssertionError):
            self.validate()

    def test_changed_instruction_is_rejected(self):
        self.data['instruction'] += ' Additional advice.'
        with self.assertRaises(AssertionError):
            self.validate()

    def test_baseline_identity_cannot_be_reused(self):
        self.data['runs'][0]['id'] = self.data['baseline_ids'][0]
        with self.assertRaises(AssertionError):
            self.validate()

    def test_missing_milestone_is_rejected(self):
        self.data['runs'][0]['milestones'].pop()
        with self.assertRaises(AssertionError):
            self.validate()

    def test_baseline_drift_is_rejected(self):
        self.data['baseline_sha256'] = '0' * 64
        with self.assertRaises(AssertionError):
            self.validate()


if __name__ == '__main__':
    unittest.main()
