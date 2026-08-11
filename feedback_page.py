# feedback_page.py
import streamlit as st
import utils

def render():
    st.title("📢 用户反馈")
    st.caption("欢迎提出建议、报告Bug，我们会尽快处理。")
    
    with st.form("feedback_form"):
        content = st.text_area("反馈内容", placeholder="请详细描述你的问题或建议...")
        if st.form_submit_button("提交反馈"):
            if content.strip():
                if utils.submit_feedback(st.session_state.nickname, content):
                    st.success("感谢你的反馈！")
                else:
                    st.error("提交失败，请稍后重试")
            else:
                st.warning("内容不能为空")