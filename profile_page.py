# ==========================================
# profile_page.py - 个人中心页面
# ==========================================
import streamlit as st
import utils
import requests

def render():
    st.title("👤 个人中心")
        # ----- 修改昵称（整合自“我的资料”）-----
    with st.expander("✏️ 修改昵称", expanded=False):
        # 获取当前用户信息（只查昵称）
        username = st.session_state.nickname
        url = f"{utils.SUPABASE_URL}/users?select=nickname&username=eq.{username}"
        try:
            response = requests.get(url, headers=utils.get_headers())
            if response.status_code == 200 and response.json():
                current_nick = response.json()[0]['nickname']
            else:
                current_nick = username
        except:
            current_nick = username

        with st.form("update_nickname_from_profile"):
            new_nick = st.text_input("新昵称", value=current_nick)
            if st.form_submit_button("更新昵称"):
                if new_nick.strip():
                    url_update = f"{utils.SUPABASE_URL}/users?username=eq.{username}"
                    data = {"nickname": new_nick}
                    resp = requests.patch(url_update, headers=utils.get_headers(), json=data)
                    if resp.status_code in [200, 204]:
                        st.success("昵称更新成功！")
                        st.session_state.nickname = new_nick
                        st.rerun()
                    else:
                        st.error("更新失败")
                else:
                    st.warning("昵称不能为空")
    tab1, tab2, tab3 = st.tabs(["📤 我发布的", "📥 我接的单", "📝 我的帖子"])
    
    with tab1:
        st.caption("这里显示你「发布且未完成」的需求。")
        my_published = utils.get_my_published_tasks(st.session_state.nickname)
        if not my_published:
            st.info("你还没有发布进行中的订单。")
        else:
            for task in my_published:
                with st.container(border=True):
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        status_icon = "🟢" if task["status"] == "待接单" else "🟡"
                        st.markdown(f"{status_icon} **{task['title']}**")
                        st.caption(f"📅 {task['pub_time']}")
                        st.text(task['description'])
                        if task["status"] == "已接单" and task.get("taker"):
                            st.success(f"🤝 接单同学：**{task['taker']}**")
                            # 添加私聊入口
                            if st.button("💬 私聊", key=f"chat_from_task_{task['id']}"):
                                st.query_params["task_id"] = task['id']
                                st.query_params["other_user"] = task['taker']
                                st.session_state.page = "💬 消息"
                                st.rerun()
                    

                    with col2:
                        if task["status"] == "已接单":
                            # 已完成按钮
                            if st.button("✅ 已完成", key=f"complete_{task['id']}"):
                                success, msg = utils.complete_task(task['id'], st.session_state.nickname)
                                if success:
                                    st.success(msg)
                                    st.rerun()
                                else:
                                    st.error(msg)
                            # 新增：取消接单按钮（仅限接单者操作）
                            if task.get('taker') == st.session_state.nickname:
                                if st.button("↩️ 取消接单", key=f"cancel_taken_{task['id']}"):
                                    success, msg = utils.cancel_taken_task(task['id'], st.session_state.nickname)
                                    if success:
                                        st.success(msg)
                                        st.rerun()
                                    else:
                                        st.error(msg)
                        elif task["status"] == "待接单":
                            st.button("⏳ 等待接单", disabled=True, key=f"waiting_{task['id']}")
                            # 发布者可删除自己的待接单任务
                            if task['publisher'] == st.session_state.nickname:
                                if st.button("🗑️ 删除", key=f"del_my_task_{task['id']}"):
                                    success, msg = utils.delete_task(task['id'], st.session_state.nickname)
                                    if success:
                                        st.success(msg)
                                        st.rerun()
                                    else:
                                        st.error(msg)
    
    with tab2:
        st.caption("这里显示你「接单且未完成」的需求。")
        my_taken = utils.get_my_taken_tasks(st.session_state.nickname)
        if not my_taken:
            st.info("你还没有接单，去广场逛逛吧！")
        else:
            for task in my_taken:
                with st.container(border=True):
                    st.markdown(f"🟡 **{task['title']}** (已接单)")
                    st.caption(f"👤 发布者：{task['publisher']}  |  📅 {task['pub_time']}")
                    st.text(task['description'])
                    # 添加私聊入口
                    if st.button("💬 私聊发布者", key=f"chat_from_taken_{task['id']}"):
                        st.query_params["task_id"] = task['id']
                        st.query_params["other_user"] = task['publisher']
                        st.session_state.page = "💬 消息"
                        st.rerun()
                    st.info("💬 请通过线下或私信联系发布者，完成交易。")
    
    with tab3:
        st.caption("这里显示你在「校园圈」发布的正常帖子（已删除的不显示）。")
        url = f"{utils.SUPABASE_URL}/posts?select=*&user_id=eq.{st.session_state.nickname}&status=eq.正常&order=created_at.desc"
        try:
            response = requests.get(url, headers=utils.get_headers())
            if response.status_code == 200:
                my_posts = response.json()
                if not my_posts:
                    st.info("你还没有发布过帖子。")
                else:
                    for p in my_posts:
                        with st.container(border=True):
                            category_emoji = {"吐槽": "💢", "求助": "🆘", "交友": "🤝", "表白": "❤️", "其他": "📌"}
                            cat_display = f"{category_emoji.get(p.get('category', '其他'), '📌')} {p.get('category', '其他')}"
                            st.markdown(f"**{p['content'][:50]}...**  {cat_display}")
                            st.caption(f"📅 {p['created_at'][:16]}  ❤️ {p['like_count']}  🕵️ {'匿名' if p['is_anonymous'] else '实名'}")
                            if st.button(f"🗑️ 删除此帖", key=f"del_profile_{p['id']}"):
                                success, msg = utils.delete_post(p['id'], st.session_state.nickname)
                                if success:
                                    st.success(msg)
                                    st.rerun()
                                else:
                                    st.error(msg)
            else:
                st.error("加载失败")
        except:
            st.error("加载失败")