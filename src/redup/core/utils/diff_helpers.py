"""Helper functions for diff operations to reduce complexity."""

from typing import List, Dict, Set
from ..models import DuplicateGroup


class GroupMatcher:
    """Helper class to find matching groups between scans."""
    
    def __init__(self, before_groups: Dict[str, DuplicateGroup], after_groups: Dict[str, DuplicateGroup]):
        """Initialize with groups from two scans."""
        self.before_groups = before_groups
        self.after_groups = after_groups
        self._before_to_after_matches: Dict[str, str] = {}
        self._after_to_before_matches: Dict[str, str] = {}
        self._find_all_matches()
    
    def _find_all_matches(self) -> None:
        """Pre-compute all matches between groups to avoid repeated comparisons."""
        for before_id, before_group in self.before_groups.items():
            for after_id, after_group in self.after_groups.items():
                if self._groups_match(before_group, after_group):
                    self._before_to_after_matches[before_id] = after_id
                    self._after_to_before_matches[after_id] = before_id
                    break  # Assume one-to-one matching for simplicity
    
    def _groups_match(self, group1: DuplicateGroup, group2: DuplicateGroup) -> bool:
        """Check if two groups represent the same duplicate (similar structure and files)."""
        # Check if they have the same type and similar similarity
        if group1.duplicate_type != group2.duplicate_type:
            return False
        
        # Check similarity scores are close
        if abs(group1.similarity_score - group2.similarity_score) > 0.1:
            return False
        
        # Check if they involve similar files (at least 50% overlap)
        files1 = {frag.file for frag in group1.fragments}
        files2 = {frag.file for frag in group2.fragments}
        
        if not files1 or not files2:
            return False
        
        overlap = len(files1.intersection(files2))
        union = len(files1.union(files2))
        
        return overlap / union >= 0.5
    
    def get_resolved_groups(self) -> List[DuplicateGroup]:
        """Find groups that were present before but not after (or changed significantly)."""
        resolved = []
        for before_id, before_group in self.before_groups.items():
            if before_id not in self._before_to_after_matches:
                # No matching group found in after scan
                resolved.append(before_group)
        return resolved
    
    def get_new_groups(self) -> List[DuplicateGroup]:
        """Find groups that are present after but not before (or changed significantly)."""
        new = []
        for after_id, after_group in self.after_groups.items():
            if after_id not in self._after_to_before_matches:
                # No matching group found in before scan
                new.append(after_group)
        return new
    
    def get_unchanged_groups(self) -> List[DuplicateGroup]:
        """Find groups that are present in both scans with similar structure."""
        unchanged = []
        for after_id, after_group in self.after_groups.items():
            if after_id in self._after_to_before_matches:
                # Found matching group in before scan
                unchanged.append(after_group)
        return unchanged


class DiffCalculator:
    """Helper class to calculate diff statistics."""
    
    @staticmethod
    def calculate_lines(groups: List[DuplicateGroup]) -> int:
        """Calculate total lines that could be saved from groups."""
        return sum(g.saved_lines_potential for g in groups)
    
    @staticmethod
    def calculate_diff_stats(resolved: List[DuplicateGroup], 
                           new: List[DuplicateGroup], 
                           unchanged: List[DuplicateGroup]) -> Dict[str, int]:
        """Calculate all diff statistics."""
        return {
            'resolved_count': len(resolved),
            'new_count': len(new),
            'unchanged_count': len(unchanged),
            'resolved_lines': sum(g.saved_lines_potential for g in resolved),
            'new_lines': sum(g.saved_lines_potential for g in new),
            'unchanged_lines': sum(g.saved_lines_potential for g in unchanged),
        }
