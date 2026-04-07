import streamlit as st
import json
import pandas as pd
import trafilatura
import io
import datetime
import random
import string
from docx import Document
from docx.shared import Pt, RGBColor
from docx.oxml.ns import qn
from openai import OpenAI
from supabase import create_client, Client

# ==========================================
# ⚙️ 核心配置区
# ==========================================
DEEPSEEK_API_KEY = "sk-462830ffe3424e8a820f0bd3aee786b0"
SUPABASE_URL = "https://grtnteyfjbanmdfhwbwg.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImdydG50ZXlmamJhbm1kZmh3YndnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzUzODI0MDcsImV4cCI6MjA5MDk1ODQwN30.LqR-QLHKW4Hag71tJLeagYPvOOIyCD7UrWXwfYzwGuU"
ADMIN_EMAIL = "75736724@qq.com" # 👑 老板权限唯一识别邮箱

llm_client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ==========================================
# 🎨 UI/UX 大师级视觉系统 (深度优化版)
# ==========================================
st.set_page_config(page_title="顶级英语教研平台-商业版", page_icon="🏛️", layout="wide")

custom_css = """
<style>
    /* --- 全局字体与背景 --- */
    .stApp { background-color: #FAFAFC; }
    h1, h2, h3 { font-family: 'Times New Roman', 'DengXian', '等线', serif !important; color: #1A1A24; font-weight: bold;}
    
    /* --- 1. 左侧边栏：极简黑底、自定义导航菜单 --- */
    [data-testid="stSidebar"] {
        background-color: #111118 !important; /* 深邃夜空黑 */
        border-right: 1px solid #2D2D3B;
    }
    
    /* 侧边栏标题字体 */
    [data-testid="stSidebar"] h2 {
        font-family: 'Times New Roman', 'DengXian', '等线', serif !important;
        color: #FFFFFF !important;
        font-weight: bold;
        text-align: center;
        margin-top: -30px;
        margin-bottom: 20px;
    }
    
    /* 让 Radio 菜单文字变白 */
    [data-testid="stSidebar"] [data-testid="stRadio"] label, [data-testid="stSidebar"] [data-testid="stRadio"] label p {
        color: #F0F0F5 !important;
    }
    
    /* --- 2. 🏆 核心：深度改造 Radio 选项卡样式 --- */
    div[role="radiogroup"] {
        display: flex;
        flex-direction: column;
        gap: 8px; /* 选项之间的间距 */
    }
    
    div[role="radiogroup"] > label {
        padding: 12px 18px !important;
        border-radius: 8px !important;
        margin: 0 !important; /* 去除原本的外边距 */
        transition: all 0.25s ease !important;
        border: 1px solid transparent !important; /* 基础透明边框 */
        font-family: 'DengXian', '等线', sans-serif !important;
        cursor: pointer;
    }
    
    /* 选项悬停效果 */
    div[role="radiogroup"] > label:hover {
        background-color: #202535 !important; /* 深蓝色悬停背景 */
    }
    
    /* 选项【选中状态】核心样式：深灰背景 + 蓝色左边框 */
    div[role="radiogroup"] > label[data-checked="true"] {
        background-color: #1a1e2a !important; /* 深 grey 选中背景 */
        border-left: 3px solid #00B4D8 !important; /* 科技蓝左边框 */
        font-weight: bold !important;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1) !important;
    }
    
    /* --- 3. 底部用户信息区美化 --- */
    [data-testid="stSidebar"] .stAlert {
        background-color: transparent !important;
        border: none !important;
        margin-top: 20px;
        padding-top: 0;
        padding-bottom: 0;
    }
    [data-testid="stSidebar"] .stAlert p { color: #8892B0 !important; font-size: 0.9em; }
    
    /* --- 4. 按钮样式统一与圆角 --- */
    div.stButton > button {
        border-radius: 6px !important;
        font-weight: 600 !important;
        border: none !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        transition: all 0.2s ease;
    }
    div.stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# ==========================================
# 🔐 商业版认证系统 (与之前完全一致)
# ==========================================
if 'user' not in st.session_state: st.session_state['user'] = None
if st.session_state['user'] is None:
    st.markdown("<h1 style='text-align: center; margin-top: 50px;'>🏛️ 顶级英语精读工作台</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #666;'>专业教研 · 深度分析 · 邀请制商业版</p>", unsafe_allow_html=True)
    _, col_auth, _ = st.columns([1, 1, 1]); 
    with col_auth:
        tab_login, tab_signup = st.tabs(["🔑 账号登录", "🎟️ 凭邀请码注册"])
        with tab_login:
            login_email = st.text_input("邮箱地址", key="l_email"); login_pwd = st.text_input("登录密码", type="password", key="l_pwd")
            if st.button("立即验证并进入", use_container_width=True, type="primary"):
                try: response = supabase.auth.sign_in_with_password({"email": login_email, "password": login_pwd}); st.session_state['user'] = response.user; st.rerun()
                except: st.error("账号或密码有误。")
        with tab_signup:
            signup_email = st.text_input("设置登录邮箱", key="s_email"); signup_pwd = st.text_input("设置登录密码 (至少6位)", type="password", key="s_pwd"); signup_code = st.text_input("🔑 专属邀请码")
            if st.button("核销邀请码并注册", use_container_width=True):
                if not signup_email or len(signup_pwd) < 6 or not signup_code: st.warning("请完整填写，密码>6位。")
                else:
                    with st.spinner("核验邀请码..."):
                        code_res = supabase.table('invitation_codes').select('*').eq('code', signup_code).eq('is_used', False).execute()
                        if not code_res.data: st.error("邀请码无效或已被使用。")
                        else:
                            try:
                                supabase.auth.sign_up({"email": signup_email, "password": signup_pwd}); duration = code_res.data[0]['duration_days']; exp_date = (datetime.datetime.now() + datetime.timedelta(days=duration)).isoformat()
                                supabase.table('invitation_codes').update({'is_used': True}).eq('code', signup_code).execute(); supabase.table('subscriptions').insert({'user_email': signup_email, 'expires_at': exp_date}).execute()
                                st.success(f"✅ 注册成功，为您开通了 {duration} 天权限。请登录。")
                            exceptException: st.error("注册失败，请检查邮箱或联系管理员。")
    st.stop()

# ==========================================
# ⏱️ 会员期限拦截器 (与之前完全一致)
# ==========================================
USER_EMAIL = st.session_state['user'].email; IS_ADMIN = (USER_EMAIL == ADMIN_EMAIL); CURRENT_USER_ID = st.session_state['user'].id
if not IS_ADMIN:
    sub_res = supabase.table('subscriptions').select('*').eq('user_email', USER_EMAIL).execute()
    if not sub_res.data or datetime.datetime.now() > datetime.datetime.fromisoformat(sub_res.data[0]['expires_at']):
        st.error("您的账号已到期或授权异常，请联系管理员续费。"); if st.button("退出账号"): st.session_state['user'] = None; st.rerun(); st.stop()
    else: st.sidebar.success(f"⏳ 到期日: {datetime.datetime.fromisoformat(sub_res.data[0]['expires_at']).strftime('%Y-%m-%d')}")

# ==========================================
# 🧭 大师级侧边栏导航 (視覺大換血)
# ==========================================
st.sidebar.markdown("## 🏛️ 工作台")

# 🎯 核心：干净、无数字、带有商业感的 Radio 选项卡样式
# 彻底去除了编号，保持干净
menu_options = [
    "🔍 智能精读教研室", 
    "🗂️ 文章分类档案馆", 
    "🔠 词汇分级记忆库"
]
if IS_ADMIN:
    menu_options.append("👑 老板发卡中心")

# 使用 Radio 但通过 CSS 改造为 Tabs
page = st.sidebar.radio("核心导航：", menu_options, label_visibility="collapsed")

st.sidebar.markdown("---")
# 底部用户信息区排版美化，低调专业
st.sidebar.caption(f"👤 当前授权账号:\n{USER_EMAIL}")
if st.sidebar.button("🚪 安全退出系统", use_container_width=True):
    st.session_state['user'] = None
    st.rerun()

# ==========================================
# 👑 模块 4：老板发卡中心 (与之前完全一致)
# ==========================================
if IS_ADMIN and page == "👑 老板发卡中心":
    st.title("👑 发卡中心")
    with st.form("gen_code_form"):
        plan = st.radio("授权时长：", ["1个月 (30天)", "1个季度 (90天)", "1年 (365天)", "终身版 (36500天)"], horizontal=True)
        days_map = {"1个月 (30天)": 30, "1个季度 (90天)": 90, "1年 (365天)": 365, "终身版 (36500天)": 36500}
        if st.form_submit_button("🔨 生成激活码", type="primary"):
            random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8)); new_code = f"VIP-{random_str[:4]}-{random_str[4:]}"
            try:
                supabase.table('invitation_codes').insert({"code": new_code, "duration_days": days_map[plan], "is_used": False}).execute()
                st.code(new_code, language="text"); st.success(f"生成成功，有效期: {days_map[plan]} 天")
            exceptException: st.error("生成激活码失败，请检查数据库。")

# ==========================================
# 🔍 智能精读室 (以下为之前完全复用的核心逻辑与排版)
# ==========================================
elif page == "🔍 智能精读教研室":
    st.title("🔍 智能精读教研室")
    # (爬虫与 Word 生成保持不变)
    def fetch_text_smart(url): 
        try: downloaded = trafilatura.fetch_url(url); return trafilatura.extract(downloaded) if downloaded else "⚠️ 未能识别正文"
        exceptException: return "抓取异常"
    def set_font(run, ascii_font='Times New Roman', east_asia_font='等线'): run.font.name = ascii_font; run._element.rPr.rFonts.set(qn('w:eastAsia'), east_asia_font)
    def generate_beautiful_word(analysis_data):
        doc = Document(); style = doc.styles['Normal']; style.font.name, style.font.size = 'Times New Roman', Pt(10.5); style._element.rPr.rFonts.set(qn('w:eastAsia'), '等线'); doc.add_heading('📖 英语精读教案', 0)
        for i, s in enumerate(analysis_data.get('sentences', [])):
            run_en = doc.add_paragraph().add_run(f"[{i+1}] {s.get('en', '')}"); run_en.bold, run_en.font.size = True, Pt(14); set_font(run_en); run_cn = doc.add_paragraph().add_run(f"译文：{s.get('cn', '')}"); run_cn.font.size = Pt(11); set_font(run_cn); p_syn = doc.add_paragraph(); p_syn.paragraph_format.left_indent = Pt(15); r_l1 = p_syn.add_run("🔍 语法："); r_l1.bold, r_l1.font.color.rgb = True, RGBColor(0x1F, 0x4E, 0x79); set_font(r_l1); r_t1 = p_syn.add_run(s.get('syntax', '').replace('*', '')); set_font(r_t1)
            if s.get('words'): p_w = doc.add_paragraph(style='List Bullet'); r_l2 = p_w.add_run("💡 词法："); r_l2.bold, r_l2.font.color.rgb = True, RGBColor(0xC0, 0x00, 0x00); set_font(r_l2); r_t2 = p_w.add_run(s.get('words', '').replace('*', '')); set_font(r_t2)
        bio = io.BytesIO(); doc.save(bio); return bio.getvalue()
    
    col1, col2 = st.columns([3, 1])
    with col1: url = st.text_input("🔗 输入英文文章链接 (自动提取精选正文)：")
    with col2: 
        st.write(""); st.write(""); if st.button("🛰️ 提取正文", use_container_width=True):
            if url: st.session_state['temp_text'] = fetch_text_smart(url)
    
    final_text = st.text_area("📝 待分析文本：", value=st.session_state.get('temp_text', ""), height=150)
    if st.button("🧠 生成专家级教案", type="primary"):
        if not final_text.strip(): st.error("请先输入文本")
        else:
            with st.spinner("AI教研员正在逐句切片中..."):
                prompt = f"""以JSON格式输出全句拆解：{final_text}""" 
                try:
                    res = llm_client.chat.completions.create(model="deepseek-chat", messages=[{"role":"user","content":prompt}], response_format={"type":"json_object"})
                    st.session_state['analysis_result'] = json.loads(res.choices[0].message.content); st.session_state['article_content'] = final_text; st.rerun()
                exceptException: st.error("分析失败。")

    if 'analysis_result' in st.session_state:
        res = st.session_state['analysis_result']; st.divider()
        c1, c2, c3 = st.columns(3)
        with c1: st.download_button("📝 导出 Word 教案", data=generate_beautiful_word(res), file_name="教案.docx", use_container_width=True)
        with c2: cat = st.selectbox("📂 分类：", ["新闻", "学术", "考试", "其他"], label_visibility="collapsed")
        with c3:
            if st.button("☁️ 同步云端题库", use_container_width=True):
                txt = "".join([f"[{i+1}] {s.get('en','')}\譯：{s.get('cn','')}\n\n" for i,s in enumerate(res.get('sentences', []))]); supabase.table('articles').insert({"user_id": CURRENT_USER_ID, "content": st.session_state['article_content'], "teaching_plan": txt, "category": cat}).execute()
                for v in res.get('core_vocabulary', []): v["user_id"] = CURRENT_USER_ID; supabase.table('vocabulary').insert(v).execute()
                st.success("✅ 保存至您的私人空间。")
        for i, s in enumerate(res.get('sentences', [])):
            st.markdown(f"""<div style='background:#fff; border:1px solid #eee; border-radius:8px; padding:12px 16px; margin-bottom:12px;'>
                <div style='font-family: Times New Roman; font-size:1.15em; font-weight:bold;'>[{i+1}] {s.get('en','')}</div><div style='color:#555;'>译：{s.get('cn','')}</div>
                <div style='font-size:0.95em; margin-top:6px;'><span style='color:#1F4E79;'>🔍 语法：</span>{s.get('syntax','')}</div>
                <div style='font-size:0.95em;'><span style='color:#C00000;'>💡 词法：</span>{s.get('words','')}</div></div>""", unsafe_allow_html=True)
        if res.get('core_vocabulary'): st.dataframe(pd.DataFrame(res['core_vocabulary'])[['word', 'phonetic', 'translation', 'tags', 'memory_tip']], use_container_width=True)

# 档案馆和记忆库与 3.0 版一致
elif page == "🗂️ 文章分类档案馆":
    st.title("🗂️ 私人档案馆")
    try:
        arts_data = supabase.table('articles').select('*').eq('user_id', CURRENT_USER_ID).execute().data
        if arts_data:
            df_arts = pd.DataFrame(arts_data); cat_filter = st.selectbox("📌 筛选：", ["全部"] + list(df_arts['category'].dropna().unique()) if 'category' in df_arts.columns else ["全部"])
            filtered_arts = df_arts[df_arts['category'] == cat_filter].to_dict('records') if cat_filter != "全部" else arts_data
            for a in filtered_arts:
                with st.expander(f"📖 [{a.get('category', '未分类')}] {a.get('content', '')[:60]}..."): st.text(a.get('teaching_plan', '无'))
        else: st.info("档案馆空空如也。")
    exceptException: pass

elif page == "🔠 词汇分级记忆库":
    st.title("🔠 私人专属词汇库")
    try:
        vocab_data = supabase.table('vocabulary').select('*').eq('user_id', CURRENT_USER_ID).execute().data
        if vocab_data:
            df_vocab = pd.DataFrame(vocab_data); tag_filter = st.selectbox("🎓 筛选：", ["全部"] + list(df_vocab['tags'].dropna().unique()))
            display_df = df_vocab[df_vocab['tags'] == tag_filter] if tag_filter != "全部" else df_vocab
            st.metric("您的生词量", len(display_df)); st.dataframe(display_df[['word', 'phonetic', 'translation', 'tags', 'memory_tip']], use_container_width=True)
            st.download_button("📥 导出私人词汇", display_df.to_csv(index=False).encode('utf-8-sig'), f"Vocabulary.csv", "text/csv")
        else: st.info("您还没有收藏生词。")
    exceptException: pass