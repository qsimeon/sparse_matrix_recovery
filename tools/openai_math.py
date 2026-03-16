"""
OpenAI Math Reasoning Wrapper

Uses frontier reasoning models for mathematical proof verification,
derivation checking, and error bound computation.

Model routing:
  - gpt-5.4 (default): Best for proofs, derivations, tight bounds
  - o3-deep-research: Deep literature + math research
  - o3-mini: Budget math tasks

All models accessed via OpenRouter for billing simplicity.

Usage:
    python openai_math.py --task "Verify this derivation: ..." --output result.json
    python openai_math.py --file derivation.tex --output result.json
    python openai_math.py --tasks tasks.json --model gpt-5.4 --output results.json
"""

import os
import json
import argparse
import time
from pathlib import Path

try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False
    print("Warning: openai not installed. Run: pip install openai")


# Model aliases → OpenRouter model IDs
MODEL_REGISTRY = {
    "gpt-5.4": "openai/gpt-5.4",
    "o3-deep-research": "openai/o3-deep-research",
    "o3-mini": "openai/o3-mini",
    "o3": "openai/o3",
    "gpt-4o": "openai/gpt-4o",
}


MATH_SYSTEM_PROMPT = """You are a mathematical reasoning assistant specializing in:
- Linear algebra and matrix analysis
- Dynamical systems and control theory
- Statistical estimation and inference
- Optimization theory and convergence analysis

When asked to verify a derivation:
1. State each step explicitly
2. Check each step for correctness
3. Identify any implicit assumptions
4. Provide the final verdict: CORRECT, INCORRECT (with explanation), or CONDITIONAL (with conditions)

When asked to derive error bounds:
1. State the setup and assumptions clearly
2. Use standard inequalities (Cauchy-Schwarz, triangle, submultiplicativity, etc.)
3. Provide tight bounds where possible
4. Discuss when bounds are achievable

When asked about identifiability:
1. State necessary and sufficient conditions precisely
2. Connect to rank conditions on the measurement/observation matrices
3. Discuss generic vs worst-case identifiability

Format mathematical expressions using LaTeX notation."""


def _resolve_model(model: str) -> str:
    """Resolve model alias to OpenRouter model ID."""
    return MODEL_REGISTRY.get(model, model if "/" in model else f"openai/{model}")


def _format_response(task, response, model, reasoning_effort, via="openrouter"):
    """Format API response into standard dict."""
    return {
        "task": task,
        "response": response.choices[0].message.content,
        "model": model,
        "reasoning_effort": reasoning_effort,
        "via": via,
        "usage": {
            "prompt_tokens": getattr(response.usage, 'prompt_tokens', 0),
            "completion_tokens": getattr(response.usage, 'completion_tokens', 0),
            "total_tokens": getattr(response.usage, 'total_tokens', 0),
        },
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }


def verify_math(
    task: str,
    model: str = "gpt-5.4",
    reasoning_effort: str = "high",
) -> dict:
    """
    Use a frontier reasoning model for math verification.

    Args:
        task: The mathematical task or derivation to verify
        model: Model name or alias (gpt-5.4, o3-deep-research, o3-mini, etc.)
        reasoning_effort: "low", "medium", or "high" (ignored by some models)

    Returns:
        dict with keys: task, response, model, reasoning_effort, timestamp
    """
    if not HAS_OPENAI:
        raise ImportError("openai package required. Install with: pip install openai")

    openrouter_key = os.environ.get("OPENROUTER_API_KEY")
    api_key = os.environ.get("OPENAI_API_KEY")

    if not openrouter_key and not api_key:
        raise ValueError("Set OPENROUTER_API_KEY or OPENAI_API_KEY")

    resolved_model = _resolve_model(model)

    # Primary path: OpenRouter (supports all models, billing active)
    last_error = None
    if openrouter_key:
        try:
            client = OpenAI(api_key=openrouter_key, base_url="https://openrouter.ai/api/v1")
            kwargs = dict(
                model=resolved_model,
                messages=[
                    {"role": "system", "content": MATH_SYSTEM_PROMPT},
                    {"role": "user", "content": task},
                ],
            )
            # Only pass reasoning_effort for models that support it
            if model in ("o3-mini", "o3"):
                kwargs["reasoning_effort"] = reasoning_effort
            response = client.chat.completions.create(**kwargs)
            return _format_response(task, response, resolved_model, reasoning_effort, via="openrouter")
        except Exception as e:
            last_error = e
            print(f"  OpenRouter failed ({e}), trying OpenAI direct...")

    # Fallback: direct OpenAI (may not support gpt-5.4 without billing)
    if api_key:
        try:
            client = OpenAI(api_key=api_key)
            # Direct OpenAI uses short model names
            direct_model = model if "/" not in model else model.split("/")[-1]
            kwargs = dict(
                model=direct_model,
                messages=[
                    {"role": "system", "content": MATH_SYSTEM_PROMPT},
                    {"role": "user", "content": task},
                ],
            )
            if direct_model in ("o3-mini", "o3"):
                kwargs["reasoning_effort"] = reasoning_effort
            response = client.chat.completions.create(**kwargs)
            return _format_response(task, response, direct_model, reasoning_effort, via="direct")
        except Exception as e:
            last_error = e
            print(f"  OpenAI direct also failed ({e})")

    raise last_error or ValueError("No working API key found")


def batch_verify(tasks: list[str], model: str = "gpt-5.4", reasoning_effort: str = "high") -> list[dict]:
    """Run multiple math verification tasks sequentially."""
    results = []
    for i, task in enumerate(tasks):
        print(f"[{i+1}/{len(tasks)}] Verifying with {model}: {task[:80]}...")
        result = verify_math(task, model, reasoning_effort)
        results.append(result)
        if i < len(tasks) - 1:
            time.sleep(2)  # Rate limiting between calls
    return results


def main():
    parser = argparse.ArgumentParser(description="Frontier Math Reasoning Tool")
    parser.add_argument("--task", type=str, help="Math task or derivation to verify")
    parser.add_argument("--file", type=str, help="Path to file containing the math task")
    parser.add_argument("--tasks", type=str, help="Path to JSON file with list of tasks")
    parser.add_argument("--output", type=str, default="math_results.json", help="Output file path")
    parser.add_argument("--model", type=str, default="gpt-5.4",
                        help=f"Model name or alias. Options: {list(MODEL_REGISTRY.keys())}")
    parser.add_argument("--effort", type=str, default="high", choices=["low", "medium", "high"])
    parser.add_argument("--list-models", action="store_true", help="List available models")
    args = parser.parse_args()

    if args.list_models:
        print("Available models:")
        for alias, full_id in MODEL_REGISTRY.items():
            print(f"  {alias:20s} → {full_id}")
        return

    if args.task:
        tasks = [args.task]
    elif args.file:
        with open(args.file) as f:
            tasks = [f.read()]
    elif args.tasks:
        with open(args.tasks) as f:
            tasks = json.load(f)
    else:
        parser.error("Provide --task, --file, or --tasks")

    results = batch_verify(tasks, model=args.model, reasoning_effort=args.effort)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Results saved to {output_path}")


if __name__ == "__main__":
    main()
