"""Robust selector builders and heuristics."""
from typing import List, Dict, Any


def parse_selector_strategies(strategies: List[Any]) -> List[Dict[str, str]]:
    """Parse selector strategies from YAML format to internal format.
    
    Args:
        strategies: List of selector strategies from task YAML
        
    Returns:
        List of dicts with 'strategy' and 'query' keys
    """
    parsed = []
    
    for s in strategies:
        if isinstance(s, dict):
            # Format: {"aria": "Pricing"} or {"text": "Pricing"}
            for strategy, query in s.items():
                parsed.append({'strategy': strategy, 'query': query})
        elif isinstance(s, str):
            # Format: "aria: Pricing" or "role: link[name=/pricing/i]"
            if ':' in s:
                parts = s.split(':', 1)
                strategy = parts[0].strip()
                query = parts[1].strip()
                
                # Handle special formats like role: link[name=/pricing/i]
                if strategy == 'role':
                    # Convert to aria strategy
                    strategy = 'aria'
                    # Extract name from role syntax if present
                    if '[name=' in query:
                        import re
                        match = re.search(r'\[name=/?([^\]]+)\]?', query)
                        if match:
                            query = match.group(1).strip('/')
                
                parsed.append({'strategy': strategy, 'query': query})
    
    return parsed


def build_default_selectors(text: str) -> List[Dict[str, str]]:
    """Build default selector strategies for a given text.
    
    Args:
        text: Text to search for
        
    Returns:
        List of selector strategies
    """
    return [
        {'strategy': 'aria', 'query': text},
        {'strategy': 'text', 'query': text},
        {'strategy': 'css', 'query': f'a[href*="{text.lower()}"]'},
        {'strategy': 'xpath', 'query': f'//a[contains(translate(., "{text.upper()}", "{text.lower()}"), "{text.lower()}")]'}
    ]
