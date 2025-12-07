"""Setup configuration for Aequitas CLI."""

from setuptools import setup, find_packages

setup(
    name="aequitas-cli",
    version="1.0.0",
    description="Command-line interface for Aequitas accounting system",
    author="Aequitas Team",
    packages=find_packages(),
    install_requires=[
        "typer[all]==0.9.0",
        "rich==13.7.0",
    ],
    entry_points={
        "console_scripts": [
            "aequitas=cli.main:app",
        ],
    },
    python_requires=">=3.11",
)
