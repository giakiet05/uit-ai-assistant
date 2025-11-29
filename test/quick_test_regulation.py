import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from llama_index.core import Document
from src.indexing.splitters import SmartNodeSplitter
import json

file_path = 'data/processed/regulation/790-qd-dhcntt_28-9-22_quy_che_dao_tao.md'

# Read file
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Load metadata
metadata_path = Path(file_path).with_suffix('.json')
if metadata_path.exists():
    with open(metadata_path, 'r', encoding='utf-8') as f:
        metadata = json.load(f)
else:
    metadata = {'document_id': Path(file_path).stem, 'category': 'regulation'}

print('📋 Document Metadata:')
print(f'   Category: {metadata.get("category")}')
print(f'   Title: {metadata.get("title", "N/A")[:60]}...')

# Create parser
parser = SmartNodeSplitter(max_tokens=7000, enable_title_merging=True, enable_pattern_detection=True)

# Parse
doc = Document(text=content, metadata=metadata)
nodes = parser.get_nodes_from_documents([doc])

print(f'\n📊 Stats: {len(nodes)} nodes\n')

# Show first 5 chunks
for i, node in enumerate(nodes[:5], 1):
    header = node.metadata.get('current_header', 'N/A')
    level = node.metadata.get('header_level', 0)
    path = node.metadata.get('header_path', [])

    print(f'--- CHUNK #{i} ---')
    print(f'Header: {header}')
    print(f'Level: {level}')
    if path:
        full = path + ([header] if header and header != 'N/A' else [])
        print(f'Hierarchy: {" > ".join(full)}')
    print()
