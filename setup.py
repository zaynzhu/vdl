"""
Setup script for video-downloader-skill.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

setup(
    name="video-downloader-skill",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A video downloader supporting Douyin, Bilibili, TikTok and more",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/video-downloader-skill",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "aiohttp>=3.9.0",
        "playwright>=1.40.0",
        "httpx>=0.25.0",
        "python-dateutil>=2.8.2",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.1.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.7.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "video-downloader=video_downloader.cli:cli_entry",
        ],
    },
)
