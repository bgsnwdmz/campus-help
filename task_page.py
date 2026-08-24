# ==========================================
# task_page.py - 任务广场页面（升级版）
# ==========================================
import streamlit as st
import utils
import datetime

def render():
    # 进入页面时，清除红点
    utils.update_user_visit_time(st.session_state.nickname, "task")
    
    # ---------- 页面顶部锚点（回顶部用） ----------
    st.markdown('<a id="top"></a>', unsafe_allow_html=True)
    
    st.title("🏫 任务广场")
    st.caption("这里只显示「待接单」的需求，先到先得！")
    
    # ---------- 发布表单 ----------
    with st.expander("📝 发布新需求", expanded=False):
        with st.form("publish_form"):
            col1, col2 = st.columns([3, 1])
            with col1:
                task_title = st.text_input("标题", placeholder="例如：代拿,代买,跑腿等")
            with col2:
                task_reward = st.text_input("报酬", placeholder="例如：5元")
            task_desc = st.text_area("描述", placeholder="详细描述你的需求...可附上联系方式")
            
            deadline = st.date_input(
                "截止日期（必填）", 
                value=datetime.date.today(),
                help="超过此日期任务将自动从广场消失"
            )
            
            uploaded_file = st.file_uploader(
                "📷 配图（可选）", 
                type=["jpg", "jpeg", "png", "webp"],
                help="上传图片，系统会自动压缩"
            )
            
            if st.form_submit_button("发布"):
                if task_title and task_desc:
                    image_url = None
                    if uploaded_file is not None:
                        file_bytes = uploaded_file.getvalue()
                        image_url = utils.upload_image_to_supabase(
                            file_bytes, 
                            "task_images", 
                            st.session_state.nickname
                        )
                        if image_url:
                            st.success("📷 图片上传成功！")
                        else:
                            st.warning("图片上传失败，任务将不带图片发布")
                    
                    deadline_dt = datetime.datetime.combine(deadline, datetime.time(23, 59, 59))
                    deadline_str = deadline_dt.isoformat()
                    full_desc = f"【报酬：{task_reward if task_reward else '面议'}】\n{task_desc}"
                    
                    if utils.add_task(task_title, full_desc, st.session_state.nickname, deadline_str, image_url):
                        st.success("发布成功！")
                        st.rerun()
                    else:
                        st.error("发布失败")
                else:
                    st.warning("请填完整")
    
    # ---------- 搜索 + 排序（新增） ----------
    col_search, col_sort = st.columns([3, 1])
    with col_search:
        search_keyword = st.text_input(
            "🔍 搜索任务", 
            placeholder="输入关键词搜索标题或描述...",
            key="task_search_input"
        )
    with col_sort:
        sort_option = st.selectbox(
            "排序方式",
            ["最新发布", "即将截止"],
            key="task_sort_select"
        )
    
    # ---------- 任务列表（分页加载） ----------
    if 'task_page' not in st.session_state:
        st.session_state.task_page = 1
    
    # 调用升级后的查询函数
    tasks, total = utils.get_public_tasks_page(
        st.session_state.task_page, 
        per_page=10,
        sort_by=sort_option,
        keyword=search_keyword
    )
    
    if not tasks:
        st.info("🎉 没有找到匹配的任务")
    else:
        for task in tasks:
            with st.container(border=True):
                if task.get('image_url'):
                    st.image(task['image_url'], width=200, caption="配图")
                    
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
        
        # 加载更多
        if st.session_state.task_page * 10 < total:
            if st.button("📥 加载更多任务"):
                st.session_state.task_page += 1
                st.rerun()
        else:
            st.caption("— 已加载全部任务 —")
    
    # ---------- 回顶部按钮 ----------
    st.markdown(
        '<a href="#top" style="display:block;text-align:center;padding:12px;'
        'background:#f0f2f6;border-radius:8px;text-decoration:none;color:#333;'
        'margin-top:20px;font-size:16px;">⬆ 回到顶部</a>',
        unsafe_allow_html=True
    )