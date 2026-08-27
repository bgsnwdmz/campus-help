# ==========================================
# app.py - 主入口（按需加载）
# ==========================================
import streamlit as st
import utils  # 只导入工具函数（登录、注册用）

# ---------- 页面配置 ----------
st.set_page_config(page_title="广幼校园互助站", page_icon="🏫")

st.markdown("""
<style>
    /* 回顶部按钮在手机端更友好 */
    a[href="#top"] {
        font-size: 16px !important;
        padding: 14px !important;
        border-radius: 12px !important;
        background: #e8ecf1 !important;
        transition: background 0.2s;
    }
    a[href="#top"]:hover {
        background: #d0d5dd !important;
    }
    /* 手机端适配 */
    @media (max-width: 768px) {
        a[href="#top"] {
            font-size: 14px !important;
            padding: 12px !important;
        }
    }
</style>
""", unsafe_allow_html=True)

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
    # ----- 登录页面的说明和公告 -----
    st.info("📌 **欢迎来到广幼校园互助站！**\n\n这里是幼专同学专属的互助平台，你可以发布任务、接单、发帖交流。\n登录后即可体验全部功能。")
    with st.expander("📢 公告（点击展开）"):
        st.markdown("""
        ### 🎉 广幼校园互助站 · 功能更新公告

        **最后更新：2026-08-16**

        ---

        #### ✅ 已上线功能

        **1. 任务广场**
        - 发布需求（标题 + 描述 + 报酬 + 截止日期）
        - 支持上传配图（自动压缩）
        - 分页加载，先到先得
        - 过期任务自动隐藏

        **2. 校园圈**
        - 发布帖子（支持分类：吐槽/求助/交友/表白/其他）
        - 匿名/实名切换
        - 支持图片上传
        - 点赞、评论、楼中楼回复
        - 分页加载

        **3. 个人中心**
        - 修改昵称
        - 查看我发布的任务（待接单/已接单）
        - 查看我接的单
        - 取消接单 / 完成任务
        - 查看我的帖子

        **4. 消息中心**
        - 基于任务的私聊
        - 未读消息红点提醒
        - 会话列表一目了然

        **5. 管理后台（仅管理员）**
        - 用户管理
        - 任务/帖子强制删除
        - 反馈处理
        - 数据统计看板（用户数、任务/帖子分布、近7天趋势）

        **6. 其他**
        - 用户反馈系统
        - 移动端适配（手机浏览器可直接访问）
        - 分页加载 + 缓存优化，流畅不卡顿

        ---

        #### 📌 使用提示
        - 任务请设置合理的截止时间
        - 接单后请主动联系发布者（消息中心）
        - 遇到问题请通过“反馈”页面告诉我们

        ---

        **祝你在广幼校园互助站使用愉快！** 🏫。
        """)
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
            
            # ---------- 新增：学号输入 ----------
            new_student_id = st.text_input(
                "学号", 
                placeholder="请输入你的学号",
                help="学号用于验证你的学生身份，请务必填写正确"
            )
            
            if st.form_submit_button("注册"):
                # 1. 检查是否填完整
                if not (new_user and new_pwd and new_nick and new_student_id):
                    st.warning("请填完整所有字段（包括学号）")
                else:
                    # 2. 调用注册函数（现在返回两个值：成功标志 + 消息）
                    success, msg = utils.register_user(new_user, new_pwd, new_nick, new_student_id)
                    if success:
                        st.success("注册成功！请登录")
                    else:
                        st.error(msg)  # 显示具体错误（如"学号已被注册"）
    
    st.sidebar.markdown("""
    # bro有话说：
    - 我是广幼25级的学生，所有大家放心使用
    - 这个网站是我个人业余时间，学习编程开发的，体验可能不是很完美，请多多包涵
    - 开发使用的技术栈：Python + Streamlit + superbase + HTML/CSS/JS
    - 学号验证是为了防止外人，乱来，破坏环境。无其他目的，不会牵扯到学习
    - 校园墙发帖，大家发言还是注意些哈，不要违反法律法规，文明发言
    - 接单后请主动联系发布者（消息中心，主要起到留言作用，建议大家加微信。）
    - 遇到问题请通过“反馈”页面告诉我，我会努力的
    ## bro的期望：
    - 主要是汇总大家的需求，给大家提供赚点零花钱的渠道-->任务功能
    - 期望大家可以分享学习或者生活的经验，互相帮助-->校园圈功能
    免责声明：
    - 1. bro也不知道该声明什么，这只是提供一个交流的平台，大家要共同维护好环境哈。
    - 2. 本网站不承担任何因使用本平台而产生的法律责任。
    - 3. 请勿发布违法、违规、色情、政治敏感等内容
    - 4. 请勿在平台上进行任何形式的诈骗、欺诈行为
    """)
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

nav_items = [task_label, post_label, "👤 个人中心", msg_label, "📢 反馈"]
# 如果是管理员，在最后追加“管理后台”
if utils.is_admin_user(st.session_state.nickname):
    nav_items.append("⚙️ 管理后台")

page = st.sidebar.radio("导航", nav_items)

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
    import admin_page  # 新建的管理后台
    admin_page.render()    
