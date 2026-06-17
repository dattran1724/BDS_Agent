from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph
from app.graph.state import RealEstateAgentState
from app.graph.nodes import (
    extractor_node,
    missing_info_detector_node,
    clarification_node,
    persona_detector_node,
    goal_detector_node,
    strategist_node,
    writer_node,
    validator_node,
    editor_node,
    confirmation_node,
)


def route_after_missing_info(state: RealEstateAgentState) -> str:
    """
    Routes the workflow after missing info check.
    Bypasses clarification only if all required fields are present, sufficient
    recommended fields are collected, or force_proceed is requested.
    """
    if not state.force_proceed:
        if state.required_missing or state.completion_score < 0.71:
            return "clarification"
    return "persona_detector"


def route_after_persona_detector(state: RealEstateAgentState) -> str:
    """
    Routes the workflow after Persona Detector.
    If the target customer is vague (confidence < 0.7) or missing, routes back to clarification.
    """
    if not state.force_proceed:
        if state.persona_name is None:
            # Inject target_customer back into recommended_missing if it wasn't already there
            if "target_customer" not in state.recommended_missing:
                state.recommended_missing.append("target_customer")
            return "clarification"
    return "confirmation"


def route_after_validator(state: RealEstateAgentState) -> str:
    """
    Routes the workflow after validator check.
    If validation fails, routes back to 'writer' for revision.
    Otherwise, routes to 'editor'.
    """
    if state.validation_result == "FAIL":
        return "writer"
    return "editor"


def create_workflow():
    """
    Assembles and compiles the LangGraph workflow with the required state transitions,
    checkpointer for memory/persistence, and human-in-the-loop interrupt configurations.
    Uses RealEstateAgentState.
    """
    workflow = StateGraph(RealEstateAgentState)

    # 1. Register all nodes
    workflow.add_node("extractor", extractor_node)
    workflow.add_node("missing_info_detector", missing_info_detector_node)
    workflow.add_node("clarification", clarification_node)
    workflow.add_node("persona_detector", persona_detector_node)
    workflow.add_node("goal_detector", goal_detector_node)
    workflow.add_node("strategist", strategist_node)
    workflow.add_node("writer", writer_node)
    workflow.add_node("validator", validator_node)
    workflow.add_node("editor", editor_node)
    workflow.add_node("confirmation", confirmation_node)

    # 2. Define edge connections
    workflow.set_entry_point("extractor")
    
    # Extractor leads directly to Missing Info Detector
    workflow.add_edge("extractor", "missing_info_detector")
    
    # Conditional edge after Missing Info Detector:
    workflow.add_conditional_edges(
        "missing_info_detector",
        route_after_missing_info,
        {
            "clarification": "clarification",
            "persona_detector": "persona_detector"
        }
    )
    
    # Clarification node loops back to extractor to scan the user's new inputs
    workflow.add_edge("clarification", "extractor")
    
    # Persona Detector conditional routing (requires confidence >= 0.7)
    workflow.add_conditional_edges(
        "persona_detector",
        route_after_persona_detector,
        {
            "clarification": "clarification",
            "confirmation": "confirmation"
        }
    )
    
    # Confirmation leads to Goal detection and Strategist
    workflow.add_edge("confirmation", "goal_detector")
    workflow.add_edge("goal_detector", "strategist")
    
    # Strategist leads to Writer (pausing due to interrupt_after strategist)
    workflow.add_edge("strategist", "writer")
    
    # Writer leads to Validator
    workflow.add_edge("writer", "validator")
    
    # Conditional edge after Validator
    workflow.add_conditional_edges(
        "validator",
        route_after_validator,
        {
            "writer": "writer",
            "editor": "editor"
        }
    )
    
    # Editor leads to END (pausing due to interrupt_after editor for human review)
    workflow.add_edge("editor", END)

    # 3. Setup Checkpointer for thread tracking & state preservation
    memory = MemorySaver()

    # 4. Compile workflow specifying nodes after which to interrupt
    compiled_graph = workflow.compile(
        checkpointer=memory,
        interrupt_after=["clarification", "confirmation", "strategist", "editor"]
    )
    
    return compiled_graph
