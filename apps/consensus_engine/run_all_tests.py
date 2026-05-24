import asyncio
import os
import sys
from pathlib import Path

# Add consensus engine folder to path
sys.path.append(str(Path(__file__).parents[2] / "apps" / "consensus_engine"))

from consensus import ConsensusEngine, GROK_MODEL, CLAUDE_MODEL, GEMINI_MODEL

TEST_CASES = [
    {
        "category": "Technical (Electromagnetics & Physics)",
        "question": "Compare Wheeler's helical coil inductance formula against Medhurst's coil self-capacitance formula in terms of high-frequency accuracy and limitations."
    },
    {
        "category": "Reasoning (Logical & Mathematical)",
        "question": "If a clock strikes 13 times at 13:00 and takes 12 seconds to complete the strikes, how long will it take to strike 6 times at 6:00, assuming identical strike intervals?"
    },
    {
        "category": "Creative (Philosophical & Analogy)",
        "question": "Write a short, poetic analogy describing the resonance of a Tesla coil as a conversation between two lovers who are physically separated but emotionally in sync."
    },
    {
        "category": "Controversial (Commercial & Scientific Viability)",
        "question": "Is high-voltage wireless power transmission via resonant magnetic coupling commercially viable for metropolitan grids compared to traditional copper cables?"
    },
    {
        "category": "Factual (Historical & Engineering Spec)",
        "question": "What exact frequency and electrical power levels did Nikola Tesla use in his Wardenclyffe Tower project, and what was the main resonant frequency of the Earth he intended to harness?"
    }
]

async def run_test_and_format(engine: ConsensusEngine, idx: int, category: str, question: str) -> str:
    print(f"Running Test {idx+1}/5: {category}...")
    try:
        responses, report = await engine.get_consensus(question)
        
        md = f"### Test Case {idx+1}: {category}\n"
        md += f"**Question**: *{question}*\n\n"
        
        for model_name, resp in responses.items():
            model_ver = GROK_MODEL if model_name == 'Grok' else CLAUDE_MODEL if model_name == 'Claude' else GEMINI_MODEL
            md += f"<details>\n<summary>🤖 {model_name} Response ({model_ver})</summary>\n\n"
            md += f"{resp}\n\n"
            md += f"</details>\n\n"
            
        md += "#### 📊 Synthesized Consensus Report\n"
        md += f"{report}\n"
        md += "\n" + "-"*80 + "\n\n"
        return md
    except Exception as e:
        print(f"Failed Test {idx+1}: {e}")
        return f"### Test Case {idx+1}: {category}\n**Question**: *{question}*\n**Error**: {str(e)}\n\n"

async def main():
    engine = ConsensusEngine()
    
    report_header = """# 🛰️ Multi-Agent Consensus Engine Evaluation Report

This report evaluates our production-grade Consensus Engine powered by three advanced LLMs: **Grok-2-1212**, **Claude-3.5-Sonnet**, and **Gemini-1.5-Pro**. The models queried in parallel represent distinct cognitive frameworks, and their convergence/divergence is moderated to generate high-quality synthesized responses.

---

"""
    
    results = []
    for idx, test in enumerate(TEST_CASES):
        res = await run_test_and_format(engine, idx, test["category"], test["question"])
        results.append(res)
        
    final_report = report_header + "".join(results)
    
    # Save the report to apps/consensus_engine/README.md
    readme_path = Path(__file__).parents[2] / "apps" / "consensus_engine" / "README.md"
    
    # Readme instructions
    readme_content = f"""# 🛰️ Multi-Agent Consensus Engine

An advanced, asynchronous multi-agent consensus network designed to coordinate, parallel-query, and logically resolve responses from three major AI foundations:
*   **xAI Grok** (`{GROK_MODEL}`)
*   **Anthropic Claude** (`{CLAUDE_MODEL}`)
*   **Google Gemini** (`{GEMINI_MODEL}`)

A specialized **Constituent-Synthesis Moderator** compiles agreements (convergence), highlights contradictions (divergence), and resolves arguments with objective reasoning.

---

## 🚀 Setup & Execution

### 1. Installation
Install the required packages in your environment:
```bash
pip install -r requirements.txt
```

### 2. Configure API Keys
Copy `.env.example` to `.env` in the project root:
```bash
cp .env.example .env
```
Fill in the API keys:
```env
GROK_API_KEY="your-key"
CLAUDE_API_KEY="your-key"
GEMINI_API_KEY="your-key"
```

### 3. Usage
Run the script from the command line:
```bash
python consensus.py "Your question here"
```
Or enter **interactive mode** by omitting the argument:
```bash
python consensus.py
```

---

## 📊 Live Evaluation & Test Case Report

{final_report}
"""
    
    with open(readme_path, "w") as f:
        f.write(readme_content)
        
    print(f"\nAll tests completed! Evaluation report saved to: {readme_path}")

if __name__ == "__main__":
    asyncio.run(main())
