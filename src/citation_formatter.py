"""
Citation formatting module for different academic citation styles.

This module provides functionality to format PubMed articles into various
citation formats including BibTeX, APA, MLA, Chicago, Vancouver, EndNote, and RIS.
"""

import logging
import re
from typing import List

from .models import Article, CitationFormat

logger = logging.getLogger(__name__)


class CitationFormatter:
    """Citation formatter for various academic styles."""

    @staticmethod
    def format_citation(article: Article, format_type: CitationFormat) -> str:
        """
        Format an article citation in the specified format.

        Args:
            article: The article to format
            format_type: The citation format to use

        Returns:
            Formatted citation string

        Raises:
            ValueError: If format type is not supported
        """
        formatters = {
            CitationFormat.APA: CitationFormatter._format_apa,
            CitationFormat.MLA: CitationFormatter._format_mla,
            CitationFormat.CHICAGO: CitationFormatter._format_chicago,
            CitationFormat.VANCOUVER: CitationFormatter._format_vancouver,
            CitationFormat.BIBTEX: CitationFormatter._format_bibtex,
            CitationFormat.ENDNOTE: CitationFormatter._format_endnote,
            CitationFormat.RIS: CitationFormatter._format_ris,
        }

        formatter = formatters.get(format_type)
        if not formatter:
            raise ValueError(f"Unsupported citation format: {format_type}")

        return formatter(article)

    @staticmethod
    def format_multiple_citations(
        articles: List[Article], format_type: CitationFormat
    ) -> List[str]:
        """
        Format multiple articles into citations.

        Args:
            articles: List of articles to format
            format_type: The citation format to use

        Returns:
            List of formatted citation strings
        """
        return [CitationFormatter.format_citation(article, format_type) for article in articles]

    @staticmethod
    def _clean_text(text: str) -> str:
        """Clean text for citation formatting."""
        if not text:
            return ""
        # Remove HTML tags and extra whitespace
        text = re.sub(r"<[^>]+>", "", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    @staticmethod
    def _format_authors_apa(authors: List[str]) -> str:
        """Format authors for APA style."""
        if not authors:
            return ""

        formatted_authors = []
        for author in authors[:20]:  # Limit to first 20 authors
            parts = author.split()
            if len(parts) >= 2:
                # Last, F. M. format
                last_name = parts[-1]
                initials = " ".join([f"{name[0]}." for name in parts[:-1]])
                formatted_authors.append(f"{last_name}, {initials}")
            else:
                formatted_authors.append(author)

        if len(authors) > 20:
            formatted_authors.append("... & " + formatted_authors[-1])
            return ", ".join(formatted_authors[:-2]) + ", " + formatted_authors[-1]
        elif len(formatted_authors) > 1:
            return ", ".join(formatted_authors[:-1]) + ", & " + formatted_authors[-1]
        else:
            return formatted_authors[0] if formatted_authors else ""

    @staticmethod
    def _format_apa(article: Article) -> str:
        """Format citation in APA style."""
        citation_parts = []

        # Authors
        authors = CitationFormatter._format_authors_apa(article.authors)
        if authors:
            citation_parts.append(authors)

        # Year
        if article.publication_date:
            year = article.publication_date[:4]
            citation_parts.append(f"({year})")

        # Title
        if article.title:
            title = CitationFormatter._clean_text(article.title)
            # Remove period at end if present
            title = title.rstrip(".")
            citation_parts.append(f"{title}.")

        # Journal
        if article.journal:
            journal_part = f"*{article.journal}*"
            if article.volume:
                journal_part += f", *{article.volume}*"
                if article.issue:
                    journal_part += f"({article.issue})"
            if article.pages:
                journal_part += f", {article.pages}"
            citation_parts.append(journal_part + ".")

        # DOI or PMID
        if article.doi:
            citation_parts.append(f"https://doi.org/{article.doi}")
        elif article.pmid:
            pmid_url = f"https://pubmed.ncbi.nlm.nih.gov/{article.pmid}/"
            citation_parts.append(pmid_url)

        return " ".join(citation_parts)

    @staticmethod
    def _format_mla(article: Article) -> str:
        """Format citation in MLA style."""
        citation_parts = []

        # Authors (Last, First format for first author)
        if article.authors:
            first_author = article.authors[0]
            parts = first_author.split()
            if len(parts) >= 2:
                mla_author = f"{parts[-1]}, {' '.join(parts[:-1])}"
            else:
                mla_author = first_author

            if len(article.authors) > 1:
                mla_author += ", et al"
            citation_parts.append(mla_author + ".")

        # Title
        if article.title:
            title = CitationFormatter._clean_text(article.title)
            title = title.rstrip(".")
            citation_parts.append(f'"{title}."')

        # Journal
        if article.journal:
            journal_part = f"*{article.journal}*"
            if article.volume:
                journal_part += f", vol. {article.volume}"
                if article.issue:
                    journal_part += f", no. {article.issue}"
            if article.publication_date:
                year = article.publication_date[:4]
                journal_part += f", {year}"
            if article.pages:
                journal_part += f", pp. {article.pages}"
            citation_parts.append(journal_part + ".")

        # Access information
        if article.pmid:
            pmid_url = f"https://pubmed.ncbi.nlm.nih.gov/{article.pmid}/"
            citation_parts.append(f"Web. {pmid_url}")

        return " ".join(citation_parts)

    @staticmethod
    def _format_chicago(article: Article) -> str:
        """Format citation in Chicago style."""
        citation_parts = []

        # Authors
        if article.authors:
            first_author = article.authors[0]
            parts = first_author.split()
            if len(parts) >= 2:
                chicago_author = f"{parts[-1]}, {' '.join(parts[:-1])}"
            else:
                chicago_author = first_author

            if len(article.authors) > 1:
                chicago_author += ", et al"
            citation_parts.append(chicago_author + ".")

        # Title
        if article.title:
            title = CitationFormatter._clean_text(article.title)
            title = title.rstrip(".")
            citation_parts.append(f'"{title}."')

        # Journal and publication details
        if article.journal:
            journal_part = f"*{article.journal}*"
            if article.volume:
                journal_part += f" {article.volume}"
                if article.issue:
                    journal_part += f", no. {article.issue}"
            if article.publication_date:
                year = article.publication_date[:4]
                journal_part += f" ({year})"
            if article.pages:
                journal_part += f": {article.pages}"
            citation_parts.append(journal_part + ".")

        # DOI or access info
        if article.doi:
            citation_parts.append(f"https://doi.org/{article.doi}.")
        elif article.pmid:
            pmid_url = f"https://pubmed.ncbi.nlm.nih.gov/{article.pmid}/"
            citation_parts.append(f"Accessed {pmid_url}.")

        return " ".join(citation_parts)

    @staticmethod
    def _format_vancouver(article: Article) -> str:
        """Format citation in Vancouver style."""
        citation_parts = []

        # Authors (initials come after surname)
        if article.authors:
            vancouver_authors = []
            for author in article.authors[:6]:  # Vancouver limits to 6 authors
                parts = author.split()
                if len(parts) >= 2:
                    last_name = parts[-1]
                    initials = "".join([name[0] for name in parts[:-1]])
                    vancouver_authors.append(f"{last_name} {initials}")
                else:
                    vancouver_authors.append(author)

            if len(article.authors) > 6:
                vancouver_authors.append("et al")

            citation_parts.append(", ".join(vancouver_authors) + ".")

        # Title
        if article.title:
            title = CitationFormatter._clean_text(article.title)
            title = title.rstrip(".")
            citation_parts.append(f"{title}.")

        # Journal abbreviation and details
        if article.journal:
            journal_part = article.journal  # In Vancouver, use journal abbreviation
            if article.publication_date:
                year = article.publication_date[:4]
                journal_part += f" {year}"
            if article.volume:
                journal_part += f";{article.volume}"
                if article.issue:
                    journal_part += f"({article.issue})"
            if article.pages:
                journal_part += f":{article.pages}"
            citation_parts.append(journal_part + ".")

        # PMID
        if article.pmid:
            citation_parts.append(f"PMID: {article.pmid}.")

        return " ".join(citation_parts)

    @staticmethod
    def _format_bibtex(article: Article) -> str:
        """Format citation in BibTeX format."""
        # Generate a citation key
        key_parts = []
        if article.authors:
            first_author_last = article.authors[0].split()[-1].lower()
            key_parts.append(first_author_last)
        if article.publication_date:
            key_parts.append(article.publication_date[:4])
        if article.title:
            # Use first word of title
            first_word = article.title.split()[0].lower()
            first_word = re.sub(r"[^a-z0-9]", "", first_word)
            key_parts.append(first_word)

        citation_key = "".join(key_parts) if key_parts else "unknown"

        bibtex_lines = ["@article{" + citation_key + ","]

        if article.title:
            title = CitationFormatter._clean_text(article.title)
            bibtex_lines.append(f"  title = {{{title}}},")

        if article.authors:
            authors_str = " and ".join(article.authors)
            bibtex_lines.append(f"  author = {{{authors_str}}},")

        if article.journal:
            bibtex_lines.append(f"  journal = {{{article.journal}}},")

        if article.volume:
            bibtex_lines.append(f"  volume = {{{article.volume}}},")

        if article.issue:
            bibtex_lines.append(f"  number = {{{article.issue}}},")

        if article.pages:
            bibtex_lines.append(f"  pages = {{{article.pages}}},")

        if article.publication_date:
            year = article.publication_date[:4]
            bibtex_lines.append(f"  year = {{{year}}},")

        if article.doi:
            bibtex_lines.append(f"  doi = {{{article.doi}}},")

        if article.pmid:
            bibtex_lines.append(f"  pmid = {{{article.pmid}}},")

        bibtex_lines.append("}")

        return "\n".join(bibtex_lines)

    @staticmethod
    def _format_endnote(article: Article) -> str:
        """Format citation in EndNote format."""
        endnote_lines = []

        # Reference type
        endnote_lines.append("%0 Journal Article")

        # Title
        if article.title:
            title = CitationFormatter._clean_text(article.title)
            endnote_lines.append(f"%T {title}")

        # Authors
        if article.authors:
            for author in article.authors:
                endnote_lines.append(f"%A {author}")

        # Journal
        if article.journal:
            endnote_lines.append(f"%J {article.journal}")

        # Volume
        if article.volume:
            endnote_lines.append(f"%V {article.volume}")

        # Issue
        if article.issue:
            endnote_lines.append(f"%N {article.issue}")

        # Pages
        if article.pages:
            endnote_lines.append(f"%P {article.pages}")

        # Date
        if article.publication_date:
            endnote_lines.append(f"%D {article.publication_date}")

        # DOI
        if article.doi:
            endnote_lines.append(f"%R {article.doi}")

        # PMID
        if article.pmid:
            endnote_lines.append(f"%M {article.pmid}")

        return "\n".join(endnote_lines)

    @staticmethod
    def _format_ris(article: Article) -> str:
        """Format citation in RIS format."""
        ris_lines = []

        # Type of reference
        ris_lines.append("TY  - JOUR")

        # Title
        if article.title:
            title = CitationFormatter._clean_text(article.title)
            ris_lines.append(f"TI  - {title}")

        # Authors
        if article.authors:
            for author in article.authors:
                ris_lines.append(f"AU  - {author}")

        # Journal
        if article.journal:
            ris_lines.append(f"JO  - {article.journal}")

        # Volume
        if article.volume:
            ris_lines.append(f"VL  - {article.volume}")

        # Issue
        if article.issue:
            ris_lines.append(f"IS  - {article.issue}")

        # Pages
        if article.pages:
            # Split page range if present
            if "-" in article.pages:
                start_page, end_page = article.pages.split("-", 1)
                ris_lines.append(f"SP  - {start_page.strip()}")
                ris_lines.append(f"EP  - {end_page.strip()}")
            else:
                ris_lines.append(f"SP  - {article.pages}")

        # Date
        if article.publication_date:
            # RIS format expects YYYY/MM/DD but we might only have year
            date_parts = article.publication_date.split("-")
            if len(date_parts) >= 1:
                ris_lines.append(f"PY  - {date_parts[0]}")
            if len(date_parts) >= 2:
                ris_lines.append(f"DA  - {article.publication_date}")

        # DOI
        if article.doi:
            ris_lines.append(f"DO  - {article.doi}")

        # PMID
        if article.pmid:
            ris_lines.append(f"AN  - {article.pmid}")

        # End of record
        ris_lines.append("ER  - ")

        return "\n".join(ris_lines)
