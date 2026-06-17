import json
import logging
import os
from typing import Any, Dict, List
from langchain_core.runnables import RunnableConfig
from langchain_core.prompts import ChatPromptTemplate
from app.graph.state import RealEstateAgentState
from app.schemas.extracted_property import ExtractedPropertyDetails
from app.schemas.agent_structures import (
    PersonaDetectionResult,
    GoalDetectionResult,
    StrategistAnglesResult,
    HallucinationCheckResult,
)

logger = logging.getLogger("agent.nodes")

PROMPTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "prompts")

def load_prompt(filename: str) -> str:
    path = os.path.join(PROMPTS_DIR, filename)
    with open(path, "r", encoding="utf-8") as f:
        return f.read().strip()


def extractor_node(state: RealEstateAgentState, config: RunnableConfig) -> Dict[str, Any]:
    """
    Reads raw user text and extracts property details using Pydantic structured output.
    Returns only the extracted fields. Missing details are set to None.
    """
    logger.info("Running Extractor Node...")
    
    llm = config.get("configurable", {}).get("llm")
    if not llm:
        from app.dependencies import get_settings
        from app.services.llm import get_llm_client
        llm = get_llm_client(get_settings())
        
    structured_llm = llm.with_structured_output(ExtractedPropertyDetails, method="function_calling")
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", load_prompt("extractor.txt")),
        ("user", "Trích xuất thông tin bất động sản chi tiết từ văn bản sau:\n\n{text}")
    ])
    
    chain = prompt | structured_llm
    extracted: ExtractedPropertyDetails = chain.invoke({"text": state.user_input})
    
    updates = {}
    fields = [
        "property_type", "location", "area", "price", "legal_status",
        "amenities", "financial_policy", "target_customer", "marketing_goal"
    ]
    for field in fields:
        val = getattr(extracted, field, None)
        if val is not None and str(val).strip() != "" and str(val).lower() != "null":
            updates[field] = val
        else:
            existing = getattr(state, field, None)
            if existing is not None:
                updates[field] = existing
    return updates



def missing_info_detector_node(state: RealEstateAgentState, config: RunnableConfig) -> Dict[str, Any]:
    """
    Checks the current state against required & recommended fields,
    populates required_missing, recommended_missing, and calculates completion_score.
    """
    logger.info("Running Missing Info Detector Node...")
    
    required_fields = [
        "property_type", "location", "price", 
        "area", "legal_status", "target_customer", "marketing_goal"
    ]
    recommended_fields = []
    
    required_missing = []
    
    def is_empty_value(val: Any) -> bool:
        if val is None:
            return True
        s = str(val).strip().lower()
        if s in ["", "null", "none", "không có thông tin", "chưa có thông tin", "không đề cập", "chưa rõ", "n/a"]:
            return True
        return False

    for field in required_fields:
        val = getattr(state, field, None)
        if is_empty_value(val):
            required_missing.append(field)
            
    recommended_missing = []
    for field in recommended_fields:
        val = getattr(state, field, None)
        if is_empty_value(val):
            recommended_missing.append(field)
            
    # Calculate completion score
    total_fields = required_fields + recommended_fields
    present_count = 0
    for field in total_fields:
        val = getattr(state, field, None)
        if val is not None and str(val).strip() != "" and str(val).lower() != "null":
            present_count += 1
            
    completion_score = round(present_count / len(total_fields), 2)
    
    return {
        "required_missing": required_missing,
        "recommended_missing": recommended_missing,
        "completion_score": completion_score,
        "missing_fields": required_missing + recommended_missing
    }


def clarification_node(state: RealEstateAgentState, config: RunnableConfig) -> Dict[str, Any]:
    """
    Formulates a clarification question in Markdown asking the user to clarify ONLY the missing fields.
    Avoids repeating already known information and increments the loop round counter.
    """
    logger.info("Running Clarification Node...")
    
    llm = config.get("configurable", {}).get("llm")
    if not llm:
        from app.dependencies import get_settings
        from app.services.llm import get_llm_client
        llm = get_llm_client(get_settings())
        
    FIELD_TRANSLATION = {
        "property_type": "Loại hình bất động sản",
        "location": "Vị trí",
        "price": "Giá bán",
        "area": "Diện tích",
        "legal_status": "Pháp lý",
        "financial_policy": "Chính sách tài chính",
        "amenities": "Tiện ích",
        "target_customer": "Khách hàng mục tiêu",
        "marketing_goal": "Mục tiêu bài viết"
    }
    
    known_info = {}
    all_fields = [
        "property_type", "location", "price", "area", "legal_status",
        "financial_policy", "amenities", "target_customer", "marketing_goal"
    ]
    for f in all_fields:
        val = getattr(state, f, None)
        if val is not None and str(val).strip() != "" and str(val).lower() != "null":
            known_info[FIELD_TRANSLATION[f]] = val
            
    required_missing_vn = [FIELD_TRANSLATION[f] for f in state.required_missing]
    recommended_missing_vn = [FIELD_TRANSLATION[f] for f in state.recommended_missing]
    
    new_info = state.user_input if state.user_input else "Không có"
    next_round = state.clarification_round + 1
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", load_prompt("clarification.txt")),
        ("user", (
            "Vòng hội thoại: {round}\n"
            "Thông tin đã ghi nhận: {known_info}\n"
            "Thông tin còn thiếu bắt buộc: {required_missing}\n"
            "Thông tin còn thiếu khuyến khích: {recommended_missing}\n"
            "Thông tin người dùng mới bổ sung: {new_info}"
        ))
    ])
    
    chain = prompt | llm
    response = chain.invoke({
        "round": next_round,
        "known_info": json.dumps(known_info, ensure_ascii=False),
        "required_missing": ", ".join(required_missing_vn) if required_missing_vn else "Không có",
        "recommended_missing": ", ".join(recommended_missing_vn) if recommended_missing_vn else "Không có",
        "new_info": new_info
    })
    
    history = list(state.conversation_history or [])
    history.append({"role": "assistant", "content": response.content})
    
    return {
        "conversation_history": history,
        "clarification_round": next_round
    }


def persona_detector_node(state: RealEstateAgentState, config: RunnableConfig) -> Dict[str, Any]:
    """
    Detects the target customer buyer persona, key pain points, and decision factors.
    Only infers from property details if target_customer explicitly contains "yêu cầu gợi ý".
    Otherwise, if target_customer is missing, returns None to trigger clarification.
    """
    logger.info("Running Persona Detector Node...")
    
    def is_empty_value(val: Any) -> bool:
        if val is None:
            return True
        s = str(val).strip().lower()
        if s in ["", "null", "none", "không có thông tin", "chưa có thông tin", "không đề cập", "chưa rõ", "n/a"]:
            return True
        return False
        
    if is_empty_value(state.target_customer):
        return {
            "persona_name": None,
            "persona_confidence": 0.0,
            "pain_points": [],
            "decision_factors": []
        }
        
    llm = config.get("configurable", {}).get("llm")
    if not llm:
        from app.dependencies import get_settings
        from app.services.llm import get_llm_client
        llm = get_llm_client(get_settings())
        
    structured_llm = llm.with_structured_output(PersonaDetectionResult, method="function_calling")
    
    is_request_inference = "yêu cầu gợi ý" in str(state.target_customer).lower()
    
    if is_request_inference:
        # Check if basic info is present before allowing inference
        if not state.property_type or not state.location or not state.price:
            return {
                "persona_name": None,
                "persona_confidence": 0.0,
                "pain_points": [],
                "decision_factors": []
            }
            
        target_cust_prompt = "Người dùng YÊU CẦU GỢI Ý khách hàng mục tiêu. Hãy tự suy luận từ thông tin BĐS (Loại hình, Vị trí, Giá...)."
    else:
        target_cust_prompt = state.target_customer
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", load_prompt("persona_detector.txt")),
        ("user", (
            "Khách hàng mục tiêu (hoặc yêu cầu): {target_customer}\n\n"
            "Thông tin bất động sản để tham khảo/suy luận:\n"
            "- Loại hình: {property_type}\n"
            "- Vị trí: {location}\n"
            "- Giá bán: {price}\n"
            "- Diện tích: {area}\n"
            "- Pháp lý: {legal_status}"
        ))
    ])
    
    chain = prompt | structured_llm
    result: PersonaDetectionResult = chain.invoke({
        "target_customer": target_cust_prompt,
        "property_type": state.property_type or "Chưa rõ",
        "location": state.location or "Chưa rõ",
        "price": state.price or "Chưa rõ",
        "area": state.area or "Chưa rõ",
        "legal_status": state.legal_status or "Chưa rõ"
    })
    
    persona_name = result.persona_name
    confidence = result.confidence
    
    if confidence < 0.7:
        persona_name = None
        
    return {
        "persona_name": persona_name,
        "persona_confidence": confidence,
        "pain_points": result.pain_points,
        "decision_factors": result.decision_factors
    }


def confirmation_node(state: RealEstateAgentState, config: RunnableConfig) -> Dict[str, Any]:
    """
    A dummy node used as an interruption point. 
    It pauses execution after gathering all info and persona, before proceeding to goal_detector.
    """
    logger.info("Running Confirmation Node (Paused)...")
    return {}


def goal_detector_node(state: RealEstateAgentState, config: RunnableConfig) -> Dict[str, Any]:
    """
    Maps the marketing goal into standard categories and recommends frameworks & CTA styles.
    """
    logger.info("Running Goal Detector Node...")
    
    llm = config.get("configurable", {}).get("llm")
    if not llm:
        from app.dependencies import get_settings
        from app.services.llm import get_llm_client
        llm = get_llm_client(get_settings())
        
    structured_llm = llm.with_structured_output(GoalDetectionResult, method="function_calling")
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", load_prompt("goal_detector.txt")),
        ("user", "Mô tả mục tiêu marketing/bài viết cần phân loại:\n\n{marketing_goal}")
    ])
    
    goal_desc = state.marketing_goal or "Promoting the property to sell quickly."
    chain = prompt | structured_llm
    result: GoalDetectionResult = chain.invoke({"marketing_goal": goal_desc})
    
    return {
        "goal_name": result.goal_name,
        "recommended_framework": result.recommended_framework,
        "recommended_cta_style": result.recommended_cta_style
    }


def strategist_node(state: RealEstateAgentState, config: RunnableConfig) -> Dict[str, Any]:
    """
    Generates exactly 3 distinct content angles/strategies based on property, persona, and goal.
    """
    logger.info("Running Strategist Node...")
    
    llm = config.get("configurable", {}).get("llm")
    if not llm:
        from app.dependencies import get_settings
        from app.services.llm import get_llm_client
        llm = get_llm_client(get_settings())
        
    structured_llm = llm.with_structured_output(StrategistAnglesResult, method="function_calling")
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", load_prompt("strategist.txt")),
        ("user", (
            "Thông tin chi tiết bất động sản:\n"
            "- Loại hình: {property_type}\n"
            "- Vị trí: {location}\n"
            "- Giá bán: {price}\n"
            "- Diện tích: {area}\n"
            "- Pháp lý: {legal_status}\n"
            "- Tiện ích: {amenities}\n"
            "- Chính sách tài chính: {financial_policy}\n\n"
            "Chân dung khách hàng: {persona} (Các nỗi đau chính: {pain_points})\n"
            "Mục tiêu marketing: {goal}"
        ))
    ])
    
    chain = prompt | structured_llm
    result: StrategistAnglesResult = chain.invoke({
        "property_type": state.property_type,
        "location": state.location,
        "price": state.price,
        "area": state.area,
        "legal_status": state.legal_status,
        "amenities": state.amenities,
        "financial_policy": state.financial_policy,
        "persona": state.persona_name,
        "pain_points": ", ".join(state.pain_points) if state.pain_points else "None",
        "goal": state.goal_name
    })
    
    # Store angles as dictionary list
    angles_list = [
        {
            "id": angle.id,
            "title": angle.title,
            "reason": angle.reason,
            "core_message": angle.core_message,
            "key_selling_point": angle.key_selling_point,
            "score": angle.score,
            "framework": angle.framework
        }
        for angle in result.angles
    ]
    
    # Create clean history payload without internal framework keys
    clean_history_angles = []
    for ang in angles_list:
        clean_ang = dict(ang)
        clean_ang.pop("framework", None)
        clean_history_angles.append(clean_ang)
        
    history = list(state.conversation_history or [])
    history.append({
        "role": "assistant",
        "type": "angles",
        "content": json.dumps({
            "recommended_angle_id": result.recommended_angle_id,
            "angles": clean_history_angles
        }, ensure_ascii=False)
    })
    
    return {
        "content_angles": angles_list,
        "recommended_angle_id": result.recommended_angle_id,
        "conversation_history": history
    }


def writer_node(state: RealEstateAgentState, config: RunnableConfig) -> Dict[str, Any]:
    """
    Generates a Facebook real estate post in Vietnamese based on the selected angle,
    target persona, goal, and property details. Length is between 300-500 words.
    """
    logger.info("Running Writer Node...")
    
    llm = config.get("configurable", {}).get("llm")
    if not llm:
        from app.dependencies import get_settings
        from app.services.llm import get_llm_client
        llm = get_llm_client(get_settings())
        
    # Resolve the selected angle framework and details internally from state
    selected_angle_obj = None
    for angle in (state.content_angles or []):
        angle_title = angle.get("title") if isinstance(angle, dict) else getattr(angle, "title", None)
        angle_id = angle.get("id") if isinstance(angle, dict) else getattr(angle, "id", None)
        if angle_title == state.selected_angle or str(angle_id) == state.selected_angle:
            selected_angle_obj = angle
            break
            
    framework = "PAS"
    angle_details = state.selected_angle or "Tổng quan dự án"
    
    if selected_angle_obj:
        framework = selected_angle_obj.get("framework") if isinstance(selected_angle_obj, dict) else getattr(selected_angle_obj, "framework", "PAS")
        title = selected_angle_obj.get("title") if isinstance(selected_angle_obj, dict) else getattr(selected_angle_obj, "title", "")
        reason = selected_angle_obj.get("reason") if isinstance(selected_angle_obj, dict) else getattr(selected_angle_obj, "reason", "")
        core_message = selected_angle_obj.get("core_message") if isinstance(selected_angle_obj, dict) else getattr(selected_angle_obj, "core_message", "")
        ksp = selected_angle_obj.get("key_selling_point") if isinstance(selected_angle_obj, dict) else getattr(selected_angle_obj, "key_selling_point", "")
        
        angle_details = (
            f"Hướng chiến lược: {title}\n"
            f"- Lý do phù hợp: {reason}\n"
            f"- Thông điệp cốt lõi: {core_message}\n"
            f"- Điểm nhấn nổi bật: {ksp}"
        )
        
    prompt = ChatPromptTemplate.from_messages([
        ("system", load_prompt("writer.txt")),
        ("user", (
            "Thông tin hướng tiếp cận chiến lược:\n{angle_details}\n"
            "Chân dung khách hàng (Persona): {persona} (Nỗi lo lắng: {pain_points}, Tiêu chí quyết định: {decision_factors})\n"
            "Mục tiêu marketing (Marketing Goal): {goal} ({cta_style}) - Raw Goal: {raw_goal}\n"
            "Thông tin chi tiết bất động sản:\n"
            "- Loại hình: {property_type}\n"
            "- Vị trí: {location}\n"
            "- Giá bán: {price}\n"
            "- Diện tích: {area}\n"
            "- Pháp lý: {legal_status}\n"
            "- Tiện ích: {amenities}\n"
            "- Chính sách tài chính: {financial_policy}\n"
            "{refinement_prompt}"
        ))
    ])
    
    # Check if we are running after validation failures to add correction feedback
    refinement_prompt = ""
    if state.issues_found:
        refinement_prompt = (
            f"\nCRITICAL: The previous draft failed validation. "
            f"Please write a NEW copy addressing these issues:\n" +
            "\n".join(f"- {issue}" for issue in state.issues_found) +
            "\nDO NOT APOLOGIZE. DO NOT EXPLAIN. JUST OUTPUT THE FACEBOOK POST CONTENT."
        )
        
    chain = prompt | llm
    response = chain.invoke({
        "angle_details": angle_details,
        "persona": state.persona_name,
        "pain_points": ", ".join(state.pain_points) if state.pain_points else "None",
        "decision_factors": ", ".join(state.decision_factors) if state.decision_factors else "None",
        "goal": state.goal_name,
        "raw_goal": state.marketing_goal or "Không có",
        "cta_style": state.recommended_cta_style,
        "property_type": state.property_type,
        "location": state.location,
        "price": state.price,
        "area": state.area,
        "legal_status": state.legal_status,
        "amenities": state.amenities,
        "financial_policy": state.financial_policy,
        "refinement_prompt": refinement_prompt
    })
    
    return {"draft_content": response.content}


def validator_node(state: RealEstateAgentState, config: RunnableConfig) -> Dict[str, Any]:
    """
    Checks the draft post for essential criteria:
    - price exists in text
    - location exists in text
    - legal status exists in text
    - CTA exists
    - no banned phrases (cam kết 100%, giá thỏa thuận, click ngay, giảm giá sốc)
    """
    logger.info("Running Validator Node...")
    draft = state.draft_content or ""
    issues = []
    
    # 1. Price existence check
    if not state.price:
        issues.append("Price is not defined in property details.")
    elif state.price.lower() not in draft.lower() and "đ" not in draft and "tỷ" not in draft and "triệu" not in draft:
        issues.append(f"Price detail ({state.price}) is missing from the post copy.")
        
    # 2. Location existence check
    if not state.location:
        issues.append("Location is not defined in property details.")
    else:
        location_parts = [part.strip().lower() for part in state.location.split(",") if len(part.strip()) > 3]
        if location_parts and not any(part in draft.lower() for part in location_parts):
            issues.append(f"Location details from '{state.location}' are missing from the post copy.")
            
    # 3. Legal status check
    if not state.legal_status:
        issues.append("Legal status is not defined in property details.")
    elif state.legal_status.lower() not in draft.lower() and "sổ" not in draft.lower() and "pháp lý" not in draft.lower() and "hợp đồng" not in draft.lower():
        issues.append(f"Legal status ({state.legal_status}) is missing from the post copy.")
        
    # 4. CTA presence check
    cta_triggers = ["inbox", "liên hệ", "hotline", "gọi ngay", "sđt", "đăng ký", "📲", "📞", "☎️", "nhắn tin", "comment"]
    if not any(trigger in draft.lower() for trigger in cta_triggers):
        issues.append("No clear Call to Action (CTA) found in the draft (e.g. hotline, phone, inbox).")
        
    # 5. Banned phrases check (case-insensitive)
    banned_phrases = [
        "vay", "vay vốn", "giải ngân", "lãi suất",
        "sổ đỏ", "sổ hộ khẩu",
        "cam kết 100%", "tuyệt đối", "chắc chắn", "cam kết sinh lời",
        "click ngay", "giảm giá sốc", "inbox ngay", "mua liền tay",
        "giá thỏa thuận",
        "không gian sống lý tưởng", "giải pháp thông minh", "giải pháp an toàn và thông minh"
    ]
    for phrase in banned_phrases:
        if phrase in draft.lower():
            issues.append(f"Contains banned phrase: '{phrase}'")
            
    # 6. Hallucination check (using LLM with structured output)
    hallucinations = []
    if draft.strip():
        llm = config.get("configurable", {}).get("llm")
        if not llm:
            from app.dependencies import get_settings
            from app.services.llm import get_llm_client
            llm = get_llm_client(get_settings())
            
        structured_llm = llm.with_structured_output(HallucinationCheckResult, method="function_calling")
        
        input_facts = {
            "property_type": state.property_type,
            "location": state.location,
            "price": state.price,
            "area": state.area,
            "legal_status": state.legal_status,
            "amenities": state.amenities,
            "financial_policy": state.financial_policy,
            "target_customer": state.target_customer,
            "marketing_goal": state.marketing_goal
        }
        input_facts = {k: v for k, v in input_facts.items() if v is not None and str(v).strip() != "" and str(v).lower() != "null"}
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", (
                "You are an expert real estate content validator assistant.\n"
                "Compare the generated Facebook post draft against the provided Input Facts.\n"
                "Identify any claims, facts, specifications, distances, or amenities in the post that are NOT explicitly mentioned or directly supported by the Input Facts.\n"
                "Examples of common hallucinations: claiming the property is 'near workplace', has 'wide roads', has 'only a few units left', or stating specific distances (like '5 minutes away') that are not defined in the Input Facts.\n"
                "Return a list of these hallucinated facts. If the post does not contain any unsupported facts, return an empty list."
            )),
            ("user", "Input Facts:\n{input_facts}\n\nGenerated Post Draft:\n{draft}")
        ])
        
        chain = prompt | structured_llm
        try:
            val_result: HallucinationCheckResult = chain.invoke({
                "input_facts": json.dumps(input_facts, ensure_ascii=False),
                "draft": draft
            })
            hallucinations = val_result.hallucinations
            for hal in hallucinations:
                issues.append(f"Phát hiện lỗi bịa đặt thông tin (Hallucination): {hal}")
        except Exception as e:
            logger.error(f"Error running hallucination detection: {str(e)}")
            
    validation_result = "FAIL" if issues else "PASS"
    current_attempts = state.validation_attempts + 1
    
    if validation_result == "FAIL" and current_attempts >= 2:
        logger.warning(f"Validation failed after {current_attempts} attempts. Bypassing loop to route to Editor.")
        validation_result = "PASS"
        issues.append("Bypassed validation loop to let user review/edit remaining issues.")
        
    return {
        "validation_result": validation_result,
        "issues_found": issues,
        "hallucinations_detected": hallucinations,
        "validation_attempts": current_attempts
    }


def editor_node(state: RealEstateAgentState, config: RunnableConfig) -> Dict[str, Any]:
    """
    Polishes and finalizes the draft content, incorporating human revision requests if any.
    Clears the revision request once completed to avoid infinite loop on resume.
    """
    logger.info("Running Editor Node...")
    draft = state.draft_content or ""
    
    if not state.revision_request:
        final_polished = draft
        history = list(state.conversation_history or [])
        history.append({"role": "assistant", "content": final_polished})
        return {
            "final_content": final_polished,
            "conversation_history": history,
            "revision_request": None,
            "validation_attempts": 0
        }
        
    # If there is a revision request, we use the LLM to refine the post copy
    llm = config.get("configurable", {}).get("llm")
    if not llm:
        from app.dependencies import get_settings
        from app.services.llm import get_llm_client
        llm = get_llm_client(get_settings())
        
    prompt = ChatPromptTemplate.from_messages([
        ("system", load_prompt("editor.txt")),
        ("user", "Original Copy:\n{draft}\n\nRevision Request:\n{revision_request}")
    ])
    
    chain = prompt | llm
    response = chain.invoke({
        "draft": draft,
        "revision_request": state.revision_request
    })
    
    history = list(state.conversation_history or [])
    history.append({"role": "assistant", "content": response.content})
    
    return {
        "final_content": response.content,
        "conversation_history": history,
        "revision_request": None,
        "validation_attempts": 0
    }

