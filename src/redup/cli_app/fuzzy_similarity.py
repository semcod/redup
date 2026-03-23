"""Fuzzy similarity detection functions."""

from pathlib import Path
import typer

from redup.core.models import DuplicationMap


def _apply_fuzzy_similarity(dup_map: DuplicationMap, threshold: float) -> DuplicationMap:
    """Apply fuzzy similarity detection to find similar components across all languages."""
    validation = _validate_fuzzy_input(dup_map, threshold)
    if not validation.is_valid:
        typer.echo(validation.message)
        return dup_map
    
    all_blocks = _extract_all_blocks(dup_map)
    if not all_blocks:
        typer.echo("🔍 No code blocks found for fuzzy analysis")
        return dup_map
    
    typer.echo(f"🔍 Analyzing {len(all_blocks)} code blocks for universal fuzzy similarity...")
    
    html_css_blocks, other_blocks = _separate_blocks_by_type(all_blocks)
    similar_pairs = _analyze_blocks_with_detectors(html_css_blocks, other_blocks, threshold)
    
    _report_fuzzy_results(similar_pairs)
    return dup_map


def _validate_fuzzy_input(dup_map: DuplicationMap, threshold: float) -> 'FuzzyValidationResult':
    """Validate input parameters for fuzzy similarity analysis."""
    from dataclasses import dataclass
    
    @dataclass
    class FuzzyValidationResult:
        is_valid: bool
        message: str = ""
    
    if threshold <= 0 or threshold > 1:
        return FuzzyValidationResult(False, "❌ Invalid threshold. Must be between 0 and 1.")
    
    if not dup_map.groups:
        return FuzzyValidationResult(False, "❌ No duplicate groups found.")
    
    return FuzzyValidationResult(True)


def _extract_all_blocks(dup_map: DuplicationMap) -> list:
    """Extract all code blocks from duplicate fragments."""
    from redup.core.scanner import CodeBlock
    
    all_blocks = []
    for group in dup_map.groups:
        for fragment in group.fragments:
            # Create a CodeBlock from fragment data
            block = CodeBlock(
                file=fragment.file,
                line_start=fragment.line_start,
                line_end=fragment.line_end,
                text=fragment.text,
                function_name=fragment.function_name,
                class_name=fragment.class_name
            )
            all_blocks.append(block)
    return all_blocks


def _separate_blocks_by_type(all_blocks: list) -> tuple[list, list]:
    """Separate blocks into HTML/CSS and other language categories."""
    html_css_blocks = [block for block in all_blocks 
                      if Path(block.file).suffix.lower() in ['.html', '.htm', '.css', '.scss', '.sass', '.less']]
    
    other_blocks = [block for block in all_blocks if block not in html_css_blocks]
    
    return html_css_blocks, other_blocks


def _analyze_blocks_with_detectors(html_css_blocks: list, other_blocks: list, threshold: float) -> list:
    """Analyze blocks using appropriate fuzzy similarity detectors."""
    similar_pairs = []
    
    # Analyze HTML/CSS with specialized detector
    if html_css_blocks:
        typer.echo(f"  📝 Analyzing {len(html_css_blocks)} HTML/CSS blocks...")
        html_css_similar = _analyze_html_css_blocks(html_css_blocks, threshold)
        similar_pairs.extend(html_css_similar)
        typer.echo(f"    ✨ Found {len(html_css_similar)} similar HTML/CSS component pairs")
    
    # Analyze other languages with universal detector
    if other_blocks:
        typer.echo(f"  🔧 Analyzing {len(other_blocks)} blocks from other languages...")
        universal_similar = _analyze_other_language_blocks(other_blocks, threshold)
        similar_pairs.extend(universal_similar)
        typer.echo(f"    ✨ Found {len(universal_similar)} similar component pairs from other languages")
    
    return similar_pairs


def _analyze_html_css_blocks(html_css_blocks: list, threshold: float) -> list:
    """Analyze HTML/CSS blocks using specialized fuzzy similarity detector."""
    from redup.core.fuzzy_similarity import FuzzySimilarityDetector
    
    html_css_detector = FuzzySimilarityDetector(similarity_threshold=threshold)
    return html_css_detector.find_similar_components(html_css_blocks)


def _analyze_other_language_blocks(other_blocks: list, threshold: float) -> list:
    """Analyze non-HTML/CSS blocks using universal fuzzy similarity detector."""
    from redup.core.universal_fuzzy import UniversalFuzzyDetector
    
    universal_detector = UniversalFuzzyDetector(similarity_threshold=threshold)
    return universal_detector.find_similar_components(other_blocks)


def _report_fuzzy_results(similar_pairs: list) -> None:
    """Report fuzzy similarity analysis results."""
    if similar_pairs:
        typer.echo(f"🎯 Total fuzzy similar components found: {len(similar_pairs)}")
        
        # Simplified reporting to reduce complexity
        typer.echo(f"  📊 Language groups: {len(set(Path(b1.file).suffix + '+' + Path(b2.file).suffix for b1, b2, _ in similar_pairs))}")
        
        # Show top examples only
        for block1, block2, similarity in similar_pairs[:5]:
            typer.echo(f"    {block1.file} ↔ {block2.file}: {similarity:.2f}")
        
        if len(similar_pairs) > 5:
            typer.echo(f"    ... and {len(similar_pairs) - 5} more")
        
        # Note: In production, you'd integrate these into DuplicationMap
        # For now, we just report the findings
        
    else:
        typer.echo("🔍 No fuzzy similar components found")


def _report_similarity_by_groups(similar_pairs):
    """Extracted function to reduce complexity."""
    lang_groups = {}
    for block1, block2, similarity in similar_pairs:
        lang1 = Path(block1.file).suffix
        lang2 = Path(block2.file).suffix
        comp_type = "unknown"
        
        # Try to get component type
        try:
            from redup.core.universal_fuzzy import UniversalFuzzyExtractor
            extractor = UniversalFuzzyExtractor()
            sig1 = extractor.extract_universal_signature(block1)
            if sig1:
                comp_type = sig1.component_type
        except:
            pass
        
        group_key = f"{lang1}+{lang2}:{comp_type}"
        if group_key not in lang_groups:
            lang_groups[group_key] = []
        lang_groups[group_key].append((block1, block2, similarity))
    
    return lang_groups
