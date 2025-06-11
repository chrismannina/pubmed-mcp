"""
Citation formatting module for different academic citation styles.

This module provides functionality to format PubMed articles into various
citation formats including BibTeX, APA, MLA, Chicago, Vancouver, EndNote,
and RIS.
"""

import logging
import re
from typing import List

from .models import Article, Author, CitationFormat

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
        """Format multiple articles as citations.

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
    def _format_authors_apa(authors: List[Author]) -> str:
        """Format authors for APA style."""
        if not authors:
            return ""

        formatted_authors = []
        authors_to_process = authors[:20] if len(authors) <= 20 else authors[:19]

        for author in authors_to_process:
            if isinstance(author, str):
                # Handle string authors (legacy format)
                parts = author.split()
                if len(parts) >= 2:
                    # Check if this looks like a real name (LastName should be alphabetic)
                    last_name = parts[-1]
                    if last_name.isalpha() and len(last_name) > 1:
                        # Last, F. M. format for real names
                        initials = " ".join([f"{name[0]}." for name in parts[:-1]])
                        formatted_authors.append(f"{last_name}, {initials}")
                    else:
                        # Keep as-is for things like "Author 24"
                        formatted_authors.append(author)
                else:
                    formatted_authors.append(author)
            else:
                # Handle Author objects
                if author.last_name:
                    author_str = author.last_name
                    if author.initials:
                        # Ensure initials have periods
                        initials = author.initials
                        if not initials.endswith("."):
                            initials += "."
                        author_str += f", {initials}"
                    elif author.first_name:
                        author_str += f", {author.first_name[0]}."
                    formatted_authors.append(author_str)
                elif author.first_name:
                    formatted_authors.append(author.first_name)

        if len(authors) > 20:
            # For more than 20 authors, show first 19, then "... & last_author"
            last_author = authors[-1]
            if isinstance(last_author, str):
                parts = last_author.split()
                if len(parts) >= 2:
                    last_name = parts[-1]
                    if last_name.isalpha() and len(last_name) > 1:
                        # Format real names
                        initials = " ".join([f"{name[0]}." for name in parts[:-1]])
                        last_formatted = f"{last_name}, {initials}"
                    else:
                        # Keep as-is for things like "Author 24"
                        last_formatted = last_author
                else:
                    last_formatted = last_author
            else:
                # Handle Author objects
                if last_author.last_name:
                    last_formatted = last_author.last_name
                    if last_author.initials:
                        initials = last_author.initials
                        if not initials.endswith("."):
                            initials += "."
                        last_formatted += f", {initials}"
                    elif last_author.first_name:
                        last_formatted += f", {last_author.first_name[0]}."
                else:
                    last_formatted = last_author.first_name or "Unknown"

            return ", ".join(formatted_authors) + ", ... & " + last_formatted
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
        if article.pub_date:
            year = article.pub_date[:4]
            citation_parts.append(f"({year})")

        # Title
        if article.title:
            title = CitationFormatter._clean_text(article.title)
            # Remove period at end if present
            title = title.rstrip(".")
            citation_parts.append(f"{title}.")

        # Journal
        if article.journal:
            journal_part = f"*{article.journal.title}*"
            if article.journal.volume:
                journal_part += f", *{article.journal.volume}*"
                if article.journal.issue:
                    journal_part += f"({article.journal.issue})"
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
            if isinstance(first_author, str):
                parts = first_author.split()
                if len(parts) >= 2:
                    mla_author = f"{parts[-1]}, {' '.join(parts[:-1])}"
                else:
                    mla_author = first_author
            else:
                # Handle Author object
                if first_author.last_name and first_author.first_name:
                    mla_author = f"{first_author.last_name}, {first_author.first_name}"
                elif first_author.last_name:
                    mla_author = first_author.last_name
                else:
                    mla_author = first_author.first_name or "Unknown Author"

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
            journal_part = f"*{article.journal.title}*"
            if article.journal.volume:
                journal_part += f", vol. {article.journal.volume}"
                if article.journal.issue:
                    journal_part += f", no. {article.journal.issue}"
            if article.pub_date:
                year = article.pub_date[:4]
                journal_part += f", {year}"
            citation_parts.append(journal_part + ".")

        # Access information
        if article.pmid:
            pmid_url = f"https://pubmed.ncbi.nlm.nih.gov/{article.pmid}/"
            citation_parts.append(f"Web. {pmid_url}")
        elif article.doi:
            citation_parts.append(f"DOI: {article.doi}.")

        return " ".join(citation_parts)

    @staticmethod
    def _format_chicago(article: Article) -> str:
        """Format citation in Chicago style."""
        citation_parts = []

        # Authors
        if article.authors:
            first_author = article.authors[0]
            if isinstance(first_author, str):
                parts = first_author.split()
                if len(parts) >= 2:
                    chicago_author = f"{parts[-1]}, {' '.join(parts[:-1])}"
                else:
                    chicago_author = first_author
            else:
                # Handle Author object
                if first_author.last_name and first_author.first_name:
                    chicago_author = f"{first_author.last_name}, {first_author.first_name}"
                elif first_author.last_name:
                    chicago_author = first_author.last_name
                else:
                    chicago_author = first_author.first_name or "Unknown Author"

            if len(article.authors) > 1:
                chicago_author += ", et al"
            citation_parts.append(chicago_author + ".")

        # Title
        if article.title:
            title = CitationFormatter._clean_text(article.title)
            title = title.rstrip(".")
            citation_parts.append(f'"{title}."')

        # Journal
        if article.journal:
            journal_part = f"*{article.journal.title}*"
            if article.journal.volume:
                journal_part += f" {article.journal.volume}"
                if article.journal.issue:
                    journal_part += f", no. {article.journal.issue}"
            if article.pub_date:
                year = article.pub_date[:4]
                journal_part += f" ({year})"
            citation_parts.append(journal_part + ".")

        # DOI or PMID
        if article.doi:
            citation_parts.append(f"https://doi.org/{article.doi}.")
        elif article.pmid:
            pmid_url = f"https://pubmed.ncbi.nlm.nih.gov/{article.pmid}/"
            citation_parts.append(pmid_url)

        return " ".join(citation_parts)

    @staticmethod
    def _format_vancouver(article: Article) -> str:
        """Format citation in Vancouver style."""
        citation_parts = []

        # Authors (up to 6, then et al.)
        if article.authors:
            vancouver_authors = []
            for i, author in enumerate(article.authors[:6]):
                if isinstance(author, str):
                    parts = author.split()
                    if len(parts) >= 2:
                        # Last FM format
                        last_name = parts[-1]
                        initials = "".join([name[0] for name in parts[:-1]])
                        vancouver_authors.append(f"{last_name} {initials}")
                    else:
                        vancouver_authors.append(author)
                else:
                    # Handle Author object
                    if author.last_name:
                        author_str = author.last_name
                        if author.initials:
                            author_str += f" {author.initials.replace('.', '')}"
                        elif author.first_name:
                            author_str += f" {author.first_name[0]}"
                        vancouver_authors.append(author_str)

            if len(article.authors) > 6:
                vancouver_authors.append("et al")

            citation_parts.append(", ".join(vancouver_authors) + ".")

        # Title
        if article.title:
            title = CitationFormatter._clean_text(article.title)
            title = title.rstrip(".")
            citation_parts.append(f"{title}.")

        # Journal
        if article.journal:
            journal_part = article.journal.title
            if article.pub_date:
                year = article.pub_date[:4]
                journal_part += f" {year}"
            if article.journal.volume:
                journal_part += f";{article.journal.volume}"
                if article.journal.issue:
                    journal_part += f"({article.journal.issue})"
            citation_parts.append(journal_part + ".")

        # PMID
        if article.pmid:
            citation_parts.append(f"PMID: {article.pmid}")

        return " ".join(citation_parts)

    @staticmethod
    def _format_bibtex(article: Article) -> str:
        """Format citation in BibTeX format."""
        # Generate citation key
        key_parts = []
        if article.authors:
            first_author = article.authors[0]
            if isinstance(first_author, str):
                key_parts.append(first_author.split()[-1].lower())
            else:
                if first_author and first_author.last_name:
                    key_parts.append(first_author.last_name.lower())

        if article.pub_date:
            key_parts.append(article.pub_date[:4])

        # Add a simple letter suffix for the first word
        if article.title:
            # Use first significant word from title
            title_words = article.title.split()
            for word in title_words:
                if len(word) > 0 and word.lower() not in [
                    "the",
                    "and",
                    "for",
                    "with",
                    "a",
                    "an",
                    "sample",  # Skip "sample" as it's not meaningful
                    "research",  # Skip "research" as it's not meaningful
                ]:
                    key_parts.append(word[0].lower())
                    break

        citation_key = "".join(key_parts) if key_parts else f"article_{article.pmid}"

        bibtex_lines = [f"@article{{{citation_key},"]

        # Title
        if article.title:
            title = CitationFormatter._clean_text(article.title)
            bibtex_lines.append(f"  title = {{{title}}},")

        # Authors
        if article.authors:
            author_list = []
            for author in article.authors:
                if isinstance(author, str):
                    author_list.append(author)
                else:
                    if author.first_name and author.last_name:
                        author_list.append(f"{author.first_name} {author.last_name}")
                    elif author.last_name:
                        author_list.append(author.last_name)
                    elif author.first_name:
                        author_list.append(author.first_name)

            if author_list:
                authors_str = " and ".join(author_list)
                bibtex_lines.append(f"  author = {{{authors_str}}},")

        # Journal
        if article.journal:
            bibtex_lines.append(f"  journal = {{{article.journal.title}}},")
            if article.journal.volume:
                bibtex_lines.append(f"  volume = {{{article.journal.volume}}},")
            if article.journal.issue:
                bibtex_lines.append(f"  number = {{{article.journal.issue}}},")

        # Year
        if article.pub_date:
            year = article.pub_date[:4]
            bibtex_lines.append(f"  year = {{{year}}},")

        # DOI
        if article.doi:
            bibtex_lines.append(f"  doi = {{{article.doi}}},")

        # PMID
        if article.pmid:
            bibtex_lines.append(f"  pmid = {{{article.pmid}}},")

        # Note: pages field removed since it's not available in Article model
        # Could be added later if journal provides page information

        bibtex_lines.append("}")
        return "\n".join(bibtex_lines)

    @staticmethod
    def _format_endnote(article: Article) -> str:
        """Format citation in EndNote format."""
        endnote_lines = []

        # Reference type (Journal Article)
        endnote_lines.append("%0 Journal Article")

        # Title
        if article.title:
            title = CitationFormatter._clean_text(article.title)
            endnote_lines.append(f"%T {title}")

        # Authors
        for author in article.authors:
            if isinstance(author, str):
                endnote_lines.append(f"%A {author}")
            else:
                if author.first_name and author.last_name:
                    endnote_lines.append(f"%A {author.first_name} {author.last_name}")
                elif author.last_name:
                    endnote_lines.append(f"%A {author.last_name}")
                elif author.first_name:
                    endnote_lines.append(f"%A {author.first_name}")

        # Journal
        if article.journal:
            endnote_lines.append(f"%J {article.journal.title}")
            if article.journal.volume:
                endnote_lines.append(f"%V {article.journal.volume}")
            if article.journal.issue:
                endnote_lines.append(f"%N {article.journal.issue}")

        # Date
        if article.pub_date:
            endnote_lines.append(f"%D {article.pub_date}")

        # DOI
        if article.doi:
            endnote_lines.append(f"%R {article.doi}")

        # PMID
        if article.pmid:
            endnote_lines.append(f"%M {article.pmid}")

        # Note: pages field removed since it's not available in Article model

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
        for author in article.authors:
            if isinstance(author, str):
                ris_lines.append(f"AU  - {author}")
            else:
                if author.first_name and author.last_name:
                    ris_lines.append(f"AU  - {author.first_name} {author.last_name}")
                elif author.last_name:
                    ris_lines.append(f"AU  - {author.last_name}")
                elif author.first_name:
                    ris_lines.append(f"AU  - {author.first_name}")

        # Journal
        if article.journal:
            ris_lines.append(f"JO  - {article.journal.title}")
            if article.journal.volume:
                ris_lines.append(f"VL  - {article.journal.volume}")
            if article.journal.issue:
                ris_lines.append(f"IS  - {article.journal.issue}")

            # Handle pages
            if hasattr(article.journal, "pages") and article.journal.pages:
                pages = article.journal.pages
                if "-" in pages:
                    # Page range (e.g., "123-456")
                    start_page, end_page = pages.split("-", 1)
                    ris_lines.append(f"SP  - {start_page.strip()}")
                    ris_lines.append(f"EP  - {end_page.strip()}")
                else:
                    # Single page
                    ris_lines.append(f"SP  - {pages.strip()}")

        # Date
        if article.pub_date:
            # Try to format date properly
            date_parts = article.pub_date.split("-")
            if len(date_parts) >= 1:
                ris_lines.append(f"PY  - {date_parts[0]}")
            ris_lines.append(f"DA  - {article.pub_date}")

        # DOI
        if article.doi:
            ris_lines.append(f"DO  - {article.doi}")

        # PMID
        if article.pmid:
            ris_lines.append(f"AN  - {article.pmid}")

        # Note: pages field handling removed since it's not available
        # in Article model

        # End of reference
        ris_lines.append("ER  - ")

        return "\n".join(ris_lines)
