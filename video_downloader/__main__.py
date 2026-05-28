"""
Allow running as: python -m video_downloader
"""

from .cli import cli_entry

if __name__ == '__main__':
    cli_entry()
