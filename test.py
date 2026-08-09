import requests
import json

# 你的 Supabase 配置（直接从 secrets.toml 读取）
SUPABASE_URL = "https://ljzfifumrfinthyldnoq.supabase.co/rest/v1"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxqemZpZnVtcmZpbnRoeWxkbm9xIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODYxODg0NzEsImV4cCI6MjEwMTc2NDQ3MX0.iyDlrNGRpQZevoUeg5mCL_FbZX4E6Tdei_ZO5Lp_Res"

# 设置请求头（包含 API Key）
headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

# 测试查询：获取 users 表的前 1 条数据
url = f"{SUPABASE_URL}/users?select=nickname&limit=1"

print(f"请求 URL: {url}")

try:
    response = requests.get(url, headers=headers)
    print(f"状态码: {response.status_code}")
    print(f"返回内容: {response.text}")
    
    if response.status_code == 200:
        print("✅ 连接成功！Supabase 工作正常")
    else:
        print("❌ 连接失败，请检查配置")
except Exception as e:
    print(f"❌ 请求异常: {e}")