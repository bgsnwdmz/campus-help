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