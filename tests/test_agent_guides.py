"""Documented agent entry points must stay discoverable and parseable."""
from pathlib import Path
import unittest
from runner import manifest

ROOT = Path(__file__).resolve().parents[1]


class AgentGuides(unittest.TestCase):
    def test_entry_points(self):
        for name in (
            'AGENTS.md',
            'CLAUDE.md',
            'GEMINI.md',
            '.github/copilot-instructions.md',
            'docs/agents/CONTRIBUTOR_SETUP.md',
            'docs/agents/EXPERIMENT_AUTHORING.md',
            'docs/agents/REPOSITORY_BOUNDARIES.md',
            'templates/contributor-preferences.md',
        ):
            self.assertTrue((ROOT / name).is_file(), name)

    def test_specialists(self):
        for name in ('contributor-onboarding', 'experiment-author'):
            path = ROOT / '.github/agents' / (name + '.agent.md')
            self.assertTrue(path.is_file())
            text = path.read_text()
            self.assertTrue(text.startswith('---\nname:'), path)
            self.assertIn('\ndescription:', text, path)
            self.assertIn('\n---\n', text, path)

    def test_reusable_skills(self):
        for name in ('contributor-setup', 'experiment-submission'):
            p = ROOT / '.agents' / 'skills' / name / 'SKILL.md'
            self.assertTrue(p.is_file())
            t = p.read_text()
            self.assertTrue(t.startswith('---\nname:'))
            self.assertIn('\ndescription:', t)
            self.assertIn('\n---\n', t)

    def test_repository_ownership_is_explicit(self):
        agents = (ROOT / 'AGENTS.md').read_text()
        boundary = (ROOT / 'docs/agents/REPOSITORY_BOUNDARIES.md').read_text()
        authoring = (ROOT / 'docs/agents/EXPERIMENT_AUTHORING.md').read_text()
        self.assertIn('tcarwash/experiment_queue', boundary)
        self.assertIn('tcarwash/dorc_experiments', boundary)
        self.assertIn('DORC-owned experiment scripts', boundary)
        self.assertIn('make separate changes', boundary)
        self.assertIn('docs/agents/REPOSITORY_BOUNDARIES.md', agents)
        self.assertIn('not in the queue', authoring)
        self.assertIn('tcarwash/dorc_experiments', authoring)

    def test_cpu_issue_template(self):
        d = manifest((ROOT / 'templates/experiment.md').read_text())
        self.assertEqual(d['schema'], 'experiment/v1')
        self.assertEqual(d['execution'], 'container')
        self.assertEqual(d['capabilities'], ['compute.cpu'])
        self.assertEqual(len(d['revision']), 40)
        self.assertTrue(d['image'].startswith('sha256:'))
