#!/usr/bin/env python3
"""Verify byte-level integrity of the published source, raw data and figures."""
import hashlib
import sys
from pathlib import Path
R=Path(__file__).resolve().parent
manifest=R/'MANIFEST_SHA256.txt'
if not manifest.is_file():raise SystemExit('Missing MANIFEST_SHA256.txt')
bad=[];count=0
for line in manifest.read_text(encoding='utf-8').splitlines():
 if not line.strip():continue
 h,path=line.split('  ',1)
 file=(R/path).resolve()
 if not file.is_relative_to(R.resolve()) or not file.is_file() or hashlib.sha256(file.read_bytes()).hexdigest()!=h:bad.append(path)
 count+=1
if bad:
 print('REPOSITORY_INTEGRITY_FAILED',len(bad),'of',count);print(*bad[:40],sep='\n');sys.exit(1)
print('REPOSITORY_INTEGRITY_OK',count,'files')
