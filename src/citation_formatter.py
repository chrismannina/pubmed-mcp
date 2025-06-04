"""
Citation formatting utilities for PubMed MCP Server.

This module provides functionality to format article citations in various
academic styles including APA, MLA, Chicago, Vancouver, BibTeX, EndNote, and RIS.
"""

import re
from datetime import datetime
from typing import Any, Dict, List

# Handle both relative and absolute imports
try:
    from .models import Article, CitationFormat
    from .utils import format_authors, format_date
except ImportError:
    from models import Article, CitationFormat
    from utils import format_authors, format_date


class CitationFormatter:
    """Format citations in various academic styles."""

    @staticmethod
    def format_citation(
        article: Article, format_type: CitationFormat, include_abstract: bool = False
    ) -> str:
        """
        Format a single article citation.

        Args:
            article: Article to format
            format_type: Citation format to use
            include_abstract: Include abstract in citation

        Returns:
            Formatted citation string
        """
        formatter_map = {
            CitationFormat.BIBTEX: CitationFormatter._format_bibtex,
            CitationFormat.APA: CitationFormatter._format_apa,
            CitationFormat.MLA: CitationFormatter._format_mla,
            CitationFormat.CHICAGO: CitationFormatter._format_chicago,
            CitationFormat.VANCOUVER: CitationFormatter._format_vancouver,
            CitationFormat.ENDNOTE: CitationFormatter._format_endnote,
            CitationFormat.RIS: CitationFormatter._format_ris,
        }

        formatter = formatter_map.get(format_type, CitationFormatter._format_bibtex)
        return formatter(article, include_abstract)

    @staticmethod
    def format_multiple_citations(
        articles: List[Article], format_type: CitationFormat, include_abstracts: bool = False
    ) -> str:
        """Format multiple articles as citations."""
        citations = []

        for article in articles:
            citation = CitationFormatter.format_citation(article, format_type, include_abstracts)
            citations.append(citation)

        if format_type in [CitationFormat.BIBTEX, CitationFormat.RIS, CitationFormat.ENDNOTE]:
            return "\n\n".join(citations)
        else:
            return "\n\n".join(f"{i+1}. {citation}" for i, citation in enumerate(citations))

    @staticmethod
    def _format_bibtex(article: Article, include_abstract: bool = False) -> str:
        """Format citation in BibTeX format."""
        # Generate citation key
        first_author = article.authors[0].last_name if article.authors else "Unknown"
        year = CitationFormatter._extract_year(article.pub_date) or "Unknown"
        key = f"{first_author.lower().replace(' ', '')}{year}"

        # Clean title
        title = article.title.replace("{", "").replace("}", "")

        # Format authors
        authors_str = (
            " and ".join(
                [
                    f"{author.last_name}, {author.first_name or author.initials or ''}"
                    for author in article.authors
                ]
            )
            if article.authors
            else "Unknown"
        )

        bibtex_parts = [
            f"@article{{{key},",
            f"  title = {{{title}}},",
            f"  author = {{{authors_str}}},",
            f"  journal = {{{article.journal.title}}},",
        ]

        if article.journal.volume:
            bibtex_parts.append(f"  volume = {{{article.journal.volume}}},")

        if article.journal.issue:
            bibtex_parts.append(f"  number = {{{article.journal.issue}}},")

        if year != "Unknown":
            bibtex_parts.append(f"  year = {{{year}}},")

        if article.doi:
            bibtex_parts.append(f"  doi = {{{article.doi}}},")

        bibtex_parts.append(f"  pmid = {{{article.pmid}}},")

        if article.journal.issn:
            bibtex_parts.append(f"  issn = {{{article.journal.issn}}},")

        if include_abstract and article.abstract:
            abstract = article.abstract.replace("{", "").replace("}", "")
            bibtex_parts.append(f"  abstract = {{{abstract}}},")

        bibtex_parts.append("}")

        return "\n".join(bibtex_parts)

    @staticmethod
    def _format_apa(article: Article, include_abstract: bool = False) -> str:
        """Format citation in APA format."""
        # Authors
        if not article.authors:
            authors_str = "Unknown Author"
        elif len(article.authors) == 1:
            author = article.authors[0]
            authors_str = f"{author.last_name}, {author.first_name[0] if author.first_name else (author.initials or 'X')}."
        elif len(article.authors) <= 7:
            formatted_authors = []
            for i, author in enumerate(article.authors):
                if i == len(article.authors) - 1 and len(article.authors) > 1:
                    formatted_authors.append("& ")
                first_initial = (
                    author.first_name[0] if author.first_name else (author.initials or "X")
                )
                formatted_authors.append(f"{author.last_name}, {first_initial}.")
                if i < len(article.authors) - 2:
                    formatted_authors.append(", ")
            authors_str = "".join(formatted_authors)
        else:
            # More than 7 authors
            formatted_authors = []
            for i in range(6):
                author = article.authors[i]
                first_initial = (
                    author.first_name[0] if author.first_name else (author.initials or "X")
                )
                formatted_authors.append(f"{author.last_name}, {first_initial}.")
                if i < 5:
                    formatted_authors.append(", ")
            formatted_authors.append(", ... ")
            last_author = article.authors[-1]
            last_initial = (
                last_author.first_name[0]
                if last_author.first_name
                else (last_author.initials or "X")
            )
            formatted_authors.append(f"& {last_author.last_name}, {last_initial}.")
            authors_str = "".join(formatted_authors)

        # Year
        year = CitationFormatter._extract_year(article.pub_date) or "n.d."

        # Title
        title = article.title.rstrip(".")

        # Journal
        journal = article.journal.title

        # Volume and issue
        volume_issue = ""
        if article.journal.volume:
            volume_issue = f"*{article.journal.volume}*"
            if article.journal.issue:
                volume_issue += f"({article.journal.issue})"

        # DOI or PMID
        identifier = ""
        if article.doi:
            identifier = f"https://doi.org/{article.doi}"
        else:
            identifier = f"PMID: {article.pmid}"

        citation_parts = [authors_str, f"({year}).", f"{title}.", f"*{journal}*"]
        if volume_issue:
            citation_parts.append(f"{volume_issue}.")
        citation_parts.append(identifier)

        citation = " ".join(citation_parts)

        if include_abstract and article.abstract:
            citation += f"\n\nAbstract: {article.abstract}"

        return citation

    @staticmethod
    def _format_mla(article: Article, include_abstract: bool = False) -> str:
        """Format citation in MLA format."""
        # First author
        if not article.authors:
            authors_str = "Unknown Author"
        else:
            first_author = article.authors[0]
            authors_str = f"{first_author.last_name}, {first_author.first_name or first_author.initials or 'Unknown'}"

            if len(article.authors) > 1:
                authors_str += ", et al"

        # Title
        title = f'"{article.title.rstrip(".")}"'

        # Journal
        journal = f"*{article.journal.title}*"

        # Volume and issue
        volume_info = ""
        if article.journal.volume:
            volume_info = f"vol. {article.journal.volume}"
            if article.journal.issue:
                volume_info += f", no. {article.journal.issue}"

        # Date
        year = CitationFormatter._extract_year(article.pub_date)
        date_str = f"{year}" if year else "n.d."

        # Page numbers (not available from PubMed typically)

        citation_parts = [authors_str, title, journal]
        if volume_info:
            citation_parts.append(volume_info)
        citation_parts.append(f"{date_str}.")

        if article.doi:
            citation_parts.append(f"doi:{article.doi}")
        else:
            citation_parts.append(f"PMID: {article.pmid}")

        citation = ", ".join(citation_parts[:-1]) + ", " + citation_parts[-1]

        if include_abstract and article.abstract:
            citation += f"\n\nAbstract: {article.abstract}"

        return citation

    @staticmethod
    def _format_chicago(article: Article, include_abstract: bool = False) -> str:
        """Format citation in Chicago format."""
        # Authors
        if not article.authors:
            authors_str = "Unknown Author"
        elif len(article.authors) == 1:
            author = article.authors[0]
            authors_str = f"{author.last_name}, {author.first_name or author.initials or 'Unknown'}"
        else:
            first_author = article.authors[0]
            authors_str = f"{first_author.last_name}, {first_author.first_name or first_author.initials or 'Unknown'}"
            if len(article.authors) <= 3:
                for author in article.authors[1:-1]:
                    authors_str += (
                        f", {author.first_name or author.initials or 'Unknown'} {author.last_name}"
                    )
                if len(article.authors) > 1:
                    last_author = article.authors[-1]
                    authors_str += f", and {last_author.first_name or last_author.initials or 'Unknown'} {last_author.last_name}"
            else:
                authors_str += ", et al"

        # Title
        title = f'"{article.title.rstrip(".")}"'

        # Journal
        journal = f"*{article.journal.title}*"

        # Volume and issue
        volume_info = ""
        if article.journal.volume:
            volume_info = f"{article.journal.volume}"
            if article.journal.issue:
                volume_info += f", no. {article.journal.issue}"

        # Date
        year = CitationFormatter._extract_year(article.pub_date)
        date_str = f"({year})" if year else "(n.d.)"

        citation_parts = [authors_str, title, journal]
        if volume_info:
            citation_parts.append(volume_info)
        citation_parts.append(date_str)

        if article.doi:
            citation_parts.append(f"https://doi.org/{article.doi}")
        else:
            citation_parts.append(f"PMID: {article.pmid}")

        citation = ". ".join(citation_parts[:-1]) + ". " + citation_parts[-1] + "."

        if include_abstract and article.abstract:
            citation += f"\n\nAbstract: {article.abstract}"

        return citation

    @staticmethod
    def _format_vancouver(article: Article, include_abstract: bool = False) -> str:
        """Format citation in Vancouver format."""
        # Authors
        if not article.authors:
            authors_str = "Unknown Author"
        else:
            formatted_authors = []
            for i, author in enumerate(article.authors):
                if i >= 6:  # Vancouver style: list first 6 authors, then et al.
                    formatted_authors.append("et al")
                    break
                first_initial = (
                    author.first_name[0] if author.first_name else (author.initials or "X")
                )
                formatted_authors.append(f"{author.last_name} {first_initial}")
            authors_str = ", ".join(formatted_authors)

        # Title
        title = article.title.rstrip(".")

        # Journal abbreviation
        journal = article.journal.iso_abbreviation or article.journal.title

        # Date
        year = CitationFormatter._extract_year(article.pub_date)

        # Volume and issue
        volume_info = ""
        if article.journal.volume:
            volume_info = f"{article.journal.volume}"
            if article.journal.issue:
                volume_info += f"({article.journal.issue})"

        citation_parts = [f"{authors_str}.", f"{title}.", f"{journal}."]
        if year:
            citation_parts.append(f"{year};")
        if volume_info:
            citation_parts.append(f"{volume_info}.")

        if article.doi:
            citation_parts.append(f"doi: {article.doi}")
        else:
            citation_parts.append(f"PMID: {article.pmid}")

        citation = " ".join(citation_parts)

        if include_abstract and article.abstract:
            citation += f"\n\nAbstract: {article.abstract}"

        return citation

    @staticmethod
    def _format_endnote(article: Article, include_abstract: bool = False) -> str:
        """Format citation in EndNote format."""
        lines = [
            "%0 Journal Article",
            f"%T {article.title}",
        ]

        # Authors
        for author in article.authors:
            full_name = f"{author.first_name or author.initials or ''} {author.last_name}".strip()
            lines.append(f"%A {full_name}")

        # Journal
        lines.append(f"%J {article.journal.title}")

        # Date
        year = CitationFormatter._extract_year(article.pub_date)
        if year:
            lines.append(f"%D {year}")

        # Volume
        if article.journal.volume:
            lines.append(f"%V {article.journal.volume}")

        # Issue
        if article.journal.issue:
            lines.append(f"%N {article.journal.issue}")

        # DOI
        if article.doi:
            lines.append(f"%R {article.doi}")

        # PMID
        lines.append(f"%M {article.pmid}")

        # Abstract
        if include_abstract and article.abstract:
            lines.append(f"%X {article.abstract}")

        return "\n".join(lines)

    @staticmethod
    def _format_ris(article: Article, include_abstract: bool = False) -> str:
        """Format citation in RIS format."""
        lines = [
            "TY  - JOUR",
            f"TI  - {article.title}",
        ]

        # Authors
        for author in article.authors:
            full_name = f"{author.last_name}, {author.first_name or author.initials or ''}".strip()
            lines.append(f"AU  - {full_name}")

        # Journal
        lines.append(f"JO  - {article.journal.title}")

        # Date
        year = CitationFormatter._extract_year(article.pub_date)
        if year:
            lines.append(f"PY  - {year}")

        # Volume
        if article.journal.volume:
            lines.append(f"VL  - {article.journal.volume}")

        # Issue
        if article.journal.issue:
            lines.append(f"IS  - {article.journal.issue}")

        # DOI
        if article.doi:
            lines.append(f"DO  - {article.doi}")

        # PMID
        lines.append(f"AN  - {article.pmid}")

        # Abstract
        if include_abstract and article.abstract:
            lines.append(f"AB  - {article.abstract}")

        lines.append("ER  - ")

        return "\n".join(lines)

    @staticmethod
    def _extract_year(date_str: str) -> str:
        """Extract year from date string."""
        if not date_str:
            return None

        # Try to extract 4-digit year
        year_match = re.search(r"\d{4}", date_str)
        if year_match:
            return year_match.group()

        return None
