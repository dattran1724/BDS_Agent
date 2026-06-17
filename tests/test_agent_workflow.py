import pytest
from fastapi.testclient import TestClient
from typing import Any

from app.main import app
from app.dependencies import get_llm
from app.schemas.extracted_property import ExtractedPropertyDetails
from app.schemas.agent_structures import (
    PersonaDetectionResult,
    GoalDetectionResult,
    StrategistAnglesResult,
    StrategicAngle,
)
from langchain_core.runnables import RunnableLambda

# --- MOCK LLM IMPLEMENTATION USING RUNNABLELAMBDA ---

class MockAIMessage:
    def __init__(self, content: str):
        self.content = content


class MockStructuredLLM(RunnableLambda):
    def __init__(self, schema):
        self.schema = schema
        super().__init__(self._mock_invoke)
        
    def _mock_invoke(self, input_data: Any) -> Any:
        name = self.schema.__name__
        if name == "ExtractedPropertyDetails":
            # Return missing legal_status and area to trigger clarification node
            return self.schema(
                property_type="Luxury Villa",
                location="123 Maple Heights, Austin, TX",
                price="$1,250,000",
                amenities="Swimming Pool, Large Backyard",
                legal_status=None,
                area=None,
                financial_policy=None
            )
        elif name == "PersonaDetectionResult":
            return self.schema(
                persona_name="Người mua cao cấp",
                confidence=0.95,
                pain_points=["Privacy concern", "High price volatility"],
                decision_factors=["Premium locations", "Security"]
            )
        elif name == "GoalDetectionResult":
            return self.schema(
                goal_name="Tạo inbox",
                recommended_framework="AIDA",
                recommended_cta_style="Hotline/Inbox direct message"
            )
        elif name == "StrategistAnglesResult":
            return self.schema(
                recommended_angle_id=1,
                angles=[
                    StrategicAngle(id=1, title="Angle 1", reason="Reason 1", core_message="Lifestyle Focus", key_selling_point="KSP 1", score=9.5, framework="AIDA"),
                    StrategicAngle(id=2, title="Angle 2", reason="Reason 2", core_message="Investment Focus", key_selling_point="KSP 2", score=8.8, framework="PAS"),
                    StrategicAngle(id=3, title="Angle 3", reason="Reason 3", core_message="Urgency Focus", key_selling_point="KSP 3", score=8.2, framework="FAB")
                ]
            )
        return self.schema()


class MockLLM(RunnableLambda):
    def __init__(self, simulate_fail_once: bool = False):
        self.simulate_fail_once = simulate_fail_once
        self.call_count = 0
        super().__init__(self._mock_invoke)

    def with_structured_output(self, schema, **kwargs):
        return MockStructuredLLM(schema)
        
    def _mock_invoke(self, input_data: Any) -> Any:
        self.call_count += 1
        prompt_text = str(input_data)
        
        # If clarification prompt
        if "missing fields" in prompt_text.lower() or "clarify" in prompt_text.lower() or "vòng hội thoại" in prompt_text.lower():
            return MockAIMessage("### Please Clarify:\n- What is the area of the villa?\n- What is the legal status?")
            
        # If editor prompt
        if "revision request" in prompt_text.lower():
            return MockAIMessage("🔥 CƠ HỘI ĐẦU TƯ BIỆT THỰ LUXURY VILLA (ĐÃ CHỈNH SỬA) 🔥\n\nVị trí: 123 Maple Heights, Austin, TX\nGiá: $1,250,000\nPháp lý: Sổ hồng chính chủ\n\nBể bơi riêng đẳng cấp, liên hệ hotline 0909123456 ngay!")

        # If writer prompt
        if self.simulate_fail_once and self.call_count == 1:
            # Generate invalid draft post: contains banned phrase "cam kết 100%" and misses price info
            return MockAIMessage("Cần bán căn biệt thự đẹp tại Maple Heights, sổ hồng chính chủ. Chúng tôi cam kết 100% hài lòng. Click ngay!")
            
        # Standard valid post (contains price, location, legal status, and CTA; no banned phrases)
        return MockAIMessage("🔥 CƠ HỘI ĐẦU TƯ BIỆT THỰ LUXURY VILLA 🔥\n\nVị trí: 123 Maple Heights, Austin, TX\nGiá: $1,250,000\nPháp lý: Sổ hồng chính chủ\n\nBể bơi riêng đẳng cấp, liên hệ hotline 0909123456 ngay!")


# Inject mock LLM provider by overriding get_llm
app.dependency_overrides[get_llm] = lambda: MockLLM(simulate_fail_once=False)

client = TestClient(app)


# --- UNIT & INTEGRATION TESTS ---

def test_health_check():
    """
    Verifies that the server health check is responsive.
    """
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "service": "bds-agent-backend"
    }


def test_complete_human_in_the_loop_workflow():
    """
    Tests the complete 3-stage human-in-the-loop workflow using mock LLM:
    1. Start workflow -> halts at clarification interrupt.
    2. Respond clarification -> halts at selected angle interrupt.
    3. Select angle -> halts at final editor review interrupt.
    4. Approve post -> completes and moves to END.
    """
    # --- STAGE 1: Start Agent ---
    payload = {"user_input": "Biệt thự cao cấp Austin, TX, giá 1.25M USD, bể bơi lớn."}
    response = client.post("/api/agent/start", json=payload)
    assert response.status_code == 201
    
    data = response.json()
    thread_id = data["thread_id"]
    assert thread_id is not None
    assert data["next_step"] == "extractor"
    
    state = data["state"]
    assert state["user_input"] == payload["user_input"]
    assert state["property_type"] == "Luxury Villa"
    assert "area" in state["missing_fields"]
    assert len(state["conversation_history"]) > 0
    assert "clarify" in state["conversation_history"][-1]["content"].lower()

    # --- STAGE 2: Submit Clarification ---
    clarify_payload = {
        "clarification_response": "Cần bán biệt thự 120m2, sổ hồng chính chủ, hướng tới người mua cao cấp để tạo inbox.",
        "area": "120 sqm",
        "legal_status": "Pink Book",
        "target_customer": "Người mua cao cấp",
        "marketing_goal": "Tạo inbox"
    }
    response = client.post(f"/api/agent/respond-clarification/{thread_id}", json=clarify_payload)
    assert response.status_code == 200
    
    data = response.json()
    assert data["next_step"] == "writer"
    
    state = data["state"]
    assert state["area"] == clarify_payload["area"]
    assert state["legal_status"] == clarify_payload["legal_status"]
    assert len(state["content_angles"]) == 3
    assert state["persona_name"] == "Người mua cao cấp"
    assert state["goal_name"] == "Tạo inbox"

    # --- STAGE 3: Select Content Angle ---
    selected_angle = state["content_angles"][1]["title"]
    angle_payload = {"selected_angle": selected_angle}
    response = client.post(f"/api/agent/select-angle/{thread_id}", json=angle_payload)
    assert response.status_code == 200
    
    data = response.json()
    assert data["next_step"] is None  # Paused after editor, next step to execute is END (represented as None)
    
    state = data["state"]
    assert state["selected_angle"] == selected_angle
    assert state["draft_content"] is not None
    assert state["final_content"] is not None
    assert state["validation_result"] == "PASS"
    assert len(state["issues_found"]) == 0

    # --- STAGE 4: Final Approval with Revision ---
    approve_payload = {"approved": False, "revision_request": "Chỉnh sửa lại thành sổ hồng chính chủ giúp tôi."}
    response = client.post(f"/api/agent/approve-post/{thread_id}", json=approve_payload)
    assert response.status_code == 200
    
    data = response.json()
    assert data["next_step"] is None
    
    state = data["state"]
    assert state["revision_request"] == approve_payload["revision_request"]
    assert "chỉnh sửa" in state["final_content"].lower()


def test_validator_failure_triggers_rewrite():
    """
    Tests the validation loop:
    If ValidatorNode detects issues (e.g. banned phrases/missing price),
    the workflow automatically reroutes back to the WriterNode.
    """
    # Use a custom Lambda override to simulate validation fail on first writer call
    app.dependency_overrides[get_llm] = lambda: MockLLM(simulate_fail_once=True)
    
    payload = {"user_input": "Bán biệt thự cao cấp."}
    response = client.post("/api/agent/start", json=payload)
    thread_id = response.json()["thread_id"]
    
    # Respond clarification
    client.post(f"/api/agent/respond-clarification/{thread_id}", json={
        "clarification_response": "Diện tích 120m2, sổ hồng chính chủ, hướng tới người mua cao cấp để tạo inbox.",
        "area": "120 sqm",
        "legal_status": "Sổ hồng chính chủ",
        "target_customer": "Người mua cao cấp",
        "marketing_goal": "Tạo inbox"
    })
    
    # Select angle (this runs writer -> validator -> loops back to writer because of failure -> validator -> passes -> editor -> pause)
    response = client.post(f"/api/agent/select-angle/{thread_id}", json={"selected_angle": "Angle 1"})
    assert response.status_code == 200
    data = response.json()
    state = data["state"]
    
    # Should finally pass because the second writer invocation returns valid post
    assert state["validation_result"] == "PASS"
    assert len(state["issues_found"]) == 0
    assert "luxury" in state["final_content"].lower()
    
    # Clean up overrides
    app.dependency_overrides[get_llm] = lambda: MockLLM(simulate_fail_once=False)
