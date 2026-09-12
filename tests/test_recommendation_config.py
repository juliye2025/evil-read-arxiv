import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_search_module():
    script = ROOT / "start-my-day" / "scripts" / "search_arxiv.py"
    spec = importlib.util.spec_from_file_location("search_arxiv_config_test", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


search = load_search_module()


class RecommendationConfigTests(unittest.TestCase):
    def test_domain_priority_changes_ranking_and_is_bounded(self):
        paper = {
            "title": "Robot Learning for Generalist Agents",
            "summary": "A foundation model for robot learning.",
            "categories": ["cs.RO"],
        }
        domains = {
            "low-priority": {
                "keywords": ["robot learning", "foundation model"],
                "arxiv_categories": ["cs.RO"],
                "priority": 1,
            },
            "high-priority": {
                "keywords": ["robot learning"],
                "arxiv_categories": ["cs.RO"],
                "priority": 10,
            },
        }

        score, domain, _ = search.calculate_relevance_score(paper, domains, [])

        self.assertEqual(domain, "high-priority")
        self.assertLessEqual(score, search.SCORE_MAX)


if __name__ == "__main__":
    unittest.main()
