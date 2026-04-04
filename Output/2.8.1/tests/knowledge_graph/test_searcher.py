"""
Tests for KnowledgeSearcher - Minimal Unit for searching knowledge nodes.

Test Cases (16):
- search: basic, type_filter, project_filter, tag_filter, date_filter, sorting, pagination, relation_expansion
- search_by_tags: single_tag, multiple_tags, nonexistent_tag, with_limit
- search_by_date_range: basic, open_ended, no_results, invalid_format
"""

import pytest
import tempfile
import os
from datetime import datetime, timedelta

from quickagents.knowledge_graph.types import NodeType, KnowledgeNode, EdgeType
from quickagents.knowledge_graph.storage.sqlite_storage import SQLiteGraphStorage
from quickagents.knowledge_graph.core.node_manager import NodeManager
from quickagents.knowledge_graph.core.edge_manager import EdgeManager
from quickagents.knowledge_graph.core.searcher import KnowledgeSearcher


class TestKnowledgeSearcherSearch:
    """Tests for KnowledgeSearcher.search()"""

    @pytest.fixture
    def setup(self):
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        storage = SQLiteGraphStorage(db_path)
        storage.initialize({})
        node_manager = NodeManager(storage)
        edge_manager = EdgeManager(storage)
        searcher = KnowledgeSearcher(storage)
        yield {
            'storage': storage,
            'node_manager': node_manager,
            'edge_manager': edge_manager,
            'searcher': searcher
        }
        os.unlink(db_path)

    def test_search_basic(self, setup):
        node_manager = setup['node_manager']
        searcher = setup['searcher']
        
        node_manager.create_node(
            NodeType.REQUIREMENT,
            "Authentication Required",
            "Users must authenticate before accessing resources"
        )
        node_manager.create_node(
            NodeType.DECISION,
            "Use JWT Tokens",
            "We decided to use JWT for authentication"
        )
        node_manager.create_node(
            NodeType.FACT,
            "Database Performance",
            "PostgreSQL handles concurrent connections well"
        )
        
        result = searcher.search("authentication")
        
        assert result.total >= 2
        assert any("authentication" in n.title.lower() or "authentication" in n.content.lower() for n in result.nodes)

    def test_search_type_filter(self, setup):
        node_manager = setup['node_manager']
        searcher = setup['searcher']
        
        node_manager.create_node(
            NodeType.REQUIREMENT,
            "Performance Requirement",
            "System must respond within 100ms"
        )
        node_manager.create_node(
            NodeType.DECISION,
            "Performance Decision",
            "We decided to use caching for performance"
        )
        
        result = searcher.search(
            "performance",
            node_types=[NodeType.REQUIREMENT]
        )
        
        assert result.total >= 1
        assert all(n.node_type == NodeType.REQUIREMENT for n in result.nodes)

    def test_search_project_filter(self, setup):
        node_manager = setup['node_manager']
        searcher = setup['searcher']
        
        node_manager.create_node(
            NodeType.REQUIREMENT,
            "Feature A",
            "Feature A description",
            project_name="project-alpha"
        )
        node_manager.create_node(
            NodeType.REQUIREMENT,
            "Feature B",
            "Feature B description",
            project_name="project-beta"
        )
        
        result = searcher.search(
            "Feature",
            filters={"project_name": "project-alpha"}
        )
        
        assert result.total >= 1
        assert all(n.project_name == "project-alpha" for n in result.nodes)

    def test_search_tag_filter(self, setup):
        node_manager = setup['node_manager']
        searcher = setup['searcher']
        
        node_manager.create_node(
            NodeType.INSIGHT,
            "API Design",
            "RESTful APIs are easier to maintain",
            tags=["api", "backend"]
        )
        node_manager.create_node(
            NodeType.INSIGHT,
            "Frontend Performance",
            "Lazy loading improves performance",
            tags=["frontend", "performance"]
        )
        
        result = searcher.search(
            "performance",
            filters={"tags": "backend"}
        )
        
        assert result.total >= 1

    def test_search_date_filter(self, setup):
        node_manager = setup['node_manager']
        searcher = setup['searcher']
        
        node1 = node_manager.create_node(
            NodeType.FACT,
            "Old Fact",
            "This is an old fact"
        )
        node2 = node_manager.create_node(
            NodeType.FACT,
            "New Fact",
            "This is a new fact"
        )
        
        start_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        end_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        result = searcher.search(
            "Fact",
            filters={"start_date": start_date, "end_date": end_date}
        )
        
        assert result.total >= 2

    def test_search_sorting(self, setup):
        node_manager = setup['node_manager']
        searcher = setup['searcher']
        
        node_manager.create_node(
            NodeType.DECISION,
            "Low Importance",
            "Minor decision",
            importance=0.3
        )
        node_manager.create_node(
            NodeType.DECISION,
            "High Importance",
            "Major decision",
            importance=0.9
        )
        
        result = searcher.search(
            "decision",
            sort_by="importance"
        )
        
        if len(result.nodes) >= 2:
            assert result.nodes[0].importance >= result.nodes[1].importance

    def test_search_pagination(self, setup):
        node_manager = setup['node_manager']
        searcher = setup['searcher']
        
        for i in range(15):
            node_manager.create_node(
                NodeType.CONCEPT,
                f"Concept {i}",
                f"Description for concept {i}"
            )
        
        page1 = searcher.search("Concept", limit=5, offset=0)
        page2 = searcher.search("Concept", limit=5, offset=5)
        
        assert len(page1.nodes) == 5
        assert len(page2.nodes) == 5
        assert page1.nodes[0].id != page2.nodes[0].id
        assert page1.has_more == True

    def test_search_relation_expansion(self, setup):
        node_manager = setup['node_manager']
        edge_manager = setup['edge_manager']
        searcher = setup['searcher']
        
        node1 = node_manager.create_node(
            NodeType.CONCEPT,
            "Core Concept",
            "This is the main concept"
        )
        node2 = node_manager.create_node(
            NodeType.CONCEPT,
            "Related Concept",
            "This is related to the core"
        )
        
        edge_manager.create_edge(
            source_id=node1.id,
            target_id=node2.id,
            edge_type=EdgeType.RELATED_TO
        )
        
        result = searcher.search(
            "Core Concept",
            expand_relations=True,
            relation_depth=1
        )
        
        assert result.total >= 1
        assert len(result.related_nodes) >= 1


class TestKnowledgeSearcherTags:
    """Tests for KnowledgeSearcher.search_by_tags()"""

    @pytest.fixture
    def setup(self):
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        storage = SQLiteGraphStorage(db_path)
        storage.initialize({})
        node_manager = NodeManager(storage)
        searcher = KnowledgeSearcher(storage)
        yield {
            'storage': storage,
            'node_manager': node_manager,
            'searcher': searcher
        }
        os.unlink(db_path)

    def test_search_by_tags_single_tag(self, setup):
        node_manager = setup['node_manager']
        searcher = setup['searcher']
        
        node_manager.create_node(
            NodeType.INSIGHT,
            "API Insight",
            "REST APIs are scalable",
            tags=["api", "backend"]
        )
        node_manager.create_node(
            NodeType.INSIGHT,
            "Frontend Tip",
            "Use lazy loading",
            tags=["frontend", "performance"]
        )
        
        result = searcher.search_by_tags(["api"])
        
        assert len(result) >= 1
        assert any("api" in n.tags for n in result)

    def test_search_by_tags_multiple_tags(self, setup):
        node_manager = setup['node_manager']
        searcher = setup['searcher']
        
        node_manager.create_node(
            NodeType.INSIGHT,
            "Backend Performance",
            "Caching improves performance",
            tags=["backend", "performance", "caching"]
        )
        node_manager.create_node(
            NodeType.INSIGHT,
            "Frontend Performance",
            "Code splitting helps",
            tags=["frontend", "performance"]
        )
        node_manager.create_node(
            NodeType.INSIGHT,
            "Security",
            "Use HTTPS",
            tags=["security"]
        )
        
        result = searcher.search_by_tags(["backend", "performance"])
        
        assert len(result) >= 2

    def test_search_by_tags_nonexistent_tag(self, setup):
        node_manager = setup['node_manager']
        searcher = setup['searcher']
        
        node_manager.create_node(
            NodeType.INSIGHT,
            "Test",
            "Test content",
            tags=["existing-tag"]
        )
        
        result = searcher.search_by_tags(["nonexistent-tag"])
        
        assert result == []

    def test_search_by_tags_with_limit(self, setup):
        node_manager = setup['node_manager']
        searcher = setup['searcher']
        
        for i in range(20):
            node_manager.create_node(
                NodeType.INSIGHT,
                f"Insight {i}",
                f"Content {i}",
                tags=["common-tag"]
            )
        
        result = searcher.search_by_tags(["common-tag"], limit=10)
        
        assert len(result) == 10


class TestKnowledgeSearcherDateRange:
    """Tests for KnowledgeSearcher.search_by_date_range()"""

    @pytest.fixture
    def setup(self):
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        storage = SQLiteGraphStorage(db_path)
        storage.initialize({})
        node_manager = NodeManager(storage)
        searcher = KnowledgeSearcher(storage)
        yield {
            'storage': storage,
            'node_manager': node_manager,
            'searcher': searcher
        }
        os.unlink(db_path)

    def test_search_by_date_range_basic(self, setup):
        node_manager = setup['node_manager']
        searcher = setup['searcher']
        
        node_manager.create_node(
            NodeType.FACT,
            "Fact 1",
            "First fact"
        )
        node_manager.create_node(
            NodeType.FACT,
            "Fact 2",
            "Second fact"
        )
        
        start_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        end_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        result = searcher.search_by_date_range(start_date, end_date)
        
        assert len(result) >= 2

    def test_search_by_date_range_open_ended(self, setup):
        node_manager = setup['node_manager']
        searcher = setup['searcher']
        
        node_manager.create_node(
            NodeType.DECISION,
            "Decision 1",
            "First decision"
        )
        
        start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        
        result = searcher.search_by_date_range(start_date, None)
        
        assert len(result) >= 1

    def test_search_by_date_range_no_results(self, setup):
        node_manager = setup['node_manager']
        searcher = setup['searcher']
        
        node_manager.create_node(
            NodeType.DECISION,
            "Recent Decision",
            "A recent decision"
        )
        
        start_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        end_date = (datetime.now() + timedelta(days=60)).strftime("%Y-%m-%d")
        
        result = searcher.search_by_date_range(start_date, end_date)
        
        assert result == []

    def test_search_by_date_range_invalid_format(self, setup):
        searcher = setup['searcher']
        
        with pytest.raises(ValueError):
            searcher.search_by_date_range("invalid-date", "2024-01-01")
