import json
from pathlib import Path

def merge_testsets():
    data_dir = Path("apps/benchmark/data/regulation")
    output_file = Path("apps/benchmark/data/regulation_full_test.json")
    
    all_questions = []
    stats = {}

    print(f"Scanning directory: {data_dir}")
    
    # Get all json files starting with 'group'
    files = sorted(list(data_dir.glob("group*.json")))
    
    if not files:
        print("No group files found!")
        return

    for file_path in files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                count = len(data)
                group_name = file_path.stem
                stats[group_name] = count
                all_questions.extend(data)
                print(f"Loaded {count} questions from {file_path.name}")
        except Exception as e:
            print(f"Error reading {file_path.name}: {e}")

    # Save merged file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_questions, f, ensure_ascii=False, indent=2)

    print("\n" + "="*40)
    print("MERGE COMPLETE")
    print("="*40)
    print(f"Total questions: {len(all_questions)}")
    print("Breakdown:")
    for group, count in stats.items():
        print(f"  - {group}: {count}")
    print(f"\nOutput saved to: {output_file}")

if __name__ == "__main__":
    merge_testsets()
