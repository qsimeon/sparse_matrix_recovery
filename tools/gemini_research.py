"""
Multi-Model Research Wrapper

Routes research queries to the best model:
  - Gemini 2.5 Pro: Large-context research with search grounding
  - o3-deep-research: Deep literature + math research (via OpenRouter)
  - Gemini Flash: Budget research queries

Usage:
    python gemini_research.py --query "your research query" --output results.json
    python gemini_research.py --queries queries.json --model gemini-2.5-pro --output results.json
    python gemini_research.py --query "..." --model o3-deep-research --output results.json
"""

import os
import json
import argparse
import time
from pathlib import Path

try:
    from google import genai
    from google.genai import types
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False

try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False


# Model routing: which backend to use
GEMINI_MODELS = {"gemini-2.0-flash", "gemini-2.5-pro", "gemini-2.0-flash-lite"}
OPENROUTER_MODELS = {"o3-deep-research", "gpt-5.4"}


def _research_gemini(query: str, model: str) -> dict:
    """Run research query via Google GenAI SDK."""
    if not HAS_GENAI:
        raise ImportError("google-genai package required. Install with: pip install google-genai")

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable not set")

    client = genai.Client(api_key=api_key)

    try:
        response = client.models.generate_content(
            model=model,
            contents=query,
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())],
                temperature=0.2,
            ),
        )

        sources = []
        if hasattr(response.candidates[0], 'grounding_metadata') and response.candidates[0].grounding_metadata:
            metadata = response.candidates[0].grounding_metadata
            if hasattr(metadata, 'grounding_chunks') and metadata.grounding_chunks:
                for chunk in metadata.grounding_chunks:
                    if hasattr(chunk, 'web') and chunk.web:
                        sources.append({
                            "title": getattr(chunk.web, 'title', ''),
                            "uri": getattr(chunk.web, 'uri', ''),
                        })

        return {
            "query": query,
            "response": response.text,
            "sources": sources,
            "model": model,
            "backend": "gemini",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        }
    except Exception as e:
        response = client.models.generate_content(
            model=model,
            contents=f"As a research assistant, provide a thorough literature review for: {query}",
            config=types.GenerateContentConfig(temperature=0.2),
        )
        return {
            "query": query,
            "response": response.text,
            "sources": [],
            "model": model,
            "backend": "gemini",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "note": f"Fallback mode (no search grounding): {str(e)}",
        }


def _research_openrouter(query: str, model: str) -> dict:
    """Run research query via OpenRouter (for o3-deep-research, gpt-5.4)."""
    if not HAS_OPENAI:
        raise ImportError("openai package required. Install with: pip install openai")

    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY environment variable not set")

    resolved = f"openai/{model}" if "/" not in model else model
    client = OpenAI(api_key=api_key, base_url="https://openrouter.ai/api/v1")

    response = client.chat.completions.create(
        model=resolved,
        messages=[
            {"role": "system", "content": "You are a research assistant. Provide thorough, "
             "well-sourced analysis with specific paper citations (author, year, journal)."},
            {"role": "user", "content": query},
        ],
    )

    return {
        "query": query,
        "response": response.choices[0].message.content,
        "sources": [],
        "model": resolved,
        "backend": "openrouter",
        "usage": {
            "prompt_tokens": getattr(response.usage, 'prompt_tokens', 0),
            "completion_tokens": getattr(response.usage, 'completion_tokens', 0),
        },
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }


def deep_research(query: str, model: str = "gemini-2.5-pro") -> dict:
    """
    Run a deep research query, routing to the appropriate backend.

    Args:
        query: The research question to investigate
        model: Model name (gemini-2.5-pro, o3-deep-research, gemini-2.0-flash, etc.)
    """
    if model in OPENROUTER_MODELS:
        return _research_openrouter(query, model)
    else:
        return _research_gemini(query, model)


def batch_research(queries: list[str], model: str = "gemini-2.5-pro") -> list[dict]:
    """Run multiple research queries sequentially with rate limiting."""
    results = []
    for i, query in enumerate(queries):
        print(f"[{i+1}/{len(queries)}] Researching with {model}: {query[:80]}...")
        result = deep_research(query, model)
        results.append(result)
        if i < len(queries) - 1:
            time.sleep(3)  # Rate limiting
    return results


def synthesize_results(results: list[dict]) -> str:
    """Combine multiple research results into a synthesis."""
    sections = []
    all_sources = []
    for r in results:
        sections.append(f"### Query: {r['query']}\n\n{r['response']}")
        all_sources.extend(r.get('sources', []))

    synthesis = "# Literature Review Synthesis\n\n"
    synthesis += "\n\n---\n\n".join(sections)

    if all_sources:
        synthesis += "\n\n---\n\n## Sources\n\n"
        seen = set()
        for s in all_sources:
            key = s.get('uri', s.get('title', ''))
            if key and key not in seen:
                seen.add(key)
                synthesis += f"- [{s.get('title', 'Untitled')}]({s.get('uri', '')})\n"

    return synthesis


def main():
    parser = argparse.ArgumentParser(description="Multi-Model Research Tool")
    parser.add_argument("--query", type=str, help="Single research query")
    parser.add_argument("--queries", type=str, help="Path to JSON file with list of queries")
    parser.add_argument("--output", type=str, default="research_results.json", help="Output file path")
    parser.add_argument("--model", type=str, default="gemini-2.5-pro",
                        help="Model: gemini-2.5-pro, o3-deep-research, gemini-2.0-flash")
    parser.add_argument("--synthesize", action="store_true", help="Also output a synthesis markdown file")
    args = parser.parse_args()

    if args.query:
        queries = [args.query]
    elif args.queries:
        with open(args.queries) as f:
            queries = json.load(f)
    else:
        parser.error("Provide --query or --queries")

    results = batch_research(queries, model=args.model)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Results saved to {output_path}")

    if args.synthesize:
        synthesis = synthesize_results(results)
        synth_path = output_path.with_suffix(".md")
        with open(synth_path, "w") as f:
            f.write(synthesis)
        print(f"Synthesis saved to {synth_path}")


if __name__ == "__main__":
    main()
