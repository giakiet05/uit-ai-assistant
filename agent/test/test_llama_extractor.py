"""
Test script for LlamaParse extractor.
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project to path
sys.path.insert(0, os.path.dirname(__file__))

from processing.extractor.llama_extractor import LlamaExtractor


def test_llama_extractor():
    """Test LlamaParse extractor with a sample file."""
    
    print("=" * 60)
    print("TESTING LLAMAPARSE EXTRACTOR")
    print("=" * 60)
    
    # Check API key
    api_key = os.getenv('LLAMA_CLOUD_API_KEY')
    if not api_key or api_key == 'your-api-key-here':
        print("❌ FAILED: LLAMA_CLOUD_API_KEY not set")
        print("   Edit .env file and add your API key")
        return False
    
    print(f"✅ API Key found: {api_key[:10]}...")
    
    # Test with a file
    test_file = input("\nEnter path to test file (PDF/DOCX): ").strip()
    
    if not os.path.exists(test_file):
        print(f"❌ File not found: {test_file}")
        return False
    
    try:
        # Create extractor
        extractor = LlamaExtractor()
        print("\n✅ LlamaExtractor created successfully")
        
        # Extract content
        print(f"\n📄 Extracting: {test_file}...")
        markdown = extractor.extract(test_file)
        
        if markdown:
            print("\n" + "=" * 60)
            print("✅ EXTRACTION SUCCESSFUL!")
            print("=" * 60)
            print(f"\nContent length: {len(markdown)} characters")
            print("\nFirst 500 characters:")
            print("-" * 60)
            print(markdown[:500])
            print("-" * 60)
            
            # Save to file
            output_file = test_file + ".llama.md"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(markdown)
            print(f"\n✅ Saved to: {output_file}")
            return True
        else:
            print("\n❌ Extraction failed - no content returned")
            return False
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False


if __name__ == "__main__":
    success = test_llama_extractor()
    sys.exit(0 if success else 1)