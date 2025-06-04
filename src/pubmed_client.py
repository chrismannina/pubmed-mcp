import asyncio
import time
import re
import logging
from typing import Dict, Any, List, Optional, Union
from urllib.parse import urlencode, quote
from xml.etree import ElementTree as ET
from datetime import datetime, timedelta

import httpx
from bs4 import BeautifulSoup

# Handle both relative and absolute imports
try:
    from .models import (
        Article, Author, Journal, MeSHTerm, SearchResult, MCPResponse,
        SortOrder, DateRange, ArticleType, CitationFormat
    )
    from .utils import (
        CacheManager, RateLimiter, rate_limited, format_authors, format_date,
        truncate_text, format_mesh_terms, build_search_query, validate_pmid
    )
except ImportError:
    from models import (
        Article, Author, Journal, MeSHTerm, SearchResult, MCPResponse,
        SortOrder, DateRange, ArticleType, CitationFormat
    )
    from utils import (
        CacheManager, RateLimiter, rate_limited, format_authors, format_date,
        truncate_text, format_mesh_terms, build_search_query, validate_pmid
    )

logger = logging.getLogger(__name__)

class PubMedClient:
    """Comprehensive PubMed client with advanced search and citation features."""
    
    def __init__(self, api_key: str, email: str, rate_limit: float = 3.0):
        """
        Initialize PubMed client.
        
        Args:
            api_key: NCBI API key
            email: User email for NCBI
            rate_limit: Requests per second limit
        """
        self.api_key = api_key
        self.email = email
        self.base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
        self.rate_limiter = RateLimiter(rate_limit)
        
        # Initialize HTTP client with common headers
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                "User-Agent": f"PubMed-MCP-Server/1.0 ({email})"
            }
        )
    
    def _build_params(self, **kwargs) -> Dict[str, str]:
        """Build common API parameters."""
        params = {
            "api_key": self.api_key,
            "email": self.email,
            "tool": "pubmed-mcp-server"
        }
        params.update({k: v for k, v in kwargs.items() if v is not None})
        return params
    
    async def _make_request(self, endpoint: str, params: Dict[str, Any]) -> httpx.Response:
        """Make rate-limited API request."""
        await self.rate_limiter.acquire()  # Apply rate limiting directly
        url = f"{self.base_url}/{endpoint}"
        response = await self.client.get(url, params=params)
        response.raise_for_status()
        return response
    
    async def search_articles(
        self,
        query: str,
        max_results: int = 20,
        sort_order: SortOrder = SortOrder.RELEVANCE,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        date_range: Optional[DateRange] = None,
        article_types: Optional[List[ArticleType]] = None,
        authors: Optional[List[str]] = None,
        journals: Optional[List[str]] = None,
        mesh_terms: Optional[List[str]] = None,
        language: Optional[str] = None,
        has_abstract: Optional[bool] = None,
        has_full_text: Optional[bool] = None,
        humans_only: Optional[bool] = None,
        cache: Optional[CacheManager] = None
    ) -> SearchResult:
        """
        Search PubMed with advanced filtering.
        
        Args:
            query: Search query
            max_results: Maximum results to return
            sort_order: Sort order for results
            date_from: Start date filter
            date_to: End date filter
            date_range: Predefined date range
            article_types: Article type filters
            authors: Author filters
            journals: Journal filters
            mesh_terms: MeSH term filters
            language: Language filter
            has_abstract: Only articles with abstracts
            has_full_text: Only articles with full text
            humans_only: Only human studies
            cache: Cache manager instance
            
        Returns:
            SearchResult containing articles and metadata
        """
        start_time = time.time()
        
        # Check cache first
        if cache:
            cache_key = cache.generate_key(
                "search", query=query, max_results=max_results, sort_order=sort_order.value,
                date_from=date_from, date_to=date_to, date_range=date_range.value if date_range else None,
                article_types=[at.value for at in article_types] if article_types else None,
                authors=authors, journals=journals, mesh_terms=mesh_terms,
                language=language, has_abstract=has_abstract, has_full_text=has_full_text,
                humans_only=humans_only
            )
            cached_result = cache.get(cache_key)
            if cached_result:
                # Convert cached article dicts back to Article objects
                cached_articles = [Article(**article_data) for article_data in cached_result["articles"]]
                cached_result["articles"] = cached_articles
                return SearchResult(**cached_result)
        
        # Handle date range shortcuts
        if date_range and not (date_from or date_to):
            date_to = datetime.now().strftime("%Y/%m/%d")
            if date_range == DateRange.LAST_YEAR:
                date_from = (datetime.now() - timedelta(days=365)).strftime("%Y/%m/%d")
            elif date_range == DateRange.LAST_5_YEARS:
                date_from = (datetime.now() - timedelta(days=365*5)).strftime("%Y/%m/%d")
            elif date_range == DateRange.LAST_10_YEARS:
                date_from = (datetime.now() - timedelta(days=365*10)).strftime("%Y/%m/%d")
        
        # Build complex search query
        search_query = build_search_query(
            query, authors=authors, journals=journals, mesh_terms=mesh_terms,
            article_types=[at.value for at in article_types] if article_types else None,
            date_from=date_from, date_to=date_to, language=language,
            has_abstract=has_abstract, has_full_text=has_full_text, humans_only=humans_only
        )
        
        logger.info(f"Executing PubMed search: {search_query}")
        
        # Search for article IDs
        search_params = self._build_params(
            db="pubmed",
            term=search_query,
            retmax=str(max_results),
            retmode="json",
            sort=sort_order.value
        )
        
        search_response = await self._make_request("esearch.fcgi", search_params)
        search_data = search_response.json()
        
        search_result = search_data.get("esearchresult", {})
        pmids = search_result.get("idlist", [])
        total_results = int(search_result.get("count", 0))
        
        # Get detailed article information
        articles = []
        if pmids:
            articles = await self._fetch_article_details(pmids, include_full_details=True)
        
        # Build result
        result_data = {
            "query": query,
            "total_results": total_results,
            "returned_results": len(articles),
            "articles": articles,  # Store Article objects directly
            "search_time": time.time() - start_time,
            "suggestions": []  # Could implement spelling suggestions
        }
        
        # Cache the result (store as dicts for serialization)
        if cache:
            cache_data = {
                **result_data,
                "articles": [article.model_dump() for article in articles]
            }
            cache.set(cache_key, cache_data)
        
        return SearchResult(**result_data)
    
    async def get_article_details(
        self,
        pmids: List[str],
        include_abstracts: bool = True,
        include_citations: bool = False,
        cache: Optional[CacheManager] = None
    ) -> List[Article]:
        """
        Get detailed article information for specific PMIDs.
        
        Args:
            pmids: List of PubMed IDs
            include_abstracts: Include abstracts
            include_citations: Include citation metrics
            cache: Cache manager instance
            
        Returns:
            List of Article objects
        """
        # Validate PMIDs
        valid_pmids = [pmid for pmid in pmids if validate_pmid(pmid)]
        if len(valid_pmids) != len(pmids):
            logger.warning(f"Some invalid PMIDs provided: {set(pmids) - set(valid_pmids)}")
        
        if not valid_pmids:
            return []
        
        # Check cache
        if cache:
            cache_key = cache.generate_key(
                "article_details", pmids=valid_pmids, 
                include_abstracts=include_abstracts, include_citations=include_citations
            )
            cached_result = cache.get(cache_key)
            if cached_result:
                return [Article(**article) for article in cached_result]
        
        articles = await self._fetch_article_details(
            valid_pmids, include_full_details=True, include_citations=include_citations
        )
        
        # Cache the result
        if cache:
            cache.set(cache_key, [article.model_dump() for article in articles])
        
        return articles
    
    async def search_by_author(
        self,
        author_name: str,
        max_results: int = 20,
        include_coauthors: bool = True,
        cache: Optional[CacheManager] = None
    ) -> SearchResult:
        """Search articles by author name."""
        start_time = time.time()
        
        if cache:
            cache_key = cache.generate_key(
                "author_search", author=author_name, max_results=max_results,
                include_coauthors=include_coauthors
            )
            cached_result = cache.get(cache_key)
            if cached_result:
                # Convert cached article dicts back to Article objects
                cached_articles = [Article(**article_data) for article_data in cached_result["articles"]]
                cached_result["articles"] = cached_articles
                return SearchResult(**cached_result)
        
        # Build author search query
        search_query = f'"{author_name}"[Author]'
        
        search_params = self._build_params(
            db="pubmed",
            term=search_query,
            retmax=str(max_results),
            retmode="json",
            sort="pub_date"
        )
        
        search_response = await self._make_request("esearch.fcgi", search_params)
        search_data = search_response.json()
        
        search_result = search_data.get("esearchresult", {})
        pmids = search_result.get("idlist", [])
        total_results = int(search_result.get("count", 0))
        
        articles = []
        if pmids:
            articles = await self._fetch_article_details(pmids, include_full_details=True)
        
        result_data = {
            "query": f"Author: {author_name}",
            "total_results": total_results,
            "returned_results": len(articles),
            "articles": articles,  # Store Article objects directly
            "search_time": time.time() - start_time,
            "suggestions": []
        }
        
        # Cache the result (store as dicts for serialization)
        if cache:
            cache_data = {
                **result_data,
                "articles": [article.model_dump() for article in articles]
            }
            cache.set(cache_key, cache_data)
        
        return SearchResult(**result_data)
    
    async def find_related_articles(
        self,
        pmid: str,
        max_results: int = 10,
        cache: Optional[CacheManager] = None
    ) -> SearchResult:
        """Find articles related to a specific PMID."""
        start_time = time.time()
        
        if not validate_pmid(pmid):
            raise ValueError(f"Invalid PMID: {pmid}")
        
        if cache:
            cache_key = cache.generate_key("related", pmid=pmid, max_results=max_results)
            cached_result = cache.get(cache_key)
            if cached_result:
                # Convert cached article dicts back to Article objects
                cached_articles = [Article(**article_data) for article_data in cached_result["articles"]]
                cached_result["articles"] = cached_articles
                return SearchResult(**cached_result)
        
        # Use elink to find related articles
        link_params = self._build_params(
            dbfrom="pubmed",
            db="pubmed",
            id=pmid,
            retmode="json",
            linkname="pubmed_pubmed"
        )
        
        link_response = await self._make_request("elink.fcgi", link_params)
        link_data = link_response.json()
        
        related_pmids = []
        linksets = link_data.get("linksets", [])
        if linksets and "linksetdbs" in linksets[0]:
            for linksetdb in linksets[0]["linksetdbs"]:
                if linksetdb.get("linkname") == "pubmed_pubmed":
                    related_pmids = linksetdb.get("links", [])[:max_results]
                    break
        
        articles = []
        if related_pmids:
            articles = await self._fetch_article_details(related_pmids, include_full_details=True)
        
        result_data = {
            "query": f"Related to PMID: {pmid}",
            "total_results": len(related_pmids),
            "returned_results": len(articles),
            "articles": articles,  # Store Article objects directly
            "search_time": time.time() - start_time,
            "suggestions": []
        }
        
        if cache:
            cache_data = {
                **result_data,
                "articles": [article.model_dump() for article in articles]
            }
            cache.set(cache_key, cache_data)
        
        return SearchResult(**result_data)
    
    async def _fetch_article_details(
        self,
        pmids: List[str],
        include_full_details: bool = True,
        include_citations: bool = False
    ) -> List[Article]:
        """Fetch detailed article information using efetch."""
        if not pmids:
            return []
        
        fetch_params = self._build_params(
            db="pubmed",
            id=",".join(pmids),
            retmode="xml"
        )
        
        fetch_response = await self._make_request("efetch.fcgi", fetch_params)
        xml_content = fetch_response.text
        
        return self._parse_pubmed_xml(xml_content, include_citations)
    
    def _parse_pubmed_xml(self, xml_content: str, include_citations: bool = False) -> List[Article]:
        """Parse PubMed XML response into Article objects."""
        articles = []
        
        try:
            root = ET.fromstring(xml_content)
            
            for article_elem in root.findall(".//PubmedArticle"):
                try:
                    article = self._parse_single_article(article_elem, include_citations)
                    if article:
                        articles.append(article)
                except Exception as e:
                    logger.error(f"Error parsing article: {e}")
                    continue
                    
        except ET.ParseError as e:
            logger.error(f"Error parsing XML: {e}")
        
        return articles
    
    def _parse_single_article(self, article_elem: ET.Element, include_citations: bool = False) -> Optional[Article]:
        """Parse a single article from XML."""
        try:
            # Get PMID
            pmid_elem = article_elem.find(".//PMID")
            if pmid_elem is None:
                return None
            pmid = pmid_elem.text
            
            # Get basic article info
            article_elem_inner = article_elem.find(".//Article")
            if article_elem_inner is None:
                return None
            
            # Title
            title_elem = article_elem_inner.find(".//ArticleTitle")
            title = title_elem.text if title_elem is not None else "No title"
            
            # Abstract
            abstract_parts = []
            for abstract_elem in article_elem_inner.findall(".//AbstractText"):
                label = abstract_elem.get("Label", "")
                text = abstract_elem.text or ""
                if label:
                    abstract_parts.append(f"{label}: {text}")
                else:
                    abstract_parts.append(text)
            abstract = " ".join(abstract_parts) if abstract_parts else None
            
            # Authors
            authors = []
            author_list = article_elem_inner.find(".//AuthorList")
            if author_list is not None:
                for author_elem in author_list.findall(".//Author"):
                    last_name_elem = author_elem.find(".//LastName")
                    first_name_elem = author_elem.find(".//ForeName")
                    initials_elem = author_elem.find(".//Initials")
                    
                    # Get affiliation
                    affiliation = None
                    affiliation_elem = author_elem.find(".//AffiliationInfo/Affiliation")
                    if affiliation_elem is not None:
                        affiliation = affiliation_elem.text
                    
                    if last_name_elem is not None:
                        author = Author(
                            last_name=last_name_elem.text,
                            first_name=first_name_elem.text if first_name_elem is not None else None,
                            initials=initials_elem.text if initials_elem is not None else None,
                            affiliation=affiliation
                        )
                        authors.append(author)
            
            # Journal information
            journal_elem = article_elem_inner.find(".//Journal")
            journal_title = "Unknown Journal"
            journal_iso = None
            journal_issn = None
            volume = None
            issue = None
            pub_date = None
            
            if journal_elem is not None:
                title_elem = journal_elem.find(".//Title")
                if title_elem is not None:
                    journal_title = title_elem.text
                
                iso_elem = journal_elem.find(".//ISOAbbreviation")
                if iso_elem is not None:
                    journal_iso = iso_elem.text
                
                issn_elem = journal_elem.find(".//ISSN")
                if issn_elem is not None:
                    journal_issn = issn_elem.text
                
                # Volume and issue
                issue_elem = journal_elem.find(".//JournalIssue")
                if issue_elem is not None:
                    volume_elem = issue_elem.find(".//Volume")
                    if volume_elem is not None:
                        volume = volume_elem.text
                    
                    issue_num_elem = issue_elem.find(".//Issue")
                    if issue_num_elem is not None:
                        issue = issue_num_elem.text
                    
                    # Publication date
                    pub_date_elem = issue_elem.find(".//PubDate")
                    if pub_date_elem is not None:
                        year_elem = pub_date_elem.find(".//Year")
                        month_elem = pub_date_elem.find(".//Month")
                        day_elem = pub_date_elem.find(".//Day")
                        
                        date_parts = []
                        if year_elem is not None:
                            date_parts.append(year_elem.text)
                        if month_elem is not None:
                            date_parts.append(month_elem.text)
                        if day_elem is not None:
                            date_parts.append(day_elem.text)
                        
                        pub_date = "/".join(date_parts) if date_parts else None
            
            journal = Journal(
                title=journal_title,
                iso_abbreviation=journal_iso,
                issn=journal_issn,
                volume=volume,
                issue=issue,
                pub_date=pub_date
            )
            
            # DOI
            doi = None
            doi_elem = article_elem.find(".//ELocationID[@EIdType='doi']")
            if doi_elem is not None:
                doi = doi_elem.text
            
            # PMC ID
            pmc_id = None
            pmc_elem = article_elem.find(".//ELocationID[@EIdType='pmc']")
            if pmc_elem is not None:
                pmc_id = pmc_elem.text
            
            # Article types
            article_types = []
            pub_type_list = article_elem.find(".//PublicationTypeList")
            if pub_type_list is not None:
                for pub_type in pub_type_list.findall(".//PublicationType"):
                    if pub_type.text:
                        article_types.append(pub_type.text)
            
            # MeSH terms
            mesh_terms = []
            mesh_list = article_elem.find(".//MeshHeadingList")
            if mesh_list is not None:
                for mesh_heading in mesh_list.findall(".//MeshHeading"):
                    descriptor_elem = mesh_heading.find(".//DescriptorName")
                    if descriptor_elem is not None:
                        mesh_term = MeSHTerm(
                            descriptor_name=descriptor_elem.text,
                            major_topic=descriptor_elem.get("MajorTopicYN", "N") == "Y",
                            ui=descriptor_elem.get("UI")
                        )
                        mesh_terms.append(mesh_term)
            
            # Keywords
            keywords = []
            keyword_list = article_elem.find(".//KeywordList")
            if keyword_list is not None:
                for keyword in keyword_list.findall(".//Keyword"):
                    if keyword.text:
                        keywords.append(keyword.text)
            
            # Languages
            languages = []
            language_list = article_elem.find(".//LanguageList")
            if language_list is not None:
                for language in language_list.findall(".//Language"):
                    if language.text:
                        languages.append(language.text)
            
            return Article(
                pmid=pmid,
                title=title,
                abstract=abstract,
                authors=authors,
                journal=journal,
                pub_date=pub_date,
                doi=doi,
                pmc_id=pmc_id,
                article_types=article_types,
                mesh_terms=mesh_terms,
                keywords=keywords,
                languages=languages,
                citation_count=None,  # Would require additional API calls
                full_text_urls=[],
                pdf_urls=[],
                grant_info=[],
                conflict_of_interest=None
            )
            
        except Exception as e:
            logger.error(f"Error parsing single article: {e}")
            return None
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose() 