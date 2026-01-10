"""
Result formatting for QueryEngine.

Converts retrieved nodes to structured output (Pydantic models).
"""

from typing import List, Literal, Dict

from llama_index.core.schema import NodeWithScore

from .schemas import (
    RegulationDocument,
    CurriculumDocument,
    RegulationRetrievalResult,
    CurriculumRetrievalResult
)


class ResultFormatter:
    """
    Formatter for retrieval results.

    Converts raw nodes to structured Pydantic models.
    """

    @staticmethod
    def _strip_metadata_from_content(content: str) -> str:
        """
        Remove prepended metadata from content.

        During indexing, metadata is prepended to content for better semantic search.
        Format:
            Tài liệu: xxx
            Tiêu đề: xxx
            Cấu trúc: xxx
            Ngày hiệu lực: xxx
            Loại: xxx
            ---
            [Actual content starts here]

        This method strips the metadata part, returning only the actual content.

        Args:
            content: Raw content with prepended metadata

        Returns:
            Clean content without metadata
        """
        # Split by separator "---"
        if "---" in content:
            parts = content.split("---", 1)
            if len(parts) == 2:
                return parts[1].strip()

        # Fallback: if no separator found, return original content
        return content

    def format(
        self,
        query: str,
        nodes: List[NodeWithScore],
        collection_type: Literal["regulation", "curriculum"]
    ) -> Dict:
        """
        Format nodes to structured output.

        Args:
            query: Original query
            nodes: Retrieved nodes
            collection_type: Type of collection

        Returns:
            Dict following RegulationRetrievalResult or CurriculumRetrievalResult schema
        """
        documents = []

        for node in nodes:
            metadata = node.node.metadata
            raw_content = node.node.get_content()

            # Strip prepended metadata from content
            clean_content = self._strip_metadata_from_content(raw_content)

            if collection_type == "regulation":
                # Build RegulationDocument
                doc_dict = {
                    "content": clean_content,
                    "title": metadata.get("title", ""),
                    "regulation_number": metadata.get("regulation_number"),
                    "hierarchy": metadata.get("hierarchy", ""),
                    "effective_date": metadata.get("effective_date"),
                    "document_type": metadata.get("document_type", "original"),
                    "year": metadata.get("year"),
                    "pdf_file": metadata.get("pdf_file"),
                    "score": round(float(node.score), 2)
                }
                # Validate with Pydantic
                doc = RegulationDocument(**doc_dict)
                documents.append(doc.model_dump())

            elif collection_type == "curriculum":
                # Build CurriculumDocument
                doc_dict = {
                    "content": clean_content,
                    "title": metadata.get("title", ""),
                    "year": metadata.get("year"),
                    "major": metadata.get("major"),
                    "major_code": metadata.get("major_code"),
                    "program_type": metadata.get("program_type"),
                    "program_name": metadata.get("program_name"),
                    "source_url": metadata.get("source_url"),
                    "score": round(float(node.score), 2)
                }
                # Validate with Pydantic
                doc = CurriculumDocument(**doc_dict)
                documents.append(doc.model_dump())

        # Build result based on collection type
        if collection_type == "regulation":
            result_obj = RegulationRetrievalResult(
                query=query,
                total_retrieved=len(documents),
                documents=documents
            )
        else:  # curriculum
            result_obj = CurriculumRetrievalResult(
                query=query,
                total_retrieved=len(documents),
                documents=documents
            )

        return result_obj.model_dump()
