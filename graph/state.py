from typing import TypedDict, List, Dict, Any, Optional

class StoryState(TypedDict):
    """
    State dùng chung cho luồng Agentic LangGraph.
    """
    user_input: str
    age_group: str
    art_style: str
    storyboard: Dict[str, Any]
    scenes: List[Dict[str, Any]]
    evaluation: Dict[str, Any]
    retry_count: int
    status: str
    error: Optional[str]
