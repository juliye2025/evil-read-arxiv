import importlib.util
import json
import subprocess
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
PDF_BYTES = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF\n"


def load_module(name, relative_path):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


resolver = load_module("source_resolver", "paper-analyze/scripts/resolve_source.py")
extractor = load_module("image_extractor", "extract-paper-images/scripts/extract_images.py")


class FixtureHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/paper.pdf":
            body = PDF_BYTES
            content_type = "application/pdf"
        elif self.path == "/posts/scaling/":
            body = b"""<!doctype html><html><head>
                <meta property="og:type" content="article">
                <meta property="og:title" content="Scaling Laws, Carefully">
                <meta name="author" content="Example Author">
                <meta property="article:published_time" content="2026-06-24">
                </head><body><article><p>Blog evidence.</p></article></body></html>"""
            content_type = "text/html; charset=utf-8"
        else:
            body = b"""<!doctype html><html><head>
                <meta property="og:title" content="Local Research Project">
                <meta name="author" content="Research Team">
                </head><body><main><a href="/paper.pdf">Paper</a></main></body></html>"""
            content_type = "text/html; charset=utf-8"
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, _format, *_args):
        return


class SourceSupportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), FixtureHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base_url = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=5)

    def test_arxiv_detection_is_strict(self):
        self.assertEqual(resolver.normalize_arxiv_id("2606.12345"), "2606.12345")
        self.assertEqual(
            resolver.normalize_arxiv_id("https://arxiv.org/abs/2606.12345v2"),
            "2606.12345v2",
        )
        self.assertIsNone(
            resolver.normalize_arxiv_id("https://example.com/posts/2026.0601/")
        )

    def test_arxiv_uses_downloaded_pdf_metadata(self):
        fetched = {
            "kind": "pdf",
            "local_pdf": "/tmp/example.pdf",
            "page_count": 12,
            "content_length": 1234,
            "title": "Metadata Title",
            "authors": "Author One; Author Two",
            "published_date": "2026-02-02",
        }
        with tempfile.TemporaryDirectory() as work, patch.object(
            resolver, "fetch_public_url", return_value=fetched
        ):
            result = resolver.resolve_source("2602.02269", work)

        self.assertEqual(result["title"], "Metadata Title")
        self.assertEqual(result["authors"], "Author One; Author Two")
        self.assertEqual(result["published_date"], "2026-02-02")

    def test_markdown_link_normalization(self):
        markdown = f"[paper.pdf]({self.base_url}/paper.pdf)"
        self.assertEqual(
            resolver.extract_source_reference(markdown),
            f"{self.base_url}/paper.pdf",
        )
        self.assertEqual(
            extractor.extract_source_reference(markdown),
            f"{self.base_url}/paper.pdf",
        )

    def test_direct_pdf_and_parent_project_metadata(self):
        with tempfile.TemporaryDirectory() as work:
            result = resolver.resolve_source(f"{self.base_url}/paper.pdf", work)
            self.assertEqual(result["source_type"], "pdf_url")
            self.assertEqual(result["title"], "Local Research Project")
            self.assertEqual(result["authors"], "Research Team")
            self.assertEqual(result["arxiv_id"], "")
            self.assertTrue(Path(result["local_pdf"]).exists())

    def test_project_page_discovers_and_downloads_pdf(self):
        with tempfile.TemporaryDirectory() as work:
            result = resolver.resolve_source(f"{self.base_url}/project/", work)
            self.assertEqual(result["source_type"], "project_page")
            self.assertEqual(result["selected_pdf_url"], f"{self.base_url}/paper.pdf")
            self.assertTrue(Path(result["local_pdf"]).exists())

    def test_blog_metadata_and_source_aware_note(self):
        with tempfile.TemporaryDirectory() as work, tempfile.TemporaryDirectory() as vault:
            url = f"{self.base_url}/posts/scaling/"
            result = resolver.resolve_source(url, work)
            self.assertEqual(result["source_type"], "blog")
            self.assertEqual(result["title"], "Scaling Laws, Carefully")
            self.assertEqual(result["authors"], "Example Author")
            self.assertEqual(result["published_date"], "2026-06-24")

            command = [
                sys.executable,
                str(ROOT / "paper-analyze/scripts/generate_note.py"),
                "--document-id",
                result["document_id"],
                "--source-type",
                "blog",
                "--source-url",
                url,
                "--title",
                result["title"],
                "--authors",
                result["authors"],
                "--published-date",
                result["published_date"],
                "--domain",
                "scaling-laws",
                "--vault",
                vault,
            ]
            subprocess.run(command, check=True, capture_output=True, text=True)
            notes = list(Path(vault).rglob("*.md"))
            self.assertEqual(len(notes), 1)
            content = notes[0].read_text(encoding="utf-8")
            self.assertIn('source_type: "blog"', content)
            self.assertIn(url, content)
            self.assertNotIn("arxiv_id:", content)
            self.assertNotIn("arxiv.org", content)

    def test_image_extractor_downloads_public_pdf(self):
        with tempfile.TemporaryDirectory() as work:
            path = extractor.download_public_pdf(f"{self.base_url}/paper.pdf", work)
            self.assertIsNotNone(path)
            self.assertTrue(Path(path).read_bytes().startswith(b"%PDF-"))

    def test_source_figure_discovery_has_no_default_count_limit(self):
        with tempfile.TemporaryDirectory() as work:
            figures_dir = Path(work) / "figures"
            figures_dir.mkdir()
            for index in range(30):
                (figures_dir / f"figure-{index}.png").write_bytes(b"image")

            figures = extractor.find_figures_from_source(work)

        self.assertEqual(len(figures), 30)

    def test_image_extractor_does_not_render_main_paper_as_source_figure(self):
        with tempfile.TemporaryDirectory() as work, tempfile.TemporaryDirectory() as output:
            work_path = Path(work)
            main_pdf = work_path / "2602.02269.pdf"
            figure_pdf = work_path / "appendix-assets" / "method.pdf"
            figure_pdf.parent.mkdir()
            for path, page_count in ((main_pdf, 2), (figure_pdf, 1)):
                document = extractor.fitz.open()
                for _ in range(page_count):
                    document.new_page()
                document.save(path)
                document.close()

            converted = []

            def record_conversion(path, _output_dir):
                converted.append(Path(path).name)
                return []

            index = Path(output) / "index.md"
            argv = ["extract_images.py", "2602.02269", output, str(index)]
            with patch.object(extractor.tempfile, "TemporaryDirectory") as temp_dir, patch.object(
                extractor, "extract_arxiv_source", return_value=True
            ), patch.object(extractor, "find_figures_from_source", return_value=[]), patch.object(
                extractor, "download_arxiv_pdf", return_value=str(main_pdf)
            ), patch.object(extractor, "extract_pdf_figures", return_value=[]), patch.object(
                extractor, "extract_from_pdf_figures", side_effect=record_conversion
            ), patch.object(sys, "argv", argv):
                temp_dir.return_value.__enter__.return_value = work
                temp_dir.return_value.__exit__.return_value = False
                extractor.main()

        self.assertEqual(converted, ["method.pdf"])

    def test_non_arxiv_graph_node_uses_document_id(self):
        with tempfile.TemporaryDirectory() as vault:
            graph_script = ROOT / "paper-analyze/scripts/update_graph.py"
            subprocess.run(
                [
                    sys.executable,
                    str(graph_script),
                    "--document-id",
                    "url-example",
                    "--source-type",
                    "blog",
                    "--source-url",
                    "https://example.com/blog/",
                    "--title",
                    "Example Blog",
                    "--domain",
                    "research",
                    "--vault",
                    vault,
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            graph_path = Path(vault) / "20_Research/PaperGraph/graph_data.json"
            graph = json.loads(graph_path.read_text(encoding="utf-8"))
            self.assertEqual(graph["nodes"][0]["id"], "url-example")
            self.assertEqual(graph["nodes"][0]["source_type"], "blog")
            self.assertEqual(graph["nodes"][0]["arxiv_id"], "")


if __name__ == "__main__":
    unittest.main()
