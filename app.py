# ==========================================
# app.py - 主入口（按需加载）
# ==========================================
import streamlit as st
import utils  # 只导入工具函数（登录、注册用）

# ---------- 页面配置 ----------
st.set_page_config(page_title="广幼校园互助站", page_icon="🏫")

# ---------- 初始化 Session ----------
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.nickname = ""

if not st.session_state.logged_in:
    if "user" in st.query_params:
        st.session_state.logged_in = True
        st.session_state.nickname = st.query_params["user"]

# ---------- 侧边栏 ----------
st.sidebar.title("🏫 广幼校园互助")

# ---------- 登录 / 注册界面 ----------
if not st.session_state.logged_in:
    st.title("🔐 请先登录")
    col1, col2 = st.columns(2)
    
    with col1:
        with st.form("login_form"):
            username = st.text_input("账号")
            password = st.text_input("密码", type="password")
            if st.form_submit_button("登录"):
                user_info = utils.login_user(username, password)
                if user_info:
                    st.session_state.logged_in = True
                    st.session_state.nickname = user_info["nickname"]
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
                    if utils.register_user(new_user, new_pwd, new_nick):
                        st.success("注册成功，请登录！")
                    else:
                        st.error("账号已存在")
                else:
                    st.warning("请填完整")
    
    st.sidebar.info("👈 注册登录后使用完整功能")
    st.stop()  # 阻止后续代码执行

# ---------- 已登录：显示导航 ----------
st.sidebar.success(f"👋 {st.session_state.nickname}")
if st.sidebar.button("🚪 退出登录"):
    st.session_state.logged_in = False
    st.session_state.nickname = ""
    st.query_params.clear()
    st.rerun()

# 计算未读红点
new_tasks = utils.get_new_task_count(st.session_state.nickname)
new_posts = utils.get_new_post_count(st.session_state.nickname)
task_label = f"📋 任务广场{' 🔴'+str(new_tasks) if new_tasks > 0 else ''}"
post_label = f"🎉 校园圈{' 🔴'+str(new_posts) if new_posts > 0 else ''}"

try:
    convs = utils.get_conversations_for_user(st.session_state.nickname)
    total_unread = sum(c['unread'] for c in convs)
    msg_label = f"💬 消息{' 🔴'+str(total_unread) if total_unread > 0 else ''}"
except Exception as e:
    # 如果消息表不存在或查询失败，直接显示不带红点的消息按钮
    msg_label = "💬 消息"

page = st.sidebar.radio("导航", [task_label, post_label, "👤 个人中心", msg_label, "📢 反馈"，"⚙️ 我的资料"])

# ---------- 核心优化：按需导入（Lazy Loading） ----------
# 只有点击对应的导航，才导入对应的页面模块
if "📋" in page:
    import task_page
    task_page.render()
elif "🎉" in page:
    import post_page
    post_page.render()
elif "👤" in page:
    import profile_page
    profile_page.render()
elif "💬" in page:
    import chat_page
    chat_page.render()
elif "反馈" in page:
    import feedback_page
    feedback_page.render()
elif "⚙️" in page:
    import profile_edit_page
    profile_edit_page.render()