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
# 🎨 UI/UX 大师级设计系统
# ==========================================
st.set_page_config(page_title="顶级英语教研平台-商业版", page_icon="🏛️", layout="wide")
custom_css = """
<style>
    [data-testid="stSidebar"] { background-color: #1A1A24 !important; border-right: 1px solid #2D2D3B; }
    [data-testid="stSidebar"], [data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] div { color: #F0F0F5 !important; }
    .stApp { background-color: #FAFAFC; }
    h1, h2, h3 { font-family: 'Times New Roman', '等线', serif !important; color: #1A1A24; }
    div.stButton > button { border-radius: 6px !important; font-weight: 600 !important; }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# ==========================================
# 🔐 商业版认证系统 (邀请码机制)
# ==========================================
if 'user' not in st.session_state:
    st.session_state['user'] = None

if st.session_state['user'] is None:
    st.markdown("<h1 style='text-align: center; margin-top: 50px;'>🏛️ 顶级英语精读工作台</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #666;'>专业教研 · 深度分析 · 邀请制商业版</p>", unsafe_allow_html=True)
    
    _, col_auth, _ = st.columns([1, 1, 1])
    with col_auth:
        tab_login, tab_signup = st.tabs(["🔑 账号登录", "🎟️ 凭邀请码注册"])
        
        # --- 登录逻辑 ---
        with tab_login:
            login_email = st.text_input("邮箱地址", key="l_email")
            login_pwd = st.text_input("登录密码", type="password", key="l_pwd")
            if st.button("立即验证并进入", use_container_width=True, type="primary"):
                with st.spinner("验证身份与使用期限..."):
                    try:
                        response = supabase.auth.sign_in_with_password({"email": login_email, "password": login_pwd})
                        st.session_state['user'] = response.user
                        st.rerun()
                    except:
                        st.error("验证失败：账号或密码有误。")
                        
        # --- 凭邀请码注册逻辑 ---
        with tab_signup:
            st.info("💡 只有通过管理员购买获取的专属邀请码，才能注册本平台。")
            signup_email = st.text_input("设置登录邮箱", key="s_email")
            signup_pwd = st.text_input("设置登录密码 (至少6位)", type="password", key="s_pwd")
            signup_code = st.text_input("🔑 输入有效的邀请码", placeholder="例如: VIP-XXXX-XXXX")
            
            if st.button("核销邀请码并注册", use_container_width=True):
                if not signup_email or len(signup_pwd) < 6 or not signup_code:
                    st.warning("请完整填写信息，密码需大于6位。")
                else:
                    with st.spinner("正在核验邀请码..."):
                        # 1. 检查邀请码是否存在且未使用
                        code_res = supabase.table('invitation_codes').select('*').eq('code', signup_code).eq('is_used', False).execute()
                        
                        if not code_res.data:
                            st.error("❌ 邀请码无效或已被其他人使用！")
                        else:
                            duration = code_res.data[0]['duration_days']
                            try:
                                # 2. 注册账号
                                response = supabase.auth.sign_up({"email": signup_email, "password": signup_pwd})
                                
                                # 3. 计算到期时间
                                exp_date = (datetime.datetime.now() + datetime.timedelta(days=duration)).isoformat()
                                
                                # 4. 更新数据库：废弃邀请码，注入订阅时间
                                supabase.table('invitation_codes').update({'is_used': True}).eq('code', signup_code).execute()
                                supabase.table('subscriptions').insert({'user_email': signup_email, 'expires_at': exp_date}).execute()
                                
                                st.success(f"✅ 注册成功！为您开通了 {duration} 天的高级使用权限。请切换到左侧登录。")
                            except Exception as e:
                                st.error(f"注册失败: 邮箱可能已被注册，或系统错误 ({e})")
    st.stop()

# ==========================================
# ⏱️ 会员期限拦截器
# ==========================================
USER_EMAIL = st.session_state['user'].email
IS_ADMIN = (USER_EMAIL == ADMIN_EMAIL)
CURRENT_USER_ID = st.session_state['user'].id

if not IS_ADMIN:
    # 老板免检，其他用户每次操作都检查是否过期
    sub_res = supabase.table('subscriptions').select('*').eq('user_email', USER_EMAIL).execute()
    if not sub_res.data:
        st.error("❌ 未检测到您的授权订阅信息，请联系管理员。")
        if st.button("退出账号"): st.session_state['user'] = None; st.rerun()
        st.stop()
    
    exp_time = datetime.datetime.fromisoformat(sub_res.data[0]['expires_at'])
    if datetime.datetime.now() > exp_time:
        st.error(f"❌ 您的账号已于 {exp_time.strftime('%Y-%m-%d')} 到期，已被系统冻结。如需继续使用，请联系管理员购买新激活码。")
        if st.button("退出账号"): st.session_state['user'] = None; st.rerun()
        st.stop()
    else:
        st.sidebar.success(f"⏳ 账号到期日: {exp_time.strftime('%Y-%m-%d')}")

# ==========================================
# 📝 核心功能函数 (完全复用)
# ==========================================
def fetch_text_smart(url):
    try:
        downloaded = trafilatura.fetch_url(url)
        return trafilatura.extract(downloaded) if downloaded else "⚠️ 未能识别正文"
    except Exception as e: return f"抓取异常: {e}"

def set_font(run, ascii_font='Times New Roman', east_asia_font='等线'):
    run.font.name = ascii_font; run._element.rPr.rFonts.set(qn('w:eastAsia'), east_asia_font)

def generate_beautiful_word(analysis_data):
    doc = Document(); style = doc.styles['Normal']
    style.font.name, style.font.size = 'Times New Roman', Pt(10.5)
    style._element.rPr.rFonts.set(qn('w:eastAsia'), '等线')
    doc.add_heading('📖 英语精读教案', 0)
    for i, s in enumerate(analysis_data.get('sentences', [])):
        run_en = doc.add_paragraph().add_run(f"[{i+1}] {s.get('en', '')}"); run_en.bold, run_en.font.size = True, Pt(14); set_font(run_en)
        run_cn = doc.add_paragraph().add_run(f"译文：{s.get('cn', '')}"); run_cn.font.size = Pt(11); set_font(run_cn)
        p_syn = doc.add_paragraph(); p_syn.paragraph_format.left_indent = Pt(15)
        r_l1 = p_syn.add_run("🔍 语法拆解："); r_l1.bold, r_l1.font.color.rgb = True, RGBColor(0x1F, 0x4E, 0x79); set_font(r_l1)
        r_t1 = p_syn.add_run(s.get('syntax', '').replace('*', '')); set_font(r_t1)
        if s.get('words'):
            p_w = doc.add_paragraph(style='List Bullet')
            r_l2 = p_w.add_run("💡 核心词法："); r_l2.bold, r_l2.font.color.rgb = True, RGBColor(0xC0, 0x00, 0x00); set_font(r_l2)
            r_t2 = p_w.add_run(s.get('words', '').replace('*', '')); set_font(r_t2)
    bio = io.BytesIO(); doc.save(bio); return bio.getvalue()

# ==========================================
# 🧭 侧边栏导航
# ==========================================
menu_options = ["🔍 1. 智能精读教研室", "🗂️ 2. 文章分类档案馆", "🔠 3. 词汇分级记忆库"]
if IS_ADMIN: menu_options.append("👑 4. 老板发卡中心")

st.sidebar.markdown(f"## 🏛️ 工作台")
page = st.sidebar.radio("核心导航：", menu_options)
st.sidebar.markdown("---")
st.sidebar.caption(f"👤 账号: {USER_EMAIL}")
if st.sidebar.button("🚪 安全退出系统"):
    st.session_state['user'] = None
    st.rerun()

# ==========================================
# 👑 模块 4：老板全自动发卡中心 (赚钱引擎)
# ==========================================
if page == "👑 4. 老板发卡中心":
    st.title("👑 邀请码发卡中心")
    st.markdown("您可以生成具有不同有效期的邀请码，发送给付费用户自行注册。")
    
    col_g1, col_g2 = st.columns([2, 1])
    with col_g1:
        # 生成邀请码面板
        with st.form("gen_code_form"):
            st.subheader("🎟️ 生成全新邀请码")
            plan = st.radio("选择授权时长：", ["1个月 (30天)", "1个季度 (90天)", "1年 (365天)", "终身版 (36500天)"], horizontal=True)
            days_map = {"1个月 (30天)": 30, "1个季度 (90天)": 90, "1年 (365天)": 365, "终身版 (36500天)": 36500}
            
            if st.form_submit_button("🔨 立即生成一枚邀请码", type="primary"):
                # 随机生成格式如 VIP-A8K9-M2N1 的邀请码
                random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
                new_code = f"VIP-{random_str[:4]}-{random_str[4:]}"
                selected_days = days_map[plan]
                
                try:
                    supabase.table('invitation_codes').insert({"code": new_code, "duration_days": selected_days, "is_used": False}).execute()
                    st.success(f"🎉 生成成功！")
                    st.code(new_code, language="text")
                    st.info(f"⬆️ 请复制上方邀请码发送给客户。注册后有效期：{selected_days} 天。")
                except Exception as e:
                    st.error(f"生成失败: {e}")

    st.divider()
    st.subheader("📋 尚未使用的库存邀请码")
    try:
        codes_data = supabase.table('invitation_codes').select('*').eq('is_used', False).execute().data
        if codes_data:
            df_codes = pd.DataFrame(codes_data)[['code', 'duration_days']]
            df_codes.rename(columns={'code': '邀请码', 'duration_days': '可用天数'}, inplace=True)
            st.dataframe(df_codes, use_container_width=True)
        else:
            st.info("目前没有未使用的库存邀请码。")
    except: pass

# ==========================================
# 🔍 以下为教研室、档案馆、记忆库模块 (与之前完全相同)
# ==========================================
elif page == "🔍 1. 智能精读教研室":
    st.title("🔍 智能精读教研室")
    col1, col2 = st.columns([3, 1])
    with col1: url = st.text_input("🔗 输入英文文章链接：")
    with col2:
        st.write(""); st.write("")
        if st.button("🛰️ 提取正文", use_container_width=True):
            if url: st.session_state['temp_text'] = fetch_text_smart(url)
    
    final_text = st.text_area("📝 待分析文本：", value=st.session_state.get('temp_text', ""), height=150)
    if st.button("🧠 生成专家级教案", type="primary"):
        if not final_text.strip(): st.error("请先输入文本")
        else:
            with st.spinner("教研员正在逐句切片..."):
                prompt = f"""以JSON格式输出：{{"sentences": [{{"en": "原句英文", "cn": "翻译", "syntax": "极简语法", "words": "核心词法"}}], "core_vocabulary": [{{"word": "单词", "phonetic": "音标", "translation": "释义", "memory_tip": "记忆法", "usage_examples": "造句", "tags": "级别"}}]}} 待分析：\n{final_text}""" 
                try:
                    res = llm_client.chat.completions.create(model="deepseek-chat", messages=[{"role":"user","content":prompt}], response_format={"type":"json_object"})
                    st.session_state['analysis_result'] = json.loads(res.choices[0].message.content)
                    st.session_state['article_content'] = final_text
                    st.rerun()
                except Exception as e: st.error(f"分析失败: {e}")

    if 'analysis_result' in st.session_state:
        res = st.session_state['analysis_result']
        st.divider()
        c1, c2, c3 = st.columns(3)
        with c1: st.download_button("📝 导出 Word 教案", data=generate_beautiful_word(res), file_name="教案.docx", use_container_width=True)
        with c2: cat = st.selectbox("📂 分类：", ["新闻", "学术", "名著", "考试", "日常", "未分类"], label_visibility="collapsed")
        with c3:
            if st.button("☁️ 同步至私人云端", use_container_width=True):
                txt = "".join([f"[{i+1}] {s.get('en','')}\n译：{s.get('cn','')}\n\n" for i,s in enumerate(res.get('sentences', []))])
                supabase.table('articles').insert({"user_id": CURRENT_USER_ID, "content": st.session_state['article_content'], "teaching_plan": txt, "category": cat}).execute()
                for v in res.get('core_vocabulary', []):
                    v["user_id"] = CURRENT_USER_ID
                    supabase.table('vocabulary').insert(v).execute()
                st.success("✅ 已私有化保存")
        for i, s in enumerate(res.get('sentences', [])):
            st.markdown(f"""<div style='background:#fff; border:1px solid #eee; border-radius:8px; padding:12px; margin-bottom:10px;'>
                <div style='font-weight:600;'>[{i+1}] {s.get('en','')}</div><div style='color:#555;'>译：{s.get('cn','')}</div>
                <div style='font-size:0.9em; margin-top:5px;'><span style='color:#1F4E79;'>🔍 语法：</span>{s.get('syntax','')}</div>
                <div style='font-size:0.9em;'><span style='color:#C00000;'>💡 词法：</span>{s.get('words','')}</div></div>""", unsafe_allow_html=True)

elif page == "🗂️ 2. 文章分类档案馆":
    st.title("🗂️ 私人文章档案馆")
    try:
        arts_data = supabase.table('articles').select('*').eq('user_id', CURRENT_USER_ID).execute().data
        if arts_data:
            df_arts = pd.DataFrame(arts_data); cat_filter = st.selectbox("📌 筛选：", ["全部"] + list(df_arts['category'].dropna().unique()) if 'category' in df_arts.columns else ["全部"])
            filtered_arts = df_arts[df_arts['category'] == cat_filter].to_dict('records') if cat_filter != "全部" else arts_data
            for a in filtered_arts:
                with st.expander(f"📖 [{a.get('category', '未分类')}] {a.get('content', '')[:60]}..."): st.text(a.get('teaching_plan', '无'))
        else: st.info("空空如也。")
    except: pass

elif page == "🔠 3. 词汇分级记忆库":
    st.title("🔠 私人专属词汇库")
    try:
        vocab_data = supabase.table('vocabulary').select('*').eq('user_id', CURRENT_USER_ID).execute().data
        if vocab_data:
            df_vocab = pd.DataFrame(vocab_data); tag_filter = st.selectbox("🎓 筛选：", ["全部"] + list(df_vocab['tags'].dropna().unique()))
            display_df = df_vocab[df_vocab['tags'] == tag_filter] if tag_filter != "全部" else df_vocab
            st.metric("生词量", len(display_df)); st.dataframe(display_df[['word', 'phonetic', 'translation', 'tags', 'memory_tip']], use_container_width=True)
        else: st.info("还没有收藏过单词。")
    except: pass