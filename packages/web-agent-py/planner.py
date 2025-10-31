"""Task planning and decomposition."""
from typing import Dict, Any, List


class Planner:
    """Plan tasks and decompose into actions."""
    
    def __init__(self, task: Dict[str, Any]):
        """Initialize planner with task specification.
        
        Args:
            task: Task specification
        """
        self.task = task
        self.state = {
            'current_url': None,
            'current_title': None,
            'visited_urls': [],
            'completed_actions': []
        }
    
    def next_action(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Determine next action based on current state.
        
        Args:
            state: Current state of execution
            
        Returns:
            Next action to take
        """
        # Simple implementation - just follow the actions list
        # More sophisticated planning could use LLM or rule-based logic
        actions = self.task.get('actions', [])
        completed = len(state.get('completed_actions', []))
        
        if completed < len(actions):
            return actions[completed]
        
        return None
    
    def update_state(self, state: Dict[str, Any], action: Dict[str, Any], 
                     result: Dict[str, Any]) -> Dict[str, Any]:
        """Update state after action execution.
        
        Args:
            state: Current state
            action: Action that was executed
            result: Result of the action
            
        Returns:
            Updated state
        """
        new_state = state.copy()
        new_state['completed_actions'].append(action)
        
        if 'url' in result:
            new_state['current_url'] = result['url']
            if result['url'] not in new_state.get('visited_urls', []):
                new_state.setdefault('visited_urls', []).append(result['url'])
        
        return new_state
