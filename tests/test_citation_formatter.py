"""Tests for the citation formatter module."""

import pytest

from src.citation_formatter import CitationFormatter
from src.models import Article, Author, CitationFormat, Journal, MeSHTerm


class TestCitationFormatter:
    """Test the CitationFormatter class."""

    @pytest.fixture
    def sample_article(self):
        """Create a sample article for testing."""
        return Article(
            pmid="12345678",
            title="A Sample Research Article on Cancer Treatment",
            abstract="This is a sample abstract describing cancer treatment research.",
            authors=[
                Author(
                    last_name="Smith",
                    first_name="John",
                    initials="J",
                    affiliation="University Hospital",
                ),
                Author(
                    last_name="Doe",
                    first_name="Jane",
                    initials="J",
                ),
                Author(last_name="Johnson", first_name="Bob", initials="B"),
            ],
            journal=Journal(
                title="Journal of Cancer Research",
                iso_abbreviation="J Cancer Res",
                issn="1234-5678",
                volume="25",
                issue="3",
                pub_date="2023",
            ),
            pub_date="2023/03/15",
            doi="10.1000/example.doi",
            pmc_id="PMC1234567",
            article_types=["Journal Article", "Research Support"],
            mesh_terms=[
                MeSHTerm(descriptor_name="Cancer", major_topic=True),
                MeSHTerm(descriptor_name="Treatment", major_topic=False),
            ],
            keywords=["cancer", "treatment", "research"],
            languages=["eng"],
        )

    @pytest.fixture
    def minimal_article(self):
        """Create a minimal article for testing edge cases."""
        return Article(
            pmid="87654321",
            title="Minimal Article",
            journal=Journal(title="Basic Journal"),
        )

    def test_format_citation_apa(self, sample_article):
        """Test APA citation formatting."""
        result = CitationFormatter.format_citation(sample_article, CitationFormat.APA)

        assert "Smith, J., Doe, J., & Johnson, B." in result
        assert "(2023)" in result
        assert "A Sample Research Article on Cancer Treatment" in result
        assert "*Journal of Cancer Research*" in result
        assert "*25*(3)" in result
        assert "https://doi.org/10.1000/example.doi" in result

    def test_format_citation_mla(self, sample_article):
        """Test MLA citation formatting."""
        result = CitationFormatter.format_citation(sample_article, CitationFormat.MLA)

        assert "Smith, John, et al." in result
        assert '"A Sample Research Article on Cancer Treatment."' in result
        assert "*Journal of Cancer Research*" in result
        assert "vol. 25" in result
        assert "no. 3" in result
        assert "2023" in result
        assert "https://pubmed.ncbi.nlm.nih.gov/12345678/" in result

    def test_format_citation_chicago(self, sample_article):
        """Test Chicago citation formatting."""
        result = CitationFormatter.format_citation(sample_article, CitationFormat.CHICAGO)

        assert "Smith, John, et al." in result
        assert '"A Sample Research Article on Cancer Treatment."' in result
        assert "*Journal of Cancer Research*" in result
        assert "25, no. 3" in result
        assert "(2023)" in result
        assert "https://doi.org/10.1000/example.doi" in result

    def test_format_citation_vancouver(self, sample_article):
        """Test Vancouver citation formatting."""
        result = CitationFormatter.format_citation(sample_article, CitationFormat.VANCOUVER)

        assert "Smith J, Doe J, Johnson B." in result
        assert "A Sample Research Article on Cancer Treatment." in result
        assert "Journal of Cancer Research 2023;25(3)" in result
        assert "PMID: 12345678" in result

    def test_format_citation_bibtex(self, sample_article):
        """Test BibTeX citation formatting."""
        result = CitationFormatter.format_citation(sample_article, CitationFormat.BIBTEX)

        assert "@article{" in result
        assert "title = {A Sample Research Article on Cancer Treatment}" in result
        assert "author = {John Smith and Jane Doe and Bob Johnson}" in result
        assert "journal = {Journal of Cancer Research}" in result
        assert "volume = {25}" in result
        assert "number = {3}" in result
        assert "year = {2023}" in result
        assert "doi = {10.1000/example.doi}" in result
        assert "pmid = {12345678}" in result

    def test_format_citation_endnote(self, sample_article):
        """Test EndNote citation formatting."""
        result = CitationFormatter.format_citation(sample_article, CitationFormat.ENDNOTE)

        assert "%0 Journal Article" in result
        assert "%T A Sample Research Article on Cancer Treatment" in result
        assert "%A John Smith" in result
        assert "%A Jane Doe" in result
        assert "%A Bob Johnson" in result
        assert "%J Journal of Cancer Research" in result
        assert "%V 25" in result
        assert "%N 3" in result
        assert "%D 2023/03/15" in result
        assert "%R 10.1000/example.doi" in result
        assert "%M 12345678" in result

    def test_format_citation_ris(self, sample_article):
        """Test RIS citation formatting."""
        result = CitationFormatter.format_citation(sample_article, CitationFormat.RIS)

        assert "TY  - JOUR" in result
        assert "TI  - A Sample Research Article on Cancer Treatment" in result
        assert "AU  - John Smith" in result
        assert "AU  - Jane Doe" in result
        assert "AU  - Bob Johnson" in result
        assert "JO  - Journal of Cancer Research" in result
        assert "VL  - 25" in result
        assert "IS  - 3" in result
        assert "PY  - 2023" in result
        assert "DA  - 2023/03/15" in result
        assert "DO  - 10.1000/example.doi" in result
        assert "AN  - 12345678" in result
        assert "ER  - " in result

    def test_format_citation_unsupported_format(self, sample_article):
        """Test error handling for unsupported citation format."""
        with pytest.raises(ValueError, match="Unsupported citation format"):
            CitationFormatter.format_citation(sample_article, "invalid_format")

    def test_format_multiple_citations(self, sample_article, minimal_article):
        """Test formatting multiple citations."""
        articles = [sample_article, minimal_article]
        result = CitationFormatter.format_multiple_citations(articles, CitationFormat.APA)

        assert len(result) == 2
        assert "Smith, J., Doe, J., & Johnson, B." in result[0]
        assert "Minimal Article" in result[1]

    def test_clean_text(self):
        """Test text cleaning functionality."""
        dirty_text = "<p>Sample text with <b>HTML</b> tags   and   extra   spaces</p>"
        clean_text = CitationFormatter._clean_text(dirty_text)

        assert clean_text == "Sample text with HTML tags and extra spaces"
        assert "<" not in clean_text
        assert ">" not in clean_text

    def test_clean_text_empty(self):
        """Test text cleaning with empty input."""
        assert CitationFormatter._clean_text("") == ""
        assert CitationFormatter._clean_text(None) == ""

    def test_format_authors_apa_many_authors(self):
        """Test APA author formatting with many authors."""
        authors = [f"Author {i}" for i in range(25)]  # More than 20 authors
        result = CitationFormatter._format_authors_apa(authors)

        assert "... & Author 24" in result  # Should truncate and show last author

    def test_format_authors_apa_single_author(self):
        """Test APA author formatting with single author."""
        authors = ["John Smith"]
        result = CitationFormatter._format_authors_apa(authors)

        assert result == "Smith, J."

    def test_format_authors_apa_two_authors(self):
        """Test APA author formatting with two authors."""
        authors = ["John Smith", "Jane Doe"]
        result = CitationFormatter._format_authors_apa(authors)

        assert result == "Smith, J., & Doe, J."

    def test_format_authors_apa_empty(self):
        """Test APA author formatting with empty list."""
        result = CitationFormatter._format_authors_apa([])
        assert result == ""

    def test_minimal_article_formatting(self, minimal_article):
        """Test formatting with minimal article data."""
        result = CitationFormatter.format_citation(minimal_article, CitationFormat.APA)

        assert "Minimal Article" in result
        assert "Basic Journal" in result
        assert "https://pubmed.ncbi.nlm.nih.gov/87654321/" in result

    def test_article_without_doi_apa(self, minimal_article):
        """Test APA formatting when DOI is not available."""
        result = CitationFormatter.format_citation(minimal_article, CitationFormat.APA)

        assert "https://pubmed.ncbi.nlm.nih.gov/87654321/" in result
        assert "doi.org" not in result

    def test_article_without_doi_mla(self, minimal_article):
        """Test MLA formatting when DOI is not available."""
        result = CitationFormatter.format_citation(minimal_article, CitationFormat.MLA)

        assert "https://pubmed.ncbi.nlm.nih.gov/87654321/" in result

    def test_bibtex_citation_key_generation(self, sample_article):
        """Test BibTeX citation key generation."""
        result = CitationFormatter.format_citation(sample_article, CitationFormat.BIBTEX)

        # Should include author last name, year, and first word of title
        assert "@article{smith2023a," in result

    def test_ris_page_range_formatting(self):
        """Test RIS page range formatting."""
        article = Article(
            pmid="12345678",
            title="Test Article",
            journal=Journal(title="Test Journal", pages="123-456"),
        )

        result = CitationFormatter.format_citation(article, CitationFormat.RIS)

        assert "SP  - 123" in result
        assert "EP  - 456" in result

    def test_ris_single_page_formatting(self):
        """Test RIS single page formatting."""
        article = Article(
            pmid="12345678",
            title="Test Article",
            journal=Journal(title="Test Journal", pages="123"),
        )

        result = CitationFormatter.format_citation(article, CitationFormat.RIS)

        assert "SP  - 123" in result
        assert "EP  -" not in result

    def test_vancouver_author_limit(self):
        """Test Vancouver style author limiting to 6 authors."""
        authors = [
            Author(last_name=f"Author{i}", first_name=f"First{i}", initials=f"F{i}")
            for i in range(10)
        ]

        article = Article(
            pmid="12345678",
            title="Test Article",
            authors=authors,
            journal=Journal(title="Test Journal"),
        )

        result = CitationFormatter.format_citation(article, CitationFormat.VANCOUVER)

        assert "et al" in result
        # Should only show first 6 authors
        assert "Author5 F5" in result
        assert "Author6 F6" not in result

    def test_edge_case_empty_fields(self):
        """Test handling of articles with empty or None fields."""
        article = Article(
            pmid="12345678",
            title="",  # Empty title
            abstract=None,
            authors=[],  # No authors
            journal=Journal(title=""),  # Empty journal
            pub_date=None,
            doi=None,
        )

        # Should not crash with empty fields
        result = CitationFormatter.format_citation(article, CitationFormat.APA)
        assert isinstance(result, str)

    def test_special_characters_in_title(self):
        """Test handling of special characters in titles."""
        article = Article(
            pmid="12345678",
            title="Special Characters: α, β, γ & More!",
            journal=Journal(title="Test Journal"),
        )

        result = CitationFormatter.format_citation(article, CitationFormat.APA)
        assert "Special Characters: α, β, γ & More!" in result

    def test_long_author_names(self):
        """Test handling of very long author names."""
        article = Article(
            pmid="12345678",
            title="Test Article",
            authors=[
                Author(
                    last_name="VeryLongLastNameThatExceedsNormalLength",
                    first_name="ExtremelyLongFirstNameThatIsUnusuallyVerbose",
                    initials="E.L.",
                )
            ],
            journal=Journal(title="Test Journal"),
        )

        result = CitationFormatter.format_citation(article, CitationFormat.APA)
        assert "VeryLongLastNameThatExceedsNormalLength" in result
