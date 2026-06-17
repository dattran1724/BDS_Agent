from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class StartAgentRequest(BaseModel):
    """
    Payload to trigger a new Facebook post generation flow.
    """
    user_input: str = Field(
        ...,
        description="Raw listing notes, details, features, or specific instructions for the post."
    )


class ClarifyResponseRequest(BaseModel):
    """
    Payload for submitting missing details to resume the workflow.
    """
    clarification_response: str = Field(
        ...,
        description="The agent's text response providing the requested missing information."
    )
    # Optional fields to directly update state variables
    area: Optional[str] = Field(None, description="Direct update for property area/size.")
    legal_status: Optional[str] = Field(None, description="Direct update for property legal status.")
    financial_policy: Optional[str] = Field(None, description="Direct update for financial policy.")
    price: Optional[str] = Field(None, description="Direct update for property price.")
    property_type: Optional[str] = Field(None, description="Direct update for property type.")
    location: Optional[str] = Field(None, description="Direct update for property location.")
    target_customer: Optional[str] = Field(None, description="Direct update for target customer.")
    marketing_goal: Optional[str] = Field(None, description="Direct update for marketing goal.")
    amenities: Optional[str] = Field(None, description="Direct update for property amenities.")
    force_proceed: Optional[bool] = Field(False, description="Whether to bypass recommended information completeness checks.")


class ConfirmInfoRequest(BaseModel):
    """
    Payload for confirming collected information or requesting modifications.
    """
    confirmed: bool = Field(
        ...,
        description="Set to true to confirm and proceed to strategy building, false if requesting changes."
    )
    modification_request: Optional[str] = Field(
        default=None,
        description="The user's message detailing what information to change."
    )
    property_type: Optional[str] = Field(None, description="Direct edit for property type.")
    location: Optional[str] = Field(None, description="Direct edit for location.")
    price: Optional[str] = Field(None, description="Direct edit for price.")
    area: Optional[str] = Field(None, description="Direct edit for area.")
    legal_status: Optional[str] = Field(None, description="Direct edit for legal status.")
    financial_policy: Optional[str] = Field(None, description="Direct edit for financial policy.")
    target_customer: Optional[str] = Field(None, description="Direct edit for target customer.")
    marketing_goal: Optional[str] = Field(None, description="Direct edit for marketing goal.")
    amenities: Optional[str] = Field(None, description="Direct edit for amenities.")



class SelectAngleRequest(BaseModel):
    """
    Payload for choosing one of the three generated content angles.
    """
    selected_angle: str = Field(
        ...,
        description="The selected content angle string."
    )


class ApprovePostRequest(BaseModel):
    """
    Payload for final approval or feedback on the post draft.
    """
    approved: bool = Field(
        ...,
        description="Set to true if approved, false if feedback/revisions are requested."
    )
    revision_request: Optional[str] = Field(
        default=None,
        description="Feedback, revision comments, or change requests if not approved."
    )
    final_content: Optional[str] = Field(
        default=None,
        description="The manually edited post content, if the user made adjustments."
    )


class AgentStateResponse(BaseModel):
    """
    Structured response returning the thread context, current state data, and the next node to run.
    """
    thread_id: str = Field(..., description="Unique identifier for the session/thread.")
    next_step: Optional[str] = Field(
        default=None,
        description="The name of the next node awaiting execution. If None, the workflow has finished."
    )
    state: Dict[str, Any] = Field(
        ...,
        description="The complete current state parameters of the agent workflow."
    )
