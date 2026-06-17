from typing import Any, List, Optional
from pydantic import BaseModel, Field


class RealEstateAgentState(BaseModel):
    """
    Represents the shared memory state of the Real Estate AI Agent workflow.
    Tracks extracted listing info, strategist angles, draft/final content,
    and user feedback at each human-in-the-loop checkpoint.
    """
    user_input: str = Field(
        default="",
        description="The raw input or prompt provided by the real estate agent."
    )
    property_type: Optional[str] = Field(
        default=None,
        description="The type of real estate property (e.g. Apartment, Villa, Townhouse)."
    )
    location: Optional[str] = Field(
        default=None,
        description="The geographical location, neighborhood, or address of the property."
    )
    area: Optional[str] = Field(
        default=None,
        description="The area/size of the property (e.g. 120 sqm, 2000 sqft) or district/region."
    )
    price: Optional[str] = Field(
        default=None,
        description="The listing price, pricing details, or price range of the property."
    )
    legal_status: Optional[str] = Field(
        default=None,
        description="The ownership status or legal document status (e.g. Pink Book, Red Book, SPA)."
    )
    financial_policy: Optional[str] = Field(
        default=None,
        description="Financial options, loan support percentages, down payment schemes, or installment policies."
    )
    amenities: Optional[str] = Field(
        default=None,
        description="Amenities associated with the property (e.g. Pool, Gym, Park, Garage)."
    )
    
    # Classification input fields
    target_customer: Optional[str] = Field(
        default=None,
        description="The primary target customer persona or buyer demographic for the post."
    )
    marketing_goal: Optional[str] = Field(
        default=None,
        description="The marketing/business objective of the Facebook post (e.g. Lead Gen, Brand Awareness, Just Sold)."
    )
    
    # Persona Detector Output Fields
    persona_name: Optional[str] = Field(
        default=None,
        description="The classified persona category (e.g. Young Family, Luxury Buyer)."
    )
    pain_points: Optional[List[str]] = Field(
        default=None,
        description="Core pain points identified for the target persona."
    )
    decision_factors: Optional[List[str]] = Field(
        default=None,
        description="Key factors influencing the persona's buying decision."
    )
    
    # Goal Detector Output Fields
    goal_name: Optional[str] = Field(
        default=None,
        description="The mapped goal category (e.g. Lead Generation, Quick Sale)."
    )
    recommended_framework: Optional[str] = Field(
        default=None,
        description="Recommended copywriting framework (e.g. AIDA, PAS) for the post."
    )
    recommended_cta_style: Optional[str] = Field(
        default=None,
        description="Recommended Call to Action style based on the goal."
    )

    missing_fields: List[str] = Field(
        default_factory=list,
        description="List of required property details/fields that are missing from the inputs."
    )
    required_missing: List[str] = Field(
        default_factory=list,
        description="List of missing required fields."
    )
    recommended_missing: List[str] = Field(
        default_factory=list,
        description="List of missing recommended fields."
    )
    completion_score: float = Field(
        default=0.0,
        description="Calculated information completeness score."
    )
    clarification_round: int = Field(
        default=0,
        description="Counter for clarification node execution loops."
    )
    persona_confidence: float = Field(
        default=0.0,
        description="Confidence score for persona detection."
    )
    hallucinations_detected: List[str] = Field(
        default_factory=list,
        description="List of hallucinated facts flagged in the generated content."
    )
    force_proceed: bool = Field(
        default=False,
        description="Bypass flag to allow proceeding with incomplete info."
    )
    
    # Strategist Node output fields
    content_angles: List[Any] = Field(
        default_factory=list,
        description="The three generated content angles/ideas for the Facebook post."
    )
    recommended_angle_id: Optional[int] = Field(
        default=None,
        description="The ID of the recommended strategic angle."
    )
    selected_angle: Optional[str] = Field(
        default=None,
        description="The selected content angle option chosen by the user."
    )
    
    draft_content: Optional[str] = Field(
        default=None,
        description="The initial draft copy of the Facebook post written by the Writer Node."
    )
    
    # Validator Node output fields
    validation_result: Optional[str] = Field(
        default=None,
        description="Result of the validation node (e.g. PASS, FAIL)."
    )
    issues_found: List[str] = Field(
        default_factory=list,
        description="List of policy or constraint issues detected in the draft content."
    )
    validation_attempts: int = Field(
        default=0,
        description="Counter for tracking the number of times writer-validator loop has executed."
    )

    
    final_content: Optional[str] = Field(
        default=None,
        description="The final polished and validated Facebook post copy written by the Editor Node."
    )
    revision_request: Optional[str] = Field(
        default=None,
        description="Feedback, revision comments, or change requests supplied by the user."
    )
    conversation_history: List[Any] = Field(
        default_factory=list,
        description="History of conversation messages, actions, or events recorded during HITL cycles."
    )
