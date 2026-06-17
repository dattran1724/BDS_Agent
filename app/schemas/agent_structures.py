from typing import List, Literal, Optional
from pydantic import BaseModel, Field


class PersonaDetectionResult(BaseModel):
    """
    Structured classification result for persona detector node.
    """
    persona_name: Optional[Literal[
        "Gia đình trẻ",
        "Nhà đầu tư F0",
        "Nhà đầu tư dài hạn",
        "Nhà đầu tư cho thuê",
        "Người mua ở thực",
        "Người mua cao cấp",
        "Người mua nghỉ dưỡng"
    ]] = Field(
        default=None,
        description="Chân dung khách hàng mục tiêu."
    )
    confidence: float = Field(
        default=0.0,
        description="Độ tin cậy của việc nhận diện (0.0 đến 1.0)."
    )
    pain_points: List[str] = Field(
        default_factory=list,
        description="Key concerns or challenges this persona faces."
    )
    decision_factors: List[str] = Field(
        default_factory=list,
        description="Top factors driving this persona's buying decision."
    )


class GoalDetectionResult(BaseModel):
    """
    Structured classification result for goal detector node.
    """
    goal_name: Literal[
        "Tạo inbox",
        "Bán gấp",
        "Giới thiệu dự án",
        "Xây niềm tin",
        "Chăm sóc khách cũ"
    ] = Field(
        ...,
        description="Mục tiêu của bài viết."
    )
    recommended_framework: Literal["PAS", "AIDA", "FAB", "SSS"] = Field(
        ...,
        description="The recommended copywriting framework aligned with the goal."
    )
    recommended_cta_style: str = Field(
        ...,
        description="The recommended Call to Action style (e.g., DM for details, Register link, Phone number call)."
    )


class StrategicAngle(BaseModel):
    """
    Individual strategic content angle definition.
    """
    id: int = Field(..., description="Unique ID of the angle (1, 2, or 3).")
    title: str = Field(..., description="Strategic angle title in Vietnamese.")
    reason: str = Field(..., description="Reason why this angle fits the customer persona/goal.")
    core_message: str = Field(..., description="The core message or value proposition for the buyer.")
    key_selling_point: str = Field(..., description="The strongest selling point/feature highlighted.")
    score: float = Field(..., description="Recommendation score out of 10 (e.g. 9.5).")
    framework: Literal["PAS", "AIDA", "FAB", "SSS"] = Field(
        ...,
        description="Copywriting framework to build the post (INTERNAL ONLY)."
    )


class StrategistAnglesResult(BaseModel):
    """
    Strategist node output containing exactly 3 distinct strategic angles and a recommendation.
    """
    recommended_angle_id: int = Field(..., description="The ID of the recommended angle (1, 2, or 3).")
    angles: List[StrategicAngle] = Field(
        ...,
        description="List containing exactly 3 clearly different strategic content angles."
    )


class HallucinationCheckResult(BaseModel):
    """
    Structured validation result for detecting hallucinated facts.
    """
    hallucinations: List[str] = Field(
        default_factory=list,
        description="List of hallucinated facts/claims found in the generated post that are not present in the input details."
    )
