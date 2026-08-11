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
                       
 # 评论区域        
st.divider()
st.subheader("💬 评论区")
comments = utils.get_comments_with_replies(post_id)
if comments:
    for cmt in comments:
        # 缩进显示回复
        indent = "  " * (1 if cmt.get('parent_id') else 0)
        prefix = f"回复 @{cmt['reply_to']}：" if cmt.get('reply_to') else ""
        st.markdown(f"{indent}**{cmt['display_name']}** · {cmt['created_at'][:16]}")
        st.markdown(f"{indent}> {prefix}{cmt['content']}")
        
        # 回复按钮（用户点击后自动填充）
        if st.button(f"💬 回复", key=f"reply_btn_{cmt['id']}"):
            # 使用 session_state 临时存储要回复的信息
            st.session_state["reply_target"] = {
                "parent_id": cmt['id'],
                "reply_to": cmt['user_id'],
                "display_name": cmt['display_name']
            }
            st.rerun()
        st.divider()
else:
    st.caption("暂无评论，来说点什么吧！")

# 评论输入框（如果有回复目标则自动带@）
reply_info = st.session_state.get("reply_target")
if reply_info:
    st.info(f"正在回复 @{reply_info['display_name']}，取消回复请刷新页面")
    default_content = f"@{reply_info['display_name']} "
else:
    default_content = ""

with st.form(key=f"comment_form_detail"):
    comment_content = st.text_input("写评论...", value=default_content)
    if st.form_submit_button("发送评论"):
        if comment_content.strip():
            parent_id = reply_info['parent_id'] if reply_info else None
            reply_to = reply_info['reply_to'] if reply_info else None
            if utils.add_comment_with_parent(post_id, st.session_state.nickname, comment_content, parent_id, reply_to):
                st.success("评论成功！")
                st.session_state["reply_target"] = None  # 清除回复状态
                st.rerun()
            else:
                st.error("评论失败")
        else:
            st.warning("评论内容不能为空")
        

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
        # ----- 发帖部分-----
         with st.expander("📝 发布新帖子", expanded=False):
         with st.form("post_form"):
        content = st.text_area("内容", placeholder="分享你的想法...")
        
        # ===== 新增分类下拉框 =====
        categories = ["吐槽", "求助", "交友", "表白", "其他"]
        category = st.selectbox("帖子分类", categories, index=0)
        
        is_anonymous = st.checkbox("匿名发布", value=True)
        if st.form_submit_button("发布"):
            if content.strip():
                # 调用时传入 category
                if utils.add_post(st.session_state.nickname, content, is_anonymous, category):
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

        category_emoji = {
               "吐槽": "💢", "求助": "🆘", "交友": "🤝", "表白": "❤️", "其他": "📌"
           }
         category_display = f"{category_emoji.get(post.get('category', '其他'), '📌')} {post.get('category', '其他')}"
        st.markdown(f"**{post['display_name']}** · {post['created_at'][:16]} · `{category_display}`")


         # ===== 点赞按钮 ===== 
         col_btn1, col_btn2 = st.columns([1, 4])
           with col_btn1:
        # 检查当前用户是否已点赞
            has_liked = utils.has_user_liked(post['id'], st.session_state.nickname)
            button_label = "❤️" if has_liked else "🤍"
    
             if st.button(button_label, key=f"like_list_{post['id']}"):
            success, msg, new_count = utils.toggle_like(post['id'], st.session_state.nickname)
         if success:
            st.session_state[f"like_count_{post['id']}"] = new_count
            st.rerun()
         else:
            st.error(msg)