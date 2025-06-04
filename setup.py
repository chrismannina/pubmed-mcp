"""
Setup configuration for PubMed MCP Server.
"""

from setuptools import find_packages, setup

# Read the requirements from requirements.txt
with open("requirements.txt", "r", encoding="utf-8") as f:
    requirements = [
        line.strip()
        for line in f
        if line.strip() and not line.startswith("#") and "pytest" not in line
    ]

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="pubmed-mcp-server",
    version="1.0.0",
    description="A comprehensive PubMed Model Context Protocol (MCP) server",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Agent Care Team",
    author_email="",
    url="https://github.com/your-org/pubmed-mcp",
    packages=find_packages(),
    install_requires=requirements,
    python_requires=">=3.10",
    entry_points={
        "console_scripts": [
            "pubmed-mcp=src.main:cli_main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Healthcare Industry",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Medical Science Apps.",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Operating System :: OS Independent",
    ],
    keywords="pubmed mcp medical literature search api",
    project_urls={
        "Bug Reports": "https://github.com/your-org/pubmed-mcp/issues",
        "Source": "https://github.com/your-org/pubmed-mcp",
        "Documentation": "https://github.com/your-org/pubmed-mcp#readme",
    },
)
