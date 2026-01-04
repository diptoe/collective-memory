"""
Collective Memory Platform - Document Processor

Processes markdown/text documents for embedding with chunking and metadata.
"""

import re
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class DocumentChunk:
    """A chunk of a processed document."""
    content: str
    metadata: Dict[str, Any]
    chunk_index: int
    total_chunks: int


class DocumentProcessor:
    """
    Process markdown/text documents for embedding.

    Features:
    - Split by markdown headers
    - Configurable chunk size with overlap
    - Metadata preservation for each chunk
    """

    DEFAULT_CHUNK_SIZE = 1000
    DEFAULT_OVERLAP = 200
    MIN_CHUNK_SIZE = 100

    def __init__(
        self,
        chunk_size: int = None,
        overlap: int = None
    ):
        """
        Initialize document processor.

        Args:
            chunk_size: Maximum characters per chunk (default 1000)
            overlap: Character overlap between chunks (default 200)
        """
        self.chunk_size = chunk_size or self.DEFAULT_CHUNK_SIZE
        self.overlap = overlap or self.DEFAULT_OVERLAP

        if self.chunk_size < self.MIN_CHUNK_SIZE:
            raise ValueError(f"chunk_size must be at least {self.MIN_CHUNK_SIZE}")
        if self.overlap >= self.chunk_size:
            raise ValueError("overlap must be less than chunk_size")

    def process_markdown(
        self,
        content: str,
        title: str = None,
        source: str = None
    ) -> List[DocumentChunk]:
        """
        Process markdown content into chunks with metadata.

        Args:
            content: Markdown content
            title: Optional document title
            source: Optional source identifier

        Returns:
            List of DocumentChunk objects
        """
        if not content or not content.strip():
            return []

        # Split by headers first
        sections = self._split_by_headers(content)

        all_chunks = []
        chunk_index = 0

        for section in sections:
            section_content = section['content'].strip()
            if not section_content:
                continue

            # Chunk the section content
            text_chunks = self._chunk_text(
                section_content,
                self.chunk_size,
                self.overlap
            )

            for i, chunk_text in enumerate(text_chunks):
                metadata = {
                    'title': title,
                    'source': source,
                    'section_header': section.get('header', ''),
                    'section_level': section.get('level', 0),
                    'section_chunk_index': i,
                    'section_chunk_count': len(text_chunks),
                }

                all_chunks.append(DocumentChunk(
                    content=chunk_text,
                    metadata=metadata,
                    chunk_index=chunk_index,
                    total_chunks=0  # Updated below
                ))
                chunk_index += 1

        # Update total_chunks
        total = len(all_chunks)
        for chunk in all_chunks:
            chunk.total_chunks = total

        return all_chunks

    def process_text(
        self,
        content: str,
        title: str = None,
        source: str = None
    ) -> List[DocumentChunk]:
        """
        Process plain text content into chunks.

        Args:
            content: Plain text content
            title: Optional document title
            source: Optional source identifier

        Returns:
            List of DocumentChunk objects
        """
        if not content or not content.strip():
            return []

        chunks = self._chunk_text(content.strip(), self.chunk_size, self.overlap)

        return [
            DocumentChunk(
                content=chunk_text,
                metadata={
                    'title': title,
                    'source': source,
                    'chunk_index': i,
                    'chunk_count': len(chunks),
                },
                chunk_index=i,
                total_chunks=len(chunks)
            )
            for i, chunk_text in enumerate(chunks)
        ]

    def _split_by_headers(self, content: str) -> List[Dict[str, Any]]:
        """
        Split markdown by headers.

        Returns list of sections with header, level, and content.
        """
        # Pattern matches # Header, ## Header, etc.
        header_pattern = r'^(#{1,6})\s+(.+)$'

        sections = []
        current_section = {
            'header': '',
            'level': 0,
            'content': ''
        }

        for line in content.split('\n'):
            match = re.match(header_pattern, line)
            if match:
                # Save previous section if it has content
                if current_section['content'].strip():
                    sections.append(current_section)

                # Start new section
                current_section = {
                    'header': match.group(2).strip(),
                    'level': len(match.group(1)),
                    'content': ''
                }
            else:
                current_section['content'] += line + '\n'

        # Don't forget the last section
        if current_section['content'].strip():
            sections.append(current_section)

        return sections

    def _chunk_text(
        self,
        text: str,
        chunk_size: int,
        overlap: int
    ) -> List[str]:
        """
        Split text into overlapping chunks.

        Tries to break at sentence boundaries when possible.
        """
        text = text.strip()
        if not text:
            return []

        if len(text) <= chunk_size:
            return [text]

        chunks = []
        start = 0

        while start < len(text):
            end = start + chunk_size

            # If we're not at the end, try to break at a sentence boundary
            if end < len(text):
                # Look backwards for sentence end (.!?\n)
                best_break = end
                for i in range(min(100, end - start)):
                    pos = end - i
                    if pos > start and text[pos - 1] in '.!?\n':
                        best_break = pos
                        break

                # If no sentence break found, try word boundary
                if best_break == end:
                    for i in range(min(50, end - start)):
                        pos = end - i
                        if pos > start and text[pos - 1] == ' ':
                            best_break = pos
                            break

                end = best_break

            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)

            # Move start position with overlap
            start = end - overlap
            if start >= len(text):
                break

        return chunks

    def chunks_to_dict(self, chunks: List[DocumentChunk]) -> List[Dict[str, Any]]:
        """Convert chunks to dictionary format."""
        return [
            {
                'content': chunk.content,
                'metadata': chunk.metadata,
                'chunk_index': chunk.chunk_index,
                'total_chunks': chunk.total_chunks,
            }
            for chunk in chunks
        ]


# Global service instance
document_processor = DocumentProcessor()
