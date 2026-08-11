# profile_edit_page.py - 我的资料
import streamlit as st
import utils
import requests
from PIL import Image
import io

def render():
    st.title("👤 我的资料")
    
    # 获取当前用户信息
    username = st.session_state.nickname
    url = f"{utils.SUPABASE_URL}/users?select=*&username=eq.{username}"
    try:
        response = requests.get(url, headers=utils.get_headers())
        if response.status_code != 200 or not response.json():
            st.error("获取用户信息失败")
            return
        user_info = response.json()[0]
    except:
        st.error("网络错误")
        return
    
    # ----- 显示当前信息 -----
    col1, col2 = st.columns([1, 2])
    with col1:
        st.image("https://img.icons8.com/fluency/96/000000/user.png", width=100)
    with col2:
        st.markdown(f"**账号**：{user_info['username']}")
        st.markdown(f"**昵称**：{user_info['nickname']}")
    
    st.divider()
    
    # ----- 修改昵称 -----
    with st.expander("✏️ 修改昵称", expanded=False):
        with st.form("update_nickname"):
            new_nick = st.text_input("新昵称", value=user_info.get('nickname', ''))
            if st.form_submit_button("更新昵称"):
                if new_nick.strip():
                    url_update = f"{utils.SUPABASE_URL}/users?username=eq.{username}"
                    data = {"nickname": new_nick}
                    resp = requests.patch(url_update, headers=utils.get_headers(), json=data)
                    if resp.status_code in [200, 204]:
                        st.success("昵称更新成功！")
                        st.session_state.nickname = new_nick
                        st.rerun()
                    else:
                        st.error("更新失败")
                else:
                    st.warning("昵称不能为空")
    
    # ----- 修改密码 -----
    with st.expander("🔑 修改密码", expanded=False):
        with st.form("update_password"):
            old_pwd = st.text_input("当前密码", type="password")
            new_pwd = st.text_input("新密码", type="password")
            confirm_pwd = st.text_input("确认新密码", type="password")
            if st.form_submit_button("修改密码"):
                if not old_pwd or not new_pwd:
                    st.warning("请填写完整")
                elif new_pwd != confirm_pwd:
                    st.warning("两次密码输入不一致")
                elif len(new_pwd) < 6:
                    st.warning("密码长度至少6位")
                else:
                    # 验证旧密码
                    if utils.login_user(username, old_pwd):
                        url_update = f"{utils.SUPABASE_URL}/users?username=eq.{username}"
                        data = {"password": utils.hash_password(new_pwd)}
                        resp = requests.patch(url_update, headers=utils.get_headers(), json=data)
                        if resp.status_code in [200, 204]:
                            st.success("密码修改成功，请重新登录")
                            st.session_state.logged_in = False
                            st.rerun()
                        else:
                            st.error("修改失败")
                    else:
                        st.error("当前密码错误")
    
    # ----- 上传头像（Supabase Storage）-----
    with st.expander("📷 更换头像", expanded=False):
        st.info("💡 头像将存储在 Supabase Storage，建议上传 200x200 以内的图片")
        uploaded_file = st.file_uploader("选择图片", type=["jpg", "png", "jpeg"])
        
        if uploaded_file is not None:
            # 压缩图片
            image = Image.open(uploaded_file)
            # 压缩到 200x200
            image.thumbnail((200, 200))
            
            # 转成字节
            img_bytes = io.BytesIO()
            image.save(img_bytes, format='JPEG', quality=80)
            img_bytes = img_bytes.getvalue()
            
            # 上传到 Supabase Storage
            storage_url = f"{utils.SUPABASE_URL}/storage/v1/object/public/avatars/{username}.jpg"
            headers = {
                "apikey": utils.SUPABASE_KEY,
                "Authorization": f"Bearer {utils.SUPABASE_KEY}",
                "Content-Type": "image/jpeg"
            }
            
            try:
                resp = requests.post(storage_url, headers=headers, data=img_bytes)
                if resp.status_code in [200, 201]:
                    st.success("头像上传成功！")
                    # 更新用户表中的头像字段
                    url_update = f"{utils.SUPABASE_URL}/users?username=eq.{username}"
                    data = {"avatar_url": f"{utils.SUPABASE_URL}/storage/v1/object/public/avatars/{username}.jpg"}
                    requests.patch(url_update, headers=utils.get_headers(), json=data)
                else:
                    st.error("上传失败，请稍后重试")
            except:
                st.error("上传失败，请检查网络")