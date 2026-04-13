"""Verify citation integrity between main.tex and references.bib."""
import re
from pathlib import Path

paper_dir = Path(__file__).parent.parent / "paper"
with open(paper_dir / "main.tex") as f:
    tex = f.read()

with open(paper_dir / "references.bib") as f:
    bib = f.read()

# Extract cited keys from LaTeX
cite_pattern = re.compile(r"\\cite[pt]?\{([^}]+)\}")
all_cited = set()
for match in cite_pattern.finditer(tex):
    for key in match.group(1).split(","):
        all_cited.add(key.strip())

# Extract bib entry keys
bib_keys = set(re.findall(r"@\w+\{(\w+)", bib))

print(f"Cited in paper: {len(all_cited)} keys")
print(f"In bib file:    {len(bib_keys)} entries")

cited_not_in_bib = all_cited - bib_keys
in_bib_not_cited = bib_keys - all_cited

if cited_not_in_bib:
    print(f"\nMISSING FROM BIB: {cited_not_in_bib}")
else:
    print("\nAll cited keys have bib entries: OK")

if in_bib_not_cited:
    print(f"UNUSED BIB ENTRIES: {in_bib_not_cited}")
else:
    print("All bib entries are cited: OK")

# List all cited keys
print("\nAll citations:")
for key in sorted(all_cited):
    status = "OK" if key in bib_keys else "MISSING"
    print(f"  {key}: {status}")
