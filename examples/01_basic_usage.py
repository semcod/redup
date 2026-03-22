"""Example: Basic reDUP usage — analyze a project directory."""

from pathlib import Path

from redup import ScanConfig, analyze
from redup.reporters.json_reporter import to_json
from redup.reporters.toon_reporter import to_toon


def main():
    # Configure scan
    config = ScanConfig(
        root=Path("."),           # project root
        extensions=[".py"],       # file types to scan
        min_block_lines=3,        # minimum block size
        min_similarity=0.85,      # fuzzy match threshold
        include_tests=False,      # skip test files
    )

    # Run analysis
    result = analyze(config=config, function_level_only=True)

    # Print summary
    print(f"Files scanned:  {result.stats.files_scanned}")
    print(f"Total lines:    {result.stats.total_lines}")
    print(f"Scan time:      {result.stats.scan_time_ms:.0f}ms")
    print(f"Duplicate groups: {result.total_groups}")
    print(f"Lines recoverable: {result.total_saved_lines}")
    print()

    # Show top duplicates
    for group in result.sorted_by_impact()[:5]:
        name = group.normalized_name or group.id
        print(f"  [{group.id}] {name} — {group.occurrences}x, "
              f"{group.total_lines}L, saves {group.saved_lines_potential}L")
        for frag in group.fragments:
            print(f"    {frag.file}:{frag.line_start}-{frag.line_end}")
    print()

    # Show refactoring suggestions
    for s in result.suggestions[:5]:
        print(f"  [{s.priority}] {s.action.value} → {s.new_module}")
        print(f"       {s.rationale}")
    print()

    # Export TOON (for LLM consumption)
    toon = to_toon(result)
    print("=== TOON output ===")
    print(toon)

    # Export JSON (for tooling)
    json_out = to_json(result)
    Path("duplication.json").write_text(json_out)
    print("Saved duplication.json")


if __name__ == "__main__":
    main()
