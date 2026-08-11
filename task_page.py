# ==========================================
# task_page.py - 任务广场页面
# ==========================================
import streamlit as st
import utils  # 导入公共函数库

def render():
    # 进入页面时，清除红点
    utils.update_user_visit_time(st.session_state.nickname, "task")
    
    st.title("🏫 任务广场")
    st.caption("这里只显示「待接单」的需求，先到先得！")
    
    # 发布表单
    with st.expander("📝 发布新需求", expanded=False):
        with st.form("publish_form"):
            col1, col2 = st.columns([3, 1])
            with col1:
                task_title = st.text_input("标题")
            with col2:
                task_reward = st.text_input("报酬")
            task_desc = st.text_area("描述")
            if st.form_submit_button("发布"):
                if task_title and task_desc:
                    full_desc = f"【报酬：{task_reward if task_reward else '面议'}】\n{task_desc}"
                    if utils.add_task(task_title, full_desc, st.session_state.nickname):
                        st.success("发布成功！")
                        st.rerun()
                    else:
                        st.error("发布失败")
                else:
                    st.warning("请填完整")
    
    # 任务列表
tasks = utils.get_public_tasks()
if not tasks:
    st.info("🎉 广场很干净，暂无待接单的需求。")
else:
    for task in tasks:
        with st.container(border=True):
            col_left, col_right = st.columns([4, 1])
            with col_left:
                st.markdown(f"🟢 **{task['title']}**")
                st.caption(f"👤 {task['publisher']}  |  🕒 {task['pub_time']}")
                st.text(task['description'])
            with col_right:
                # ===== 操作按钮区域 =====
                # 如果是发布者，显示"删除"按钮
                if task['publisher'] == st.session_state.nickname:
                    if st.button("🗑️ 删除", key=f"del_task_{task['id']}"):
                        success, msg = utils.delete_task(task['id'], st.session_state.nickname)
                        if success:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)
                else:
                    # 非发布者显示"接单"按钮
                    if st.button("✋ 我来接", key=f"pub_{task['id']}"):
                        success, msg = utils.accept_task(task['id'], st.session_state.nickname)
                        if success:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)