"""
Quick fix script for datetime serialization issues.
Run: python fix_datetime_issue.py
"""
import re

def fix_save_json():
    """Fix _save_json method in daa_student_crawler.py"""
    
    filepath = "../src/crawler/daa_student_crawler.py"
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace json.dump with custom encoder
    old_code = '''json.dump(data, f, ensure_ascii=False, indent=2)'''
    
    new_code = '''# Custom datetime handler
            def datetime_handler(obj):
                from datetime import datetime
                if isinstance(obj, datetime):
                    return obj.isoformat()
                raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
            
            json.dump(data, f, ensure_ascii=False, indent=2, default=datetime_handler)'''
    
    content = content.replace(old_code, new_code)
    
    # Replace .dict() with .model_dump(mode='json')
    content = re.sub(
        r'(\w+)\.dict\(\)',
        r'\1.model_dump(mode="json")',
        content
    )
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Fixed _save_json method")
    print("✅ Replaced .dict() with .model_dump(mode='json')")

if __name__ == "__main__":
    fix_save_json()
    print("\n🎉 Fixes applied! Run test again:")
    print("python src/test_hybrid_crawler.py")