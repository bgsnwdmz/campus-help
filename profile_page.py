# ==========================================
# profile_page.py - 个人中心页面
# ==========================================
import streamlit as st
import utils
import requests

def render():
    st.title("👤 个人中心")
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
                            if st.button("✅ 已完成", key=f"complete_{task['id']}"):
                                success, msg = utils.complete_task(task['id'], st.session_state.nickname)
                                if success:
                                    st.success(msg)
                                    st.rerun()
                                else:
                                    st.error(msg)
                        else:
                            st.button("⏳ 等待接单", disabled=True)
    
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