"""Server-side draft archive. Filenames never come from user input."""
from datetime import datetime,timezone
from pathlib import Path
import json
import os
import re
import uuid

def storage_root(configured=''):
    configured=str(configured).strip()
    if os.name!='nt' and re.match(r'^[A-Za-z]:[\\/]',configured):
        return Path('ndmc_data').resolve(), 'Windows BASE_DIR cannot be used on this server; using ./ndmc_data.'
    default='C:/Tmp/Monthly_Plan' if os.name=='nt' else './ndmc_data'
    return Path(configured or default).expanduser().resolve(), ''

def save_draft(draft,root):
    root.mkdir(parents=True,exist_ok=True)
    name=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'_'+uuid.uuid4().hex+'.json'
    target=root/name
    # Exclusive creation avoids overwriting another sub-stream's submission.
    fd=os.open(target,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    with os.fdopen(fd,'w',encoding='utf-8') as f:
        json.dump(draft,f,indent=2,ensure_ascii=False,allow_nan=False)
    return name

def archived_files(root):
    if not root.exists():return []
    return sorted((p for p in root.glob('*.json') if p.is_file() and not p.is_symlink()),reverse=True)
