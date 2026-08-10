# ==========================================
# 1. 导入工具箱
# ==========================================
import streamlit as st
import datetime
import hashlib
import requests
import json

# ==========================================
# 2. Supabase 配置
# ==========================================
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

def get_headers():
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }

# ==========================================
# 3. 辅助函数（用户认证 + 任务功能）
# ==========================================

def hash_password(pwd):
    return hashlib.sha256(pwd.encode()).hexdigest()

# ----- 注册 -----
def register_user(username, password, nickname):
    url = f"{SUPABASE_URL}/users"
    data = {"username": username, "password": hash_password(password), "nickname": nickname}
    try:
        response = requests.post(url, headers=get_headers(), json=data)
        return response.status_code in [200, 201]
    except:
        return False

# ----- 登录 -----
def login_user(username, password):
    url = f"{SUPABASE_URL}/users?select=nickname&username=eq.{username}&password=eq.{hash_password(password)}"
    try:
        response = requests.get(url, headers=get_headers())
        if response.status_code == 200 and response.json():
            return response.json()[0]["nickname"]
        return None
    except:
        return None

# ----- 任务相关（不变）-----
def add_task(title, desc, publisher):
    url = f"{SUPABASE_URL}/tasks"
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    data = {"title": title, "description": desc, "publisher": publisher, "pub_time": now, "status": "待接单", "taker": ""}
    try:
        response = requests.post(url, headers=get_headers(), json=data)
        return response.status_code in [200, 201]
    except:
        return False

def get_public_tasks():
    url = f"{SUPABASE_URL}/tasks?select=id,title,description,publisher,pub_time&status=eq.待接单&order=id.desc"
    try:
        response = requests.get(url, headers=get_headers())
        return response.json() if response.status_code == 200 else []
    except:
        return []

def get_my_published_tasks(nickname):
    url = f"{SUPABASE_URL}/tasks?select=*&publisher=eq.{nickname}&status=neq.已完成&order=id.desc"
    try:
        response = requests.get(url, headers=get_headers())
        return response.json() if response.status_code == 200 else []
    except:
        return []

def get_my_taken_tasks(nickname):
    url = f"{SUPABASE_URL}/tasks?select=*&taker=eq.{nickname}&status=neq.已完成&order=id.desc"
    try:
        response = requests.get(url, headers=get_headers())
        return response.json() if response.status_code == 200 else []
    except:
        return []

def accept_task(task_id, taker):
    url_check = f"{SUPABASE_URL}/tasks?select=publisher,status&id=eq.{task_id}"
    try:
        response = requests.get(url_check, headers=get_headers())
        if response.status_code != 200:
            return False, "查询失败"
        data = response.json()
        if not data:
            return False, "任务不存在"
        task = data[0]
        if task["publisher"] == taker:
            return False, "不能接自己的单！"
        if task["status"] != "待接单":
            return False, "已被接走！"
        url_update = f"{SUPABASE_URL}/tasks?id=eq.{task_id}"
        response = requests.patch(url_update, headers=get_headers(), json={"status": "已接单", "taker": taker})
        return (True, "接单成功！") if response.status_code in [200, 204] else (False, "更新失败")
    except:
        return False, "出错"

def complete_task(task_id, current_user):
    url_check = f"{SUPABASE_URL}/tasks?select=publisher&id=eq.{task_id}"
    try:
        response = requests.get(url_check, headers=get_headers())
        if response.status_code != 200:
            return False, "查询失败"
        data = response.json()
        if not data or data[0]["publisher"] != current_user:
            return False, "无权限"
        url_update = f"{SUPABASE_URL}/tasks?id=eq.{task_id}"
        response = requests.patch(url_update, headers=get_headers(), json={"status": "已完成"})
        return (True, "🎉 已完成！") if response.status_code in [200, 204] else (False, "更新失败")
    except:
        return False, "出错"

# ==========================================
# 4. ===== 校园圈相关函数（新增）=====
# ==========================================

# ----- 发布帖子 -----
def add_post(user_id, content, is_anonymous):
    url = f"{SUPABASE_URL}/posts"
    data = {
        "user_id": user_id,
        "content": content,
        "is_anonymous": is_anonymous,
        "created_at": datetime.datetime.now().isoformat()
    }
    try:
        response = requests.post(url, headers=get_headers(), json=data)
        return response.status_code in [200, 201]
    except:
        return False

# ----- 获取所有帖子（含评论数）-----
def get_all_posts():
    # 先查帖子
    url_posts = f"{SUPABASE_URL}/posts?select=*&status=eq.正常&order=created_at.desc"
    try:
        response = requests.get(url_posts, headers=get_headers())
        if response.status_code != 200:
            return []
        posts = response.json()
        
        # 对每个帖子，查询评论数
        for post in posts:
            url_count = f"{SUPABASE_URL}/comments?select=id&post_id=eq.{post['id']}&status=eq.正常"
            count_resp = requests.get(url_count, headers=get_headers())
            post["comment_count"] = len(count_resp.json()) if count_resp.status_code == 200 else 0
            
            # 如果是匿名，隐藏发布者
            if post["is_anonymous"]:
                post["display_name"] = "匿名同学"
            else:
                # 根据 user_id 查昵称
                url_user = f"{SUPABASE_URL}/users?select=nickname&username=eq.{post['user_id']}"
                user_resp = requests.get(url_user, headers=get_headers())
                if user_resp.status_code == 200 and user_resp.json():
                    post["display_name"] = user_resp.json()[0]["nickname"]
                else:
                    post["display_name"] = post["user_id"]
        return posts
    except:
        return []

# ----- 点赞/取消点赞（简化版：只增不减）-----
def like_post(post_id):
    # 先查当前点赞数
    url_get = f"{SUPABASE_URL}/posts?select=like_count&id=eq.{post_id}"
    try:
        resp = requests.get(url_get, headers=get_headers())
        if resp.status_code != 200:
            return False
        current = resp.json()[0]["like_count"] if resp.json() else 0
        url_update = f"{SUPABASE_URL}/posts?id=eq.{post_id}"
        resp = requests.patch(url_update, headers=get_headers(), json={"like_count": current + 1})
        return resp.status_code in [200, 204]
    except:
        return False

# ----- 发表评论 -----
def add_comment(post_id, user_id, content):
    url = f"{SUPABASE_URL}/comments"
    data = {
        "post_id": post_id,
        "user_id": user_id,
        "content": content,
        "created_at": datetime.datetime.now().isoformat()
    }
    try:
        response = requests.post(url, headers=get_headers(), json=data)
        return response.status_code in [200, 201]
    except:
        return False

# ----- 获取某个帖子的所有评论 -----
def get_comments(post_id):
    url = f"{SUPABASE_URL}/comments?select=*&post_id=eq.{post_id}&status=eq.正常&order=created_at.asc"
    try:
        response = requests.get(url, headers=get_headers())
        if response.status_code != 200:
            return []
        comments = response.json()
        # 补充每个评论者的昵称
        for comment in comments:
            url_user = f"{SUPABASE_URL}/users?select=nickname&username=eq.{comment['user_id']}"
            user_resp = requests.get(url_user, headers=get_headers())
            if user_resp.status_code == 200 and user_resp.json():
                comment["display_name"] = user_resp.json()[0]["nickname"]
            else:
                comment["display_name"] = comment["user_id"]
        return comments
    except:
        return []

# ==========================================
# 5. 网页界面
# ==========================================
st.set_page_config(page_title="校园互助站", page_icon="🏫")

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.nickname = ""

if not st.session_state.logged_in:
    if "user" in st.query_params:
        st.session_state.logged_in = True
        st.session_state.nickname = st.query_params["user"]

st.sidebar.title("🏫 校园互助")

if st.session_state.logged_in:
    st.sidebar.success(f"👋 {st.session_state.nickname}")
    if st.sidebar.button("🚪 退出登录"):
        st.session_state.logged_in = False
        st.session_state.nickname = ""
        st.query_params.clear()
        st.rerun()
    
    # ===== 导航栏新增“校园圈”=====
    page = st.sidebar.radio("导航", ["📋 任务广场", "🎉 校园圈", "👤 个人中心"])
else:
    # ----- 登录/注册界面（不变）-----
    st.title("🔐 请先登录")
    col1, col2 = st.columns(2)
    with col1:
        with st.form("login_form"):
            username = st.text_input("账号")
            password = st.text_input("密码", type="password")
            if st.form_submit_button("登录"):
                nickname = login_user(username, password)
                if nickname:
                    st.session_state.logged_in = True
                    st.session_state.nickname = nickname
                    st.query_params["user"] = username
                    st.rerun()
                else:
                    st.error("账号或密码错误")
    with col2:
        with st.form("register_form"):
            new_user = st.text_input("设置账号")
            new_pwd = st.text_input("设置密码", type="password")
            new_nick = st.text_input("昵称")
            if st.form_submit_button("注册"):
                if new_user and new_pwd and new_nick:
                    if register_user(new_user, new_pwd, new_nick):
                        st.success("注册成功，请登录！")
                    else:
                        st.error("账号已存在")
                else:
                    st.warning("请填完整")
    st.sidebar.info("👈 登录后使用完整功能")
    st.stop()

# ==========================================
# 6. 页面路由
# ==========================================

# ----- 任务广场（不变）-----
if page == "📋 任务广场":
    st.title("🏫 任务广场")
    st.caption("这里只显示「待接单」的需求，先到先得！")
    
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
                    if add_task(task_title, full_desc, st.session_state.nickname):
                        st.success("发布成功！")
                        st.rerun()
                    else:
                        st.error("发布失败")
                else:
                    st.warning("请填完整")
    
    tasks = get_public_tasks()
    if not tasks:
        st.info("🎉 广场很干净，暂无待接单的需求。")
    else:
        for task in tasks:
            task_id = task["id"]
            with st.container(border=True):
                col_left, col_right = st.columns([4, 1])
                with col_left:
                    st.markdown(f"🟢 **{task['title']}**")
                    st.caption(f"👤 {task['publisher']}  |  🕒 {task['pub_time']}")
                    st.text(task['description'])
                with col_right:
                    if st.button("✋ 我来接", key=f"pub_{task_id}"):
                        success, msg = accept_task(task_id, st.session_state.nickname)
                        if success:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)

# ==========================================
# 7. ===== 校园圈页面（新增）=====
# ==========================================
elif page == "🎉 校园圈":
    st.title("🎉 校园圈")
    st.caption("匿名吐槽 · 实名评论 · 分享校园生活")
    
    # ----- 发帖区域 -----
    with st.expander("📝 发布新帖子", expanded=False):
        with st.form("post_form"):
            content = st.text_area("内容", placeholder="分享你的想法、吐槽、求助...")
            is_anonymous = st.checkbox("匿名发布（不显示你的昵称）", value=True)
            submitted = st.form_submit_button("发布")
            if submitted and content.strip():
                # 获取当前用户的真实用户名（用于后台识别）
                # 注意：这里用 session_state 里的 nickname 作为 user_id，但实际应该用 username
                # 因代码里只存了 nickname，我们暂时用 nickname 当 user_id（后续可优化）
                user_id = st.session_state.nickname
                if add_post(user_id, content, is_anonymous):
                    st.success("发布成功！")
                    st.rerun()
                else:
                    st.error("发布失败，请重试")
            elif submitted:
                st.warning("内容不能为空")
    
    # ----- 显示帖子列表 -----
    posts = get_all_posts()
    if not posts:
        st.info("📭 暂无帖子，快来发表第一条动态吧！")
    else:
        for post in posts:
            with st.container(border=True):
                # 帖子头部
                col1, col2 = st.columns([3, 1])
                with col1:
                    if post["is_anonymous"]:
                        st.markdown(f"**🕵️ 匿名同学** · {post['created_at'][:16]}")
                    else:
                        st.markdown(f"**👤 {post['display_name']}** · {post['created_at'][:16]}")
                with col2:
                    st.caption(f"❤️ {post['like_count']}  💬 {post['comment_count']}")
                
                # 帖子内容
                st.markdown(f"_{post['content']}_")
                
                # 操作按钮
                col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 2])
                with col_btn1:
                    if st.button("❤️ 点赞", key=f"like_{post['id']}"):
                        if like_post(post['id']):
                            st.rerun()
                        else:
                            st.error("点赞失败")
                with col_btn2:
                    # 展开评论区的按钮（用 session_state 控制展开）
                    comment_key = f"show_comment_{post['id']}"
                    if comment_key not in st.session_state:
                        st.session_state[comment_key] = False
                    if st.button("💬 评论", key=f"comment_btn_{post['id']}"):
                        st.session_state[comment_key] = not st.session_state[comment_key]
                        st.rerun()
                
                # ----- 评论区域（展开）-----
                if st.session_state.get(comment_key, False):
                    st.divider()
                    st.caption("💬 评论区（实名评论）")
                    
                    # 显示已有评论
                    comments = get_comments(post['id'])
                    if comments:
                        for cmt in comments:
                            st.markdown(f"**{cmt['display_name']}** · {cmt['created_at'][:16]}")
                            st.markdown(f"> {cmt['content']}")
                    else:
                        st.caption("暂无评论，来说点什么吧！")
                    
                    # 评论输入框
                    with st.form(key=f"comment_form_{post['id']}"):
                        comment_content = st.text_input("写评论...", key=f"comment_input_{post['id']}")
                        if st.form_submit_button("发送评论"):
                            if comment_content.strip():
                                user_id = st.session_state.nickname
                                if add_comment(post['id'], user_id, comment_content):
                                    st.success("评论成功！")
                                    st.rerun()
                                else:
                                    st.error("评论失败")
                            else:
                                st.warning("评论内容不能为空")

# ==========================================
# 8. 个人中心（增加显示我的帖子）
# ==========================================
elif page == "👤 个人中心":
    st.title("👤 个人中心")
    tab1, tab2, tab3 = st.tabs(["📤 我发布的", "📥 我接的单", "📝 我的帖子"])
    
    with tab1:
        st.caption("这里显示你「发布且未完成」的需求。")
        my_published = get_my_published_tasks(st.session_state.nickname)
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
                    with col2:
                        if task["status"] == "已接单":
                            if st.button("✅ 已完成", key=f"complete_{task['id']}"):
                                success, msg = complete_task(task['id'], st.session_state.nickname)
                                if success:
                                    st.success(msg)
                                    st.rerun()
                                else:
                                    st.error(msg)
                        else:
                            st.button("⏳ 等待接单", disabled=True)
    
    with tab2:
        st.caption("这里显示你「接单且未完成」的需求。")
        my_taken = get_my_taken_tasks(st.session_state.nickname)
        if not my_taken:
            st.info("你还没有接单，去广场逛逛吧！")
        else:
            for task in my_taken:
                with st.container(border=True):
                    st.markdown(f"🟡 **{task['title']}** (已接单)")
                    st.caption(f"👤 发布者：{task['publisher']}  |  📅 {task['pub_time']}")
                    st.text(task['description'])
                    st.info("💬 请通过线下或私信联系发布者，完成交易。")
    
    with tab3:
        st.caption("这里显示你在「校园圈」发布的所有帖子（含已删除的）。")
        # 查询当前用户的所有帖子
        url = f"{SUPABASE_URL}/posts?select=*&user_id=eq.{st.session_state.nickname}&order=created_at.desc"
        try:
            response = requests.get(url, headers=get_headers())
            if response.status_code == 200:
                my_posts = response.json()
                if not my_posts:
                    st.info("你还没有发布过帖子。")
                else:
                    for p in my_posts:
                        with st.container(border=True):
                            status_tag = "🟢 正常" if p["status"] == "正常" else "🔴 已删除"
                            st.markdown(f"**{p['content'][:50]}...**  {status_tag}")
                            st.caption(f"📅 {p['created_at'][:16]}  ❤️ {p['like_count']}  🕵️ {'匿名' if p['is_anonymous'] else '实名'}")
            else:
                st.error("加载失败")
        except:
            st.error("加载失败")