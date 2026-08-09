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

# 通用的请求头（所有请求都需要）
def get_headers():
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }

# ==========================================
# 3. 辅助函数（全部改用 requests）
# ==========================================

def hash_password(pwd):
    return hashlib.sha256(pwd.encode()).hexdigest()

# ----- 注册 -----
def register_user(username, password, nickname):
    url = f"{SUPABASE_URL}/users"
    data = {
        "username": username,
        "password": hash_password(password),
        "nickname": nickname
    }
    try:
        response = requests.post(url, headers=get_headers(), json=data)
        if response.status_code in [200, 201]:
            return True
        else:
            return False
    except:
        return False

# ----- 登录 -----
def login_user(username, password):
    url = f"{SUPABASE_URL}/users?select=nickname&username=eq.{username}&password=eq.{hash_password(password)}"
    try:
        response = requests.get(url, headers=get_headers())
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                return data[0]["nickname"]
        return None
    except:
        return None

# ----- 发布任务 -----
def add_task(title, desc, publisher):
    url = f"{SUPABASE_URL}/tasks"
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    data = {
        "title": title,
        "description": desc,
        "publisher": publisher,
        "pub_time": now,
        "status": "待接单",
        "taker": ""
    }
    try:
        response = requests.post(url, headers=get_headers(), json=data)
        return response.status_code in [200, 201]
    except:
        return False

# ----- 广场：只看待接单 -----
def get_public_tasks():
    url = f"{SUPABASE_URL}/tasks?select=id,title,description,publisher,pub_time&status=eq.待接单&order=id.desc"
    try:
        response = requests.get(url, headers=get_headers())
        if response.status_code == 200:
            return response.json()
        return []
    except:
        return []

# ----- 我发布的（未完成）-----
def get_my_published_tasks(nickname):
    url = f"{SUPABASE_URL}/tasks?select=*&publisher=eq.{nickname}&status=neq.已完成&order=id.desc"
    try:
        response = requests.get(url, headers=get_headers())
        if response.status_code == 200:
            return response.json()
        return []
    except:
        return []

# ----- 我接的单（未完成）-----
def get_my_taken_tasks(nickname):
    url = f"{SUPABASE_URL}/tasks?select=*&taker=eq.{nickname}&status=neq.已完成&order=id.desc"
    try:
        response = requests.get(url, headers=get_headers())
        if response.status_code == 200:
            return response.json()
        return []
    except:
        return []

# ----- 接单（防重复）-----
def accept_task(task_id, taker):
    # 1. 先查当前状态
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
            return False, "哎呀，这个任务刚刚被别人接走了！"
        
        # 2. 更新
        url_update = f"{SUPABASE_URL}/tasks?id=eq.{task_id}"
        update_data = {"status": "已接单", "taker": taker}
        response = requests.patch(url_update, headers=get_headers(), json=update_data)
        if response.status_code in [200, 204]:
            return True, "接单成功！"
        else:
            return False, "更新失败，请重试"
    except Exception as e:
        return False, f"出错: {str(e)}"

# ----- 完成订单 -----
def complete_task(task_id, current_user):
    # 1. 校验：必须是发布者
    url_check = f"{SUPABASE_URL}/tasks?select=publisher&id=eq.{task_id}"
    try:
        response = requests.get(url_check, headers=get_headers())
        if response.status_code != 200:
            return False, "查询失败"
        data = response.json()
        if not data or data[0]["publisher"] != current_user:
            return False, "你没有权限结单"
        
        # 2. 更新
        url_update = f"{SUPABASE_URL}/tasks?id=eq.{task_id}"
        update_data = {"status": "已完成"}
        response = requests.patch(url_update, headers=get_headers(), json=update_data)
        if response.status_code in [200, 204]:
            return True, "🎉 任务已完成！"
        else:
            return False, "更新失败"
    except Exception as e:
        return False, f"出错: {str(e)}"

# ==========================================
# 4. 网页界面（完全不变）
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
    page = st.sidebar.radio("导航", ["📋 任务广场", "👤 个人中心"])
else:
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
# 5. 页面路由（完全不变）
# ==========================================
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
                        st.error("发布失败，请重试")
                else:
                    st.warning("请填完整")
    
    tasks = get_public_tasks()
    if not tasks:
        st.info("🎉 广场很干净，暂无待接单的需求。")
    else:
        for task in tasks:
            task_id = task["id"]
            title = task["title"]
            desc = task["description"]
            publisher = task["publisher"]
            pub_time = task["pub_time"]
            with st.container(border=True):
                col_left, col_right = st.columns([4, 1])
                with col_left:
                    st.markdown(f"🟢 **{title}**")
                    st.caption(f"👤 {publisher}  |  🕒 {pub_time}")
                    st.text(desc)
                with col_right:
                    if st.button("✋ 我来接", key=f"pub_{task_id}"):
                        success, msg = accept_task(task_id, st.session_state.nickname)
                        if success:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)

elif page == "👤 个人中心":
    st.title("👤 个人中心")
    tab1, tab2 = st.tabs(["📤 我发布的", "📥 我接的单"])
    
    with tab1:
        st.caption("这里显示你「发布且未完成」的需求。")
        my_published = get_my_published_tasks(st.session_state.nickname)
        if not my_published:
            st.info("你还没有发布进行中的订单。")
        else:
            for task in my_published:
                task_id = task["id"]
                title = task["title"]
                desc = task["description"]
                publisher = task["publisher"]
                taker = task["taker"]
                pub_time = task["pub_time"]
                status = task["status"]
                with st.container(border=True):
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        if status == "待接单":
                            st.markdown(f"🟢 **{title}** (待接单)")
                        else:
                            st.markdown(f"🟡 **{title}** (已接单)")
                        st.caption(f"📅 {pub_time}")
                        st.text(desc)
                        if status == "已接单" and taker:
                            st.success(f"🤝 接单同学：**{taker}**")
                    with col2:
                        if status == "已接单":
                            if st.button("✅ 已完成", key=f"complete_{task_id}"):
                                success, msg = complete_task(task_id, st.session_state.nickname)
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
                task_id = task["id"]
                title = task["title"]
                desc = task["description"]
                publisher = task["publisher"]
                pub_time = task["pub_time"]
                with st.container(border=True):
                    st.markdown(f"🟡 **{title}** (已接单)")
                    st.caption(f"👤 发布者：{publisher}  |  📅 {pub_time}")
                    st.text(desc)
                    st.info("💬 请通过线下或私信联系发布者，完成交易。")