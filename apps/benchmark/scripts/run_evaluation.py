"""
Run RAG evaluation using Ragas.

This script:
1. Loads test set (question + ground_truth)
2. Calls RAG API to get answers for each question
3. Evaluates using Ragas metrics (answer correctness, similarity, relevancy)
4. Saves results to JSON
"""

import json
import os
import threading
from pathlib import Path
from datetime import datetime
from typing import Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from datasets import Dataset
from dotenv import load_dotenv
from ragas import evaluate
from ragas.metrics import answer_correctness, answer_similarity, answer_relevancy
from ragas.run_config import RunConfig
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI


load_dotenv()

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8080")
CHAT_ENDPOINT = f"{API_BASE_URL}/api/v1/chat"
LOGIN_ENDPOINT = f"{API_BASE_URL}/api/v1/auth/local/login"
REFRESH_ENDPOINT = f"{API_BASE_URL}/api/v1/auth/refresh"

LOGIN_EMAIL = os.getenv("LOGIN_EMAIL", "")
LOGIN_PASSWORD = os.getenv("LOGIN_PASSWORD", "")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
RAGAS_MODEL = os.getenv("RAGAS_MODEL", "gpt-4.1-mini")

# Parallel processing config
MAX_WORKERS = int(os.getenv("MAX_WORKERS", "10"))  # Number of concurrent requests


class TokenManager:
    """
    Manages authentication tokens with auto-refresh.

    Features:
    - Auto login on initialization
    - Background thread to refresh token every 50 minutes
    - Thread-safe token access
    """

    def __init__(self):
        self.access_token = None
        self.refresh_token = None
        self.lock = threading.Lock()
        self.refresh_thread = None
        self.stop_refresh = threading.Event()

        # Login on initialization
        self.login()

        # Start auto-refresh thread
        self.start_auto_refresh()

    def login(self) -> bool:
        """Login and get access_token + refresh_token."""
        if not LOGIN_EMAIL or not LOGIN_PASSWORD:
            print("[WARNING] LOGIN_EMAIL or LOGIN_PASSWORD not set in .env")
            print("[WARNING] Token auto-refresh disabled")
            return False

        try:
            response = requests.post(
                LOGIN_ENDPOINT,
                json={
                    "identifier": LOGIN_EMAIL,
                    "password": LOGIN_PASSWORD
                },
                timeout=30
            )
            response.raise_for_status()

            data = response.json()

            if data.get("success") and "data" in data:
                with self.lock:
                    self.access_token = data["data"]["access_token"]
                    self.refresh_token = data["data"]["refresh_token"]

                print(f"[INFO] Login successful - Token acquired")
                return True
            else:
                print(f"[ERROR] Login failed: {data.get('message', 'Unknown error')}")
                return False

        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Login request failed: {e}")
            return False

    def refresh(self) -> bool:
        """Refresh access_token using refresh_token."""
        if not self.refresh_token:
            print("[WARNING] No refresh_token available, attempting login...")
            return self.login()

        try:
            response = requests.post(
                REFRESH_ENDPOINT,
                json={
                    "refresh_token": self.refresh_token
                },
                timeout=30
            )
            response.raise_for_status()

            data = response.json()

            if data.get("success") and "data" in data:
                with self.lock:
                    self.access_token = data["data"]["access_token"]
                    # Some APIs also return new refresh_token
                    if "refresh_token" in data["data"]:
                        self.refresh_token = data["data"]["refresh_token"]

                print(f"[INFO] Token refreshed successfully")
                return True
            else:
                print(f"[ERROR] Token refresh failed: {data.get('message', 'Unknown error')}")
                # Try login again
                return self.login()

        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Token refresh request failed: {e}")
            # Try login again
            return self.login()

    def get_token(self) -> Optional[str]:
        """Get current access_token (thread-safe)."""
        with self.lock:
            return self.access_token

    def start_auto_refresh(self):
        """Start background thread to auto-refresh token every 50 minutes."""
        if not LOGIN_EMAIL or not LOGIN_PASSWORD:
            return

        def refresh_loop():
            while not self.stop_refresh.is_set():
                # Wait 50 minutes (3000 seconds) before refresh
                # Access token expires after 1 hour, so 50 min is safe
                if self.stop_refresh.wait(timeout=3000):
                    break

                print(f"\n[INFO] Auto-refreshing token (every 50 minutes)...")
                self.refresh()

        self.refresh_thread = threading.Thread(target=refresh_loop, daemon=True)
        self.refresh_thread.start()
        print(f"[INFO] Auto-refresh enabled (every 50 minutes)")

    def stop_auto_refresh(self):
        """Stop auto-refresh thread."""
        if self.refresh_thread:
            self.stop_refresh.set()
            self.refresh_thread.join(timeout=5)
            print(f"[INFO] Auto-refresh stopped")


# Global token manager instance
token_manager = None


def load_test_set(test_set_path: Path) -> list[dict]:
    """Load test set from JSON file."""
    print(f"Loading test set from {test_set_path}")

    with open(test_set_path, 'r', encoding='utf-8') as f:
        test_set = json.load(f)

    print(f"Loaded {len(test_set)} questions")
    return test_set


def call_rag_api(question: str, session_id: Optional[str] = None) -> str:
    """
    Call RAG API to get answer for a question.

    Args:
        question: Question to ask
        session_id: Optional session ID for multi-turn conversation

    Returns:
        Answer from RAG system
    """
    global token_manager

    payload = {
        "message": question,
    }

    if session_id:
        payload["session_id"] = session_id

    headers = {"Content-Type": "application/json"}

    # Get token from TokenManager (auto-refreshed)
    if token_manager:
        access_token = token_manager.get_token()
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"

    try:
        response = requests.post(
            CHAT_ENDPOINT,
            json=payload,
            headers=headers,
            timeout=300
        )
        response.raise_for_status()

        data = response.json()

        # Extract answer from response
        # API format: {"data": {"message": {"content": "answer"}}}
        if "data" in data and "message" in data["data"]:
            answer = data["data"]["message"].get("content", "")
        else:
            # Fallback to old format
            answer = data.get("response", data.get("answer", ""))

        return answer

    except requests.exceptions.RequestException as e:
        print(f"Error calling RAG API: {e}")
        return f"[ERROR: {str(e)}]"


def generate_answers(test_set: list[dict]) -> list[dict]:
    """
    Generate answers for all questions in test set by calling RAG API in parallel.

    Uses ThreadPoolExecutor to send multiple requests concurrently.

    Returns:
        Test set with answers added
    """
    print(f"\nGenerating answers for {len(test_set)} questions...")
    print(f"API endpoint: {CHAT_ENDPOINT}")
    print(f"Parallel workers: {MAX_WORKERS}")
    print(f"Expected speedup: ~{MAX_WORKERS}x faster\n")

    def generate_answer_for_item(item_with_index):
        """Helper function to generate answer for single item (for parallel execution)."""
        idx, item = item_with_index
        question = item['question']
        answer = call_rag_api(question)
        return idx, answer

    # Use ThreadPoolExecutor for parallel processing
    completed_count = 0
    total = len(test_set)

    # Create list of (index, item) tuples
    items_with_index = list(enumerate(test_set))

    # Dictionary to store results by index (to maintain order)
    answers_dict = {}

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # Submit all tasks
        future_to_idx = {
            executor.submit(generate_answer_for_item, item): item[0]
            for item in items_with_index
        }

        # Process completed futures as they finish
        for future in as_completed(future_to_idx):
            idx, answer = future.result()
            answers_dict[idx] = answer

            completed_count += 1
            print(f"[{completed_count}/{total}] Completed question #{idx + 1}")

    # Add answers to test_set in original order
    for idx, item in enumerate(test_set):
        item['answer'] = answers_dict[idx]

    print(f"\nAll answers generated!")
    return test_set


def prepare_ragas_dataset(test_set: list[dict]) -> Dataset:
    """
    Prepare dataset in Ragas format.

    Ragas expects:
    - question: str
    - answer: str (generated by RAG)
    - ground_truth: str
    """
    print("\nPreparing Ragas dataset...")

    ragas_data = {
        "question": [item['question'] for item in test_set],
        "answer": [item['answer'] for item in test_set],
        "ground_truth": [item['ground_truth'] for item in test_set],
    }

    dataset = Dataset.from_dict(ragas_data)

    print(f"Dataset prepared with {len(dataset)} samples")
    return dataset


def get_ragas_llm():
    """
    Initialize LLM for Ragas evaluation.

    Priority:
    1. Use RAGAS_MODEL from .env (default: gemini-2.0-flash-exp)
    2. If starts with 'gpt-', use OpenAI
    3. Otherwise use Google Gemini
    """
    model_name = RAGAS_MODEL

    print(f"\nInitializing Ragas LLM judge: {model_name}")

    if model_name.startswith("gpt-"):
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not found in .env")

        llm = ChatOpenAI(
            model=model_name,
            api_key=OPENAI_API_KEY,
            temperature=0
        )
        print("Using OpenAI model")
    else:
        if not GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY not found in .env")

        llm = ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=GOOGLE_API_KEY,
            temperature=0
        )
        print("Using Google Gemini model")

    return llm


def run_evaluation(dataset: Dataset) -> dict:
    """
    Run Ragas evaluation.

    Metrics:
    - answer_correctness: Semantic + factual correctness vs ground_truth
    - answer_similarity: Cosine similarity between answer and ground_truth
    - answer_relevancy: Answer relevance to question
    """
    print("\nRunning Ragas evaluation...")
    print("Metrics:")
    print("  - answer_correctness: Semantic + factual correctness")
    print("  - answer_similarity: Cosine similarity with ground_truth")
    print("  - answer_relevancy: Relevance to question")

    llm = get_ragas_llm()

    metrics = [
        answer_correctness,
        answer_similarity,
        answer_relevancy,
    ]

    # Configure evaluation with higher timeout and retries to avoid TimeoutError
    run_config = RunConfig(
        timeout=300,       # 5 minutes per evaluation (default: 180s)
        max_retries=10,    # Max retry attempts (default: 10)
        max_wait=60,       # Max wait between retries in seconds (default: 60s)
        max_workers=16     # Parallel workers (default: 16)
    )

    result = evaluate(
        dataset,
        metrics=metrics,
        llm=llm,
        run_config=run_config,
        batch_size=10      # Process 10 samples concurrently
    )

    print("\nEvaluation completed!")
    return result


def save_results(test_set: list[dict], ragas_result, output_path: Path):
    """Save evaluation results to JSON."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        raw_scores = {
            "answer_correctness": ragas_result["answer_correctness"],
            "answer_similarity": ragas_result["answer_similarity"],
            "answer_relevancy": ragas_result["answer_relevancy"],
        }
    except (KeyError, TypeError):
        try:
            raw_scores = {
                "answer_correctness": ragas_result.get("answer_correctness", 0.0),
                "answer_similarity": ragas_result.get("answer_similarity", 0.0),
                "answer_relevancy": ragas_result.get("answer_relevancy", 0.0),
            }
        except:
            raw_scores = {
                "answer_correctness": 0.0,
                "answer_similarity": 0.0,
                "answer_relevancy": 0.0,
            }

    # Calculate average scores
    avg_scores = {}
    for metric, score in raw_scores.items():
        if isinstance(score, list):
            avg_scores[metric] = sum(score) / len(score) if score else 0.0
        else:
            avg_scores[metric] = float(score) if score else 0.0

    # Prepare individual scores for each question
    test_results = []
    for i, item in enumerate(test_set):
        result_item = {
            "id": item['id'],
            "question": item['question'],
            "ground_truth": item['ground_truth'],
            "answer": item['answer'],
            "scores": {},
            "metadata": item['metadata'],
        }

        # Add individual scores for this question
        for metric, scores_list in raw_scores.items():
            if isinstance(scores_list, list) and i < len(scores_list):
                result_item["scores"][metric] = float(scores_list[i])
            else:
                result_item["scores"][metric] = 0.0

        test_results.append(result_item)

    results = {
        "metadata": {
            "timestamp": datetime.now().isoformat(),
            "test_set_size": len(test_set),
            "api_endpoint": CHAT_ENDPOINT,
        },
        "average_scores": avg_scores,
        "test_results": test_results
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\nResults saved to {output_path}")


def print_summary(ragas_result):
    """Print evaluation summary."""
    print("\n" + "="*60)
    print("EVALUATION RESULTS")
    print("="*60)

    try:
        scores = {
            "Answer Correctness": ragas_result["answer_correctness"],
            "Answer Similarity": ragas_result["answer_similarity"],
            "Answer Relevancy": ragas_result["answer_relevancy"],
        }
    except (KeyError, TypeError):
        try:
            scores = {
                "Answer Correctness": ragas_result.get("answer_correctness", 0.0),
                "Answer Similarity": ragas_result.get("answer_similarity", 0.0),
                "Answer Relevancy": ragas_result.get("answer_relevancy", 0.0),
            }
        except:
            print("Warning: Could not extract scores from result")
            print(f"Result type: {type(ragas_result)}")
            print(f"Result: {ragas_result}")
            return

    for metric, score in scores.items():
        if isinstance(score, list):
            avg_score = sum(score) / len(score) if score else 0.0
            print(f"{metric:25s}: {avg_score:.4f}")
        else:
            print(f"{metric:25s}: {score:.4f}")

    print("="*60)


def main():
    global token_manager

    data_dir = Path(__file__).parent.parent / "data"
    results_dir = Path(__file__).parent.parent / "results"

    test_set_name = os.getenv("TEST_SET", "regulation_test_sample.json")
    test_set_path = data_dir / test_set_name

    print("="*60)
    print("RAG EVALUATION WITH RAGAS")
    print("="*60)
    print(f"Test set: {test_set_name}")
    print(f"API endpoint: {CHAT_ENDPOINT}")
    print("="*60)

    if not OPENAI_API_KEY and not GOOGLE_API_KEY:
        print("\nWARNING: No API keys found!")
        print("Set OPENAI_API_KEY or GOOGLE_API_KEY in .env file")
        print("Ragas needs LLM to evaluate answers")
        return

    # Initialize token manager (auto-login + auto-refresh)
    print("\n[INFO] Initializing authentication...")
    token_manager = TokenManager()

    if not token_manager.get_token():
        print("[WARNING] No access token available")
        print("[WARNING] Proceeding without authentication (might fail if API requires auth)")

    try:
        test_set = load_test_set(test_set_path)

        test_set_with_answers = generate_answers(test_set)

        dataset = prepare_ragas_dataset(test_set_with_answers)

        ragas_result = run_evaluation(dataset)

        print_summary(ragas_result)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"evaluation_{test_set_name.replace('.json', '')}_{timestamp}.json"
        output_path = results_dir / output_filename

        save_results(test_set_with_answers, ragas_result, output_path)

        print(f"\nDone! Check results at: {output_path}")

    finally:
        # Clean up token manager
        if token_manager:
            token_manager.stop_auto_refresh()


if __name__ == "__main__":
    main()
