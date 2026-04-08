import streamlit as st
import json
import pandas as pd
import trafilatura
import io
import datetime
import random
import string
import re
import hashlib
import extra_streamlit_components as esc
from docx import Document
from docx.shared import Pt, RGBColor
from docx.oxml import parse_xml
from docx.oxml.ns import qn, nsdecls
from openai import OpenAI
from supabase import create_client, Client
from pypdf import PdfReader

# ==========================================
# ⚙️ 核心配置区
# ==========================================
DEEPSEEK_API_KEY = st.secrets["DEEPSEEK_API_KEY"]
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
ADMIN_EMAIL = "75736724@qq.com" # 👑 老板权限
CONTACT_WECHAT = "你的微信号" 

llm_client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ==========================================
# 🍪 商业级加密 Cookie 记忆引擎
# ==========================================
@st.cache_resource
def get_cookie_manager():
    return esc.CookieManager()

cookie_manager = get_cookie_manager()

def get_secure_sign(email):
    # 使用 SHA-256 防篡改加密，防止黑客伪造 Cookie
    return hashlib.sha256(f"{email}{SUPABASE_KEY}".encode()).hexdigest()

class SimpleUser:
    def __init__(self, email, uid):
        self.email = email
        self.id = uid

# ==========================================
# 🎨 UI/UX 极致紧凑视觉系统
# ==========================================
st.set_page_config(page_title="顶级英语教研平台-商业版", page_icon="🏛️", layout="wide")

custom_css = """
<style>
    .stApp { background-color: #FAFAFC; }
    h1, h2, h3, h4, h5 { font-family: 'Times New Roman', 'DengXian', '等线', serif !important; color: #1A1A24; font-weight: bold;}
    section[data-testid="stSidebar"] { min-width: 220px !important; max-width: 220px !important; background-color: #111118 !important; border-right: 1px solid #2D2D3B; }
    section[data-testid="stSidebar"] h2 { font-family: 'Times New Roman', 'DengXian', '等线', serif !important; color: #FFFFFF !important; font-size: 1.1em !important; text-align: center; margin-top: -30px; margin-bottom: 20px; }
    section[data-testid="stSidebar"] div[role="radiogroup"] > label { background-color: transparent !important; padding: 8px 10px !important; border-radius: 6px !important; margin: 0 !important; border: none !important; cursor: pointer; }
    section[data-testid="stSidebar"] div[role="radiogroup"] > label p { color: #8892B0 !important; font-size: 0.85em !important; }
    section[data-testid="stSidebar"] div[role="radiogroup"] > label[data-checked="true"] { background-color: #1a1e2a !important; border-left: 3px solid #00B4D8 !important; }
    section[data-testid="stSidebar"] div[role="radiogroup"] > label[data-checked="true"] p { color: #FFFFFF !important; font-weight: bold !important; }
    div.stButton > button { border-radius: 6px !important; font-weight: 600 !important; border: none !important; box-shadow: 0 2px 4px rgba(0,0,0,0.05); transition: all 0.2s ease; }
    div.stButton > button:hover { transform: translateY(-1px); box-shadow: 0 4px 8px rgba(0,0,0,0.1); }
    .stTextInput input, .stTextArea textarea { border-radius: 6px !important; border: 1px solid #E0E4E8 !important; }
    div[data-baseweb="tab-list"] { gap: 10px; }
    div[data-baseweb="tab"] { padding: 8px 12px !important; font-size: 0.9em !important; }
    .toc-radio div[role="radiogroup"] > label { padding: 8px 10px !important; background: transparent !important; border: none !important; border-radius: 4px; transition: all 0.2s; }
    .toc-radio div[role="radiogroup"] > label:hover { background-color: #EAECEF !important; }
    .toc-radio div[role="radiogroup"] > label[data-checked="true"] { background-color: #E2E6EA !important; border-left: 3px solid #1F4E79 !important; }
    .toc-radio div[role="radiogroup"] > label[data-checked="true"] p { font-weight: bold !important; color: #111 !important;}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# ==========================================
# 🛠️ 核心工具函数区
# ==========================================
def set_font(run, ascii_font='Times New Roman', east_asia_font='等线'): 
    run.font.name = ascii_font; run._element.rPr.rFonts.set(qn('w:eastAsia'), east_asia_font)

def export_plain_text_to_word(text_content):
    doc = Document(); style = doc.styles['Normal']; style.font.name = 'Times New Roman'
    style._element.rPr.rFonts.set(qn('w:eastAsia'), '等线'); doc.add_heading('📖 英语精读教案 (备份)', 0)
    for line in text_content.split('\n'):
        if line.strip(): p = doc.add_paragraph(); set_font(p.add_run(line))
    bio = io.BytesIO(); doc.save(bio); return bio.getvalue()

def generate_beautiful_word(analysis_data, full_text=""):
    doc = Document()
    try:
        bg = parse_xml(f'<w:background {nsdecls("w")} w:color="F4F6F1"/>')
        doc.settings.element.insert(0, bg); shape = parse_xml(f'<w:displayBackgroundShape {nsdecls("w")}/>'); doc.settings.element.append(shape)
    except: pass
    style = doc.styles['Normal']; style.font.name = 'Times New Roman'
    style._element.rPr.rFonts.set(qn('w:eastAsia'), '等线')
    doc.add_heading('📖 英语专家级精读教案', level=1)
    if full_text:
        doc.add_heading('一、 英文原文', level=2)
        run_org = doc.add_paragraph().add_run(full_text.strip()); run_org.font.size, run_org.font.color.rgb = Pt(11), RGBColor(0x33, 0x33, 0x33); set_font(run_org)
    doc.add_heading('二、 逐句解析', level=2)
    for i, s in enumerate(analysis_data.get('sentences', [])):
        run_en = doc.add_paragraph().add_run(f"[{i+1}] {s.get('en', '')}"); run_en.bold, run_en.font.size = True, Pt(12); set_font(run_en)
        run_cn = doc.add_paragraph().add_run(f"译文：{s.get('cn', '')}"); run_cn.font.size, run_cn.font.color.rgb = Pt(10.5), RGBColor(0x55, 0x55, 0x55); set_font(run_cn)
        p_syn = doc.add_paragraph(); p_syn.paragraph_format.left_indent = Pt(15)
        r_syn = p_syn.add_run(f"🔍 语法：{s.get('syntax','')}\n💡 词法：{s.get('words','')}"); r_syn.font.size = Pt(10.5); set_font(r_syn)
        doc.add_paragraph().paragraph_format.space_after = Pt(6)
    v_list = analysis_data.get('core_vocabulary', [])
    if v_list:
        doc.add_heading('三、 核心词汇表', level=2)
        table = doc.add_table(rows=1, cols=4); table.style = 'Table Grid'
        for i, h in enumerate(['单词', '音标', '释义', '例句']): set_font(table.rows[0].cells[i].paragraphs[0].add_run(h))
        for v in v_list:
            row = table.add_row().cells; row[0].text, row[1].text, row[2].text, row[3].text = v.get('word',''), v.get('phonetic',''), v.get('translation',''), v.get('usage_examples','')
    bio = io.BytesIO(); doc.save(bio); return bio.getvalue()

def fetch_text_smart(url): 
    try: return trafilatura.extract(trafilatura.fetch_url(url)) if trafilatura.fetch_url(url) else "⚠️ 未能识别正文"
    except: return "抓取异常"

def extract_text_from_file(uploaded_file):
    if uploaded_file.type == "text/plain": return uploaded_file.read().decode("utf-8")
    elif uploaded_file.type == "application/pdf":
        return "\n".join([page.extract_text() for page in PdfReader(uploaded_file).pages if page.extract_text()])
    elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        return "\n".join([para.text for para in Document(uploaded_file).paragraphs])
    return ""

def format_reading_text(text):
    cleaned = text.replace('\r\n', '\n').replace('\n\n', '§§§')
    cleaned = cleaned.replace('\n', ' ')
    return cleaned.replace('§§§', '<br><br>')

# ==========================================
# 🔐 认证与无感登录系统
# ==========================================
if 'user' not in st.session_state: st.session_state['user'] = None

# 尝试从 Cookie 中无感恢复登录状态
if st.session_state['user'] is None:
    c_email = cookie_manager.get("saved_email")
    c_uid = cookie_manager.get("saved_uid")
    c_sign = cookie_manager.get("saved_sign")
    
    if c_email and c_uid and c_sign:
        if c_sign == get_secure_sign(c_email):
            st.session_state['user'] = SimpleUser(c_email, c_uid)

if st.session_state['user'] is None:
    st.markdown("<h1 style='text-align: center; margin-top:50px;'>🏛️ 顶级英语精读工作台</h1>", unsafe_allow_html=True)
    _, col_auth, _ = st.columns([1, 1, 1])
    with col_auth:
        tab_login, tab_signup = st.tabs(["🔑 登录", "🎟️ 凭邀请码注册"])
        with tab_login:
            email = st.text_input("邮箱"); pwd = st.text_input("密码", type="password")
            if st.button("进入系统", use_container_width=True, type="primary"):
                try: 
                    res = supabase.auth.sign_in_with_password({"email": email, "password": pwd})
                    st.session_state['user'] = res.user
                    # 登录成功，种下 30 天免登录 Cookie
                    cookie_manager.set("saved_email", res.user.email, max_age=30*24*3600)
                    cookie_manager.set("saved_uid", res.user.id, max_age=30*24*3600)
                    cookie_manager.set("saved_sign", get_secure_sign(res.user.email), max_age=30*24*3600)
                    st.rerun()
                except: st.error("账号或密码有误")
        with tab_signup:
            s_email = st.text_input("设置邮箱"); s_pwd = st.text_input("设置密码(>6位)", type="password"); s_code = st.text_input("邀请码")
            if st.button("注册"):
                code_res = supabase.table('invitation_codes').select('*').eq('code', s_code).eq('is_used', False).execute()
                if code_res.data:
                    try:
                        supabase.auth.sign_up({"email": s_email, "password": s_pwd})
                        exp = (datetime.datetime.now() + datetime.timedelta(days=code_res.data[0]['duration_days'])).isoformat()
                        supabase.table('invitation_codes').update({'is_used': True, 'used_by': s_email}).eq('code', s_code).execute()
                        supabase.table('subscriptions').insert({'user_email': s_email, 'expires_at': exp}).execute()
                        st.success("注册成功！请切换登录。")
                    except: st.error("注册失败，可能邮箱已被使用。")
                else: st.error("邀请码无效或已使用")
    st.stop()

# ==========================================
# 🛡️ 订阅状态拦截系统
# ==========================================
USER_EMAIL = st.session_state['user'].email; IS_ADMIN = (USER_EMAIL == ADMIN_EMAIL); CURRENT_USER_ID = st.session_state['user'].id

current_exp = None
is_expired = False
if not IS_ADMIN:
    sub_res = supabase.table('subscriptions').select('*').eq('user_email', USER_EMAIL).execute()
    if sub_res.data:
        current_exp = datetime.datetime.fromisoformat(sub_res.data[0]['expires_at'])
        if datetime.datetime.now() > current_exp: is_expired = True
    else:
        is_expired = True

if 'nav_page' not in st.session_state: st.session_state['nav_page'] = "📚 公共教材图书馆"
menu_options = ["📚 公共教材图书馆", "🔍 智能精读教研室", "🗂️ 文章分类档案馆", "🔠 词汇分级记忆库"]
if IS_ADMIN: menu_options.append("👑 老板管理后台")

st.sidebar.markdown("## 🏛️ 工作台")
default_idx = menu_options.index(st.session_state['nav_page']) if st.session_state['nav_page'] in menu_options else 0
page = st.sidebar.radio("导航", menu_options, index=default_idx, label_visibility="collapsed")
st.session_state['nav_page'] = page 

st.sidebar.markdown("---")
st.sidebar.caption(f"👤 {USER_EMAIL}")
if current_exp and not IS_ADMIN:
    status_icon = "🔴" if is_expired else "🟢"
    st.sidebar.caption(f"{status_icon} VIP到期日: {current_exp.strftime('%Y-%m-%d')}")

# 安全退出：不仅清空内存，还要删除 Cookie
if st.sidebar.button("🚪 退出系统", use_container_width=True): 
    cookie_manager.delete("saved_email")
    cookie_manager.delete("saved_uid")
    cookie_manager.delete("saved_sign")
    st.session_state['user'] = None
    st.rerun()

if not IS_ADMIN and is_expired:
    st.warning("⚠️ 您的 VIP 授权已到期，系统已暂停您的操作权限。")
    st.info(f"👉 您的账号资料已安全锁定。请联系管理员微信 **{CONTACT_WECHAT}** 进行续费激活，解锁全部权限！")
    st.stop()


# ==========================================
# 👑 模块：老板 CRM 管理后台
# ==========================================
if IS_ADMIN and page == "👑 老板管理后台":
    st.title("👑 老板全能控制台")
    
    tab_gen, tab_users, tab_codes = st.tabs(["🎟️ 激活码生成", "👥 用户管理 & 一键续费", "📋 激活码查账明细"])
    
    with tab_gen:
        st.markdown("#### 🔨 生成新激活码")
        with st.form("gen_code_form"):
            plan = st.radio("授权时长：", ["7天试用", "1个月", "3个月", "1年", "终身"], horizontal=True)
            days_map = {"7天试用": 7, "1个月": 30, "3个月": 90, "1年": 365, "终身": 36500}
            if st.form_submit_button("🔨 立即生成", type="primary"):
                new_code = f"VIP-{''.join(random.choices(string.ascii_uppercase + string.digits, k=8))}"
                try:
                    supabase.table('invitation_codes').insert({"code": new_code, "duration_days": days_map[plan], "is_used": False}).execute()
                    st.success(f"生成成功: {new_code}"); st.code(new_code)
                except: st.error("生成失败")

    with tab_users:
        st.markdown("#### 👥 客户关系管理")
        try:
            sub_data = supabase.table('subscriptions').select('*').execute().data
            if sub_data:
                df_subs = pd.DataFrame(sub_data)
                now_dt = datetime.datetime.now()
                df_subs['到期时间'] = pd.to_datetime(df_subs['expires_at'])
                df_subs['状态'] = df_subs['到期时间'].apply(lambda x: "🔴 已过期" if x < now_dt else "🟢 正常")
                
                st.metric("总注册用户数", len(df_subs))
                
                user_list = df_subs['user_email'].tolist()
                selected_user = st.selectbox("🔍 搜索或选择要操作的客户账号：", user_list)
                
                if selected_user:
                    user_info = df_subs[df_subs['user_email'] == selected_user].iloc[0]
                    curr_exp = user_info['到期时间']
                    
                    st.markdown(f"""
                    <div style='background:#F4F6F1; padding:15px; border-radius:8px; border:1px solid #EAECEF; margin-bottom:15px;'>
                        <b style='font-size:1.1em;'>客户：{selected_user}</b><br>
                        当前状态：{user_info['状态']}<br>
                        到期时间：{curr_exp.strftime('%Y-%m-%d %H:%M:%S')}
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.markdown("##### ⚡ 老板特权：一键充值 (免密续费)")
                    col_r1, col_r2, col_r3 = st.columns(3)
                    add_days = 0
                    if col_r1.button("💸 续费 30 天", use_container_width=True): add_days = 30
                    if col_r2.button("💸 续费 90 天", use_container_width=True): add_days = 90
                    if col_r3.button("💸 续费 365 天", use_container_width=True): add_days = 365
                    
                    if add_days > 0:
                        base_date = curr_exp if curr_exp > now_dt else now_dt
                        new_exp = base_date + datetime.timedelta(days=add_days)
                        try:
                            supabase.table('subscriptions').update({'expires_at': new_exp.isoformat()}).eq('user_email', selected_user).execute()
                            st.success(f"✅ 续费成功！已为 {selected_user} 增加 {add_days} 天。")
                        except Exception as e: st.error(f"续费失败: {e}")
            else: st.info("当前还没有注册用户。")
        except: st.error("加载用户数据失败。")

    with tab_codes:
        st.markdown("#### 📋 激活码核销账本")
        try:
            codes_data = supabase.table('invitation_codes').select('*').execute().data
            if codes_data:
                df_codes = pd.DataFrame(codes_data)
                df_codes['状态'] = df_codes['is_used'].apply(lambda x: "🔴 已核销" if x else "🟢 未使用")
                if 'used_by' in df_codes.columns:
                    display_codes = df_codes[['code', 'duration_days', '状态', 'used_by', 'created_at']]
                    display_codes.columns = ['激活码', '授权天数', '状态', '使用者', '生成时间']
                    display_codes['使用者'] = display_codes['使用者'].fillna('-')
                else:
                    display_codes = df_codes[['code', 'duration_days', '状态', 'created_at']]
                    display_codes.columns = ['激活码', '授权天数', '状态', '生成时间']
                st.dataframe(display_codes.sort_values(by='生成时间', ascending=False), use_container_width=True, hide_index=True)
            else: st.info("还没有生成过激活码。")
        except: pass


# ==========================================
# 📚 模块：公共教材图书馆
# ==========================================
elif page == "📚 公共教材图书馆":
    
    if IS_ADMIN:
        with st.expander("👑 馆长专属：上传新教材/小说", expanded=False):
            lib_title = st.text_input("篇目标题")
            lib_cat = st.selectbox("分类", ["新概念", "小学教材", "初中教材", "高中教材", "英文名著", "课外阅读", "其他"])
            upload_method = st.radio("录入方式", ["手动粘贴", "📂 上传本地文档"], horizontal=True, label_visibility="collapsed")
            lib_content = ""
            if upload_method == "手动粘贴": lib_content = st.text_area("正文", height=100)
            else:
                uploaded_file = st.file_uploader("选择文档", type=["pdf", "docx", "txt"])
                if uploaded_file: lib_content = extract_text_from_file(uploaded_file); st.success("提取成功！")
            
            if st.button("⬆️ 上传至公共书架", type="primary"):
                if lib_title and lib_content.strip():
                    supabase.table('public_library').insert({"title": lib_title, "category": lib_cat, "content": lib_content}).execute()
                    st.success("✅ 上传成功！"); st.rerun()

    try:
        lib_data = supabase.table('public_library').select('*').execute().data
        if lib_data:
            df_lib = pd.DataFrame(lib_data); categories = ["全部"] + list(df_lib['category'].dropna().unique())
            
            cat_filter = st.selectbox("📌 书架分类", categories)
            filtered_lib = [a for a in lib_data if a.get('category') == cat_filter] if cat_filter != "全部" else lib_data
            
            if filtered_lib:
                st.divider()
                col_toc, col_read, col_tools = st.columns([1, 2.5, 1.2], gap="medium")
                with col_toc:
                    st.markdown("##### 📑 目录")
                    st.markdown("<div class='toc-radio'>", unsafe_allow_html=True)
                    options = [f"📖 {a.get('title', '')}" for a in filtered_lib]
                    selected_title = st.radio("目录", options, label_visibility="collapsed")
                    st.markdown("</div>", unsafe_allow_html=True)
                    selected_item = filtered_lib[options.index(selected_title)]
                
                with col_read:
                    st.markdown(f"#### {selected_item.get('title')}")
                    clean_html_text = format_reading_text(selected_item.get('content', ''))
                    st.markdown(f"""
                    <div style='background-color: #F3F6F0; padding: 25px 30px; border-radius: 8px; font-family: "Times New Roman", serif; font-size: 1.15em; color: #2C3E50; line-height: 1.6; text-align: justify; height: 600px; overflow-y: auto; border: 1px solid #EAECEF; box-shadow: inset 0 2px 4px rgba(0,0,0,0.02);'>
                        {clean_html_text}
                    </div>
                    """, unsafe_allow_html=True)

                with col_tools:
                    st.markdown("#### 🛠️ 伴读助手")
                    tab_dict, tab_clip = st.tabs(["🔍 查词", "📝 摘抄"])
                    
                    with tab_dict:
                        st.caption("复制左侧生词粘贴查阅")
                        lookup_word = st.text_input("输入英文生词", label_visibility="collapsed", placeholder="例如: consecutive")
                        if st.button("💡 翻译并存入记忆库", type="primary", use_container_width=True):
                            if lookup_word:
                                with st.spinner("查词中..."):
                                    prompt = f"""分析单词: {lookup_word}。返回纯JSON: {{"word":"{lookup_word}","phonetic":"音标","translation":"精准中文释义","memory_tip":"一句精简的词根或联想记忆法","usage_examples":"一个简短实用的英文例句及中文","tags":"阅读生词"}}"""
                                    try:
                                        res = llm_client.chat.completions.create(model="deepseek-chat", messages=[{"role":"user","content":prompt}], response_format={"type":"json_object"})
                                        word_data = json.loads(res.choices[0].message.content)
                                        st.info(f"**{word_data.get('word')}** {word_data.get('phonetic')}\n\n**释义**：{word_data.get('translation')}\n\n**记忆**：{word_data.get('memory_tip')}")
                                        word_data['user_id'] = CURRENT_USER_ID; supabase.table('vocabulary').insert(word_data).execute()
                                        st.success("✅ 已保存至记忆库")
                                    except: st.error("查词失败")
                    
                    with tab_clip:
                        st.caption("复制左侧长难句解析")
                        clip_sentence = st.text_area("输入句子", label_visibility="collapsed", height=100, placeholder="粘贴您想精读的句子...")
                        if st.button("✍️ 解析并存入档案馆", type="primary", use_container_width=True):
                            if clip_sentence:
                                with st.spinner("解析中..."):
                                    prompt = f"""深度解析此句，返回JSON: {{"sentences":[{{"en":"{clip_sentence}","cn":"精美的翻译","syntax":"极简语法框架拆解","words":"核心词组解析"}}]}}"""
                                    try:
                                        res = llm_client.chat.completions.create(model="deepseek-chat", messages=[{"role":"user","content":prompt}], response_format={"type":"json_object"})
                                        clip_data = json.loads(res.choices[0].message.content); s = clip_data['sentences'][0]
                                        txt = f"[{1}] {s.get('en','')}\n译：{s.get('cn','')}\n🔍 语法：{s.get('syntax','')}\n💡 词法：{s.get('words','')}\n\n"
                                        supabase.table('articles').insert({"user_id": CURRENT_USER_ID, "content": clip_sentence, "teaching_plan": txt, "translation": json.dumps(clip_data), "category": "摘抄好句"}).execute()
                                        st.success("✅ 解析完成！已保存至【档案馆-摘抄好句】")
                                        st.markdown(f"<div style='font-size:0.9em; background:#fff; padding:10px; border-radius:5px; border:1px solid #eee;'><b>译：</b>{s.get('cn')}<br><br><b>语法：</b>{s.get('syntax')}</div>", unsafe_allow_html=True)
                                    except: st.error("解析失败")
            else: st.info("该分类下暂无内容。")
        else: st.info("📚 图书馆书架还是空的，请等待馆长上新！")
    except: pass

# ==========================================
# 🔍 模块：教研室
# ==========================================
elif page == "🔍 智能精读教研室":
    st.title("🔍 智能精读教研室")
    col1, col2 = st.columns([4, 1])
    with col1: url = st.text_input("🔗 输入英文文章链接：")
    with col2: 
        st.write(""); st.write("")
        if st.button("🛰️ 提取网页", use_container_width=True):
            if url: st.session_state['temp_text'] = fetch_text_smart(url)
    
    final_text = st.text_area("📝 待分析文本：", value=st.session_state.get('temp_text', ""), height=200)
    
    if st.button("🧠 生成专家级教案", type="primary"):
        if not final_text.strip(): st.error("请先输入文本")
        else:
            with st.spinner("AI正在切片..."):
                prompt = f"""以JSON格式输出全句拆解：{{"sentences": [{{"en": "原句英文", "cn": "翻译", "syntax": "极简语法", "words": "核心词法"}}], "core_vocabulary": [{{"word": "单词", "phonetic": "音标", "translation": "释义", "memory_tip": "记忆法", "usage_examples": "造句", "tags": "级别"}}]}} 待分析：\n{final_text[:5000]}""" 
                try:
                    res = llm_client.chat.completions.create(model="deepseek-chat", messages=[{"role":"user","content":prompt}], response_format={"type":"json_object"})
                    st.session_state['analysis_result'] = json.loads(res.choices[0].message.content); st.session_state['article_content'] = final_text; st.rerun()
                except Exception: st.error("分析失败")

    if 'analysis_result' in st.session_state:
        res = st.session_state['analysis_result']; st.divider()
        c1, c2, c3 = st.columns(3)
        with c1: st.download_button("📝 导出 Word", data=generate_beautiful_word(res, st.session_state.get('article_content', '')), file_name="教案.docx", use_container_width=True)
        with c2: cat = st.selectbox("📂 保存分类：", ["精读课文", "课外拓展", "考试阅读", "未分类"], label_visibility="collapsed")
        with c3:
            if st.button("☁️ 归档至私人空间", use_container_width=True):
                txt = "".join([f"[{i+1}] {s.get('en','')}\n译：{s.get('cn','')}\n🔍 语法：{s.get('syntax','').replace('*', '')}\n💡 词法：{s.get('words','').replace('*', '')}\n\n" for i,s in enumerate(res.get('sentences', []))])
                try:
                    supabase.table('articles').insert({"user_id": CURRENT_USER_ID, "content": st.session_state['article_content'], "teaching_plan": txt, "translation": json.dumps(res), "category": cat}).execute()
                    for v in res.get('core_vocabulary', []): v["user_id"] = CURRENT_USER_ID; supabase.table('vocabulary').insert(v).execute()
                    st.success("✅ 归档成功！")
                except Exception: st.error("保存失败")
                    
        for i, s in enumerate(res.get('sentences', [])):
            st.markdown(f"""<div style='background:#F4F6F1; border-radius:8px; padding:12px; margin-bottom:8px;'>
                <div style='font-family: Times New Roman; font-size:1.05em; font-weight:bold;'>[{i+1}] {s.get('en','')}</div><div style='color:#555; font-size:0.95em;'>译：{s.get('cn','')}</div>
                <div style='font-size:0.9em; margin-top:4px;'><span style='color:#1F4E79;'>🔍 语法：</span>{s.get('syntax','')}</div><div style='font-size:0.9em;'><span style='color:#C00000;'>💡 词法：</span>{s.get('words','')}</div></div>""", unsafe_allow_html=True)

# ==========================================
# 🗂️ 档案馆
# ==========================================
elif page == "🗂️ 文章分类档案馆":
    st.title("🗂️ 私人档案馆")
    try:
        arts_data = supabase.table('articles').select('*').eq('user_id', CURRENT_USER_ID).execute().data
        if arts_data:
            df_arts = pd.DataFrame(arts_data); categories = ["全部"] + list(df_arts['category'].dropna().unique())
            tabs = st.tabs(categories)
            for i, tab in enumerate(tabs):
                with tab:
                    filtered_arts = [a for a in arts_data if a.get('category') == categories[i]] if categories[i] != "全部" else arts_data
                    if filtered_arts:
                        col_list, col_content = st.columns([1, 3.5], gap="large")
                        with col_list:
                            options = [f"{idx+1}. {a.get('content', '')[:25]}..." for idx, a in enumerate(filtered_arts)]
                            selected_title = st.radio("选择文章", options, key=f"radio_{i}", label_visibility="collapsed")
                        with col_content:
                            selected_art = filtered_arts[options.index(selected_title)]
                            art_id = selected_art.get('id'); raw_json = selected_art.get('translation', '')
                            try: full_analysis = json.loads(raw_json) if raw_json else None
                            except: full_analysis = None
                            
                            c1, c2 = st.columns(2)
                            with c1: 
                                word_data = generate_beautiful_word(full_analysis, selected_art.get('content', '')) if full_analysis else export_plain_text_to_word(selected_art.get('teaching_plan', ''))
                                st.download_button("📥 重新导出", data=word_data, file_name="归档教案.docx", use_container_width=True, key=f"dl_{art_id}_{i}")
                            with c2: 
                                if st.button("🗑️ 永久删除", key=f"del_{art_id}_{i}", use_container_width=True):
                                    supabase.table('articles').delete().eq('id', art_id).execute(); st.rerun()
                                    
                            st.markdown("##### 📰 原文/摘抄"); st.markdown(f"<div style='background-color:#F3F6F0; padding:12px; border-radius:6px; max-height:120px; overflow-y:auto; margin-bottom:15px;'>{selected_art.get('content','')}</div>", unsafe_allow_html=True)
                            st.markdown("##### 🔬 解析"); st.markdown(f"<div style='background-color:#F3F6F0; padding:16px; border-radius:6px; white-space:pre-wrap;'>{selected_art.get('teaching_plan','').strip()}</div>", unsafe_allow_html=True)
                    else: st.info("暂无记录。")
        else: st.info("空空如也。")
    except: pass

elif page == "🔠 词汇分级记忆库":
    st.title("🔠 私人词汇库")
    try:
        vocab_data = supabase.table('vocabulary').select('*').eq('user_id', CURRENT_USER_ID).execute().data
        if vocab_data:
            df_vocab = pd.DataFrame(vocab_data); tag_filter = st.selectbox("🎓 筛选：", ["全部"] + list(df_vocab['tags'].dropna().unique()))
            display_df = df_vocab[df_vocab['tags'] == tag_filter] if tag_filter != "全部" else df_vocab
            st.metric("生词量", len(display_df)); st.dataframe(display_df[['word', 'phonetic', 'translation', 'tags', 'memory_tip']], use_container_width=True)
        else: st.info("无词汇。")
    except: pass