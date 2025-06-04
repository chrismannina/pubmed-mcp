"""
PubMed MCP Server

A comprehensive Model Context Protocol server for PubMed literature search and management.
"""

__version__ = "1.0.0"
__author__ = "Chris Mannina"

from .server import PubMedMCPServer
from .pubmed_client import PubMedClient
from .models import *

__all__ = [
    "PubMedMCPServer",
    "PubMedClient",
] 