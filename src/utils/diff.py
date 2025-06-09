"""Content change detection and diffing utilities."""

import difflib
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import re

from src.utils.hashing import hash_content, content_similarity_hash
from src.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ContentChange:
    """Represents a change in content."""
    
    change_type: str  # added, removed, modified
    old_value: Optional[str]
    new_value: Optional[str]
    location: Optional[str]  # e.g., line number, section
    significance: float  # 0.0 to 1.0
    description: str


class ChangeDetector:
    """Detect and analyze changes in content."""
    
    def __init__(self):
        """Initialize change detector."""
        self.significance_threshold = 0.1
        
    def detect_changes(self, old_content: str, new_content: str) -> Dict[str, any]:
        """Detect changes between two versions of content."""
        # Quick hash comparison
        old_hash = hash_content(old_content)
        new_hash = hash_content(new_content)
        
        if old_hash == new_hash:
            return {
                "changed": False,
                "hash_changed": False,
                "changes": [],
                "summary": "No changes detected"
            }
        
        # Similarity comparison
        old_sim_hash = content_similarity_hash(old_content)
        new_sim_hash = content_similarity_hash(new_content)
        
        similarity_changed = old_sim_hash != new_sim_hash
        
        # Detailed diff analysis
        changes = self._analyze_changes(old_content, new_content)
        
        # Calculate overall significance
        total_significance = sum(c.significance for c in changes)
        significant_changes = [c for c in changes if c.significance >= self.significance_threshold]
        
        return {
            "changed": True,
            "hash_changed": True,
            "old_hash": old_hash,
            "new_hash": new_hash,
            "similarity_changed": similarity_changed,
            "total_changes": len(changes),
            "significant_changes": len(significant_changes),
            "total_significance": total_significance,
            "changes": [self._change_to_dict(c) for c in significant_changes],
            "summary": self._generate_change_summary(changes)
        }
    
    def _analyze_changes(self, old_content: str, new_content: str) -> List[ContentChange]:
        """Analyze detailed changes between content versions."""
        changes = []
        
        # Line-by-line diff
        old_lines = old_content.splitlines()
        new_lines = new_content.splitlines()
        
        differ = difflib.unified_diff(old_lines, new_lines, lineterm='')
        diff_lines = list(differ)
        
        if not diff_lines:
            return changes
        
        # Process diff output
        added_lines = 0
        removed_lines = 0
        modified_sections = []
        
        i = 0
        while i < len(diff_lines):
            line = diff_lines[i]
            
            if line.startswith('+++') or line.startswith('---'):
                i += 1
                continue
            
            if line.startswith('@@'):
                # Parse hunk header
                match = re.match(r'@@ -(\d+),?(\d*) \+(\d+),?(\d*) @@', line)
                if match:
                    old_start = int(match.group(1))
                    new_start = int(match.group(3))
                    modified_sections.append((old_start, new_start))
                i += 1
                continue
            
            if line.startswith('+') and not line.startswith('+++'):
                added_lines += 1
                content = line[1:]
                significance = self._calculate_line_significance(content)
                
                changes.append(ContentChange(
                    change_type="added",
                    old_value=None,
                    new_value=content,
                    location=f"line {i}",
                    significance=significance,
                    description=f"Added: {content[:50]}..."
                ))
            
            elif line.startswith('-') and not line.startswith('---'):
                removed_lines += 1
                content = line[1:]
                significance = self._calculate_line_significance(content)
                
                changes.append(ContentChange(
                    change_type="removed",
                    old_value=content,
                    new_value=None,
                    location=f"line {i}",
                    significance=significance,
                    description=f"Removed: {content[:50]}..."
                ))
            
            i += 1
        
        # Detect structural changes
        structural_changes = self._detect_structural_changes(old_content, new_content)
        changes.extend(structural_changes)
        
        return changes
    
    def _calculate_line_significance(self, line: str) -> float:
        """Calculate the significance of a line change."""
        line = line.strip()
        
        # Empty lines or whitespace
        if not line:
            return 0.0
        
        # Comments (various languages)
        if any(line.startswith(c) for c in ['#', '//', '/*', '*', '--']):
            return 0.2
        
        # Import/include statements
        if any(word in line.lower() for word in ['import', 'include', 'require', 'use']):
            return 0.7
        
        # Function/class definitions
        if any(word in line for word in ['def ', 'class ', 'function ', 'const ', 'let ', 'var ']):
            return 0.8
        
        # Headers in markdown
        if line.startswith('#'):
            return 0.6
        
        # URLs
        if 'http://' in line or 'https://' in line:
            return 0.5
        
        # Default significance
        return 0.4
    
    def _detect_structural_changes(self, old_content: str, new_content: str) -> List[ContentChange]:
        """Detect structural changes in content."""
        changes = []
        
        # Detect heading changes in markdown
        old_headings = re.findall(r'^(#{1,6})\s+(.+)$', old_content, re.MULTILINE)
        new_headings = re.findall(r'^(#{1,6})\s+(.+)$', new_content, re.MULTILINE)
        
        if old_headings != new_headings:
            changes.append(ContentChange(
                change_type="modified",
                old_value=str(old_headings),
                new_value=str(new_headings),
                location="document structure",
                significance=0.7,
                description="Document structure changed"
            ))
        
        # Detect code block changes
        old_code_blocks = len(re.findall(r'```[\s\S]*?```', old_content))
        new_code_blocks = len(re.findall(r'```[\s\S]*?```', new_content))
        
        if old_code_blocks != new_code_blocks:
            changes.append(ContentChange(
                change_type="modified",
                old_value=f"{old_code_blocks} code blocks",
                new_value=f"{new_code_blocks} code blocks",
                location="code blocks",
                significance=0.6,
                description=f"Code blocks changed from {old_code_blocks} to {new_code_blocks}"
            ))
        
        # Detect link changes
        old_links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', old_content)
        new_links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', new_content)
        
        if len(old_links) != len(new_links):
            changes.append(ContentChange(
                change_type="modified",
                old_value=f"{len(old_links)} links",
                new_value=f"{len(new_links)} links",
                location="links",
                significance=0.5,
                description=f"Number of links changed from {len(old_links)} to {len(new_links)}"
            ))
        
        return changes
    
    def _generate_change_summary(self, changes: List[ContentChange]) -> str:
        """Generate a human-readable summary of changes."""
        if not changes:
            return "No changes detected"
        
        added = sum(1 for c in changes if c.change_type == "added")
        removed = sum(1 for c in changes if c.change_type == "removed")
        modified = sum(1 for c in changes if c.change_type == "modified")
        
        summary_parts = []
        
        if added:
            summary_parts.append(f"{added} additions")
        if removed:
            summary_parts.append(f"{removed} deletions")
        if modified:
            summary_parts.append(f"{modified} modifications")
        
        significance = sum(c.significance for c in changes) / len(changes)
        
        if significance > 0.7:
            summary_parts.append("(major changes)")
        elif significance > 0.4:
            summary_parts.append("(moderate changes)")
        else:
            summary_parts.append("(minor changes)")
        
        return ", ".join(summary_parts)
    
    def _change_to_dict(self, change: ContentChange) -> Dict[str, any]:
        """Convert ContentChange to dictionary."""
        return {
            "type": change.change_type,
            "old_value": change.old_value,
            "new_value": change.new_value,
            "location": change.location,
            "significance": change.significance,
            "description": change.description
        }
    
    def get_visual_diff(self, old_content: str, new_content: str) -> str:
        """Generate a visual diff for display."""
        old_lines = old_content.splitlines()
        new_lines = new_content.splitlines()
        
        differ = difflib.unified_diff(
            old_lines,
            new_lines,
            fromfile='Previous Version',
            tofile='Current Version',
            lineterm=''
        )
        
        return '\n'.join(differ)


# Singleton instance
change_detector = ChangeDetector()


# Convenience functions
def detect_changes(old_content: str, new_content: str) -> Dict[str, any]:
    """Detect changes between two versions of content."""
    return change_detector.detect_changes(old_content, new_content)


def get_visual_diff(old_content: str, new_content: str) -> str:
    """Get visual diff between two versions."""
    return change_detector.get_visual_diff(old_content, new_content)


def is_significant_change(old_content: str, new_content: str, 
                         threshold: float = 0.1) -> bool:
    """Check if change is significant."""
    result = detect_changes(old_content, new_content)
    return result.get("total_significance", 0) >= threshold