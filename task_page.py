# ==========================================
# task_page.py - 任务广场页面
# ==========================================
import streamlit as st
import utils
import datetime

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
                task_title = st.text_input("标题", placeholder="例如：代拿,代买,跑腿等")
            with col2:
                task_reward = st.text_input("报酬", placeholder="例如：5元")
            task_desc = st.text_area("描述", placeholder="详细描述你的需求...可附上联系方式，网站也可以私聊就是需要刷新")
            
            # ---------- 截止时间（必填，默认今天） ----------
            deadline = st.date_input(
                "截止日期（必填）", 
                value=datetime.date.today(),
                help="超过此日期任务将自动从广场消失，建议选明天或更晚"
            )
            
            if st.form_submit_button("发布"):
                if task_title and task_desc:
                    # 截止时间转为 ISO 格式字符串（当天 23:59:59）
                    deadline_dt = datetime.datetime.combine(deadline, datetime.time(23, 59, 59))
                    deadline_str = deadline_dt.isoformat()
                    
                    full_desc = f"【报酬：{task_reward if task_reward else '面议'}】\n{task_desc}"
                    if utils.add_task(task_title, full_desc, st.session_state.nickname, deadline_str):
                        st.success("发布成功！")
                        st.rerun()
                    else:
                        st.error("发布失败")
                else:
                    st.warning("请填完整")
    
    # ---------- 任务列表（分页加载） ----------
    if 'task_page' not in st.session_state:
        st.session_state.task_page = 1

    tasks, total = utils.get_public_tasks_page(st.session_state.task_page, per_page=10)

    if not tasks:
        st.info("🎉 广场很干净，暂无待接单的需求。")
    else:
        for task in tasks:
            with st.container(border=True):
                col_left, col_right = st.columns([4, 1])
                with col_left:
                    st.markdown(f"🟢 **{task['title']}**")
                    st.caption(f"👤 {task['publisher']}  |  🕒 {task['pub_time']}")
                    if task.get('deadline'):
                        st.caption(f"⏰ 截止：{task['deadline'][:10]}")
                    st.text(task['description'])
                with col_right:
                    if task['publisher'] == st.session_state.nickname:
                        if st.button("🗑️ 删除", key=f"del_task_{task['id']}"):
                            success, msg = utils.delete_task(task['id'], st.session_state.nickname)
                            if success:
                                st.success(msg)
                                st.rerun()
                            else:
                                st.error(msg)
                    else:
                        if st.button("✋ 我来接", key=f"pub_{task['id']}"):
                            success, msg = utils.accept_task(task['id'], st.session_state.nickname)
                            if success:
                                st.success(msg)
                                st.rerun()
                            else:
                                st.error(msg)

        # 判断是否还有更多
        if st.session_state.task_page * 10 < total:
            if st.button("📥 加载更多任务"):
                st.session_state.task_page += 1
                st.rerun()
        else:
            st.caption("— 已加载全部任务 —")