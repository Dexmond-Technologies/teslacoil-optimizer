#!/usr/bin/env python3
"""
Consensus Engine: Multi-Agent Parallel AI Consensus Mechanism
Queries Grok (xAI), Claude (Anthropic), and Gemini (Google) in parallel,
and implements a meta-reasoning moderator to synthesize a unified consensus.
"""

import asyncio
import os
import sys
import logging
from typing import Dict, Optional, Tuple, List
from pathlib import Path

import httpx
from dotenv import load_dotenv

# Define terminal ANSI colors
class Colors:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format=f"{Colors.OKBLUE}[%(asctime)s]{Colors.ENDC} %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("ConsensusEngine")

# Load environment variables
# Look in the current directory and also the root directory of the workspace
env_paths = [Path(__file__).parent / ".env", Path(__file__).parents[2] / ".env"]
loaded = False
for path in env_paths:
    if path.exists():
        load_dotenv(dotenv_path=path)
        logger.info(f"Loaded environment variables from: {path.resolve()}")
        loaded = True
        break

if not loaded:
    load_dotenv()
    logger.warning("No explicit .env file found; loaded defaults from environment.")

# Helper to retrieve API keys supporting multiple naming formats
def get_api_key(primary: str, fallback_aliases: List[str]) -> Optional[str]:
    key = os.getenv(primary)
    if key:
        return key.strip("\"'")
    for alias in fallback_aliases:
        key = os.getenv(alias)
        if key:
            return key.strip("\"'")
    return None

# Resolve keys
GROK_KEY = get_api_key("GROK_API_KEY", ["GROK-API", "XAI_API_KEY"])
CLAUDE_KEY = get_api_key("CLAUDE_API_KEY", ["CLAUDE_API", "ANTHROPIC_API_KEY"])
GEMINI_KEY = get_api_key("GEMINI_API_KEY", ["GEMINI_API", "GOOGLE_API_KEY"])

# Model Definitions with fallback environment overrides
GROK_MODEL = os.getenv("GROK_MODEL", "grok-2-latest")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-20241022")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

# Setup headers and endpoints
TIMEOUT = 45.0  # 45-second timeout for deep reasoning/generation calls

class ConsensusEngine:
    def __init__(self):
        self.grok_key = GROK_KEY
        self.claude_key = CLAUDE_KEY
        self.gemini_key = GEMINI_KEY

        # Report configuration status
        logger.info(f"xAI Grok Configured: {self.grok_key is not None}")
        logger.info(f"Anthropic Claude Configured: {self.claude_key is not None}")
        logger.info(f"Google Gemini Configured: {self.gemini_key is not None}")

    async def query_grok(self, client: httpx.AsyncClient, prompt: str) -> str:
        """Query the xAI Grok API asynchronously."""
        if not self.grok_key:
            return "Error: Grok API Key is not configured."
        
        url = "https://api.x.ai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.grok_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": GROK_MODEL,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2
        }
        
        try:
            response = await client.post(url, headers=headers, json=data, timeout=TIMEOUT)
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"].strip()
            else:
                return f"Grok API Error (HTTP {response.status_code}): {response.text}"
        except httpx.TimeoutException:
            return "Error: Grok query timed out."
        except Exception as e:
            return f"Error contacting Grok: {str(e)}"

    async def query_claude(self, client: httpx.AsyncClient, prompt: str) -> str:
        """Query the Anthropic Claude API asynchronously."""
        if not self.claude_key:
            return "Error: Claude API Key is not configured."
        
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": self.claude_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        data = {
            "model": CLAUDE_MODEL,
            "max_tokens": 1500,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2
        }
        
        try:
            response = await client.post(url, headers=headers, json=data, timeout=TIMEOUT)
            if response.status_code == 200:
                return response.json()["content"][0]["text"].strip()
            else:
                return f"Claude API Error (HTTP {response.status_code}): {response.text}"
        except httpx.TimeoutException:
            return "Error: Claude query timed out."
        except Exception as e:
            return f"Error contacting Claude: {str(e)}"

    async def query_gemini(self, client: httpx.AsyncClient, prompt: str) -> str:
        """Query the Google Gemini API asynchronously."""
        if not self.gemini_key:
            return "Error: Gemini API Key is not configured."
        
        # Google Generative Language REST API endpoint
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={self.gemini_key}"
        headers = {
            "Content-Type": "application/json"
        }
        data = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt}
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.2
            }
        }
        
        try:
            response = await client.post(url, headers=headers, json=data, timeout=TIMEOUT)
            if response.status_code == 200:
                candidates = response.json().get("candidates", [])
                if candidates:
                    return candidates[0]["content"]["parts"][0]["text"].strip()
                else:
                    return f"Gemini response has no candidates: {response.text}"
            else:
                return f"Gemini API Error (HTTP {response.status_code}): {response.text}"
        except httpx.TimeoutException:
            return "Error: Gemini query timed out."
        except Exception as e:
            return f"Error contacting Gemini: {str(e)}"

    async def run_consensus_moderator(
        self, client: httpx.AsyncClient, query: str, responses: Dict[str, str]
    ) -> str:
        """
        Takes the constituent model outputs and feeds them into a moderator
        to synthesize points of agreement, disagreement, and a unified final consensus.
        """
        # Formulate moderator prompt
        moderator_prompt = f"""You are a master scientific synthesizer, impartial moderator, and cognitive arbiter. 
Your task is to critically analyze three responses from different AI models (Grok, Claude, and Gemini) responding to the same user query, and produce a balanced, accurate, and high-quality final consensus answer.

### Original User Query:
{query}

### AI Responses to Analyze:
1. **Grok Response**:
{responses.get('Grok', 'Error or No Response')}

2. **Claude Response**:
{responses.get('Claude', 'Error or No Response')}

3. **Gemini Response**:
{responses.get('Gemini', 'Error or No Response')}

### Guidelines for Consensus Synthesis:
1. **Analyze Convergence**: Identify critical concepts, values, facts, and conclusions where all active models fully agree.
2. **Analyze Divergence**: Identify key contradictions, varying emphases, edge cases, or perspectives where they differ.
3. **Consensus Level**: Rate the consensus as:
   - "High" (fully aligned in facts and primary conclusions).
   - "Medium" (agree on the core answer, but differ on secondary nuances or implementation details).
   - "Low" (major contradictions, contrasting opinions, or different answers).
4. **Resolution Logic**: Do NOT simply do a majority vote. Reconcile disagreements using logical consistency, rigorous physical laws, empirical standards, and deep analytical reasoning.
5. **Synthesize Final Answer**: Formulate a comprehensive, complete, and state-of-the-art response that represents the scientific/intellectual consensus. If disagreement remains, outline the competing viewpoints clearly and give a well-reasoned final opinion.

### Output Format:
You MUST format your output strictly as follows:

## 📊 Consensus Level
[High / Medium / Low]

## 🤝 Points of Convergence
- [Agreement Point 1]
- [Agreement Point 2]

## ⚡ Points of Divergence
- [Disagreement/Nuance Point 1]
- [Disagreement/Nuance Point 2]

## 📝 Consensus Analysis & Resolution
[Detailed analytical reasoning explaining how the three models compare, any biases identified, and how contradictions are reconciled.]

## 🎯 Final Consensus Answer
[Your definitive, highly comprehensive, and high-quality synthesized consensus response.]
"""

        # Query the best available model to act as the synthesis moderator
        # We prioritize Claude, then Gemini, then Grok
        def is_valid(resp: str) -> bool:
            return resp and not any(x in resp for x in ["Error", "API Error", "Skipped", "Fail", "invalid"])

        if self.claude_key and is_valid(responses.get("Claude")):
            logger.info("Executing Synthesis Moderator via Anthropic Claude...")
            return await self.query_claude(client, moderator_prompt)
        elif self.gemini_key and is_valid(responses.get("Gemini")):
            logger.info("Executing Synthesis Moderator via Google Gemini...")
            return await self.query_gemini(client, moderator_prompt)
        elif self.grok_key and is_valid(responses.get("Grok")):
            logger.info("Executing Synthesis Moderator via xAI Grok...")
            return await self.query_grok(client, moderator_prompt)
        else:
            return "Error: No active AI model is available to perform the synthesis moderation."

    async def get_consensus(self, query: str) -> Tuple[Dict[str, str], str]:
        """
        Executes parallel calls to the active models and triggers the
        consensus synthesis stage.
        """
        limits = httpx.Limits(max_keepalive_connections=5, max_connections=10)
        async with httpx.AsyncClient(limits=limits) as client:
            # Query all models concurrently
            tasks = {
                "Grok": self.grok_gated_query(client, query),
                "Claude": self.claude_gated_query(client, query),
                "Gemini": self.gemini_gated_query(client, query)
            }
            
            logger.info(f"Broadcasting query in parallel: '{query}'")
            results = await asyncio.gather(*tasks.values())
            responses = dict(zip(tasks.keys(), results))
            
            # Synthesize consensus
            consensus_report = await self.run_consensus_moderator(client, query, responses)
            return responses, consensus_report

    async def grok_gated_query(self, client: httpx.AsyncClient, query: str) -> str:
        if not self.grok_key:
            return "Skipped: Grok API Key is not configured."
        return await self.query_grok(client, query)

    async def claude_gated_query(self, client: httpx.AsyncClient, query: str) -> str:
        if not self.claude_key:
            return "Skipped: Claude API Key is not configured."
        return await self.query_claude(client, query)

    async def gemini_gated_query(self, client: httpx.AsyncClient, query: str) -> str:
        if not self.gemini_key:
            return "Skipped: Gemini API Key is not configured."
        return await self.query_gemini(client, query)


def print_box(title: str, content: str, color: str = Colors.OKCYAN):
    print(f"\n{color}{Colors.BOLD}{'=' * 80}{Colors.ENDC}")
    print(f"{color}{Colors.BOLD}🤖 {title}{Colors.ENDC}")
    print(f"{color}{Colors.BOLD}{'=' * 80}{Colors.ENDC}")
    print(content)
    print(f"{color}{Colors.BOLD}{'=' * 80}{Colors.ENDC}\n")


async def main():
    if len(sys.argv) < 2:
        print(f"{Colors.WARNING}Usage: python consensus.py \"your question here\"{Colors.ENDC}")
        print("Please enter a question to start. Entering interactive mode...")
        try:
            query = input(f"\n{Colors.BOLD}Enter your question: {Colors.ENDC}")
        except (KeyboardInterrupt, EOFError):
            print("\nExiting.")
            sys.exit(0)
    else:
        query = sys.argv[1]

    if not query.strip():
        print(f"{Colors.FAIL}Error: Question cannot be empty.{Colors.ENDC}")
        sys.exit(1)

    engine = ConsensusEngine()
    
    print(f"\n{Colors.HEADER}{Colors.BOLD}=== TCO MULTI-AGENT CONSENSUS MECHANISM ==={Colors.ENDC}")
    print(f"Query: '{query}'\n")

    try:
        responses, report = await engine.get_consensus(query)
        
        # Print individual models
        for name, response in responses.items():
            color = Colors.OKGREEN if not response.startswith("Error") and not response.startswith("Skipped") else Colors.WARNING
            print_box(f"{name} Response ({GROK_MODEL if name == 'Grok' else CLAUDE_MODEL if name == 'Claude' else GEMINI_MODEL})", response, color)

        # Print unified consensus report
        print_box("Unified Consensus Report", report, Colors.HEADER)

    except Exception as e:
        logger.error(f"Execution failed: {str(e)}", exc_info=True)


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
