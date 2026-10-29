"""
Knowledge Retriever Tool (RAG Engine)
Loads financial knowledge base JSON and performs semantic keyword/text retrieval
to inject accurate, educational financial rules into agent reasoning context.
"""

import json
import os
import re
from typing import List, Dict, Any

class KnowledgeRetriever:
    def __init__(self, knowledge_file_path: str = None):
        if knowledge_file_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            knowledge_file_path = os.path.join(base_dir, "data", "financial_knowledge.json")
        
        self.knowledge_file_path = knowledge_file_path
        self.knowledge_base: List[Dict[str, Any]] = []
        self.load_knowledge_base()

    def load_knowledge_base(self):
        """Load JSON knowledge base from disk."""
        if os.path.exists(self.knowledge_file_path):
            try:
                with open(self.knowledge_file_path, "r", encoding="utf-8") as f:
                    self.knowledge_base = json.load(f)
            except Exception as e:
                print(f"[KnowledgeRetriever] Error loading knowledge base: {e}")
                self.knowledge_base = []
        else:
            print(f"[KnowledgeRetriever] File not found: {self.knowledge_file_path}")
            self.knowledge_base = []

    def query(self, search_text: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Query knowledge base using keyword overlap and term relevance scoring.
        """
        if not search_text or not self.knowledge_base:
            return self.knowledge_base[:top_k]

        query_words = set(re.findall(r'\w+', search_text.lower()))

        scored_items = []
        for item in self.knowledge_base:
            score = 0
            # Check topic match
            topic_words = set(re.findall(r'\w+', item.get('topic', '').lower()))
            score += len(query_words.intersection(topic_words)) * 3

            # Check keywords match
            keywords = [kw.lower() for kw in item.get('keywords', [])]
            for kw in keywords:
                if kw in search_text.lower():
                    score += 4
                for qw in query_words:
                    if qw in kw:
                        score += 1

            # Check summary match
            summary_words = set(re.findall(r'\w+', item.get('summary', '').lower()))
            score += len(query_words.intersection(summary_words)) * 1

            scored_items.append((score, item))

        scored_items.sort(key=lambda x: x[0], reverse=True)
        results = [item for score, item in scored_items if score > 0]

        if not results:
            return self.knowledge_base[:top_k]

        return results[:top_k]
