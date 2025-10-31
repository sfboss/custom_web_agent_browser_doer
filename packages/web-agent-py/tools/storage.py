"""Evidence pack writer, hashing, and signing."""
import json
import hashlib
import os
from pathlib import Path
from typing import Dict, Any, List
import subprocess


def sha256_file(filepath: str) -> str:
    """Calculate SHA256 hash of a file.
    
    Args:
        filepath: Path to file
        
    Returns:
        Hex string of SHA256 hash
    """
    h = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()


def get_git_commit() -> str:
    """Get current git commit hash.
    
    Returns:
        Git commit hash or 'unknown' if not in git repo
    """
    try:
        result = subprocess.run(
            ['git', 'rev-parse', 'HEAD'],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return 'unknown'


class EvidencePack:
    """Manager for evidence pack creation and organization."""
    
    def __init__(self, session_dir: Path):
        """Initialize evidence pack.
        
        Args:
            session_dir: Directory for this session's evidence
        """
        self.session_dir = session_dir
        self.evidence_dir = session_dir / 'evidence'
        self.selectors_data: Dict[str, Any] = {}
        self.reasoning_log: List[Dict[str, Any]] = []
        
        # Create directories
        self.evidence_dir.mkdir(parents=True, exist_ok=True)
    
    def add_selector_attempt(self, action_id: str, name: str, attempts: List[Dict], final: Dict):
        """Record selector attempts for an action.
        
        Args:
            action_id: ID of the action
            name: Name of the selector
            attempts: List of attempted selectors
            final: Final successful selector
        """
        self.selectors_data[action_id] = {
            'name': name,
            'attempts': attempts,
            'final': final
        }
    
    def add_reasoning(self, step: int, action: str, thought: str, result: str):
        """Add reasoning step to log.
        
        Args:
            step: Step number
            action: Action taken
            thought: Reasoning/thought process
            result: Result of the action
        """
        import time
        self.reasoning_log.append({
            'ts': time.time(),
            'step': step,
            'action': action,
            'thought': thought,
            'result': result
        })
    
    def save_selectors(self):
        """Save selectors.json file."""
        selectors_path = self.evidence_dir / 'selectors.json'
        with open(selectors_path, 'w') as f:
            json.dump(self.selectors_data, f, indent=2)
    
    def save_reasoning(self):
        """Save reasoning.jsonl file."""
        reasoning_path = self.session_dir / 'reasoning.jsonl'
        with open(reasoning_path, 'w') as f:
            for entry in self.reasoning_log:
                f.write(json.dumps(entry) + '\n')
    
    def save_manifest(self, task_id: str, start_time: float, end_time: float):
        """Save run.json manifest with checksums.
        
        Args:
            task_id: ID of the task
            start_time: Task start timestamp
            end_time: Task end timestamp
        """
        # Collect evidence files
        evidence_files = sorted([str(p.relative_to(self.session_dir)) 
                                for p in self.evidence_dir.glob('*')])
        
        # Calculate checksums
        checksums = {}
        for f in evidence_files:
            full_path = self.session_dir / f
            if full_path.is_file():
                checksums[f] = sha256_file(str(full_path))
        
        manifest = {
            'task_id': task_id,
            'git_commit': get_git_commit(),
            'start_time': start_time,
            'end_time': end_time,
            'duration_seconds': end_time - start_time,
            'evidence_files': evidence_files,
            'checksums': checksums
        }
        
        manifest_path = self.session_dir / 'run.json'
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)
    
    def mark_success(self):
        """Create success.flag file."""
        flag_path = self.session_dir / 'success.flag'
        flag_path.touch()
    
    def save_all(self, task_id: str, start_time: float, end_time: float, success: bool = True):
        """Save all evidence pack components.
        
        Args:
            task_id: ID of the task
            start_time: Task start timestamp
            end_time: Task end timestamp
            success: Whether task was successful
        """
        self.save_selectors()
        self.save_reasoning()
        self.save_manifest(task_id, start_time, end_time)
        
        if success:
            self.mark_success()
