# chat_page.py - 消息中心
import streamlit as st
import utils

def render():
    st.title("💬 消息中心")
    
    # 检查是否在会话详情模式
    if "task_id" in st.query_params and "other_user" in st.query_params:
        task_id = int(st.query_params["task_id"])
        other_user = st.query_params["other_user"]
        
        # 标记已读
        utils.mark_messages_read(st.session_state.nickname, task_id)
        
        # 显示返回按钮
        if st.button("← 返回会话列表"):
            st.query_params.clear()
            st.rerun()
        
        st.subheader(f"与 {other_user} 的对话（任务ID: {task_id}）")
        
        # 获取消息历史
        messages = utils.get_messages_between(st.session_state.nickname, other_user, task_id)
        if messages:
            for msg in messages:
                sender = "我" if msg['from_user'] == st.session_state.nickname else msg['from_user']
                st.markdown(f"**{sender}** ({msg['created_at'][:16]})")
                st.markdown(f"> {msg['content']}")
                st.divider()
        else:
            st.info("暂无消息，开始聊天吧！")
        
        # 发送消息
        with st.form(key="send_msg_form"):
            new_msg = st.text_input("说点什么...", key="msg_input")
            if st.form_submit_button("发送"):
                if new_msg.strip():
                    if utils.send_message(st.session_state.nickname, other_user, new_msg, task_id):
                        st.success("发送成功！")
                        st.rerun()
                    else:
                        st.error("发送失败")
                else:
                    st.warning("内容不能为空")
    else:
        # 会话列表
        convs = utils.get_conversations_for_user(st.session_state.nickname)
        if not convs:
            st.info("暂无会话，当你的任务被接单或你接单后，可以开始聊天。")
        else:
            for conv in convs:
                with st.container(border=True):
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.markdown(f"**{conv['other_nick']}** ({conv['task_title']})")
                        st.caption(f"最新: {conv['last_msg']}")
                    with col2:
                        if conv['unread'] > 0:
                            st.markdown(f"🔴 {conv['unread']} 条未读")
                        if st.button("进入聊天", key=f"chat_{conv['task_id']}"):
                            st.query_params["task_id"] = conv['task_id']
                            st.query_params["other_user"] = conv['other_user']
                            st.rerun()