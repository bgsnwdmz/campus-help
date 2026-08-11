# ==========================================
# utils.py - 公共工具箱
# ==========================================
import streamlit as st
import requests
import datetime
import hashlib

# ---------- 配置 ----------
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

def get_headers():
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }

def hash_password(pwd):
    return hashlib.sha256(pwd.encode()).hexdigest()

# ---------- 用户相关 ----------
def register_user(username, password, nickname):
    url = f"{SUPABASE_URL}/users"
    now = datetime.datetime.now().isoformat()
    data = {
        "username": username,
        "password": hash_password(password),
        "nickname": nickname,
        "last_task_visit": now,
        "last_post_visit": now
    }
    try:
        response = requests.post(url, headers=get_headers(), json=data)
        return response.status_code in [200, 201]
    except:
        return False

def login_user(username, password):
    url = f"{SUPABASE_URL}/users?select=nickname,last_task_visit,last_post_visit&username=eq.{username}&password=eq.{hash_password(password)}"
    try:
        response = requests.get(url, headers=get_headers())
        if response.status_code == 200 and response.json():
            user = response.json()[0]
            return {
                "nickname": user["nickname"],
                "last_task_visit": user.get("last_task_visit"),
                "last_post_visit": user.get("last_post_visit")
            }
        return None
    except:
        return None

def update_user_visit_time(username, visit_type):
    now = datetime.datetime.now().isoformat()
    field = "last_task_visit" if visit_type == "task" else "last_post_visit"
    url = f"{SUPABASE_URL}/users?username=eq.{username}"
    try:
        response = requests.patch(url, headers=get_headers(), json={field: now})
        return response.status_code in [200, 204]
    except:
        return False

def get_user_visit_time(username, visit_type):
    field = "last_task_visit" if visit_type == "task" else "last_post_visit"
    url = f"{SUPABASE_URL}/users?select={field}&username=eq.{username}"
    try:
        response = requests.get(url, headers=get_headers())
        if response.status_code == 200 and response.json():
            return response.json()[0].get(field)
        return None
    except:
        return None

# ---------- 任务相关 ----------
@st.cache_data(ttl=60)
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

@st.cache_data(ttl=60)
def get_new_task_count(username):
    last_visit = get_user_visit_time(username, "task")
    if not last_visit:
        return 0
    url = f"{SUPABASE_URL}/tasks?select=id&status=eq.待接单&pub_time=gt.{last_visit}"
    try:
        response = requests.get(url, headers=get_headers())
        return len(response.json()) if response.status_code == 200 else 0
    except:
        return 0

# ---------- 帖子相关 ----------

def add_post(user_id, content, is_anonymous, category):
    url = f"{SUPABASE_URL}/posts"
    data = {
        "user_id": user_id,
        "content": content,
        "is_anonymous": is_anonymous,
        "category": category,  # 新增
        "created_at": datetime.datetime.now().isoformat()
    }
    try:
        response = requests.post(url, headers=get_headers(), json=data)
        return response.status_code in [200, 201]
    except:
        return False

@st.cache_data(ttl=60)
def get_all_posts(limit=50):
    url_posts = f"{SUPABASE_URL}/posts?select=*&status=eq.正常&order=created_at.desc&limit={limit}"
    try:
        response = requests.get(url_posts, headers=get_headers())
        if response.status_code != 200:
            return []
        posts = response.json()
        for post in posts:
            url_count = f"{SUPABASE_URL}/comments?select=id&post_id=eq.{post['id']}&status=eq.正常"
            count_resp = requests.get(url_count, headers=get_headers())
            post["comment_count"] = len(count_resp.json()) if count_resp.status_code == 200 else 0
            if post["is_anonymous"]:
                post["display_name"] = "匿名同学"
            else:
                url_user = f"{SUPABASE_URL}/users?select=nickname&username=eq.{post['user_id']}"
                user_resp = requests.get(url_user, headers=get_headers())
                if user_resp.status_code == 200 and user_resp.json():
                    post["display_name"] = user_resp.json()[0]["nickname"]
                else:
                    post["display_name"] = post["user_id"]
        return posts
    except:
        return []

def get_post_by_id(post_id):
    url = f"{SUPABASE_URL}/posts?select=*&id=eq.{post_id}&status=eq.正常"
    try:
        response = requests.get(url, headers=get_headers())
        if response.status_code != 200 or not response.json():
            return None
        post = response.json()[0]
        if post["is_anonymous"]:
            post["display_name"] = "匿名同学"
        else:
            url_user = f"{SUPABASE_URL}/users?select=nickname&username=eq.{post['user_id']}"
            user_resp = requests.get(url_user, headers=get_headers())
            if user_resp.status_code == 200 and user_resp.json():
                post["display_name"] = user_resp.json()[0]["nickname"]
            else:
                post["display_name"] = post["user_id"]
        return post
    except:
        return None

@st.cache_data(ttl=60)
def get_new_post_count(username):
    last_visit = get_user_visit_time(username, "post")
    if not last_visit:
        return 0
    url = f"{SUPABASE_URL}/posts?select=id&status=eq.正常&created_at=gt.{last_visit}"
    try:
        response = requests.get(url, headers=get_headers())
        return len(response.json()) if response.status_code == 200 else 0
    except:
        return 0

def delete_post(post_id, current_user):
    url_check = f"{SUPABASE_URL}/posts?select=user_id&id=eq.{post_id}"
    try:
        response = requests.get(url_check, headers=get_headers())
        if response.status_code != 200 or not response.json():
            return False, "帖子不存在"
        if response.json()[0]["user_id"] != current_user:
            return False, "你不是作者，无权删除"
        url_update = f"{SUPABASE_URL}/posts?id=eq.{post_id}"
        response = requests.patch(url_update, headers=get_headers(), json={"status": "已删除"})
        return (True, "删除成功") if response.status_code in [200, 204] else (False, "删除失败")
    except:
        return False, "出错"

def like_post(post_id):
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

def get_comments(post_id):
    url = f"{SUPABASE_URL}/comments?select=*&post_id=eq.{post_id}&status=eq.正常&order=created_at.asc"
    try:
        response = requests.get(url, headers=get_headers())
        if response.status_code != 200:
            return []
        comments = response.json()
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

# ----- 获取帖子（仅正常状态，供个人中心使用）-----
def get_my_posts_by_status(username, status_filter='正常'):
    """
    获取当前用户的所有帖子，可按状态过滤
    status_filter: '正常' 或 '已删除' 或 None（全部）
    """
    url = f"{SUPABASE_URL}/posts?select=*&user_id=eq.{username}&order=created_at.desc"
    if status_filter:
        url += f"&status=eq.{status_filter}"
    try:
        response = requests.get(url, headers=get_headers())
        return response.json() if response.status_code == 200 else []
    except:
        return []

# ----- 检查用户是否已点赞 -----
def has_user_liked(post_id, user_id):
    url = f"{SUPABASE_URL}/likes?select=id&post_id=eq.{post_id}&user_id=eq.{user_id}"
    try:
        response = requests.get(url, headers=get_headers())
        return len(response.json()) > 0 if response.status_code == 200 else False
    except:
        return False

# ----- 点赞（带防重复逻辑）-----
def toggle_like(post_id, user_id):
    """
    如果已点赞则取消点赞，否则点赞
    返回: (success, message, new_like_count)
    """
    # 1. 先检查是否已点赞
    if has_user_liked(post_id, user_id):
        # 取消点赞：删除记录
        url = f"{SUPABASE_URL}/likes?post_id=eq.{post_id}&user_id=eq.{user_id}"
        try:
            response = requests.delete(url, headers=get_headers())
            if response.status_code not in [200, 204]:
                return False, "取消点赞失败", 0
            # 更新帖子点赞数 -1
            return update_like_count(post_id, -1)
        except:
            return False, "网络错误", 0
    else:
        # 点赞：插入记录
        url = f"{SUPABASE_URL}/likes"
        data = {"post_id": post_id, "user_id": user_id}
        try:
            response = requests.post(url, headers=get_headers(), json=data)
            if response.status_code not in [200, 201]:
                return False, "点赞失败", 0
            return update_like_count(post_id, 1)
        except:
            return False, "网络错误", 0

def update_like_count(post_id, delta):
    """
    更新帖子的点赞数
    delta: 1 或 -1
    """
    # 先查当前点赞数
    url_get = f"{SUPABASE_URL}/posts?select=like_count&id=eq.{post_id}"
    try:
        resp = requests.get(url_get, headers=get_headers())
        if resp.status_code != 200 or not resp.json():
            return False, "帖子不存在", 0
        current = resp.json()[0]["like_count"]
        new_count = max(0, current + delta)  # 防止负数
        
        url_update = f"{SUPABASE_URL}/posts?id=eq.{post_id}"
        resp = requests.patch(url_update, headers=get_headers(), json={"like_count": new_count})
        if resp.status_code in [200, 204]:
            return True, "操作成功", new_count
        return False, "更新失败", 0
    except:
        return False, "网络错误", 0

# ----- 获取帖子的分类统计（用于展示）-----
def get_category_labels():
    return ["吐槽", "求助", "交友", "表白", "其他"]

# ==========================================
# 评论回复相关
# ==========================================

def add_comment_with_parent(post_id, user_id, content, parent_id=None, reply_to=None):
    """新增评论，支持父评论和@回复"""
    url = f"{SUPABASE_URL}/comments"
    data = {
        "post_id": post_id,
        "user_id": user_id,
        "content": content,
        "parent_id": parent_id,
        "reply_to": reply_to or "",
        "created_at": datetime.datetime.now().isoformat()
    }
    try:
        response = requests.post(url, headers=get_headers(), json=data)
        return response.status_code in [200, 201]
    except:
        return False

def get_comments_with_replies(post_id):
    """获取帖子所有评论（含回复），按时间排序，构建树形结构"""
    url = f"{SUPABASE_URL}/comments?select=*&post_id=eq.{post_id}&status=eq.正常&order=created_at.asc"
    try:
        response = requests.get(url, headers=get_headers())
        if response.status_code != 200:
            return []
        comments = response.json()
        # 补全显示名称
        for c in comments:
            url_user = f"{SUPABASE_URL}/users?select=nickname&username=eq.{c['user_id']}"
            user_resp = requests.get(url_user, headers=get_headers())
            c["display_name"] = user_resp.json()[0]["nickname"] if user_resp.status_code == 200 and user_resp.json() else c["user_id"]
        # 构建回复树
        # 简单扁平显示：每条评论显示其回复链（通过缩进或前缀）
        return comments
    except:
        return []

# ==========================================
# 私聊消息相关
# ==========================================

def send_message(from_user, to_user, content, task_id=None):
    url = f"{SUPABASE_URL}/messages"
    data = {
        "from_user": from_user,
        "to_user": to_user,
        "content": content,
        "task_id": task_id,
        "is_read": False,
        "created_at": datetime.datetime.now().isoformat()
    }
    try:
        response = requests.post(url, headers=get_headers(), json=data)
        return response.status_code in [200, 201]
    except:
        return False

def get_messages_between(user1, user2, task_id=None):
    """获取两人之间的消息（若指定任务则仅该任务）"""
    query = f"&from_user=eq.{user1}&to_user=eq.{user2}&order=created_at.asc"
    if task_id:
        query += f"&task_id=eq.{task_id}"
    url = f"{SUPABASE_URL}/messages?select=*&or=(from_user.eq.{user1},to_user.eq.{user1})&or=(from_user.eq.{user2},to_user.eq.{user2})&order=created_at.asc"
    # 更精确：查两人之间所有消息，不区分方向
    try:
        response = requests.get(url, headers=get_headers())
        if response.status_code != 200:
            return []
        msgs = response.json()
        # 只保留这两个人之间的
        filtered = [m for m in msgs if (m['from_user'] == user1 and m['to_user'] == user2) or (m['from_user'] == user2 and m['to_user'] == user1)]
        return filtered
    except:
        return []

def get_conversations_for_user(username):
    """
    获取当前用户的所有会话（基于任务）
    返回列表：[{'task_id': ..., 'other_user': ..., 'last_msg': ..., 'unread': 0}]
    """
    # 1. 获取当前用户参与的所有任务（发布或接单）
    # 简化：从 tasks 表中查询
    url_tasks = f"{SUPABASE_URL}/tasks?select=id,title,publisher,taker&or=(publisher.eq.{username},taker.eq.{username})"
    try:
        resp = requests.get(url_tasks, headers=get_headers())
        if resp.status_code != 200:
            return []
        tasks = resp.json()
        convs = []
        for task in tasks:
            other = task['taker'] if task['publisher'] == username else task['publisher']
            if not other:
                continue
            # 获取该任务的最新一条消息
            url_msg = f"{SUPABASE_URL}/messages?select=*&task_id=eq.{task['id']}&order=created_at.desc&limit=1"
            msg_resp = requests.get(url_msg, headers=get_headers())
            last_msg = msg_resp.json()[0] if msg_resp.status_code == 200 and msg_resp.json() else None
            # 未读消息数（当前用户为接收者且is_read=false）
            url_unread = f"{SUPABASE_URL}/messages?select=id&task_id=eq.{task['id']}&to_user=eq.{username}&is_read=eq.false"
            unread_resp = requests.get(url_unread, headers=get_headers())
            unread_count = len(unread_resp.json()) if unread_resp.status_code == 200 else 0
            # 获取对方昵称
            url_user = f"{SUPABASE_URL}/users?select=nickname&username=eq.{other}"
            user_resp = requests.get(url_user, headers=get_headers())
            other_nick = user_resp.json()[0]['nickname'] if user_resp.status_code == 200 and user_resp.json() else other
            convs.append({
                'task_id': task['id'],
                'task_title': task['title'],
                'other_user': other,
                'other_nick': other_nick,
                'last_msg': last_msg['content'] if last_msg else '暂无消息',
                'last_time': last_msg['created_at'] if last_msg else '',
                'unread': unread_count
            })
        return convs
    except:
        return []

def mark_messages_read(username, task_id=None):
    """将当前用户作为接收者的消息标记为已读，可指定任务"""
    query = f"to_user=eq.{username}&is_read=eq.false"
    if task_id:
        query += f"&task_id=eq.{task_id}"
    url = f"{SUPABASE_URL}/messages?{query}"
    try:
        # 批量更新
        resp = requests.patch(url, headers=get_headers(), json={"is_read": True})
        return resp.status_code in [200, 204]
    except:
        return False

# ==========================================
# 用户反馈相关
# ==========================================

def submit_feedback(user_id, content):
    url = f"{SUPABASE_URL}/feedbacks"
    data = {"user_id": user_id, "content": content, "created_at": datetime.datetime.now().isoformat()}
    try:
        response = requests.post(url, headers=get_headers(), json=data)
        return response.status_code in [200, 201]
    except:
        return False