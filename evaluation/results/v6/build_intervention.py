"""Validate the separate instruction experiment and its browser data."""
import argparse
import hashlib
import json
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CONFIGURATIONS = [('astra', effort) for effort in ('low', 'medium', 'high', 'xhigh')]
CONFIGURATIONS += [('sol', effort) for effort in ('medium', 'high')]
RATES = {
    'astra': {'uncached_input': 10, 'cached_input': 1, 'output': 50},
    'sol': {'uncached_input': 4, 'cached_input': 0.4, 'output': 20},
}


def validated_data():
    data = json.loads((ROOT / 'intervention-runs.json').read_text())
    assert data['schema_version'] == 3
    assert re.fullmatch(r'https://github.com/kkondaurov/sweatbench-runs/tree/[a-f0-9]{40}/v6/interventions/readable-elixir', data['source_archive'])
    assert re.fullmatch(r'[a-f0-9]{64}', data['source_archive_index_sha256'])
    baseline_bytes = (ROOT / 'accepted-runs.json').read_bytes()
    assert hashlib.sha256(baseline_bytes).hexdigest() == data['baseline_sha256']
    baseline = json.loads(baseline_bytes)
    assert len(baseline['runs']) == 98
    family_definitions = {f['family']: (f['track'], f['stage']) for f in baseline['families_model_view']}
    groups = {f'{family}-{effort}' for family, effort in CONFIGURATIONS}
    controls = [r for r in baseline['runs'] if r['group'] in groups]
    assert len(controls) == 22
    assert set(data['baseline_ids']) == {r['id'] for r in controls}
    assert hashlib.sha256((data['instruction'] + '\n').encode()).hexdigest() == data['instruction_sha256']
    assert data['benchmark_commit'] == '5fda9a09255529b027cadf836c0c16c867a039e5'
    expected = [(family, effort, sample) for family, effort in CONFIGURATIONS for sample in (1, 2, 3)]
    assert [(r['family'], r['effort'], r['sample']) for r in data['runs']] == expected
    assert len({r['id'] for r in data['runs']}) == 18
    assert not ({r['id'] for r in data['runs']} & {r['id'] for r in baseline['runs']})
    fields = ('input_tokens', 'cached_input_tokens', 'cache_write_input_tokens',
              'output_tokens', 'reasoning_output_tokens')
    for run in data['runs']:
        family = run['family']
        assert run['id'] == f"v6-readable-{family}-{run['effort']}-{run['sample']:02}"
        assert run['baseline_group'] == f"{family}-{run['effort']}"
        model = data['models'][family]
        assert run['model'] == model['name']
        assert model['rates_per_million'] == RATES[family]
        count = 3 if family == 'astra' else 5
        assert model['baseline_count'] == count
        assert len([r for r in controls if r['group'] == run['baseline_group']]) == count
        families = run['final_families']
        assert len(families) == len({f['id'] for f in families}) == 49
        assert {f['id']: (f['track'], f['stage']) for f in families} == family_definitions
        assert {f['status'] for f in families} <= {'passed', 'failed'}
        assert all(bool(f['failing_members']) == (f['status'] == 'failed') for f in families)
        for track, key, total in [('core', 'core', 39), ('judgment', 'maintenance', 10)]:
            members = [f for f in families if f['track'] == track]
            assert len(members) == total
            assert run[key] == sum(f['status'] == 'passed' for f in members)
        failed_scenarios = {member for f in families for member in f['failing_members']}
        assert run['scenarios_final'] == 94 - len(failed_scenarios)
        assert 0 <= run['scenarios_ship'] <= 94
        stages = run['milestones']
        assert [m['milestone'] for m in stages] == list(range(1, 8))
        for stage in stages:
            assert stage['integrity_status'] == 'passed' and stage['agent_attempts'] >= 1
            assert stage['runtime_seconds'] >= 0 and math.isfinite(stage['runtime_seconds'])
            assert 0 <= stage['scenarios_passed'] <= stage['scenarios_total']
            for key in ('report_sha256', 'snapshot_sha256'):
                assert len(stage[key]) == 64 and all(c in '0123456789abcdef' for c in stage[key])
            assert all(isinstance(stage[key], int) and stage[key] >= 0 for key in fields)
            assert stage['cached_input_tokens'] <= stage['input_tokens']
            assert stage['reasoning_output_tokens'] <= stage['output_tokens']
            rates = model['rates_per_million']
            cost = ((stage['input_tokens'] - stage['cached_input_tokens']) * rates['uncached_input']
                    + stage['cached_input_tokens'] * rates['cached_input']
                    + stage['output_tokens'] * rates['output']) / 1e6
            assert math.isclose(stage['cost'], cost, abs_tol=1e-9)
        assert math.isclose(run['cost'], sum(m['cost'] for m in stages), abs_tol=1e-9)
        assert math.isclose(run['runtime_seconds'], sum(m['runtime_seconds'] for m in stages), abs_tol=1e-6)
        assert all(run['usage'][key] == sum(m[key] for m in stages) for key in fields)
        assert run['usage']['session_count'] == 7 and run['usage']['descendant_sessions'] == 0
        assert run['usage']['cache_write_input_tokens'] == 0
        assert run['usage']['max_request_input_tokens'] == max(m['max_request_input_tokens'] for m in stages)
        assert run['usage']['max_request_input_tokens'] <= 272000
        for key, measured in [('prod_loc', 'production_loc_measured'), ('test_loc', 'test_loc_measured')]:
            assert isinstance(run[key], int) and run[key] == run['structure'][measured]
    # The browser consumes the same audited records without a network fetch.
    return data


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    output = '// Generated by build_intervention.py; edit intervention-runs.json instead.\n'
    output += 'const readabilityIntervention = ' + json.dumps(validated_data(), indent=2) + ';\n'
    path = ROOT / 'intervention-data.js'
    if args.check:
        assert path.read_text() == output, 'intervention-data.js is stale'
    else:
        path.write_text(output)
    print('Intervention validated: 18 separate runs, 126 milestones, 22 historical controls; scores, usage and costs reconcile.')
