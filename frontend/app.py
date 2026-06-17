import streamlit as st
import requests

# Backend FastAPI URL
BACKEND_URL = "https://bds-agent-vm7a.onrender.com"

st.set_page_config(
    page_title="AI Agent Viết Bài Bất Động Sản",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# App Title and Theme Styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #4B5563;
        margin-bottom: 1.5rem;
    }
    /* Global Font Size Bump */
    p, li, span, label, .stMarkdown, .stButton>button, .stTextInput input, .stTextArea textarea {
        font-size: 1.15rem !important;
    }
    /* Chat Input Font Size */
    textarea[data-testid="stChatInputTextArea"], .stChatInput textarea {
        font-size: 1.15rem !important;
    }
    /* User Message Styling (Right Aligned) */
    .user-message-container {
        display: flex;
        justify-content: flex-end;
        align-items: flex-start;
        margin-bottom: 1.2rem;
        width: 100%;
    }
    .user-message-bubble {
        background-color: #2563EB; /* Premium blue */
        color: #FFFFFF;
        padding: 0.8rem 1.2rem;
        border-radius: 1.2rem 1.2rem 0.2rem 1.2rem;
        max-width: 70%;
        font-size: 1.15rem;
        line-height: 1.6;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        white-space: pre-wrap; /* Preserve newlines and spaces */
        font-family: inherit;
        text-align: left;
    }
    .user-message-avatar {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        background-color: #DBEAFE;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-left: 0.75rem;
        font-size: 1.3rem;
        flex-shrink: 0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    /* ChatGPT-like Card Frame for Final Post */
    .post-card-container {
        border: 1px solid #E5E7EB;
        border-radius: 12px;
        padding: 1.5rem;
        background-color: #FAFAFA;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        margin-bottom: 1.5rem;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">🏠 AI Agent Viết Bài BĐS Facebook</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Hệ thống tạo nội dung dạng Chatbot hội thoại thông minh và hỗ trợ tương tác trực tiếp</div>', unsafe_allow_html=True)

# Initialize Session States
if "thread_id" not in st.session_state:
    st.session_state.thread_id = None
if "agent_state" not in st.session_state:
    st.session_state.agent_state = None
if "next_step" not in st.session_state:
    st.session_state.next_step = None
if "api_key" not in st.session_state:
    st.session_state.api_key = ""
if "editing_final_content" not in st.session_state:
    st.session_state.editing_final_content = False
if "local_final_content" not in st.session_state:
    st.session_state.local_final_content = ""
if "show_missing_warning" not in st.session_state:
    st.session_state.show_missing_warning = False
if "pending_payload" not in st.session_state:
    st.session_state.pending_payload = None
if "missing_fields_names" not in st.session_state:
    st.session_state.missing_fields_names = []


def get_headers():
    headers = {}
    if st.session_state.api_key.strip():
        headers["X-API-Key"] = st.session_state.api_key.strip()
    return headers


def reset_session():
    st.session_state.thread_id = None
    st.session_state.agent_state = None
    st.session_state.next_step = None
    st.session_state.editing_final_content = False
    st.session_state.local_final_content = ""
    st.session_state.show_missing_warning = False
    st.session_state.pending_payload = None
    st.session_state.missing_fields_names = []


# --- SIDEBAR: Configuration ---
with st.sidebar:
    st.header("⚙️ Cấu hình")
    
    # API Key Configuration
    with st.expander("🔑 Cấu hình API Key", expanded=True):
        api_key_input = st.text_input(
            "API Key",
            type="password",
            value=st.session_state.api_key,
            placeholder="Để trống để dùng API Key hệ thống"
            # help="Nếu nhập, khóa này sẽ được gửi trong header X-API-Key để chạy mô hình."
        )
        if api_key_input != st.session_state.api_key:
            st.session_state.api_key = api_key_input
            st.rerun()

    if st.session_state.thread_id:
        st.markdown("---")
        if st.button("🔄 Tạo Bài Viết Mới", type="secondary", use_container_width=True):
            reset_session()
            st.rerun()


# --- MAIN PAGE: Interactive Chatbot Flow ---
st.subheader("💬 Trò chuyện cùng Agent")

# Always display the welcome message first
with st.chat_message("assistant", avatar="🤖"):
    st.write(
        "👋 **Chào mừng bạn đến với AI Agent Viết Bài Bất Động Sản!**\n\n"
        "Tôi sẽ giúp bạn viết bài đăng Facebook chuyên nghiệp, thu hút nhiều inbox và tối ưu hóa nội dung.\n\n"
        "Hãy nhập thông tin thô về bất động sản của bạn (ví dụ: vị trí, diện tích, giá bán, tiện ích, pháp lý, hoặc chính sách trả góp...) vào ô chat phía dưới để chúng ta bắt đầu!"
    )

selected_angle_btn = None

# Render Chat History if active session exists
if st.session_state.thread_id and st.session_state.agent_state:
    state = st.session_state.agent_state
    history = state.get("conversation_history", []) or []
    
    # Ensure local final content is synced from backend if it hasn't been set yet
    if state.get("final_content") and not st.session_state.local_final_content:
        st.session_state.local_final_content = state.get("final_content")

    import html
    import json
    for msg_idx, msg in enumerate(history):
        role = msg.get("role")
        content = msg.get("content")
        msg_type = msg.get("type", "")
        
        if role == "assistant":
            with st.chat_message("assistant", avatar="🤖"):
                if msg_type == "angles":
                    try:
                        parsed_angles = json.loads(content)
                        recommended_id = 1
                        angles_list = []
                        
                        is_new_format = isinstance(parsed_angles, dict)
                        if is_new_format:
                            recommended_id = parsed_angles.get("recommended_angle_id", 1)
                            angles_list = parsed_angles.get("angles", [])
                        else:
                            angles_list = parsed_angles
                            
                        st.markdown("### 📐 Các hướng tiếp cận nội dung đề xuất:")
                        
                        if is_new_format:
                            number_emojis = ["1️⃣", "2️⃣", "3️⃣"]
                            for idx, ang in enumerate(angles_list):
                                st.markdown("━━━━━━━━━━")
                                st.markdown(f"### {number_emojis[idx]} {ang.get('title')}")
                                st.markdown(f"**Phù hợp:**\n{ang.get('reason')}")
                                st.markdown(f"**Điểm nổi bật:**\n{ang.get('key_selling_point')}")
                                st.markdown(f"**Thông điệp cốt lõi:**\n{ang.get('core_message')}")
                                st.markdown(f"**Điểm đề xuất:**\n`{ang.get('score')}/10`")
                            st.markdown("━━━━━━━━━━")
                            st.markdown(f"💡 **Khuyến nghị:**\nHướng số {recommended_id}")
                        else:
                            for idx, ang in enumerate(angles_list):
                                st.markdown(f"**Hướng {idx+1}: {ang.get('title')}**")
                                st.markdown(f"- **Nỗi đau khách hàng:** {ang.get('customer_pain_point')}")
                                st.markdown(f"- **Thông điệp cốt lõi:** {ang.get('core_message')}")
                                st.markdown("---")
                                
                        st.markdown("**Hãy chọn hướng tiếp cận (bạn có thể bấm chọn lại bất cứ lúc nào để tạo lại bài viết):**")
                        
                        # Render quick reply buttons inside the history message card
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            if st.button("🎯 Chọn Hướng 1", key=f"hist_select_angle_{msg_idx}_1", use_container_width=True):
                                selected_angle_btn = angles_list[0].get("title")
                        with col2:
                            if st.button("🎯 Chọn Hướng 2", key=f"hist_select_angle_{msg_idx}_2", use_container_width=True):
                                selected_angle_btn = angles_list[1].get("title")
                        with col3:
                            if st.button("🎯 Chọn Hướng 3", key=f"hist_select_angle_{msg_idx}_3", use_container_width=True):
                                selected_angle_btn = angles_list[2].get("title")
                    except Exception as e:
                        st.error(f"Lỗi hiển thị hướng đề xuất: {str(e)}")
                else:
                    st.markdown(content)
        elif role == "user":
            avatar_char = "👤" if msg_type != "feedback" else "📝"
            escaped_content = html.escape(content)
            st.markdown(
                f"""
                <div class="user-message-container">
                    <div class="user-message-bubble">{escaped_content}</div>
                    <div class="user-message-avatar">{avatar_char}</div>
                </div>
                """,
                unsafe_allow_html=True
            )

# Render state-specific interactive prompts in the chat flow
next_node = st.session_state.next_step

if st.session_state.thread_id and st.session_state.agent_state:
    state = st.session_state.agent_state
    
    # 1. Persona Detector / Clarification Point
    if next_node == "extractor":
        # st.info("🚨 **Cần sự can thiệp của bạn (HITL 1):** Agent cần thêm thông tin để làm rõ. Bạn có thể nhập câu trả lời vào ô chat phía dưới.")
        
        # Display warning confirm box if triggered
        if st.session_state.get("show_missing_warning", False):
            st.warning(f"⚠️ **Thông tin chưa đầy đủ!** Bạn chưa nhập các trường: **{', '.join(st.session_state.missing_fields_names)}**.")
            st.write("Nếu bỏ qua, Agent sẽ tạo bài viết mà không có các thông tin này (hoặc tự sử dụng các câu chữ tránh). Bạn có muốn tiếp tục?")
            col_warn1, col_warn2 = st.columns(2)
            with col_warn1:
                if st.button("👉 Bỏ qua & Tiếp tục", type="primary", key="confirm_proceed_missing", use_container_width=True):
                    with st.spinner("Đang cập nhật thông tin và tiếp tục xây dựng chiến lược..."):
                        try:
                            payload = dict(st.session_state.pending_payload)
                            payload["force_proceed"] = True
                            res = requests.post(
                                f"{BACKEND_URL}/api/agent/respond-clarification/{st.session_state.thread_id}",
                                json=payload,
                                headers=get_headers()
                            )
                            if res.status_code == 200:
                                data = res.json()
                                st.session_state.agent_state = data["state"]
                                st.session_state.next_step = data["next_step"]
                                st.session_state.local_final_content = data["state"].get("final_content") or ""
                                st.session_state.editing_final_content = False
                                st.session_state.show_missing_warning = False
                                st.session_state.pending_payload = None
                                st.session_state.missing_fields_names = []
                                st.rerun()
                            else:
                                st.error(f"Lỗi gửi thông tin làm rõ: {res.text}")
                        except Exception as e:
                            st.error(f"Lỗi kết nối: {str(e)}")
            with col_warn2:
                if st.button("✏️ Quay lại điền thêm", type="secondary", key="cancel_proceed_missing", use_container_width=True):
                    st.session_state.show_missing_warning = False
                    st.session_state.pending_payload = None
                    st.session_state.missing_fields_names = []
                    st.rerun()
        else:
            # Helper expander for quick structured fields input
            with st.expander("🛠️ Bảng điền nhanh các trường thông tin", expanded=False):
                st.write("Các trường trống là thông tin còn thiếu. Bạn có thể bổ sung tại đây hoặc gõ câu trả lời vào ô chat bên dưới:")
                col1, col2, col3 = st.columns(3)
                with col1:
                    area_input = st.text_input("Diện tích", value=state.get("area") or "", placeholder="Ví dụ: 120m2")
                    price_input = st.text_input("Giá bán", value=state.get("price") or "", placeholder="Ví dụ: 2 tỷ")
                    target_customer_input = st.text_input("Khách hàng mục tiêu", value=state.get("target_customer") or "", placeholder="Ví dụ: vợ chồng trẻ")
                with col2:
                    legal_input = st.text_input("Pháp lý", value=state.get("legal_status") or "", placeholder="Ví dụ: Sổ hồng riêng")
                    property_type_input = st.text_input("Loại hình BĐS", value=state.get("property_type") or "", placeholder="Ví dụ: Căn hộ")
                    marketing_goal_input = st.text_input("Mục tiêu marketing", value=state.get("marketing_goal") or "", placeholder="Ví dụ: Tạo inbox tư vấn")
                with col3:
                    policy_input = st.text_input("Chính sách tài chính", value=state.get("financial_policy") or "", placeholder="Ví dụ: Hỗ trợ vay 70%")
                    location_input = st.text_input("Vị trí", value=state.get("location") or "", placeholder="Ví dụ: Quận 2, TP.HCM")
                
                st.markdown("---")
                if st.button("📤 Gửi thông tin", type="primary", key="quick_submit_fields", use_container_width=True):
                    payload = {
                        "clarification_response": "Cập nhật thông tin chi tiết qua bảng điền nhanh.",
                        "area": area_input if area_input.strip() else None,
                        "price": price_input if price_input.strip() else None,
                        "legal_status": legal_input if legal_input.strip() else None,
                        "financial_policy": policy_input if policy_input.strip() else None,
                        "property_type": property_type_input if property_type_input.strip() else None,
                        "location": location_input if location_input.strip() else None,
                        "target_customer": target_customer_input if target_customer_input.strip() else None,
                        "marketing_goal": marketing_goal_input if marketing_goal_input.strip() else None
                    }
                    
                    # Check for missing required fields
                    required_labels = {
                        "property_type": "Loại hình BĐS",
                        "location": "Vị trí",
                        "price": "Giá bán",
                        "area": "Diện tích",
                        "legal_status": "Pháp lý",
                        "target_customer": "Khách hàng mục tiêu",
                        "marketing_goal": "Mục tiêu marketing"
                    }
                    missing_names = []
                    for field_key, field_name in required_labels.items():
                        val = payload[field_key]
                        if val is None or val.strip() == "":
                            missing_names.append(field_name)
                            
                    if missing_names:
                        st.session_state.show_missing_warning = True
                        st.session_state.pending_payload = payload
                        st.session_state.missing_fields_names = missing_names
                        st.rerun()
                    else:
                        with st.spinner("Đang cập nhật thông tin và tiếp tục xây dựng chiến lược..."):
                            try:
                                res = requests.post(
                                    f"{BACKEND_URL}/api/agent/respond-clarification/{st.session_state.thread_id}",
                                    json=payload,
                                    headers=get_headers()
                                )
                                if res.status_code == 200:
                                    data = res.json()
                                    st.session_state.agent_state = data["state"]
                                    st.session_state.next_step = data["next_step"]
                                    st.session_state.local_final_content = data["state"].get("final_content") or ""
                                    st.session_state.editing_final_content = False
                                    st.rerun()
                                else:
                                    st.error(f"Lỗi gửi thông tin làm rõ: {res.text}")
                            except Exception as e:
                                st.error(f"Lỗi kết nối: {str(e)}")


    # 2.5 Confirmation Point
    if next_node == "goal_detector":
        with st.chat_message("assistant", avatar="🤖"):
            st.markdown("📋 **Thông tin đã thu thập đầy đủ. Vui lòng kiểm tra lại trước khi tôi lên chiến lược:**")
            if st.session_state.get("is_editing_confirmation", False):
                with st.container(border=True):
                    st.markdown("### Chỉnh sửa thông tin")
                    c_col1, c_col2 = st.columns(2)
                    with c_col1:
                        c_ptype = st.text_input("Loại hình BĐS", value=state.get("property_type") or "", key="c_ptype")
                        c_area = st.text_input("Diện tích", value=state.get("area") or "", key="c_area")
                        c_price = st.text_input("Giá bán", value=state.get("price") or "", key="c_price")
                        c_legal = st.text_input("Pháp lý", value=state.get("legal_status") or "", key="c_legal")
                    with c_col2:
                        c_loc = st.text_input("Vị trí", value=state.get("location") or "", key="c_loc")
                        c_tc = st.text_input("Khách hàng mục tiêu", value=state.get("target_customer") or "", key="c_tc")
                        c_mg = st.text_input("Mục tiêu marketing", value=state.get("marketing_goal") or "", key="c_mg")
                        c_policy = st.text_input("Chính sách tài chính", value=state.get("financial_policy") or "", key="c_policy")
                    c_amen = st.text_area("Tiện ích", value=state.get("amenities") or "", key="c_amen")

                col_cancel, col_confirm = st.columns([2, 8])
                with col_cancel:
                    if st.button("❌ Hủy", key="cancel_edit_conf", use_container_width=True):
                        st.session_state.is_editing_confirmation = False
                        st.rerun()
                with col_confirm:
                    if st.button("✅ Lưu & Lên chiến lược", type="primary", key="save_edit_conf", use_container_width=True):
                        with st.spinner("Đang cập nhật & xây dựng chiến lược..."):
                            try:
                                payload = {
                                    "confirmed": True,
                                    "area": st.session_state.get("c_area", "").strip() or None,
                                    "price": st.session_state.get("c_price", "").strip() or None,
                                    "target_customer": st.session_state.get("c_tc", "").strip() or None,
                                    "legal_status": st.session_state.get("c_legal", "").strip() or None,
                                    "property_type": st.session_state.get("c_ptype", "").strip() or None,
                                    "marketing_goal": st.session_state.get("c_mg", "").strip() or None,
                                    "financial_policy": st.session_state.get("c_policy", "").strip() or None,
                                    "location": st.session_state.get("c_loc", "").strip() or None,
                                    "amenities": st.session_state.get("c_amen", "").strip() or None
                                }
                                res = requests.post(
                                    f"{BACKEND_URL}/api/agent/confirm-info/{st.session_state.thread_id}",
                                    json=payload,
                                    headers=get_headers()
                                )
                                if res.status_code == 200:
                                    data = res.json()
                                    st.session_state.agent_state = data["state"]
                                    st.session_state.next_step = data["next_step"]
                                    st.session_state.local_final_content = data["state"].get("final_content") or ""
                                    st.session_state.editing_final_content = False
                                    st.session_state.is_editing_confirmation = False
                                    st.rerun()
                                else:
                                    st.error(f"Lỗi xác nhận: {res.text}")
                            except Exception as e:
                                st.error(f"Lỗi kết nối: {str(e)}")

            else:
                with st.container(border=True):
                    st.markdown(f"- **Loại hình:** {state.get('property_type') or 'Chưa rõ'}")
                    st.markdown(f"- **Vị trí:** {state.get('location') or 'Chưa rõ'}")
                    st.markdown(f"- **Diện tích:** {state.get('area') or 'Chưa rõ'}")
                    st.markdown(f"- **Giá bán:** {state.get('price') or 'Chưa rõ'}")
                    st.markdown(f"- **Pháp lý:** {state.get('legal_status') or 'Chưa rõ'}")
                    st.markdown(f"- **Chính sách:** {state.get('financial_policy') or 'Chưa rõ'}")
                    st.markdown(f"- **Tiện ích:** {state.get('amenities') or 'Chưa rõ'}")
                    
                    tc_raw = state.get('target_customer') or 'Chưa xác định'
                    persona = state.get('persona_name') or 'Chưa rõ'
                    
                    if "yêu cầu gợi ý" in tc_raw.lower() and persona != "Chưa rõ":
                        st.markdown(f"- **Khách hàng mục tiêu:** {persona} *(Hệ thống tự suy luận)*")
                    else:
                        st.markdown(f"- **Khách hàng mục tiêu:** {tc_raw}")
                    
                    st.markdown(f"- **Mục tiêu marketing:** {state.get('marketing_goal') or 'Chưa rõ'}")

                col_edit, col_confirm = st.columns([2, 8])
                with col_edit:
                    if st.button("✏️ Chỉnh sửa", key="edit_conf_btn", use_container_width=True):
                        st.session_state.is_editing_confirmation = True
                        st.rerun()
                with col_confirm:
                    if st.button("✅ Xác nhận thông tin chuẩn & Lên chiến lược", type="primary", key="confirm_conf_btn", use_container_width=True):
                        with st.spinner("Đang xây dựng chiến lược nội dung..."):
                            try:
                                payload = {
                                    "confirmed": True
                                }
                                res = requests.post(
                                    f"{BACKEND_URL}/api/agent/confirm-info/{st.session_state.thread_id}",
                                    json=payload,
                                    headers=get_headers()
                                )
                                if res.status_code == 200:
                                    data = res.json()
                                    st.session_state.agent_state = data["state"]
                                    st.session_state.next_step = data["next_step"]
                                    st.session_state.local_final_content = data["state"].get("final_content") or ""
                                    st.session_state.editing_final_content = False
                                    st.rerun()
                                else:
                                    st.error(f"Lỗi xác nhận: {res.text}")
                            except Exception as e:
                                st.error(f"Lỗi kết nối: {str(e)}")

            st.markdown("<div style='text-align: center; color: gray; margin-top: 10px;'>Hoặc nếu có thông tin nào sai/cần bổ sung, bạn có thể nhập vào ô chat bên dưới 👇</div>", unsafe_allow_html=True)



    # 3. Editor / Final Approval Point
    if next_node is None and state.get("final_content"):
        with st.chat_message("assistant", avatar="🤖"):
            st.success("✅ **Hoàn thành bài viết!** Đây là nội dung Facebook đã tối ưu hóa:")
            
            with st.container(border=True):
                if st.session_state.get("editing_final_content", False):
                    edited_content = st.text_area(
                        "✏️ Chỉnh sửa bài viết:",
                        value=st.session_state.local_final_content,
                        height=350,
                        key="edit_post_textarea"
                    )
                    col_save, col_cancel = st.columns([1, 4])
                    with col_save:
                        if st.button("💾 Lưu", type="primary", key="save_edited_post", use_container_width=True):
                            st.session_state.local_final_content = edited_content
                            st.session_state.editing_final_content = False
                            st.rerun()
                    with col_cancel:
                        if st.button("❌ Hủy", key="cancel_edited_post", use_container_width=True):
                            st.session_state.editing_final_content = False
                            st.rerun()
                else:
                    col_edit, col_spacer, col_dl = st.columns([2, 8, 2])
                    with col_edit:
                        if st.button("✏️ Chỉnh sửa", key="edit_post_btn", type="secondary", use_container_width=True):
                            st.session_state.editing_final_content = True
                            st.rerun()
                    with col_dl:
                        st.download_button(
                            label="📥 Tải về",
                            data=st.session_state.local_final_content,
                            file_name="bai_viet_facebook.txt",
                            mime="text/plain",
                            help="Tải xuống bài viết",
                            use_container_width=True
                        )
                    st.markdown("---")
                    # Preserve single newlines in markdown by adding 2 spaces before \n
                    formatted_content = st.session_state.local_final_content.replace('\n', '  \n')
                    st.markdown(formatted_content)
            
            # if state.get("issues_found"):
            #     with st.expander("⚠️ Lịch sử kiểm duyệt nội dung (Validator Node)", expanded=False):
            #         st.write(f"Kết quả kiểm duyệt: **{state.get('validation_result')}**")
            #         for issue in state.get("issues_found", []):
            #             st.write(f"- {issue}")
            
            # st.markdown("<div style='text-align: center; color: gray; margin-top: 10px;'>Bạn có thể copy hoặc nhập phản hồi ở dưới nếu muốn Agent sửa đổi bài viết 👇</div>", unsafe_allow_html=True)


# --- INPUT HANDLING: st.chat_input and quick buttons ---
chat_msg = st.chat_input("Nhập câu trả lời hoặc yêu cầu của bạn tại đây...")

# Process Quick Angle Button Click
if selected_angle_btn:
    with st.spinner("Đang soạn thảo bài viết, kiểm duyệt nội dung và tối ưu hóa bài đăng..."):
        try:
            res = requests.post(
                f"{BACKEND_URL}/api/agent/select-angle/{st.session_state.thread_id}",
                json={"selected_angle": selected_angle_btn},
                headers=get_headers()
            )
            if res.status_code == 200:
                data = res.json()
                st.session_state.agent_state = data["state"]
                st.session_state.next_step = data["next_step"]
                st.session_state.local_final_content = data["state"].get("final_content") or ""
                st.session_state.editing_final_content = False
                st.rerun()
            else:
                st.error(f"Lỗi khi chọn hướng: {res.text}")
        except Exception as e:
            st.error(f"Lỗi kết nối: {str(e)}")

# Process Chat Input Message
elif chat_msg:
    # 1. No Active Session: Start Workflow
    if not st.session_state.thread_id:
        with st.spinner("Đang khởi tạo Agent, phân tích thông tin và kiểm tra các yêu cầu..."):
            try:
                res = requests.post(
                    f"{BACKEND_URL}/api/agent/start",
                    json={"user_input": chat_msg},
                    headers=get_headers()
                )
                if res.status_code == 201:
                    data = res.json()
                    st.session_state.thread_id = data["thread_id"]
                    st.session_state.agent_state = data["state"]
                    st.session_state.next_step = data["next_step"]
                    st.session_state.local_final_content = data["state"].get("final_content") or ""
                    st.session_state.editing_final_content = False
                    st.rerun()
                else:
                    st.error(f"Lỗi khởi động tiến trình: {res.text}")
            except Exception as e:
                st.error(f"Không thể kết nối tới Backend: {str(e)}")
                
    # 2. Clarification Phase: Respond Clarification
    elif next_node == "extractor":
        with st.spinner("Đang cập nhật thông tin và tiếp tục xây dựng chiến lược..."):
            # Prepare payload, combining chat text and optional helper inputs
            payload = {
                "clarification_response": chat_msg,
                "area": area_input if 'area_input' in locals() and area_input.strip() else None,
                "price": price_input if 'price_input' in locals() and price_input.strip() else None,
                "legal_status": legal_input if 'legal_input' in locals() and legal_input.strip() else None,
                "financial_policy": policy_input if 'policy_input' in locals() and policy_input.strip() else None,
                "property_type": property_type_input if 'property_type_input' in locals() and property_type_input.strip() else None,
                "location": location_input if 'location_input' in locals() and location_input.strip() else None,
                "target_customer": target_customer_input if 'target_customer_input' in locals() and target_customer_input.strip() else None,
                "marketing_goal": marketing_goal_input if 'marketing_goal_input' in locals() and marketing_goal_input.strip() else None
            }
            try:
                res = requests.post(
                    f"{BACKEND_URL}/api/agent/respond-clarification/{st.session_state.thread_id}",
                    json=payload,
                    headers=get_headers()
                )
                if res.status_code == 200:
                    data = res.json()
                    st.session_state.agent_state = data["state"]
                    st.session_state.next_step = data["next_step"]
                    st.session_state.local_final_content = data["state"].get("final_content") or ""
                    st.session_state.editing_final_content = False
                    st.rerun()
                else:
                    st.error(f"Lỗi gửi thông tin làm rõ: {res.text}")
            except Exception as e:
                st.error(f"Lỗi kết nối: {str(e)}")
                
    # 2.5 Confirmation Phase: Modify Info
    elif next_node == "goal_detector":
        with st.spinner("Đang cập nhật lại thông tin..."):
            try:
                res = requests.post(
                    f"{BACKEND_URL}/api/agent/confirm-info/{st.session_state.thread_id}",
                    json={"confirmed": False, "modification_request": chat_msg},
                    headers=get_headers()
                )
                if res.status_code == 200:
                    data = res.json()
                    st.session_state.agent_state = data["state"]
                    st.session_state.next_step = data["next_step"]
                    st.session_state.local_final_content = data["state"].get("final_content") or ""
                    st.session_state.editing_final_content = False
                    st.rerun()
                else:
                    st.error(f"Lỗi gửi yêu cầu sửa đổi: {res.text}")
            except Exception as e:
                st.error(f"Lỗi kết nối: {str(e)}")
                
    # 3. Angle Selection Phase: Parse Choice or Send Warning
    elif next_node == "writer":
        selected = None
        angles = state.get("content_angles", [])
        text = chat_msg.lower().strip()
        
        # Check if number matches
        if "1" in text or (angles and angles[0].get("title").lower() in text):
            selected = angles[0].get("title")
        elif "2" in text or (angles and angles[1].get("title").lower() in text):
            selected = angles[1].get("title")
        elif "3" in text or (angles and angles[2].get("title").lower() in text):
            selected = angles[2].get("title")
        else:
            # Check title matches
            for ang in angles:
                if ang.get("title").lower() in text:
                    selected = ang.get("title")
                    break
        
        if selected:
            with st.spinner("Đang soạn thảo bài viết, kiểm duyệt nội dung và tối ưu hóa bài đăng..."):
                try:
                    res = requests.post(
                        f"{BACKEND_URL}/api/agent/select-angle/{st.session_state.thread_id}",
                        json={"selected_angle": selected},
                        headers=get_headers()
                    )
                    if res.status_code == 200:
                        data = res.json()
                        st.session_state.agent_state = data["state"]
                        st.session_state.next_step = data["next_step"]
                        st.session_state.local_final_content = data["state"].get("final_content") or ""
                        st.session_state.editing_final_content = False
                        st.rerun()
                    else:
                        st.error(f"Lỗi khi chọn hướng: {res.text}")
                except Exception as e:
                    st.error(f"Lỗi kết nối: {str(e)}")
        else:
            st.warning("Vui lòng chọn hướng bằng cách gõ số 1, 2 hoặc 3 (hoặc click nút chọn nhanh).")
            
    # 4. Final Approval / Revision Phase: Determine Yes/No or Send Feedback
    elif next_node is None and state.get("final_content"):
        text = chat_msg.lower().strip()
        confirm_words = ["ok", "duyệt", "đồng ý", "approve", "tốt rồi", "được rồi", "yêu thích", "thích", "yes", "y", "phê duyệt"]
        
        # Check if user says yes/ok to approve
        if any(w == text or f" {w} " in f" {text} " for w in confirm_words):
            call_approve = True
            rev_req = None
        else:
            call_approve = False
            rev_req = chat_msg
            
        with st.spinner("Đang gửi phản hồi..."):
            try:
                res = requests.post(
                    f"{BACKEND_URL}/api/agent/approve-post/{st.session_state.thread_id}",
                    json={"approved": call_approve, "revision_request": rev_req, "final_content": st.session_state.local_final_content},
                    headers=get_headers()
                )
                if res.status_code == 200:
                    data = res.json()
                    st.session_state.agent_state = data["state"]
                    st.session_state.next_step = data["next_step"]
                    st.session_state.local_final_content = data["state"].get("final_content") or ""
                    st.session_state.editing_final_content = False
                    st.rerun()
                else:
                    st.error(f"Lỗi gửi phản hồi: {res.text}")
            except Exception as e:
                st.error(f"Lỗi kết nối: {str(e)}")
