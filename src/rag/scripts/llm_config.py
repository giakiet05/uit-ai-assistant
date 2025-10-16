"""
LLM configuration module
Handles setup for different LLM providers (Ollama, OpenAI)
"""

from llama_index.llms.ollama import Ollama
from llama_index.llms.openai import OpenAI
from llama_index.core import Settings as LlamaSettings
from config import Config

class LLMConfigurator:
    """Configure LLM based on provider settings"""
    
    def __init__(self):
        self.config = Config
        self.llm = None
        self._setup_llm()
    
    def _setup_llm(self):
        """Setup LLM based on configuration"""
        print("\n🤖 Setting up LLM...")
        
        if self.config.LLM_PROVIDER == "openai":
            self._setup_openai()
        elif self.config.LLM_PROVIDER == "ollama":
            self._setup_ollama()
        else:
            raise ValueError(f"Unsupported LLM provider: {self.config.LLM_PROVIDER}")
        
        # Set global LLM
        LlamaSettings.llm = self.llm
    
    def _setup_openai(self):
        """Setup OpenAI LLM"""
        if not self.config.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is required for OpenAI provider")
        
        self.llm = OpenAI(
            api_key=self.config.OPENAI_API_KEY,
            model=self.config.OPENAI_MODEL,
            temperature=self.config.TEMPERATURE
        )
        
        print(f"✓ OpenAI LLM configured: {self.config.OPENAI_MODEL}")
    
    def _setup_ollama(self):
        """Setup Ollama LLM"""
        self.llm = Ollama(
            model=self.config.OLLAMA_MODEL,
            base_url=self.config.OLLAMA_BASE_URL,
            temperature=0.1,
            request_timeout=300.0, # 5 minutes timeout
            system_prompt="Bạn là trợ lý AI giáo dục. Luôn trả lời bằng tiếng Việt."
        )
        
        print(f"✓ Ollama LLM configured: {self.config.OLLAMA_MODEL}")
        print(f"  Base URL: {self.config.OLLAMA_BASE_URL}")
        print(f"  Temperature: 0.1 (focused responses)")
        print(f"  Timeout: 300s")
        print(f"  Language: Vietnamese enforced")
        try:
            import requests
            response = requests.get(f"{self.config.OLLAMA_BASE_URL}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                model_names = [m['name'] for m in models]
                if self.config.OLLAMA_MODEL in model_names:
                    print(f"✓ Model '{self.config.OLLAMA_MODEL}' is available")
                else:
                    print(f"⚠ Warning: Model '{self.config.OLLAMA_MODEL}' not found")
                    print(f"  Available models: {', '.join(model_names)}")
                    print(f"  Run: ollama pull {self.config.OLLAMA_MODEL}")
            else:
                print(f"⚠ Warning: Cannot verify Ollama models")
        except Exception as e:
            print(f"⚠ Warning: Cannot connect to Ollama at {self.config.OLLAMA_BASE_URL}")
            print(f"  Error: {e}")
            print(f"  Make sure Ollama is running: ollama serve")
    
    def get_llm(self):
        """Get configured LLM instance"""
        return self.llm
    
    def test_connection(self) -> bool:
        """Test LLM connection"""
        try:
            print("\n🔍 Testing LLM connection...")
            response = self.llm.complete("Hello, this is a test.")
            print(f"✓ LLM connection successful")
            print(f"  Response: {response.text[:100]}...")
            return True
        except Exception as e:
            print(f"❌ LLM connection failed: {e}")
            return False

if __name__ == "__main__":
    # Test LLM configuration
    configurator = LLMConfigurator()
    configurator.test_connection()
