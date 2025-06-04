"""
PubMed MCP Server

A comprehensive Model Context Protocol server for PubMed literature search and management.
"""

__version__ = "1.0.0"
__author__ = "Chris Mannina"

from .models import *
from .pubmed_client import PubMedClient
from .server import PubMedMCPServer

__all__ = [
    "PubMedMCPServer",
    "PubMedClient",
]
