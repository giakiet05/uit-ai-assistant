#!/usr/bin/env python3
"""Test flatten_table_stage directly on file 547"""

import sys
from pathlib import Path
from dotenv import load_dotenv

# Add knowledge-builder src to path
kb_src = Path(__file__).parent / "apps" / "knowledge-builder" / "src"
sys.path.insert(0, str(kb_src))

# Load env
env_path = Path(__file__).parent / "apps" / "knowledge-builder" / ".env"
load_dotenv(env_path)

from pipeline.stages.flatten_table_stage import FlattenTableStage
from pipeline.core.pipeline_state import PipelineState

# File paths
input_file = Path("data/stages/regulation/790-qd-dhcntt_28-9-22_quy_che_dao_tao/05-fixed.md")
output_file = Path("data/stages/regulation/790-qd-dhcntt_28-9-22_quy_che_dao_tao/06-flattened.md")

print(f"Input: {input_file}")
print(f"Output: {output_file}")
print(f"Output exists: {output_file.exists()}")

# Create stage
print("\nCreating FlattenTableStage with 30min timeout...")
stage = FlattenTableStage()

# Create state with required params
state = PipelineState(document_id="790", category="regulation")

# Run
print("\nRunning stage (this may take several minutes)...")
result = stage.execute(
    input_path=input_file,
    output_path=output_file,
    state=state
)

print(f"\nResult: {result}")
print(f"Output exists now: {output_file.exists()}")

if output_file.exists():
    content = output_file.read_text()
    table_count = content.count("<table>")
    print(f"Tables in output: {table_count}")
    if table_count == 0:
        print("✅ SUCCESS! All tables flattened!")
    else:
        print(f"❌ FAILED! Still has {table_count} tables")
