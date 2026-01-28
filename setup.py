"""Setup script for COL."""

from setuptools import setup, find_packages

setup(
    name="col",
    version="0.1.0",
    description="A model-agnostic context engine for LLM orchestration",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Sid Valecha",
    url="https://github.com/sidvalecha/context-orchestrator",
    packages=find_packages(),
    install_requires=[
        "pydantic>=2.0.0",
        "typer>=0.9.0",
        "python-dotenv>=1.0.0",
        "openai>=1.0.0",
        "anthropic>=0.18.0",
        "groq>=0.4.0",
        "pyyaml>=6.0.0",
        "rich>=13.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "col=col.cli:main",
        ],
    },
    python_requires=">=3.10",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Typing :: Typed",
    ],
    keywords="llm context orchestration openai anthropic groq",
)
