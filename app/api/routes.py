import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from langgraph.graph.state import CompiledStateGraph

from app.dependencies import get_workflow, get_llm
from app.schemas.api_models import (
    AgentStateResponse,
    ApprovePostRequest,
    ClarifyResponseRequest,
    ConfirmInfoRequest,
    SelectAngleRequest,
    StartAgentRequest,
)
router = APIRouter(prefix="/api/agent", tags=["AI Agent Router"])


def clean_state_for_api(state_values: dict) -> dict:
    """
    Clones the state values and strips out internal copywriting frameworks
    from the content_angles field so they are never exposed to the public API.
    """
    if not state_values:
        return {}
    cleaned = dict(state_values)
    if "content_angles" in cleaned and cleaned["content_angles"]:
        cleaned_angles = []
        for angle in cleaned["content_angles"]:
            angle_data = dict(angle) if isinstance(angle, dict) else angle.model_dump() if hasattr(angle, "model_dump") else {}
            if angle_data:
                angle_data.pop("framework", None)
                cleaned_angles.append(angle_data)
        cleaned["content_angles"] = cleaned_angles
    return cleaned


@router.post("/start", response_model=AgentStateResponse, status_code=status.HTTP_201_CREATED)
async def start_agent_workflow(
    request: StartAgentRequest,
    graph: CompiledStateGraph = Depends(get_workflow),
    llm = Depends(get_llm)
):
    """
    Initializes a new workflow thread with raw user_input and runs the agent graph
    until the first interrupt point (after Clarification Node).
    """
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id, "llm": llm}}
    
    # Initialize the graph with user_input and an empty history
    initial_state = {
        "user_input": request.user_input,
        "conversation_history": [{"role": "user", "content": request.user_input}]
    }
    
    try:
        # Run graph execution until it hits the first interrupt ("clarification" node)
        for _ in graph.stream(initial_state, config):
            pass
        
        # Retrieve the paused state
        current_state = graph.get_state(config)
        
        return AgentStateResponse(
            thread_id=thread_id,
            next_step=current_state.next[0] if current_state.next else None,
            state=clean_state_for_api(current_state.values)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start workflow: {str(e)}"
        )


@router.get("/state/{thread_id}", response_model=AgentStateResponse)
async def get_agent_state(
    thread_id: str,
    graph: CompiledStateGraph = Depends(get_workflow)
):
    """
    Retrieves the current state and next step details for a specific thread ID.
    """
    config = {"configurable": {"thread_id": thread_id}}
    current_state = graph.get_state(config)
    
    if not current_state.values:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Thread session '{thread_id}' not found or has no active state."
        )
        
    return AgentStateResponse(
        thread_id=thread_id,
        next_step=current_state.next[0] if current_state.next else None,
        state=clean_state_for_api(current_state.values)
    )


@router.post("/respond-clarification/{thread_id}", response_model=AgentStateResponse)
async def respond_clarification(
    thread_id: str,
    request: ClarifyResponseRequest,
    graph: CompiledStateGraph = Depends(get_workflow),
    llm = Depends(get_llm)
):
    """
    Submits user clarification response to resolve missing information,
    and resumes the workflow until the next interrupt (after Strategist Node).
    """
    config = {"configurable": {"thread_id": thread_id, "llm": llm}}
    current_state = graph.get_state(config)
    
    if not current_state.values:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Thread session '{thread_id}' not found."
        )
    
    # Verify we are indeed waiting at the clarification interrupt point (next node is extractor)
    if not current_state.next or current_state.next[0] != "extractor":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Agent is not expecting clarification. Current next step is: {current_state.next}"
        )

    try:
        # Get existing history and append the user response
        history = current_state.values.get("conversation_history", []) or []
        updated_history = list(history) + [{"role": "user", "content": request.clarification_response}]
        
        # Prepare state updates for resuming
        updates = {
            "conversation_history": updated_history,
            "user_input": request.clarification_response,
            "force_proceed": request.force_proceed or False
        }
        
        # Merge manual field overrides from the quick-edit panel if provided
        fields = [
            "property_type", "location", "area", "price", "legal_status",
            "financial_policy", "amenities", "target_customer", "marketing_goal"
        ]
        for field in fields:
            req_val = getattr(request, field, None)
            if req_val is not None:
                updates[field] = req_val

        # Update state at clarification node
        graph.update_state(
            config,
            updates,
            as_node="clarification"
        )
        
        # Resume execution: stream(None, ...) signals resuming from current checkpoints
        for _ in graph.stream(None, config):
            pass
            
        updated_state = graph.get_state(config)
        
        return AgentStateResponse(
            thread_id=thread_id,
            next_step=updated_state.next[0] if updated_state.next else None,
            state=clean_state_for_api(updated_state.values)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to resume workflow after clarification: {str(e)}"
        )


@router.post("/confirm-info/{thread_id}", response_model=AgentStateResponse)
async def confirm_info(
    thread_id: str,
    request: ConfirmInfoRequest,
    graph: CompiledStateGraph = Depends(get_workflow),
    llm = Depends(get_llm)
):
    """
    Submits user confirmation of the collected information.
    If confirmed, resumes to Strategy building. 
    If not, loops back to Extractor with the modification request.
    """
    config = {"configurable": {"thread_id": thread_id, "llm": llm}}
    current_state = graph.get_state(config)
    
    if not current_state.values:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Thread session '{thread_id}' not found."
        )
        
    # Verify we are at the confirmation interrupt
    if not current_state.next or current_state.next[0] != "goal_detector":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Agent is not expecting confirmation. Current next step is: {current_state.next}"
        )

    try:
        if request.confirmed:
            # Check for direct edits in the request and update state before resuming
            updates = {}
            fields_to_check = [
                "property_type", "location", "price", "area", 
                "legal_status", "financial_policy", "target_customer", 
                "marketing_goal", "amenities"
            ]
            for field in fields_to_check:
                val = getattr(request, field, None)
                if val is not None: # Note: empty string allows clearing a field
                    updates[field] = val
            
            if updates:
                graph.update_state(config, updates)

            # Simply resume the execution to goal_detector
            for _ in graph.stream(None, config):
                pass
        else:
            # User wants to modify info. Route back to extractor.
            history = current_state.values.get("conversation_history", []) or []
            updated_history = list(history) + [{"role": "user", "content": request.modification_request}]
            
            updates = {
                "conversation_history": updated_history,
                "user_input": request.modification_request
            }
            
            # Update state as if we just finished clarification node, so it transitions to extractor
            graph.update_state(
                config,
                updates,
                as_node="clarification"
            )
            
            # Resume execution (it will flow clarification -> extractor -> ...)
            for _ in graph.stream(None, config):
                pass
                
        updated_state = graph.get_state(config)
        
        return AgentStateResponse(
            thread_id=thread_id,
            next_step=updated_state.next[0] if updated_state.next else None,
            state=clean_state_for_api(updated_state.values)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process confirmation: {str(e)}"
        )


@router.post("/select-angle/{thread_id}", response_model=AgentStateResponse)
async def select_angle(
    thread_id: str,
    request: SelectAngleRequest,
    graph: CompiledStateGraph = Depends(get_workflow),
    llm = Depends(get_llm)
):
    """
    Submits the selected content angle chosen by the user, and resumes
    the workflow until the final interrupt (after Editor Node).
    """
    config = {"configurable": {"thread_id": thread_id, "llm": llm}}
    current_state = graph.get_state(config)
    
    if not current_state.values:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Thread session '{thread_id}' not found."
        )
        
    # Validate selected angle exists in angles generated
    angles = current_state.values.get("content_angles", [])
    if not angles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No content angles have been generated yet for this thread."
        )
        
    angle_titles = [angle.get("title") if isinstance(angle, dict) else getattr(angle, "title", "") for angle in angles]
    if request.selected_angle not in angle_titles:
        # Check if the user selected by ID (e.g. "1", "2", "3")
        angle_ids = [str(angle.get("id")) if isinstance(angle, dict) else str(getattr(angle, "id", "")) for angle in angles]
        if request.selected_angle in angle_ids:
            # Map selected_angle ID back to the corresponding title
            for angle in angles:
                aid = angle.get("id") if isinstance(angle, dict) else getattr(angle, "id", None)
                if str(aid) == request.selected_angle:
                    request.selected_angle = angle.get("title") if isinstance(angle, dict) else getattr(angle, "title", "")
                    break
        else:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Selected angle '{request.selected_angle}' is invalid. Choose from: {angle_titles}"
            )

    try:
        # Get existing history and append the user's angle selection choice
        history = current_state.values.get("conversation_history", []) or []
        updated_history = list(history) + [{"role": "user", "content": f"Tôi chọn hướng tiếp cận: {request.selected_angle}"}]
        
        # Update state with selected angle
        graph.update_state(
            config,
            {
                "selected_angle": request.selected_angle,
                "conversation_history": updated_history
            },
            as_node="strategist"
        )
        
        # Resume execution
        for _ in graph.stream(None, config):
            pass
            
        updated_state = graph.get_state(config)
        
        return AgentStateResponse(
            thread_id=thread_id,
            next_step=updated_state.next[0] if updated_state.next else None,
            state=clean_state_for_api(updated_state.values)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to resume workflow after angle selection: {str(e)}"
        )


@router.post("/approve-post/{thread_id}", response_model=AgentStateResponse)
async def approve_post(
    thread_id: str,
    request: ApprovePostRequest,
    graph: CompiledStateGraph = Depends(get_workflow),
    llm = Depends(get_llm)
):
    """
    Finalizes the workflow by approving the generated post or submitting revision request
    feedback to finish the agent run.
    """
    config = {"configurable": {"thread_id": thread_id, "llm": llm}}
    current_state = graph.get_state(config)
    
    if not current_state.values:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Thread session '{thread_id}' not found."
        )
        
    # Verify we are at the end/editor interrupt
    if current_state.next:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Agent is not expecting final approval. Current next step is: {current_state.next}"
        )

    try:
        history = current_state.values.get("conversation_history", []) or []
        feedback_content = request.revision_request or "Approved post."
        updated_history = list(history) + [{"role": "user", "type": "feedback", "content": feedback_content}]

        updates = {
            "conversation_history": updated_history,
            "revision_request": request.revision_request
        }
        
        if request.final_content is not None:
            updates["final_content"] = request.final_content
        
        if request.revision_request:
            # Prepare state for editor node
            from app.graph.nodes import editor_node
            from app.graph.state import RealEstateAgentState
            
            state_dict = dict(current_state.values)
            if request.final_content is not None:
                state_dict["final_content"] = request.final_content
            state_dict["revision_request"] = request.revision_request
            state_obj = RealEstateAgentState(**state_dict)
            
            # Execute editor node
            editor_result = editor_node(state_obj, config)
            updates["final_content"] = editor_result["final_content"]
            
        graph.update_state(
            config,
            updates,
            as_node="editor"
        )
        
        # Resume to let the workflow complete its run to END
        for _ in graph.stream(None, config):
            pass
            
        updated_state = graph.get_state(config)
        
        return AgentStateResponse(
            thread_id=thread_id,
            next_step=updated_state.next[0] if updated_state.next else None,
            state=clean_state_for_api(updated_state.values)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to finalise workflow approval: {str(e)}"
        )
