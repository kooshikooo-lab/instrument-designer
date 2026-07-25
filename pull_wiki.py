#!/usr/bin/env python3
"""
Pull wiki from GitHub and sync to local directory.
Usage: python pull_wiki.py
"""
import subprocess
import os
import sys

WIKI_REPO = "https://github.com/kooshikooo-lab/instrument-designer.wiki.git"
WIKI_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "wiki-local")

def pull_wiki():
    if os.path.exists(os.path.join(WIKI_DIR, ".git")):
        print("Wiki repo exists, pulling latest...")
        result = subprocess.run(["git", "pull"], cwd=WIKI_DIR, capture_output=True, text=True)
        print(result.stdout)
        if result.returncode != 0:
            print(f"Error: {result.stderr}")
    else:
        print("Cloning wiki repo...")
        result = subprocess.run(["git", "clone", WIKI_REPO, WIKI_DIR], capture_output=True, text=True)
        print(result.stdout)
        if result.returncode != 0:
            print(f"Error: {result.stderr}")
            print("\nWiki may not exist yet on GitHub. Using local WIKI.md instead.")
            local_wiki = os.path.join(os.path.dirname(os.path.abspath(__file__)), "WIKI.md")
            if os.path.exists(local_wiki):
                print(f"Local WIKI.md found at: {local_wiki}")
                return local_wiki
            return None
    
    # List wiki pages
    if os.path.exists(WIKI_DIR):
        pages = [f for f in os.listdir(WIKI_DIR) if f.endswith(".md")]
        print(f"\nWiki pages ({len(pages)}):")
        for p in sorted(pages):
            print(f"  - {p}")
        return WIKI_DIR
    return None

if __name__ == "__main__":
    result = pull_wiki()
    if result:
        print(f"\nWiki available at: {result}")
