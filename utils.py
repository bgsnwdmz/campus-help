# ==========================================
# utils.py - 公共工具箱
# ==========================================
import streamlit as st
import requests
import datetime
import hashlib
import datetime
import io
import re
from PIL import Image

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

def validate_student_id(sid):
    
    if not sid or not sid.strip():
        return False, "学号不能为空"
    
    # 去掉首尾空格
    sid = sid.strip()
    
    # 🔥🔥🔥 在这里改你的学校学号规则 🔥🔥🔥
    pattern = r'^\d{12}$'  
    if re.match(pattern, sid):
        return True, sid
    else:
        return False, "学号格式不正确（请输入12位数字学号）"

# ---------- 用户相关 ----------
def register_user(username, password, nickname, student_id):
    url = f"{SUPABASE_URL}/users"
    now = datetime.datetime.now().isoformat()
    data = {
        "username": username,
        "password": hash_password(password),
        "nickname": nickname,
        "student_id": student_id.strip(),
        "last_task_visit": now,
        "last_post_visit": now
    }
    try:
        response = requests.post(url, headers=get_headers(), json=data)
        if response.status_code in [200, 201]:
            return True, "注册成功"
        elif response.status_code == 409 or "duplicate key" in response.text:
            # 学号或用户名重复
            return False, "学号已被注册，请确认是否正确"
        else:
            return False, f"注册失败（{response.status_code}）"
    except Exception as e:
        return False, f"网络错误：{str(e)}"

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
def add_task(title, desc, publisher, deadline=None, image_url=None):
    url = f"{SUPABASE_URL}/tasks"
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    data = {
        "title": title,
        "description": desc,
        "publisher": publisher,
        "pub_time": now,
        "status": "待接单",
        "taker": "",
        "deadline": deadline,
        "image_url": image_url  # 新增字段
    }
    try:
        response = requests.post(url, headers=get_headers(), json=data)
        return response.status_code in [200, 201]
    except:
        return False

def get_public_tasks():
    url = f"{SUPABASE_URL}/tasks?select=id,title,description,publisher,pub_time&status=eq.待接单&or=(deadline.is.null,deadline.gt.{now})&order=id.desc"
    try:
        response = requests.get(url, headers=get_headers())
        return response.json() if response.status_code == 200 else []
    except:
        return []

def get_my_published_tasks(nickname):
    """获取当前用户发布的、未过期且未完成的任务（待接单或已接单）"""
    now = datetime.datetime.now().isoformat()
    url = f"{SUPABASE_URL}/tasks?select=*&publisher=eq.{nickname}&status=in.(待接单,已接单)&or=(deadline.is.null,deadline.gt.{now})&order=id.desc"
    try:
        response = requests.get(url, headers=get_headers())
        return response.json() if response.status_code == 200 else []
    except:
        return []

def get_my_taken_tasks(nickname):
    """获取当前用户已接单、未过期且未完成的任务（已接单）"""
    now = datetime.datetime.now().isoformat()
    url = f"{SUPABASE_URL}/tasks?select=*&taker=eq.{nickname}&status=eq.已接单&or=(deadline.is.null,deadline.gt.{now})&order=id.desc"
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


def delete_task(task_id, current_user):
    """
    发布者删除自己的任务（仅限待接单状态）
    返回: (success, message)
    """
    # 1. 先查询任务状态和发布者
    url_check = f"{SUPABASE_URL}/tasks?select=publisher,status&id=eq.{task_id}"
    try:
        response = requests.get(url_check, headers=get_headers())
        if response.status_code != 200 or not response.json():
            return False, "任务不存在"
        
        task = response.json()[0]
        
        # 2. 权限校验：必须是发布者
        if task["publisher"] != current_user:
            return False, "只有发布者可以删除此任务"
        
        # 3. 状态校验：只有待接单才能删除
        if task["status"] != "待接单":
            return False, "任务已被接单，无法删除。如需取消，请联系接单方。"
        
        # 4. 执行删除（软删除：将状态改为已删除）
        url_update = f"{SUPABASE_URL}/tasks?id=eq.{task_id}"
        response = requests.patch(url_update, headers=get_headers(), json={
            "status": "已删除",
            "cancelled_by": current_user,
            "cancelled_at": datetime.datetime.now().isoformat()
        })
        return (True, "任务已删除") if response.status_code in [200, 204] else (False, "删除失败")
    except Exception as e:
        return False, f"出错: {str(e)}"


def cancel_taken_task(task_id, current_user):
    """
    接单者取消已接单的任务
    返回: (success, message)
    """
    # 1. 先查询任务状态和接单人
    url_check = f"{SUPABASE_URL}/tasks?select=taker,status,publisher&id=eq.{task_id}"
    try:
        response = requests.get(url_check, headers=get_headers())
        if response.status_code != 200 or not response.json():
            return False, "任务不存在"
        
        task = response.json()[0]
        
        # 2. 权限校验：必须是接单者
        if task.get("taker") != current_user:
            return False, "只有接单者可以取消接单"
        
        # 3. 状态校验：只有已接单才能取消
        if task["status"] != "已接单":
            return False, "任务当前状态不允许取消接单"
        
        # 4. 执行取消：将状态改回待接单，清空接单人
        url_update = f"{SUPABASE_URL}/tasks?id=eq.{task_id}"
        response = requests.patch(url_update, headers=get_headers(), json={
            "status": "待接单",
            "taker": "",
            "cancelled_by": current_user,
            "cancelled_at": datetime.datetime.now().isoformat()
        })
        return (True, "已取消接单，任务已重新上架") if response.status_code in [200, 204] else (False, "取消失败")
    except Exception as e:
        return False, f"出错: {str(e)}"


def get_new_task_count(username):
    last_visit = get_user_visit_time(username, "task")
    if not last_visit:
        return 0
    now = datetime.datetime.now().isoformat()
    url = f"{SUPABASE_URL}/tasks?select=id&status=eq.待接单&pub_time=gt.{last_visit}&or=(deadline.is.null,deadline.gt.{now})"
    try:
        response = requests.get(url, headers=get_headers())
        return len(response.json()) if response.status_code == 200 else 0
    except:
        return 0

# ---------- 帖子相关 ----------

def add_post(user_id, content, is_anonymous, category, image_url=None):
    url = f"{SUPABASE_URL}/posts"
    data = {
        "user_id": user_id,
        "content": content,
        "is_anonymous": is_anonymous,
        "category": category,
        "created_at": datetime.datetime.now().isoformat(),
        "image_url": image_url  # 新增字段
    }
    try:
        response = requests.post(url, headers=get_headers(), json=data)
        return response.status_code in [200, 201]
    except:
        return False

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
    url_tasks = f"{SUPABASE_URL}/tasks?select=id,title,publisher,taker&or=(publisher.eq.{username},taker.eq.{username})"
    try:
        resp = requests.get(url_tasks, headers=get_headers())
        if resp.status_code != 200:
            return []
        tasks = resp.json()
        convs = []
        for task in tasks:
            # 处理 taker 为空的情况
            other = task.get('taker') if task.get('publisher') == username else task.get('publisher')
            if not other or other == '':
                continue
            # 获取该任务的最新一条消息
            url_msg = f"{SUPABASE_URL}/messages?select=*&task_id=eq.{task['id']}&order=created_at.desc&limit=1"
            msg_resp = requests.get(url_msg, headers=get_headers())
            last_msg = msg_resp.json()[0] if msg_resp.status_code == 200 and msg_resp.json() else None
            # 未读消息数
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
    except Exception as e:
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

# ==========================================
# 替换 get_public_tasks_page（支持搜索 + 排序）
# ==========================================
def get_public_tasks_page(page=1, per_page=10, sort_by="最新发布", keyword=""):
    offset = (page - 1) * per_page
    now = datetime.datetime.now().isoformat()
    
    # ---------- 1. 构建筛选条件 ----------
    # 基础：待接单 + 未过期
    filters = "status=eq.待接单&or=(deadline.is.null,deadline.gt.{now})"
    
    # 关键词搜索（标题或描述包含关键词）
    if keyword and keyword.strip():
        keyword = keyword.strip()
        # 使用 ilike 模糊匹配（%keyword%）
        filters += f"&or=(title.ilike.*{keyword}*,description.ilike.*{keyword}*)"
    
    # ---------- 2. 构建排序 ----------
    if sort_by == "即将截止":
        order_clause = "order=deadline.asc.nullslast"  # 截止时间升序，空值排最后
    else:  # "最新发布"
        order_clause = "order=id.desc"  # ID 降序 = 最新发布
    
    # ---------- 3. 查询数据 ----------
    url = (
        f"{SUPABASE_URL}/tasks"
        f"?select=id,title,description,publisher,pub_time,deadline,image_url"
        f"&{filters}"
        f"&{order_clause}"
        f"&limit={per_page}"
        f"&offset={offset}"
    )
    
    try:
        response = requests.get(url, headers=get_headers())
        tasks = response.json() if response.status_code == 200 else []
        
        # ---------- 4. 获取总数（同样应用筛选） ----------
        count_url = f"{SUPABASE_URL}/tasks?select=id&{filters}"
        count_resp = requests.get(count_url, headers=get_headers())
        total = len(count_resp.json()) if count_resp.status_code == 200 else 0
        
        return tasks, total
    except Exception as e:
        print(f"get_public_tasks_page 报错: {e}")
        return [], 0


# ==========================================
# 替换 get_all_posts_page（支持搜索）
# ==========================================
def get_all_posts_page(page=1, per_page=10, sort_by="最新", category="全部", keyword=""):
    offset = (page - 1) * per_page
    
    # ---------- 1. 构建筛选条件 ----------
    filters = "status=eq.正常"
    
    # 分类筛选
    if category and category != "全部":
        filters += f"&category=eq.{category}"
    
    # 关键词搜索（内容包含关键词）
    if keyword and keyword.strip():
        keyword = keyword.strip()
        filters += f"&content.ilike.*{keyword}*"
    
    # ---------- 2. 构建排序 ----------
    if sort_by == "最热":
        order_clause = "order=like_count.desc,created_at.desc"
    else:  # "最新"
        order_clause = "order=created_at.desc"
    
    # ---------- 3. 查询数据 ----------
    url_posts = (
        f"{SUPABASE_URL}/posts"
        f"?select=*"
        f"&{filters}"
        f"&{order_clause}"
        f"&limit={per_page}"
        f"&offset={offset}"
    )
    
    try:
        response = requests.get(url_posts, headers=get_headers())
        if response.status_code != 200:
            return [], 0
        posts = response.json()
        
        # 补充评论数和显示名称
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
        
        # 获取总数（同样应用筛选）
        count_url = f"{SUPABASE_URL}/posts?select=id&{filters}"
        count_resp = requests.get(count_url, headers=get_headers())
        total = len(count_resp.json()) if count_resp.status_code == 200 else 0
        
        return posts, total
    except Exception as e:
        print(f"get_all_posts_page 报错: {e}")
        return [], 0


# ---------- 管理员配置（硬编码白名单，后续可迁移到数据库） ----------
# 🔥 重要：把下面列表里的 "你的用户名：nickname " 改成你自己的登录账号！
ADMIN_WHITELIST = ["浪迹天涯", "admin"]  # 可以加多个

def is_admin_user(username):
    """判断当前用户是否为管理员"""
    if not username:
        return False
    return username in ADMIN_WHITELIST

# ---------- 管理后台专用查询（不过滤任何状态） ----------

def admin_get_all_users():
    """获取所有用户（用于管理面板）"""
    url = f"{SUPABASE_URL}/users?select=username,nickname,avatar_url,last_task_visit,last_post_visit&order=username.asc"
    try:
        resp = requests.get(url, headers=get_headers())
        return resp.json() if resp.status_code == 200 else []
    except:
        return []

def admin_get_all_tasks():
    """获取所有任务（含已删除、已过期），按发布时间降序"""
    url = f"{SUPABASE_URL}/tasks?select=*&order=id.desc"
    try:
        resp = requests.get(url, headers=get_headers())
        return resp.json() if resp.status_code == 200 else []
    except:
        return []

def admin_get_all_posts():
    """获取所有帖子（含已删除），按发布时间降序"""
    url = f"{SUPABASE_URL}/posts?select=*&order=id.desc"
    try:
        resp = requests.get(url, headers=get_headers())
        return resp.json() if resp.status_code == 200 else []
    except:
        return []

def admin_get_all_feedbacks():
    """获取所有反馈，按时间降序"""
    url = f"{SUPABASE_URL}/feedbacks?select=*&order=id.desc"
    try:
        resp = requests.get(url, headers=get_headers())
        return resp.json() if resp.status_code == 200 else []
    except:
        return []

def admin_delete_task_force(task_id):
    """管理员强制删除任务（物理删除，谨慎）"""
    url = f"{SUPABASE_URL}/tasks?id=eq.{task_id}"
    try:
        resp = requests.delete(url, headers=get_headers())
        return resp.status_code in [200, 204]
    except:
        return False

def admin_delete_post_force(post_id):
    """管理员强制删除帖子（物理删除）"""
    url = f"{SUPABASE_URL}/posts?id=eq.{post_id}"
    try:
        resp = requests.delete(url, headers=get_headers())
        return resp.status_code in [200, 204]
    except:
        return False

def admin_mark_feedback_done(feedback_id):
    """管理员标记反馈为已处理（软标记，需在 feedbacks 表加 status 字段）"""
    # 注意：如果 feedbacks 表没有 status 字段，需要先 ALTER TABLE 添加
    url = f"{SUPABASE_URL}/feedbacks?id=eq.{feedback_id}"
    try:
        resp = requests.patch(url, headers=get_headers(), json={"status": "已处理"})
        return resp.status_code in [200, 204]
    except:
        return False       

# ==========================================
# 追加到 utils.py 末尾（统计看板相关）
# ==========================================

import pandas as pd
from collections import defaultdict
import datetime as dt

def admin_get_stats_summary():
    """
    获取平台核心统计数据
    返回字典：用户总数、各状态任务数、各状态帖子数、各状态反馈数
    """
    stats = {
        "total_users": 0,
        "tasks": {"待接单": 0, "已接单": 0, "已完成": 0, "已删除": 0},
        "posts": {"正常": 0, "已删除": 0},
        "feedbacks": {"待处理": 0, "已处理": 0}
    }
    
    # 1. 用户总数
    try:
        resp = requests.get(f"{SUPABASE_URL}/users?select=username", headers=get_headers())
        if resp.status_code == 200:
            stats["total_users"] = len(resp.json())
    except:
        pass
    
    # 2. 任务状态统计
    try:
        resp = requests.get(f"{SUPABASE_URL}/tasks?select=status", headers=get_headers())
        if resp.status_code == 200:
            for task in resp.json():
                status = task.get("status", "未知")
                if status in stats["tasks"]:
                    stats["tasks"][status] += 1
    except:
        pass
    
    # 3. 帖子状态统计
    try:
        resp = requests.get(f"{SUPABASE_URL}/posts?select=status", headers=get_headers())
        if resp.status_code == 200:
            for post in resp.json():
                status = post.get("status", "未知")
                if status in stats["posts"]:
                    stats["posts"][status] += 1
    except:
        pass
    
    # 4. 反馈状态统计（如果 feedbacks 表没有 status 字段，默认为"待处理"）
    try:
        resp = requests.get(f"{SUPABASE_URL}/feedbacks?select=status", headers=get_headers())
        if resp.status_code == 200:
            for fb in resp.json():
                status = fb.get("status", "待处理")
                if status in stats["feedbacks"]:
                    stats["feedbacks"][status] += 1
        else:
            # 如果表没有 status 字段，全部算作待处理
            resp2 = requests.get(f"{SUPABASE_URL}/feedbacks?select=id", headers=get_headers())
            if resp2.status_code == 200:
                stats["feedbacks"]["待处理"] = len(resp2.json())
    except:
        pass
    
    return stats


def admin_get_daily_trends(days=7):
    """
    获取近 N 天每日新增任务和帖子数量
    返回 pandas DataFrame，列：日期, 新增任务, 新增帖子
    """
    # 计算起始日期
    end_date = dt.date.today()
    start_date = end_date - dt.timedelta(days=days - 1)
    
    # 初始化字典
    date_range = [start_date + dt.timedelta(days=i) for i in range(days)]
    date_strs = [d.isoformat() for d in date_range]
    
    task_counts = defaultdict(int)
    post_counts = defaultdict(int)
    
    # 1. 获取任务发布时间（只取 pub_time 日期部分）
    try:
        resp = requests.get(f"{SUPABASE_URL}/tasks?select=pub_time", headers=get_headers())
        if resp.status_code == 200:
            for task in resp.json():
                pub = task.get("pub_time", "")
                if pub:
                    # pub_time 格式："YYYY-MM-DD HH:MM"
                    date_part = pub[:10]  # 取前10位
                    if date_part in date_strs:
                        task_counts[date_part] += 1
    except:
        pass
    
    # 2. 获取帖子创建时间
    try:
        resp = requests.get(f"{SUPABASE_URL}/posts?select=created_at", headers=get_headers())
        if resp.status_code == 200:
            for post in resp.json():
                created = post.get("created_at", "")
                if created:
                    # created_at 格式："YYYY-MM-DDTHH:MM:SS..."
                    date_part = created[:10]
                    if date_part in date_strs:
                        post_counts[date_part] += 1
    except:
        pass
    
    # 构建 DataFrame
    data = []
    for d in date_range:
        d_str = d.isoformat()
        data.append({
            "日期": d_str,
            "新增任务": task_counts.get(d_str, 0),
            "新增帖子": post_counts.get(d_str, 0)
        })
    
    df = pd.DataFrame(data)
    # 格式化日期显示（如 "08-15"）
    df["日期显示"] = pd.to_datetime(df["日期"]).dt.strftime("%m-%d")
    return df  

# ==========================================
# 图片上传与压缩（追加到 utils.py 末尾）
# ==========================================

def compress_image(file_bytes, max_width=800, quality=75):
    """
    压缩图片，返回压缩后的 bytes 和文件后缀
    - 最大宽度 800px（等比缩放）
    - JPEG 质量 75%
    - 输出格式：JPEG
    """
    try:
        img = Image.open(io.BytesIO(file_bytes))
        
        # 转换为 RGB（防止 RGBA 无法保存为 JPEG）
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        
        # 等比缩放
        if img.width > max_width:
            ratio = max_width / img.width
            new_size = (max_width, int(img.height * ratio))
            img = img.resize(new_size, Image.Resampling.LANCZOS)
        
        # 压缩到内存
        output = io.BytesIO()
        img.save(output, format="JPEG", quality=quality, optimize=True)
        return output.getvalue()
    except Exception as e:
        # 如果压缩失败，返回原数据（但后续上传可能会因体积过大失败）
        print(f"压缩失败: {e}")
        return file_bytes


def upload_image_to_supabase(file_bytes, bucket_name, username, file_extension="jpg"):
    """
    上传图片到 Supabase Storage
    返回：公开 URL 或 None
    """
    if not file_bytes:
        return None
    
    # 1. 压缩图片
    compressed_bytes = compress_image(file_bytes)
    
    # 2. 生成唯一文件名
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    file_name = f"{username}_{timestamp}.jpg"
    
    # 3. 构造 Storage API URL
    base_url = SUPABASE_URL.replace("/rest/v1", "")  # 去掉 /rest/v1
    storage_url = f"{base_url}/storage/v1/object/{bucket_name}/{file_name}"
    
    # 4. 上传
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "image/jpeg",
        "x-upsert": "true"
    }
    
    try:
        response = requests.put(storage_url, headers=headers, data=compressed_bytes)
        # ----- 调试信息 -----
        if response.status_code not in [200, 201]:
            st.error(f"上传失败，状态码：{response.status_code}")
            st.error(f"响应内容：{response.text}")
            return None
        # 返回公开 URL
        public_url = f"{base_url}/storage/v1/object/public/{bucket_name}/{file_name}"
        return public_url
    except Exception as e:
        st.error(f"上传异常：{str(e)}")
        return None
       