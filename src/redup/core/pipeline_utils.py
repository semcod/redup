from redup.core.models import DuplicateGroup, DuplicateFragment, DuplicateType
from redup.core.hasher import HashedBlock

def blocks_to_group(group_id: str, blocks: list[HashedBlock], dup_type: DuplicateType, similarity: float = 1.0, normalized_hash: str = "") -> DuplicateGroup:
    seen = set()
    fragments = []
    for hb in blocks:
        block = hb.block
        key = (block.file, block.line_start)
        if key in seen: continue
        seen.add(key)
        fragments.append(DuplicateFragment(file=block.file, line_start=block.line_start, line_end=block.line_end, text=block.text, function_name=block.function_name, class_name=block.class_name))
    if len(fragments) < 2: return DuplicateGroup(id=group_id, duplicate_type=dup_type)
    name = fragments[0].function_name if fragments[0].function_name else None
    return DuplicateGroup(id=group_id, duplicate_type=dup_type, fragments=fragments, similarity_score=similarity, normalized_hash=normalized_hash, normalized_name=name)

def deduplicate_groups(groups: list[DuplicateGroup]) -> list[DuplicateGroup]:
    if not groups: return groups
    sorted_groups = sorted(groups, key=lambda g: g.impact_score, reverse=True)
    kept, seen_locations = [], set()
    for group in sorted_groups:
        if group.occurrences < 2: continue
        locations = {(f.file, f.line_start, f.line_end) for f in group.fragments}
        if len(locations - seen_locations) >= 2:
            kept.append(group)
            seen_locations.update(locations)
    return kept