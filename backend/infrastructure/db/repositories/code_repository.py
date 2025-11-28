"""
Code Repository

Repository for ICD-10 and CPT/HCPCS code search operations.
Supports both semantic search (with pgvector) and keyword search.
"""

import logging
from typing import List, Optional
from dataclasses import dataclass

from sqlalchemy.orm import Session
from sqlalchemy import text

logger = logging.getLogger(__name__)


@dataclass
class CodeSearchResult:
    """Result from code search operations."""
    code: str
    description: str
    category: Optional[str] = None
    chapter: Optional[str] = None
    code_type: Optional[str] = None
    is_billable: bool = True
    is_active: bool = True
    score: Optional[float] = None


class CodeRepository:
    """
    Repository for ICD-10 and CPT/HCPCS code operations.

    Supports:
    - Semantic search using pgvector embeddings
    - Keyword/text search
    - Code lookup by exact match
    """

    def __init__(self, db: Session):
        self.db = db

    def search_icd10(
        self,
        query: str,
        limit: int = 10,
        include_subcodes: bool = True
    ) -> List[CodeSearchResult]:
        """
        Search ICD-10 codes using semantic similarity or keyword match.

        Args:
            query: Search query (condition name, code, or description)
            limit: Maximum results to return
            include_subcodes: Whether to include child codes

        Returns:
            List of matching CodeSearchResult objects
        """
        try:
            # First try exact code match
            exact_results = self._search_icd10_exact(query, limit)
            if exact_results:
                return exact_results

            # Try semantic search if embeddings available
            semantic_results = self._search_icd10_semantic(query, limit)
            if semantic_results:
                return semantic_results

            # Fall back to keyword search
            return self._search_icd10_keyword(query, limit)

        except Exception as e:
            logger.error(f"ICD-10 search failed: {e}")
            return []

    def _search_icd10_exact(self, query: str, limit: int) -> List[CodeSearchResult]:
        """Search by exact code match."""
        query_upper = query.strip().upper()

        sql = text("""
            SELECT code, description, category, chapter, is_billable
            FROM icd10_codes
            WHERE code ILIKE :code_pattern
            ORDER BY code
            LIMIT :limit
        """)

        result = self.db.execute(sql, {
            "code_pattern": f"{query_upper}%",
            "limit": limit
        })

        return [
            CodeSearchResult(
                code=row.code,
                description=row.description,
                category=row.category if hasattr(row, 'category') else None,
                chapter=row.chapter if hasattr(row, 'chapter') else None,
                is_billable=row.is_billable if hasattr(row, 'is_billable') else True
            )
            for row in result.fetchall()
        ]

    def _search_icd10_semantic(self, query: str, limit: int) -> List[CodeSearchResult]:
        """Search using semantic similarity with pgvector."""
        try:
            # Check if embeddings table exists and has data
            sql = text("""
                SELECT code, description, category, chapter, is_billable,
                       1 - (embedding <=> (
                           SELECT embedding FROM icd10_embeddings
                           WHERE description ILIKE :query_pattern
                           LIMIT 1
                       )) as score
                FROM icd10_codes c
                JOIN icd10_embeddings e ON c.code = e.code
                ORDER BY score DESC
                LIMIT :limit
            """)

            result = self.db.execute(sql, {
                "query_pattern": f"%{query}%",
                "limit": limit
            })

            return [
                CodeSearchResult(
                    code=row.code,
                    description=row.description,
                    category=row.category if hasattr(row, 'category') else None,
                    chapter=row.chapter if hasattr(row, 'chapter') else None,
                    is_billable=row.is_billable if hasattr(row, 'is_billable') else True,
                    score=row.score if hasattr(row, 'score') else None
                )
                for row in result.fetchall()
            ]
        except Exception as e:
            logger.debug(f"Semantic search not available: {e}")
            return []

    def _search_icd10_keyword(self, query: str, limit: int) -> List[CodeSearchResult]:
        """Search by keyword in description."""
        sql = text("""
            SELECT code, description, category, chapter, is_billable
            FROM icd10_codes
            WHERE description ILIKE :query_pattern
               OR code ILIKE :code_pattern
            ORDER BY
                CASE WHEN code ILIKE :code_pattern THEN 0 ELSE 1 END,
                LENGTH(description)
            LIMIT :limit
        """)

        result = self.db.execute(sql, {
            "query_pattern": f"%{query}%",
            "code_pattern": f"{query}%",
            "limit": limit
        })

        return [
            CodeSearchResult(
                code=row.code,
                description=row.description,
                category=row.category if hasattr(row, 'category') else None,
                chapter=row.chapter if hasattr(row, 'chapter') else None,
                is_billable=row.is_billable if hasattr(row, 'is_billable') else True
            )
            for row in result.fetchall()
        ]

    def search_cpt(
        self,
        query: str,
        limit: int = 10,
        code_type: Optional[str] = None
    ) -> List[CodeSearchResult]:
        """
        Search CPT/HCPCS codes using semantic similarity or keyword match.

        Args:
            query: Search query (procedure name, code, or description)
            limit: Maximum results to return
            code_type: Filter by code type ('cpt' or 'hcpcs')

        Returns:
            List of matching CodeSearchResult objects
        """
        try:
            # First try exact code match
            exact_results = self._search_cpt_exact(query, limit, code_type)
            if exact_results:
                return exact_results

            # Try semantic search if embeddings available
            semantic_results = self._search_cpt_semantic(query, limit, code_type)
            if semantic_results:
                return semantic_results

            # Fall back to keyword search
            return self._search_cpt_keyword(query, limit, code_type)

        except Exception as e:
            logger.error(f"CPT search failed: {e}")
            return []

    def _search_cpt_exact(
        self,
        query: str,
        limit: int,
        code_type: Optional[str]
    ) -> List[CodeSearchResult]:
        """Search by exact code match."""
        query_upper = query.strip().upper()

        type_filter = ""
        params = {"code_pattern": f"{query_upper}%", "limit": limit}

        if code_type:
            type_filter = "AND code_type = :code_type"
            params["code_type"] = code_type.upper()

        sql = text(f"""
            SELECT code, description, category, code_type, is_active
            FROM cpt_codes
            WHERE code ILIKE :code_pattern
            {type_filter}
            ORDER BY code
            LIMIT :limit
        """)

        result = self.db.execute(sql, params)

        return [
            CodeSearchResult(
                code=row.code,
                description=row.description,
                category=row.category if hasattr(row, 'category') else None,
                code_type=row.code_type if hasattr(row, 'code_type') else "CPT",
                is_active=row.is_active if hasattr(row, 'is_active') else True
            )
            for row in result.fetchall()
        ]

    def _search_cpt_semantic(
        self,
        query: str,
        limit: int,
        code_type: Optional[str]
    ) -> List[CodeSearchResult]:
        """Search using semantic similarity with pgvector."""
        try:
            type_filter = ""
            params = {"query_pattern": f"%{query}%", "limit": limit}

            if code_type:
                type_filter = "AND c.code_type = :code_type"
                params["code_type"] = code_type.upper()

            sql = text(f"""
                SELECT c.code, c.description, c.category, c.code_type, c.is_active,
                       1 - (e.embedding <=> (
                           SELECT embedding FROM cpt_embeddings
                           WHERE description ILIKE :query_pattern
                           LIMIT 1
                       )) as score
                FROM cpt_codes c
                JOIN cpt_embeddings e ON c.code = e.code
                WHERE 1=1 {type_filter}
                ORDER BY score DESC
                LIMIT :limit
            """)

            result = self.db.execute(sql, params)

            return [
                CodeSearchResult(
                    code=row.code,
                    description=row.description,
                    category=row.category if hasattr(row, 'category') else None,
                    code_type=row.code_type if hasattr(row, 'code_type') else "CPT",
                    is_active=row.is_active if hasattr(row, 'is_active') else True,
                    score=row.score if hasattr(row, 'score') else None
                )
                for row in result.fetchall()
            ]
        except Exception as e:
            logger.debug(f"Semantic search not available: {e}")
            return []

    def _search_cpt_keyword(
        self,
        query: str,
        limit: int,
        code_type: Optional[str]
    ) -> List[CodeSearchResult]:
        """Search by keyword in description."""
        type_filter = ""
        params = {
            "query_pattern": f"%{query}%",
            "code_pattern": f"{query}%",
            "limit": limit
        }

        if code_type:
            type_filter = "AND code_type = :code_type"
            params["code_type"] = code_type.upper()

        sql = text(f"""
            SELECT code, description, category, code_type, is_active
            FROM cpt_codes
            WHERE (description ILIKE :query_pattern OR code ILIKE :code_pattern)
            {type_filter}
            ORDER BY
                CASE WHEN code ILIKE :code_pattern THEN 0 ELSE 1 END,
                LENGTH(description)
            LIMIT :limit
        """)

        result = self.db.execute(sql, params)

        return [
            CodeSearchResult(
                code=row.code,
                description=row.description,
                category=row.category if hasattr(row, 'category') else None,
                code_type=row.code_type if hasattr(row, 'code_type') else "CPT",
                is_active=row.is_active if hasattr(row, 'is_active') else True
            )
            for row in result.fetchall()
        ]

    def get_icd10_by_code(self, code: str) -> Optional[CodeSearchResult]:
        """Get ICD-10 code by exact match."""
        sql = text("""
            SELECT code, description, category, chapter, is_billable
            FROM icd10_codes
            WHERE code = :code
        """)

        result = self.db.execute(sql, {"code": code.upper()}).fetchone()

        if result:
            return CodeSearchResult(
                code=result.code,
                description=result.description,
                category=result.category if hasattr(result, 'category') else None,
                chapter=result.chapter if hasattr(result, 'chapter') else None,
                is_billable=result.is_billable if hasattr(result, 'is_billable') else True
            )
        return None

    def get_cpt_by_code(self, code: str) -> Optional[CodeSearchResult]:
        """Get CPT/HCPCS code by exact match."""
        sql = text("""
            SELECT code, description, category, code_type, is_active
            FROM cpt_codes
            WHERE code = :code
        """)

        result = self.db.execute(sql, {"code": code.upper()}).fetchone()

        if result:
            return CodeSearchResult(
                code=result.code,
                description=result.description,
                category=result.category if hasattr(result, 'category') else None,
                code_type=result.code_type if hasattr(result, 'code_type') else "CPT",
                is_active=result.is_active if hasattr(result, 'is_active') else True
            )
        return None
