# ==========================================
# admin_page.py - 管理后台（仅管理员可见）
# ==========================================
import streamlit as st
import utils
import pandas as pd
import datetime

def render():
    st.title("⚙️ 管理后台")
    st.caption(f"当前管理员：{st.session_state.nickname}")

    # 防止非管理员直接访问（双重保险）
    if not utils.is_admin_user(st.session_state.nickname):
        st.error("⛔ 你没有权限访问此页面")
        return

    tab1, tab2, tab3, tab4 ,tab5= st.tabs(["👥 用户管理", "📋 任务管理", "🎉 帖子管理", "📢 反馈管理", "📊 统计统计"])

    # ---------- Tab 1: 用户管理 ----------
    with tab1:
        st.subheader("所有注册用户")
        users = utils.admin_get_all_users()
        if not users:
            st.info("暂无用户")
        else:
            # 用表格展示用户列表
            user_data = []
            for u in users:
                user_data.append({
                    "账号": u.get("username", ""),
                    "昵称": u.get("nickname", ""),
                    "最近访问任务": u.get("last_task_visit", "")[:16] if u.get("last_task_visit") else "无",
                    "最近访问帖子": u.get("last_post_visit", "")[:16] if u.get("last_post_visit") else "无",
                })
            st.dataframe(user_data, use_container_width=True)

    # ---------- Tab 2: 任务管理 ----------
    with tab2:
        st.subheader("所有任务（含已删除/已完成）")
        tasks = utils.admin_get_all_tasks()
        if not tasks:
            st.info("暂无任务")
        else:
            for task in tasks:
                with st.container(border=True):
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        # 根据状态显示不同图标
                        status_icon = {
                            "待接单": "🟢",
                            "已接单": "🟡",
                            "已完成": "✅",
                            "已删除": "❌"
                        }.get(task.get("status", ""), "⚪")
                        st.markdown(f"{status_icon} **{task['title']}** (ID: {task['id']})")
                        st.caption(f"发布者：{task['publisher']}  |  接单者：{task.get('taker', '无')}  |  截止：{task.get('deadline', '无')[:10] if task.get('deadline') else '无'}")
                        st.text(task.get('description', '')[:100] + ("..." if len(task.get('description', '')) > 100 else ""))
                    with col2:
                        # 强制删除按钮（仅限非待接单状态，或所有状态均可，这里保留全部删除能力）
                        if st.button(f"🗑️ 强制删除", key=f"admin_del_task_{task['id']}"):
                            if utils.admin_delete_task_force(task['id']):
                                st.success(f"任务 {task['id']} 已强制删除")
                                st.rerun()
                            else:
                                st.error("删除失败")
            st.caption("⚠️ 强制删除会直接从数据库移除，无法恢复，请谨慎操作。")

    # ---------- Tab 3: 帖子管理 ----------
    with tab3:
        st.subheader("所有帖子（含已删除）")
        posts = utils.admin_get_all_posts()
        if not posts:
            st.info("暂无帖子")
        else:
            for post in posts:
                with st.container(border=True):
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        status_tag = "❌ 已删除" if post.get("status") == "已删除" else "✅ 正常"
                        st.markdown(f"**{status_tag}** 用户：{post['user_id']}  |  {post['created_at'][:16]}")
                        st.text(post.get('content', '')[:150] + ("..." if len(post.get('content', '')) > 150 else ""))
                        st.caption(f"点赞：{post.get('like_count', 0)}  |  匿名：{'是' if post.get('is_anonymous') else '否'}  |  分类：{post.get('category', '其他')}")
                    with col2:
                        if st.button(f"🗑️ 强制删除", key=f"admin_del_post_{post['id']}"):
                            if utils.admin_delete_post_force(post['id']):
                                st.success(f"帖子 {post['id']} 已强制删除")
                                st.rerun()
                            else:
                                st.error("删除失败")

    # ---------- Tab 4: 反馈管理 ----------
    with tab4:
        st.subheader("用户反馈列表")
        feedbacks = utils.admin_get_all_feedbacks()
        if not feedbacks:
            st.info("暂无反馈")
        else:
            for fb in feedbacks:
                with st.container(border=True):
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        status = fb.get("status", "待处理")
                        status_emoji = "🟡" if status == "待处理" else "✅"
                        st.markdown(f"{status_emoji} **{fb['user_id']}**  ·  {fb['created_at'][:16]}")
                        st.text(fb.get('content', ''))
                    with col2:
                        if status == "待处理":
                            if st.button(f"✅ 标记已处理", key=f"admin_mark_fb_{fb['id']}"):
                                if utils.admin_mark_feedback_done(fb['id']):
                                    st.success("已标记")
                                    st.rerun()
                                else:
                                    st.error("操作失败")
                        else:
                            st.caption("已处理 ✅")
          # ---------- Tab 5: 数据统计 ----------
    with tab5:
        st.subheader("📊 平台数据总览")
        
        # 获取统计数据
        stats = utils.admin_get_stats_summary()
        trend_df = utils.admin_get_daily_trends(days=7)
        
        # ----- 顶部指标卡（4列）-----
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("👥 注册用户", stats["total_users"])
        with col2:
            total_tasks = sum(stats["tasks"].values())
            st.metric("📋 总任务", total_tasks)
        with col3:
            total_posts = sum(stats["posts"].values())
            st.metric("🎉 总帖子", total_posts)
        with col4:
            total_fb = sum(stats["feedbacks"].values())
            st.metric("📢 总反馈", total_fb)
        
        st.divider()
        
        # ----- 第一行图表：任务状态分布 + 帖子状态分布 -----
        col_left, col_right = st.columns(2)
        
        with col_left:
            st.markdown("**📋 任务状态分布**")
            task_status_df = pd.DataFrame({
                "状态": list(stats["tasks"].keys()),
                "数量": list(stats["tasks"].values())
            })
            if task_status_df["数量"].sum() > 0:
                st.bar_chart(task_status_df.set_index("状态"))
            else:
                st.caption("暂无任务数据")
        
        with col_right:
            st.markdown("**🎉 帖子状态分布**")
            post_status_df = pd.DataFrame({
                "状态": list(stats["posts"].keys()),
                "数量": list(stats["posts"].values())
            })
            if post_status_df["数量"].sum() > 0:
                st.bar_chart(post_status_df.set_index("状态"))
            else:
                st.caption("暂无帖子数据")
        
        # ----- 第二行图表：近7天趋势 -----
        st.divider()
        st.markdown("**📈 近7天新增趋势**")
        if not trend_df.empty and (trend_df["新增任务"].sum() + trend_df["新增帖子"].sum()) > 0:
            # 绘制折线图
            st.line_chart(trend_df.set_index("日期显示")[["新增任务", "新增帖子"]])
            # 同时显示表格数据
            with st.expander("📋 查看详细数据"):
                st.dataframe(trend_df[["日期显示", "新增任务", "新增帖子"]], use_container_width=True)
        else:
            st.info("近7天暂无新增数据")                      