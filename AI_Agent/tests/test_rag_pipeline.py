"""
Comprehensive tests for the RAG pipeline.
Tests chunking, retrieval, file validation, and error handling.
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

AI_AGENT_DIR = Path(__file__).resolve().parents[1]
if str(AI_AGENT_DIR) not in sys.path:
    sys.path.insert(0, str(AI_AGENT_DIR))

from scripts import ask as ask_module
from scripts import build_index as build_index_module
from scripts.utils import validate_file_content


def _vectorize(text: str) -> list[float]:
    """Deterministic toy embedding for offline tests."""
    base = float(len(text))
    return [base, base + 1.0, base + 2.0, base + 3.0]


class TestFileValidation:
    """Test file content validation."""
    
    def test_valid_file(self):
        """Valid file should pass validation."""
        content = "This is a valid markdown file with sufficient content."
        is_valid, msg = validate_file_content("test.md", content)
        assert is_valid
        assert msg == ""
    
    def test_empty_file(self):
        """Empty file should fail validation."""
        is_valid, msg = validate_file_content("empty.md", "")
        assert not is_valid
        assert "empty" in msg.lower()
    
    def test_whitespace_only_file(self):
        """File with only whitespace should fail."""
        is_valid, msg = validate_file_content("whitespace.md", "   \n\n  \t  ")
        assert not is_valid
        assert "empty" in msg.lower() or "whitespace" in msg.lower()
    
    def test_too_short_file(self):
        """Very short file should fail."""
        is_valid, msg = validate_file_content("short.md", "Hi")
        assert not is_valid
        assert "short" in msg.lower()
    
    def test_corrupted_file(self):
        """File with mostly binary/non-printable content should fail."""
        content = "\x00\x01\x02\x03\x04" * 100  # Binary garbage
        is_valid, msg = validate_file_content("corrupted.md", content)
        assert not is_valid
        assert "corrupted" in msg.lower() or "binary" in msg.lower()


class TestChunking:
    """Test text chunking strategy."""
    
    def test_chunk_normal_text(self, monkeypatch):
        """Chunking should handle normal text."""
        # Mock tiktoken encoder function
        class MockEncoder:
            def encode(self, text):
                # Simple word-based tokenization
                return text.split()
            
            def decode(self, tokens):
                return " ".join(tokens)
        
        monkeypatch.setattr(build_index_module, "get_encoder", lambda: MockEncoder())
        
        text = " ".join([f"word{i}" for i in range(100)])
        chunks = list(build_index_module.chunk_text(text, max_tokens=20, overlap=5))
        
        assert len(chunks) > 1, "Should create multiple chunks"
        # Each chunk should be non-empty
        assert all(chunk.strip() for chunk in chunks)
    
    def test_chunk_empty_text(self, monkeypatch):
        """Empty text should return no chunks."""
        class MockEncoder:
            def encode(self, text):
                return []
            
            def decode(self, tokens):
                return ""
        
        monkeypatch.setattr(build_index_module, "get_encoder", lambda: MockEncoder())
        
        chunks = list(build_index_module.chunk_text("", max_tokens=500))
        assert chunks == []
    
    def test_chunk_short_text(self, monkeypatch):
        """Short text should create single chunk."""
        class MockEncoder:
            def encode(self, text):
                return text.split()
            
            def decode(self, tokens):
                return " ".join(tokens)
        
        monkeypatch.setattr(build_index_module, "get_encoder", lambda: MockEncoder())
        
        text = "Short text here"
        chunks = list(build_index_module.chunk_text(text, max_tokens=500))
        assert len(chunks) == 1


class TestBuildIndex:
    """Test index building with various file conditions."""
    
    def test_build_with_valid_files(self, tmp_path, monkeypatch):
        """Building index with valid files should succeed."""
        # Mock tiktoken encoder
        class MockEncoder:
            def encode(self, text):
                return text.split()
            def decode(self, tokens):
                return " ".join(tokens)
        
        monkeypatch.setattr(build_index_module, "get_encoder", lambda: MockEncoder())
        
        repo_root = tmp_path / "repo"
        corpus_dir = repo_root / "Knowledge_Base_MarkDown"
        corpus_dir.mkdir(parents=True)
        
        # Create valid markdown files
        (corpus_dir / "doc1.md").write_text("Valid document with sufficient content.", encoding="utf-8")
        (corpus_dir / "doc2.md").write_text("Another valid document with more text here.", encoding="utf-8")
        
        index_path = repo_root / "AI_Agent" / "test.faiss"
        meta_path = repo_root / "AI_Agent" / "test.meta.pkl"
        index_path.parent.mkdir(parents=True)
        
        monkeypatch.setattr(build_index_module, "REPO_ROOT", repo_root)
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")  # Mock API key
        monkeypatch.setattr(
            build_index_module,
            "embed_batches",
            lambda client, chunks: [_vectorize(chunk) for chunk in chunks],
        )
        monkeypatch.setattr(build_index_module, "OpenAI", lambda: object())
        
        build_index_module.build_index(
            source=corpus_dir,
            index_path=index_path,
            meta_path=meta_path,
            max_tokens=200,
            overlap=0,
            batch_size=2,
        )
        
        assert index_path.exists()
        assert meta_path.exists()
    
    def test_build_skips_empty_files(self, tmp_path, monkeypatch, capsys):
        """Empty files should be skipped with warning."""
        # Mock tiktoken encoder
        class MockEncoder:
            def encode(self, text):
                return text.split()
            def decode(self, tokens):
                return " ".join(tokens)
        
        monkeypatch.setattr(build_index_module, "get_encoder", lambda: MockEncoder())
        
        repo_root = tmp_path / "repo"
        corpus_dir = repo_root / "Knowledge_Base_MarkDown"
        corpus_dir.mkdir(parents=True)
        
        # Create empty file
        (corpus_dir / "empty.md").write_text("", encoding="utf-8")
        # Create valid file
        (corpus_dir / "valid.md").write_text("Valid document content here.", encoding="utf-8")
        
        index_path = repo_root / "AI_Agent" / "test.faiss"
        meta_path = repo_root / "AI_Agent" / "test.meta.pkl"
        index_path.parent.mkdir(parents=True)
        
        monkeypatch.setattr(build_index_module, "REPO_ROOT", repo_root)
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")  # Mock API key
        monkeypatch.setattr(
            build_index_module,
            "embed_batches",
            lambda client, chunks: [_vectorize(chunk) for chunk in chunks],
        )
        monkeypatch.setattr(build_index_module, "OpenAI", lambda: object())
        
        build_index_module.build_index(
            source=corpus_dir,
            index_path=index_path,
            meta_path=meta_path,
            max_tokens=200,
            overlap=0,
            batch_size=2,
        )
        
        captured = capsys.readouterr()
        assert "empty.md" in captured.out.lower()
        assert "warning" in captured.out.lower() or "skip" in captured.out.lower()


class TestRetrieval:
    """Test document retrieval."""
    
    def test_retrieve_with_results(self, tmp_path, monkeypatch):
        """Retrieval should return relevant documents."""
        # Mock tiktoken encoder
        class MockEncoder:
            def encode(self, text):
                return text.split()
            def decode(self, tokens):
                return " ".join(tokens)
        
        monkeypatch.setattr(build_index_module, "get_encoder", lambda: MockEncoder())
        
        repo_root = tmp_path / "repo"
        corpus_dir = repo_root / "Knowledge_Base_MarkDown"
        corpus_dir.mkdir(parents=True)
        
        doc_path = corpus_dir / "governance.md"
        doc_text = "AI governance framework and ethical guidelines for actuaries."
        doc_path.write_text(doc_text, encoding="utf-8")
        
        index_path = repo_root / "AI_Agent" / "test.faiss"
        meta_path = repo_root / "AI_Agent" / "test.meta.pkl"
        index_path.parent.mkdir(parents=True)
        
        monkeypatch.setattr(build_index_module, "REPO_ROOT", repo_root)
        monkeypatch.setattr(ask_module, "REPO_ROOT", repo_root)
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")  # Mock API key
        monkeypatch.setattr(
            build_index_module,
            "embed_batches",
            lambda client, chunks: [_vectorize(chunk) for chunk in chunks],
        )
        monkeypatch.setattr(build_index_module, "OpenAI", lambda: object())
        
        build_index_module.build_index(
            source=corpus_dir,
            index_path=index_path,
            meta_path=meta_path,
            max_tokens=200,
            overlap=0,
            batch_size=2,
        )
        
        monkeypatch.setattr(ask_module, "INDEX_PATH", index_path)
        monkeypatch.setattr(ask_module, "META_PATH", meta_path)
        monkeypatch.setattr(ask_module, "_INDEX_CACHE", None)
        monkeypatch.setattr(ask_module, "_DOCS_CACHE", None)
        
        class DummyEmbeddings:
            def create(self, model, input):
                data = [SimpleNamespace(embedding=_vectorize(item)) for item in input]
                return SimpleNamespace(data=data)
        
        dummy_client = SimpleNamespace(embeddings=DummyEmbeddings())
        
        # Patch the _create_embedding function
        monkeypatch.setattr(ask_module, "_create_embedding", lambda client, text: _vectorize(text))
        
        hits = ask_module.retrieve(dummy_client, doc_text, k=1)
        assert len(hits) >= 1, "Should retrieve at least one chunk"
        assert "governance.md" in hits[0]["path"]
        assert "governance" in hits[0]["text"].lower()
    
    def test_retrieve_with_similarity_threshold(self, tmp_path, monkeypatch):
        """Similarity threshold should filter low-quality results."""
        # Mock tiktoken encoder
        class MockEncoder:
            def encode(self, text):
                return text.split()
            def decode(self, tokens):
                return " ".join(tokens)
        
        monkeypatch.setattr(build_index_module, "get_encoder", lambda: MockEncoder())
        
        repo_root = tmp_path / "repo"
        corpus_dir = repo_root / "Knowledge_Base_MarkDown"
        corpus_dir.mkdir(parents=True)
        
        doc_path = corpus_dir / "test.md"
        doc_text = "Test document with some content."
        doc_path.write_text(doc_text, encoding="utf-8")
        
        index_path = repo_root / "AI_Agent" / "test.faiss"
        meta_path = repo_root / "AI_Agent" / "test.meta.pkl"
        index_path.parent.mkdir(parents=True)
        
        monkeypatch.setattr(build_index_module, "REPO_ROOT", repo_root)
        monkeypatch.setattr(ask_module, "REPO_ROOT", repo_root)
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")  # Mock API key
        monkeypatch.setattr(
            build_index_module,
            "embed_batches",
            lambda client, chunks: [_vectorize(chunk) for chunk in chunks],
        )
        monkeypatch.setattr(build_index_module, "OpenAI", lambda: object())
        
        build_index_module.build_index(
            source=corpus_dir,
            index_path=index_path,
            meta_path=meta_path,
            max_tokens=200,
            overlap=0,
            batch_size=2,
        )
        
        monkeypatch.setattr(ask_module, "INDEX_PATH", index_path)
        monkeypatch.setattr(ask_module, "META_PATH", meta_path)
        monkeypatch.setattr(ask_module, "_INDEX_CACHE", None)
        monkeypatch.setattr(ask_module, "_DOCS_CACHE", None)
        
        class DummyEmbeddings:
            def create(self, model, input):
                data = [SimpleNamespace(embedding=_vectorize(item)) for item in input]
                return SimpleNamespace(data=data)
        
        dummy_client = SimpleNamespace(embeddings=DummyEmbeddings())
        monkeypatch.setattr(ask_module, "_create_embedding", lambda client, text: _vectorize(text))
        
        # With very high threshold, might get fewer results
        hits_high_threshold = ask_module.retrieve(dummy_client, "completely different query", k=5, similarity_threshold=0.9)
        # With no threshold, should get all requested results
        hits_no_threshold = ask_module.retrieve(dummy_client, "completely different query", k=5, similarity_threshold=0.0)
        
        # High threshold should return same or fewer results
        assert len(hits_high_threshold) <= len(hits_no_threshold)


class TestNoMatchResponse:
    """Test handling when no matching documents are found."""
    
    def test_empty_results_handling(self, tmp_path, monkeypatch):
        """System should handle gracefully when no documents match."""
        # Mock tiktoken encoder
        class MockEncoder:
            def encode(self, text):
                return text.split()
            def decode(self, tokens):
                return " ".join(tokens)
        
        monkeypatch.setattr(build_index_module, "get_encoder", lambda: MockEncoder())
        
        repo_root = tmp_path / "repo"
        corpus_dir = repo_root / "Knowledge_Base_MarkDown"
        corpus_dir.mkdir(parents=True)
        
        doc_path = corpus_dir / "specific.md"
        doc_text = "Very specific topic about quantum computing."
        doc_path.write_text(doc_text, encoding="utf-8")
        
        index_path = repo_root / "AI_Agent" / "test.faiss"
        meta_path = repo_root / "AI_Agent" / "test.meta.pkl"
        index_path.parent.mkdir(parents=True)
        
        monkeypatch.setattr(build_index_module, "REPO_ROOT", repo_root)
        monkeypatch.setattr(ask_module, "REPO_ROOT", repo_root)
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")  # Mock API key
        monkeypatch.setattr(
            build_index_module,
            "embed_batches",
            lambda client, chunks: [_vectorize(chunk) for chunk in chunks],
        )
        monkeypatch.setattr(build_index_module, "OpenAI", lambda: object())
        
        build_index_module.build_index(
            source=corpus_dir,
            index_path=index_path,
            meta_path=meta_path,
            max_tokens=200,
            overlap=0,
            batch_size=2,
        )
        
        monkeypatch.setattr(ask_module, "INDEX_PATH", index_path)
        monkeypatch.setattr(ask_module, "META_PATH", meta_path)
        monkeypatch.setattr(ask_module, "_INDEX_CACHE", None)
        monkeypatch.setattr(ask_module, "_DOCS_CACHE", None)
        
        class DummyEmbeddings:
            def create(self, model, input):
                data = [SimpleNamespace(embedding=_vectorize(item)) for item in input]
                return SimpleNamespace(data=data)
        
        dummy_client = SimpleNamespace(embeddings=DummyEmbeddings())
        monkeypatch.setattr(ask_module, "_create_embedding", lambda client, text: _vectorize(text))
        
        # With very high threshold, should potentially get no results
        hits = ask_module.retrieve(dummy_client, "completely unrelated topic", k=1, similarity_threshold=0.99)
        
        # The system should handle this gracefully
        # If no hits, the main() function should print "I don't have enough information"
        assert isinstance(hits, list)  # Should return a list, even if empty
