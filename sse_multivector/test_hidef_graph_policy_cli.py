"""Exercise graph restrictions through the actual HiDeF CLI and saved inputs."""

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


class GraphPolicyCliTests(unittest.TestCase):
    def fixture(self, root):
        graph_dir, data_dir = root / 'graph', root / 'data'
        graph_dir.mkdir()
        note_ids = ['n0', 'n1', 'n1', 'n2', 'n3']
        inputs = {
            'baseline': ('hdbv3-cross-note-edges-v1/response.json', {}),
            'request': ('hdbv3-cross-note-edges-v1/request.json', {}),
            'vector_map': ('vectors/vector-map.json', {'vectors': [
                {'vector_id': f'v{i}', 'note_id': n} for i, n in enumerate(note_ids)]}),
            'notes': ('reviewed-input.json', {'notes': [
                {'note_id': n, 'text': n} for n in sorted(set(note_ids))]}),
        }
        sources = {}
        for key, (name, value) in inputs.items():
            path = data_dir / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(value))
            sources[key] = {'path': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
        graph_path = graph_dir / 'graph.net'
        graph_path.write_text('*Vertices 5\n' + ''.join(f'{i} "v{i}"\n' for i in range(5))
                              + '*Edges\n0 1 0.9\n0 2 0.8\n0 3 0.3\n1 3 0.4\n2 3 0.7\n')
        hierarchy = {'schema_version': 'infomap-hierarchy-v1', 'run_id': 'I03',
                     'sources': sources, 'vector_count': 5,
                     'canonical_unique_ids': [f'v{i}' for i in range(5)],
                     'alias_groups': [[f'v{i}'] for i in range(5)]}
        (graph_dir / 'hierarchy.json').write_text(json.dumps(hierarchy))
        (graph_dir / 'configuration.json').write_text(json.dumps({'sources': sources, 'graph': {
            'sha256': hashlib.sha256(graph_path.read_bytes()).hexdigest(), 'undirected_edges': 5}}))
        return graph_dir, data_dir, hierarchy

    def test_cli_applies_policy_and_records_original_and_actual_graphs(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            graph_dir, data_dir, reference = self.fixture(root)
            originals = {p: p.read_bytes() for d in (graph_dir, data_dir) for p in d.rglob('*') if p.is_file()}
            expected = {
                'original': ['0 1 0.9', '0 2 0.8', '0 3 0.3', '1 3 0.4', '2 3 0.7'],
                'mutual_best_per_note': ['0 1 0.9', '0 3 0.3', '2 3 0.7'],
                'strongest_edges_matched': ['0 1 0.9', '0 2 0.8', '2 3 0.7'],
            }
            for policy, edges in expected.items():
                with self.subTest(policy=policy):
                    output = root / policy
                    command = [sys.executable, str(Path(__file__).with_name('hidef_experiment.py')),
                               '--graph-directory', str(graph_dir), '--data-directory', str(data_dir),
                               '--output', str(output), '--run-id', 'HDFv2-' + policy,
                               '--graph-policy', policy, '--minres', '.1', '--maxres', '2',
                               '--density', '.4', '--neighbors', '2', '--persistence', '2']
                    plan = subprocess.run(command + ['--plan'], capture_output=True, text=True)
                    self.assertEqual(plan.returncode, 0, plan.stderr)
                    self.assertFalse(output.exists())
                    planned = json.loads(plan.stdout)
                    self.assertEqual(planned['graph_policy']['policy'], policy)
                    self.assertEqual(planned['input_graph']['edges'], 5)
                    self.assertEqual(planned['graph']['edges'], len(edges))
                    run = subprocess.run(command, capture_output=True, text=True)
                    self.assertEqual(run.returncode, 0, run.stderr)
                    config = json.loads((output / 'configuration.json').read_text())
                    self.assertEqual(planned, config)
                    actual = (output / 'graph.net').read_bytes()
                    self.assertEqual(actual.decode().splitlines()[7:], edges)
                    self.assertEqual(config['graph']['sha256'], hashlib.sha256(actual).hexdigest())
                    self.assertEqual(config['graph_policy']['isolated_vector_ids'], [4])
                    hierarchy = json.loads((output / 'hierarchy.json').read_text())
                    for key in ('sources', 'canonical_unique_ids', 'alias_groups', 'vector_count'):
                        self.assertEqual(hierarchy[key], reference[key])
                    self.assertEqual(hierarchy['groups'][0]['vector_ids'], list(range(5)))
                    partitions = json.loads((output / 'raw-partitions.json').read_text())['partitions']
                    for partition in partitions:
                        members = partition['membership']
                        self.assertEqual(len(members), 5)
                        self.assertEqual(members.count(members[4]), 1)
                    manifest = json.loads((output / 'manifest.json').read_text())['sha256']
                    for name, digest in manifest.items():
                        self.assertEqual(hashlib.sha256((output / name).read_bytes()).hexdigest(), digest)
                    before = {p.name: p.read_bytes() for p in output.iterdir()}
                    repeat = subprocess.run(command, capture_output=True, text=True)
                    self.assertNotEqual(repeat.returncode, 0)
                    self.assertIn('output already exists', repeat.stderr)
                    self.assertEqual(before, {p.name: p.read_bytes() for p in output.iterdir()})
            self.assertEqual(originals, {p: p.read_bytes() for p in originals})


if __name__ == '__main__':
    unittest.main()
