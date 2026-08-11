# ==========================================
# post_page.py - 校园圈页面
# ==========================================
import streamlit as st
import utils

def render():
    # 进入页面时，清除红点
    utils.update_user_visit_time(st.session_state.nickname, "post")
    
    # 检查是否在查看详情页
    if "post_id" in st.query_params:
        # ----- 详情页模式 -----
        post_id = int(st.query_params["post_id"])
        post = utils.get_post_by_id(post_id)
        
        if not post:
            st.error("帖子不存在或已被删除")
            if st.button("返回校园圈"):
                st.query_params.clear()
                st.rerun()
            return
        
        st.title("📄 帖子详情")
        if st.button("← 返回校园圈"):
            st.query_params.clear()
            st.rerun()
        
        st.divider()
        
        col1, col2 = st.columns([4, 1])
        with col1:
            st.markdown(f"**{post['display_name']}** · {post['created_at'][:16]}")
        with col2:
            st.caption(f"❤️ {post['like_count']}  💬 {post.get('comment_count', 0)}")
        
        st.markdown(f"_{post['content']}_")
        
        col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 2])
        with col_btn1:
            if st.button("❤️ 点赞"):
                if utils.like_post(post_id):
                    st.rerun()
                else:
                    st.error("点赞失败")
        with col_btn2:
            if post['user_id'] == st.session_state.nickname:
                if st.button("🗑️ 删除帖子"):
                    success, msg = utils.delete_post(post_id, st.session_state.nickname)
                    if success:
                        st.success(msg)
                        st.query_params.clear()
                        st.rerun()
                    else:
                        st.error(msg)
        
        st.divider()
        st.subheader("💬 评论区")
        comments = utils.get_comments(post_id)
        if comments:
            for cmt in comments:
                st.markdown(f"**{cmt['display_name']}** · {cmt['created_at'][:16]}")
                st.markdown(f"> {cmt['content']}")
        else:
            st.caption("暂无评论，来说点什么吧！")
        
        with st.form(key=f"comment_form_detail"):
            comment_content = st.text_input("写评论...")
            if st.form_submit_button("发送评论"):
                if comment_content.strip():
                    if utils.add_comment(post_id, st.session_state.nickname, comment_content):
                        st.success("评论成功！")
                        st.rerun()
                    else:
                        st.error("评论失败")
                else:
                    st.warning("评论内容不能为空")
    else:
        # ----- 列表模式 -----
        st.title("🎉 校园圈")
        st.caption("匿名吐槽 · 实名评论 · 分享校园生活")
        
        with st.expander("📝 发布新帖子", expanded=False):
            with st.form("post_form"):
                content = st.text_area("内容", placeholder="分享你的想法...")
                is_anonymous = st.checkbox("匿名发布", value=True)
                if st.form_submit_button("发布"):
                    if content.strip():
                        if utils.add_post(st.session_state.nickname, content, is_anonymous):
                            st.success("发布成功！")
                            st.rerun()
                        else:
                            st.error("发布失败")
                    else:
                        st.warning("内容不能为空")
        
        posts = utils.get_all_posts()
        if not posts:
            st.info("📭 暂无帖子")
        else:
            for post in posts:
                with st.container(border=True):
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.markdown(f"**{post['display_name']}** · {post['created_at'][:16]}")
                    with col2:
                        st.caption(f"❤️ {post['like_count']}  💬 {post['comment_count']}")
                    
                    content = post['content']
                    if len(content) > 200:
                        st.markdown(f"_{content[:200]}..._")
                        if st.button("📖 查看全文", key=f"readmore_{post['id']}"):
                            st.query_params["post_id"] = post['id']
                            st.rerun()
                    else:
                        st.markdown(f"_{content}_")
                    
                    col_btn1, col_btn2 = st.columns([1, 4])
                    with col_btn1:
                        if st.button("❤️", key=f"like_list_{post['id']}"):
                            if utils.like_post(post['id']):
                                st.rerun()
                    if post['user_id'] == st.session_state.nickname:
                        with col_btn2:
                            if st.button("🗑️ 删除", key=f"del_list_{post['id']}"):
                                success, msg = utils.delete_post(post['id'], st.session_state.nickname)
                                if success:
                                    st.success(msg)
                                    st.rerun()
                                else:
                                    st.error(msg)