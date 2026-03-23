"""Enhanced reporting with metrics and visualizations."""

from __future__ import annotations

import json
import time
from collections import defaultdict, Counter
from pathlib import Path
from typing import Any, Dict, List

from redup.core.models import (
    DuplicateFragment,
    DuplicateGroup,
    DuplicateType,
    DuplicationMap,
    ScanStats,
)


class EnhancedReporter:
    """Enhanced reporter with detailed metrics and visualizations."""
    
    def __init__(self, dup_map: DuplicationMap):
        self.dup_map = dup_map
        self.stats = dup_map.stats
        self.groups = dup_map.groups
    
    def generate_metrics_report(self) -> Dict[str, Any]:
        """Generate comprehensive metrics report."""
        metrics = {
            "scan_metrics": self._get_scan_metrics(),
            "duplication_metrics": self._get_duplication_metrics(),
            "language_metrics": self._get_language_metrics(),
            "file_metrics": self._get_file_metrics(),
            "complexity_metrics": self._get_complexity_metrics(),
            "refactoring_metrics": self._get_refactoring_metrics(),
        }
        return metrics
    
    def _get_scan_metrics(self) -> Dict[str, Any]:
        """Get scanning performance metrics."""
        return {
            "files_scanned": self.stats.files_scanned,
            "total_lines": self.stats.total_lines,
            "total_blocks": self.stats.total_blocks,
            "scan_time_ms": self.stats.scan_time_ms,
            "lines_per_second": self.stats.total_lines / max(self.stats.scan_time_ms / 1000, 0.001),
            "blocks_per_file": self.stats.total_blocks / max(self.stats.files_scanned, 1),
            "avg_file_size_lines": self.stats.total_lines / max(self.stats.files_scanned, 1),
        }
    
    def _get_duplication_metrics(self) -> Dict[str, Any]:
        """Get duplication analysis metrics."""
        total_fragments = sum(len(g.fragments) for g in self.groups)
        total_dup_lines = sum(g.saved_lines_potential for g in self.groups)
        
        # Group by type
        type_counts = Counter(g.duplicate_type for g in self.groups)
        
        # Similarity distribution
        similarities = [g.similarity_score for g in self.groups if g.similarity_score > 0]
        
        return {
            "total_groups": len(self.groups),
            "total_fragments": total_fragments,
            "total_duplicate_lines": total_dup_lines,
            "duplication_percentage": (total_dup_lines / max(self.stats.total_lines, 1)) * 100,
            "by_type": dict(type_counts),
            "avg_similarity": sum(similarities) / max(len(similarities), 1),
            "similarity_distribution": self._bucket_similarities(similarities),
            "largest_group_size": max((len(g.fragments) for g in self.groups), default=0),
            "avg_group_size": total_fragments / max(len(self.groups), 1),
        }
    
    def _get_language_metrics(self) -> Dict[str, Any]:
        """Get language-specific metrics."""
        lang_stats = defaultdict(lambda: {
            "files": set(),
            "groups": 0,
            "dup_lines": 0,
            "fragments": 0
        })
        
        for group in self.groups:
            for fragment in group.fragments:
                ext = Path(fragment.file).suffix
                lang_stats[ext]["files"].add(fragment.file)
                lang_stats[ext]["fragments"] += 1
                lang_stats[ext]["dup_lines"] += fragment.line_count
        
        for group in self.groups:
            # Count group once per language it appears in
            langs_in_group = set(Path(f.file).suffix for f in group.fragments)
            for lang in langs_in_group:
                lang_stats[lang]["groups"] += 1
        
        # Convert sets to counts
        for lang, stats in lang_stats.items():
            stats["files"] = len(stats["files"])
        
        return dict(lang_stats)
    
    def _get_file_metrics(self) -> Dict[str, Any]:
        """Get file-level metrics."""
        file_stats = defaultdict(lambda: {
            "groups": 0,
            "fragments": 0,
            "dup_lines": 0
        })
        
        for group in self.groups:
            for fragment in group.fragments:
                file_stats[fragment.file]["groups"] += 1
                file_stats[fragment.file]["fragments"] += 1
                file_stats[fragment.file]["dup_lines"] += fragment.line_count
        
        # Find most problematic files
        sorted_files = sorted(
            file_stats.items(),
            key=lambda x: x[1]["dup_lines"],
            reverse=True
        )
        
        return {
            "total_files_with_dups": len(file_stats),
            "top_files": sorted_files[:10],
            "avg_dups_per_file": sum(s["dup_lines"] for s in file_stats.values()) / max(len(file_stats), 1),
        }
    
    def _get_complexity_metrics(self) -> Dict[str, Any]:
        """Get complexity-related metrics."""
        group_sizes = [len(g.fragments) for g in self.groups]
        group_lines = [g.saved_lines_potential for g in self.groups]
        
        return {
            "size_distribution": self._bucket_group_sizes(group_sizes),
            "complexity_score": self._calculate_complexity_score(),
            "high_impact_groups": len([g for g in self.groups if g.impact_score > 100]),
            "max_group_size": max(group_sizes, default=0),
            "avg_group_lines": sum(group_lines) / max(len(group_lines), 1),
        }
    
    def _get_refactoring_metrics(self) -> Dict[str, Any]:
        """Get refactoring-related metrics."""
        suggestions = self.dup_map.suggestions or []
        
        type_counts = Counter(s.action.value for s in suggestions)
        risk_distribution = Counter(s.risk_level.value for s in suggestions)
        priority_distribution = Counter(s.priority for s in suggestions)
        
        return {
            "total_suggestions": len(suggestions),
            "by_action": dict(type_counts),
            "by_risk": dict(risk_distribution),
            "by_priority": dict(priority_distribution),
            "total_potential_savings": sum(s.priority for s in suggestions),
            "high_priority_suggestions": len([s for s in suggestions if s.priority >= 8]),
        }
    
    def _bucket_similarities(self, similarities: List[float]) -> Dict[str, int]:
        """Bucket similarity scores for distribution analysis."""
        buckets = defaultdict(int)
        for sim in similarities:
            if sim >= 0.95:
                buckets["95-100%"] += 1
            elif sim >= 0.90:
                buckets["90-95%"] += 1
            elif sim >= 0.85:
                buckets["85-90%"] += 1
            elif sim >= 0.80:
                buckets["80-85%"] += 1
            else:
                buckets["<80%"] += 1
        return dict(buckets)
    
    def _bucket_group_sizes(self, sizes: List[int]) -> Dict[str, int]:
        """Bucket group sizes for distribution analysis."""
        buckets = defaultdict(int)
        for size in sizes:
            if size >= 10:
                buckets["10+"] += 1
            elif size >= 5:
                buckets["5-9"] += 1
            elif size >= 3:
                buckets["3-4"] += 1
            else:
                buckets["2"] += 1
        return dict(buckets)
    
    def _calculate_complexity_score(self) -> float:
        """Calculate overall complexity score."""
        if not self.groups:
            return 0.0
        
        # Weight by group size and similarity
        total_score = 0.0
        for group in self.groups:
            size_factor = len(group.fragments) ** 0.5  # Square root to reduce exponential growth
            similarity_factor = group.similarity_score or 1.0
            total_score += size_factor * similarity_factor
        
        return total_score / len(self.groups)
    
    def generate_visualization_data(self) -> Dict[str, Any]:
        """Generate data for visualizations."""
        return {
            "duplication_chart": self._get_duplication_chart_data(),
            "language_chart": self._get_language_chart_data(),
            "file_chart": self._get_file_chart_data(),
            "timeline_data": self._get_timeline_data(),
        }
    
    def _get_duplication_chart_data(self) -> Dict[str, Any]:
        """Get data for duplication overview chart."""
        type_counts = Counter(g.duplicate_type for g in self.groups)
        return {
            "labels": list(type_counts.keys()),
            "data": list(type_counts.values()),
            "title": "Duplicates by Type"
        }
    
    def _get_language_chart_data(self) -> Dict[str, Any]:
        """Get data for language distribution chart."""
        lang_metrics = self._get_language_metrics()
        return {
            "labels": list(lang_metrics.keys()),
            "data": [stats["dup_lines"] for stats in lang_metrics.values()],
            "title": "Duplicate Lines by Language"
        }
    
    def _get_file_chart_data(self) -> Dict[str, Any]:
        """Get data for top problematic files chart."""
        file_metrics = self._get_file_metrics()
        top_files = file_metrics["top_files"][:10]
        
        return {
            "labels": [Path(f[0]).name for f in top_files],
            "data": [f[1]["dup_lines"] for f in top_files],
            "title": "Top 10 Files by Duplicate Lines"
        }
    
    def _get_timeline_data(self) -> Dict[str, Any]:
        """Get timeline data (placeholder for future enhancement)."""
        return {
            "labels": ["Scan", "Analysis", "Reporting"],
            "data": [self.stats.scan_time_ms, 0, 0],  # Placeholder
            "title": "Processing Timeline"
        }
    
    def save_enhanced_report(self, output_path: Path) -> None:
        """Save enhanced report with metrics and visualizations."""
        report = {
            "metadata": {
                "generated_at": time.time(),
                "project_path": self.dup_map.project_path,
                "redup_version": "0.3.2"
            },
            "metrics": self.generate_metrics_report(),
            "visualizations": self.generate_visualization_data(),
            "groups_summary": [
                {
                    "id": g.id,
                    "type": g.duplicate_type.value,
                    "fragments": len(g.fragments),
                    "similarity": g.similarity_score,
                    "impact_score": g.impact_score,
                    "saved_lines": g.saved_lines
                }
                for g in self.groups[:20]  # Top 20 groups
            ]
        }
        
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
