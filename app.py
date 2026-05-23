# -*- coding: utf-8 -*-
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
# -*- coding: utf-8 -*-
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import os
import sys
import numpy as np
import re
from PIL import Image
from clip_score import get_consistency_score, highlight_conflict
import base64
from textwrap import dedent
import math
import json
from datetime import datetime

# ========== 强制设置项目根目录 ==========
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(PROJECT_ROOT)
print(f"[启动] 项目根目录: {PROJECT_ROOT}")

# 加载环境变量（从 .env 文件）
env_path = os.path.join(PROJECT_ROOT, '.env')
if os.path.exists(env_path):
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()


# PDF导出相关导入
try:
    from xhtml2pdf import pisa
    PDF_SUPPORTED = True
except ImportError:
    PDF_SUPPORTED = False

# 报告导出函数
def get_report_markdown():
    """生成Markdown格式的研判报告"""
    score = st.session_state.score
    text = st.session_state.text
    explanation = st.session_state.explanation
    img_path = st.session_state.img_path
    
    # 判断结论
    if score >= 70:
        verdict = "高度可信"
        verdict_level = "A"
    elif score >= 45:
        verdict = "内容存疑"
        verdict_level = "B"
    else:
        verdict = "疑似谣言"
        verdict_level = "C"
    
    md = f"""# 多模态谣言检测研判报告

## 基本信息

- **检测时间**: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}
- **图像文件**: {os.path.basename(img_path) if img_path else '未上传'}
- **一致性得分**: {score:.2f}分
- **研判结论**: {verdict} (等级: {verdict_level})

---

## 待检测文本

```
{text}
```

---

## 智能研判分析

{explanation}

---

**报告生成**: 图文一致性多模态谣言检测系统
**版本**: v2.5 专业版
"""
    return md

def get_report_html():
    """生成HTML格式的研判报告"""
    score = st.session_state.score
    text = st.session_state.text
    explanation = st.session_state.explanation
    img_path = st.session_state.img_path
    
    # 判断结论
    if score >= 70:
        verdict = "高度可信"
        verdict_color = "#10b981"
        verdict_bg = "rgba(16, 185, 129, 0.1)"
    elif score >= 45:
        verdict = "内容存疑"
        verdict_color = "#f59e0b"
        verdict_bg = "rgba(245, 158, 11, 0.1)"
    else:
        verdict = "疑似谣言"
        verdict_color = "#ef4444"
        verdict_bg = "rgba(239, 68, 68, 0.1)"
    
    # 提前处理需要插入的值
    current_time = datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')
    img_name = os.path.basename(img_path) if img_path else '未上传'
    score_str = f"{score:.2f}"
    escaped_text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    escaped_explanation = explanation.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('\n', '<br/>')
    
    # 使用字符串拼接而非f-string来避免反斜杠问题
    html = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>多模态谣言检测研判报告</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; max-width: 800px; margin: 0 auto; padding: 40px 20px; background: #f8fafc; }
        .report-container { background: white; border-radius: 16px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); padding: 40px; }
        .report-header { border-bottom: 2px solid #e2e8f0; padding-bottom: 20px; margin-bottom: 30px; }
        .report-title { font-size: 24px; font-weight: 800; color: #1e293b; margin: 0; }
        .report-subtitle { color: #64748b; margin-top: 8px; }
        .info-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px; margin-bottom: 30px; }
        .info-item { background: #f8fafc; padding: 16px; border-radius: 8px; }
        .info-label { font-size: 12px; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.5px; }
        .info-value { font-size: 16px; font-weight: 600; color: #1e293b; margin-top: 4px; }
        .verdict-badge { display: inline-block; padding: 8px 20px; border-radius: 20px; font-weight: 700; color: ''' + verdict_color + '''; background: ''' + verdict_bg + '''; border: 1px solid ''' + verdict_color + '''; }
        .section-title { font-size: 18px; font-weight: 700; color: #1e293b; margin-top: 30px; margin-bottom: 16px; padding-bottom: 8px; border-bottom: 1px solid #e2e8f0; }
        .text-content { background: #f8fafc; padding: 20px; border-radius: 8px; font-family: "Courier New", monospace; font-size: 14px; line-height: 1.6; color: #475569; white-space: pre-wrap; }
        .analysis-content { font-size: 15px; line-height: 1.8; color: #334155; }
        .report-footer { border-top: 1px solid #e2e8f0; padding-top: 20px; margin-top: 40px; text-align: center; color: #94a3b8; font-size: 13px; }
        .score-display { font-size: 36px; font-weight: 800; color: ''' + verdict_color + '''; }
    </style>
</head>
<body>
    <div class="report-container">
        <div class="report-header">
            <h1 class="report-title">多模态谣言检测研判报告</h1>
            <p class="report-subtitle">Multi-Modal Rumor Detection Analysis Report</p>
        </div>
        
        <div class="info-grid">
            <div class="info-item">
                <div class="info-label">检测时间</div>
                <div class="info-value">''' + current_time + '''</div>
            </div>
            <div class="info-item">
                <div class="info-label">图像文件</div>
                <div class="info-value">''' + img_name + '''</div>
            </div>
            <div class="info-item">
                <div class="info-label">一致性得分</div>
                <div class="info-value score-display">''' + score_str + '''</div>
            </div>
            <div class="info-item">
                <div class="info-label">研判结论</div>
                <div class="info-value">''' + verdict + '''</div>
            </div>
        </div>
        
        <div style="text-align: center; margin-bottom: 30px;">
            <span class="verdict-badge">''' + verdict + '''</span>
        </div>
        
        <div>
            <h2 class="section-title">待检测文本</h2>
            <div class="text-content">''' + escaped_text + '''</div>
        </div>
        
        <div>
            <h2 class="section-title">智能研判分析</h2>
            <div class="analysis-content">''' + escaped_explanation + '''</div>
        </div>
        
        <div class="report-footer">
            报告生成：图文一致性多模态谣言检测系统 | 版本：v2.5 专业版
        </div>
    </div>
</body>
</html>'''
    return html

def get_report_json():
    """生成JSON格式的研判报告"""
    score = st.session_state.score
    text = st.session_state.text
    explanation = st.session_state.explanation
    img_path = st.session_state.img_path
    
    # 判断结论
    if score >= 70:
        verdict = "高度可信"
        verdict_level = "A"
        risk_level = "低"
    elif score >= 45:
        verdict = "内容存疑"
        verdict_level = "B"
        risk_level = "中"
    else:
        verdict = "疑似谣言"
        verdict_level = "C"
        risk_level = "高"
    
    report = {
        "report_version": "2.5",
        "generated_at": datetime.now().isoformat(),
        "data_source": {
            "image_file": os.path.basename(img_path) if img_path else None,
            "text_content": text
        },
        "analysis_result": {
            "consistency_score": round(float(score), 2),
            "verdict": verdict,
            "verdict_level": verdict_level,
            "risk_level": risk_level
        },
        "analysis_report": explanation,
        "system_info": {
            "name": "图文一致性多模态谣言检测系统",
            "version": "v2.5 专业版"
        }
    }
    
    return json.dumps(report, ensure_ascii=False, indent=2)

def get_report_pdf():
    """生成真正的PDF格式研判报告"""
    # 使用reportlab生成PDF
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.utils import simpleSplit
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from io import BytesIO
    import os
    
    # 注册中文字体
    try:
        # 尝试注册系统中文字体
        font_path = "C:/Windows/Fonts/simhei.ttf"  # 黑体
        if os.path.exists(font_path):
            pdfmetrics.registerFont(TTFont('SimHei', font_path))
            chinese_font = 'SimHei'
        else:
            # 尝试其他中文字体
            font_path = "C:/Windows/Fonts/simsun.ttc"
            if os.path.exists(font_path):
                pdfmetrics.registerFont(TTFont('SimSun', font_path))
                chinese_font = 'SimSun'
            else:
                chinese_font = 'Helvetica'
    except:
        chinese_font = 'Helvetica'
    
    score = st.session_state.score
    text = st.session_state.text
    explanation = st.session_state.explanation
    img_path = st.session_state.img_path
    
    # 判断结论
    if score >= 70:
        verdict = "高度可信"
        verdict_level = "A"
    elif score >= 45:
        verdict = "内容存疑"
        verdict_level = "B"
    else:
        verdict = "疑似谣言"
        verdict_level = "C"
    
    current_time = datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')
    img_name = os.path.basename(img_path) if img_path else '未上传'
    score_str = f"{score:.2f}分"
    
    # 创建PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=50, rightMargin=50, topMargin=50, bottomMargin=50)
    styles = getSampleStyleSheet()
    
    # 创建自定义样式（使用中文字体）
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontName=chinese_font,
        fontSize=20,
        alignment=1,
        textColor=colors.darkblue,
        spaceAfter=20
    )
    
    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Heading2'],
        fontName=chinese_font,
        fontSize=12,
        alignment=1,
        textColor=colors.gray,
        spaceAfter=20
    )
    
    section_style = ParagraphStyle(
        'Section',
        parent=styles['Heading2'],
        fontName=chinese_font,
        fontSize=14,
        textColor=colors.darkblue,
        spaceBefore=15,
        spaceAfter=10
    )
    
    normal_style = ParagraphStyle(
        'Normal',
        parent=styles['Normal'],
        fontName=chinese_font,
        fontSize=12,
        leading=18,
        textColor=colors.black
    )
    
    elements = []
    
    # 标题
    elements.append(Paragraph('多模态谣言检测研判报告', title_style))
    elements.append(Paragraph('Multi-Modal Rumor Detection Analysis Report', subtitle_style))
    
    # 基本信息表格
    info_data = [
        ['检测时间', current_time],
        ['图像文件', img_name],
        ['一致性得分', score_str],
        ['研判结论', f'{verdict} (等级: {verdict_level})']
    ]
    
    info_table = Table(info_data, colWidths=[120, 300])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightblue),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.darkblue),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ('FONTNAME', (0, 0), (-1, -1), chinese_font)  # 设置表格字体
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 20))
    
    # 待检测文本
    elements.append(Paragraph('待检测文本', section_style))
    text_content = Paragraph(text.replace('\n', '<br/>'), normal_style)
    elements.append(text_content)
    elements.append(Spacer(1, 15))
    
    # 智能研判分析
    elements.append(Paragraph('智能研判分析', section_style))
    explanation_content = Paragraph(explanation.replace('\n', '<br/>'), normal_style)
    elements.append(explanation_content)
    elements.append(Spacer(1, 20))
    
    # 页脚
    footer_style = ParagraphStyle(
        'Footer',
        fontName=chinese_font,
        fontSize=10,
        alignment=1,
        textColor=colors.gray
    )
    elements.append(Paragraph('报告生成：图文一致性多模态谣言检测系统 | 版本：v2.5 专业版', footer_style))
    
    # 生成PDF
    doc.build(elements)
    buffer.seek(0)
    
    return buffer.getvalue()

def clean_report_content(content):
    """清理报告内容中的多余符号和重复内容"""
    # 移除重复的标题符号（###+ 变为 ###）
    content = re.sub(r'###+', '###', content)
    
    # 移除列表项前多余的 `- **` 格式（如 `- **结论**:` 变为 `**结论**:`）
    content = re.sub(r'^-\s*\*\*([^*]+)\*\*:', r'**\1**:', content, flags=re.MULTILINE)
    
    # 移除列表项前的 `- `（保留纯文本）
    content = re.sub(r'^-\s+', '', content, flags=re.MULTILINE)
    
    # 移除重复的星号（***+ 变为 **）
    content = re.sub(r'\*\*\*+', '**', content)
    
    # 移除单独的 `-` 符号行
    content = re.sub(r'^\s*-\s*$', '', content, flags=re.MULTILINE)
    
    # 移除多余的空行（3个以上换行变为2个）
    content = re.sub(r'\n{3,}', '\n\n', content)
    
    # 移除开头和结尾的空行
    content = content.strip()
    
    return content

def generate_fast_report(score, text):
    """快速生成研判报告（本地规则，无需调用LLM）"""
    if score >= 80:
        verdict = "高度可信"
        confidence = "极高"
        color_tag = "🟢"
    elif score >= 70:
        verdict = "可信新闻"
        confidence = "高"
        color_tag = "🟢"
    elif score >= 55:
        verdict = "基本可信"
        confidence = "中等"
        color_tag = "🟡"
    elif score >= 45:
        verdict = "内容存疑"
        confidence = "较低"
        color_tag = "🟡"
    elif score >= 30:
        verdict = "疑似谣言"
        confidence = "低"
        color_tag = "🔴"
    else:
        verdict = "高度疑似谣言"
        confidence = "极低"
        color_tag = "🔴"
    
    text_length = len(text.strip())
    
    # 提前处理需要插入的值，避免f-string中的反斜杠问题
    match_degree = "高度匹配" if score >= 70 else "部分匹配" if score >= 45 else "匹配度较低"
    risk_level = "**风险等级：低**" if score >= 70 else "**风险等级：中**" if score >= 45 else "**风险等级：高**"
    
    if score >= 70:
        warning_text = ""
        suggestion = "- 信息可信，可正常传播引用。"
    elif score >= 45:
        warning_text = "⚠️ 注意：文本与图像特征存在不一致之处，建议进一步核实信息来源。"
        suggestion = "- 建议交叉验证多个信息源后再做判断。\n- 关注信息发布者的可信度和历史记录。"
    else:
        warning_text = "🚨 警告：图文信息存在明显矛盾，该内容疑似经过篡改或误导性编辑。"
        suggestion = "- 强烈建议不要转发或传播此内容。\n- 如需引用，请等待官方权威来源核实。\n- 可向平台举报可疑内容。"
    
    # 使用字符串拼接而非f-string
    report = "### 综合判定\n"
    report += color_tag + " **" + verdict + "**（置信度 " + confidence + "）\n\n"
    report += "依据图文一致性算法分析，本案例的图文匹配度为 **" + str(score)[:4] + "/100分**。\n\n"
    report += "---\n\n### 图文一致性深入剖析\n"
    report += "- **文本长度**: " + str(text_length) + " 字\n"
    report += "- **核心特征**: 系统已完成图像-文本交叉特征比对分析\n"
    report += "- **匹配程度**: " + match_degree + "\n\n"
    report += "---\n\n### 风险评估与疑点提示\n"
    report += risk_level + "\n\n" + warning_text + "\n\n"
    report += "---\n\n### 应对建议\n"
    report += suggestion + "\n\n---\n\n"
    report += "*本报告由系统自动生成（快速模式）*"
    
    return report

# 1. 页面基本配置
st.set_page_config(
    page_title="图文一致性多模态谣言检测系统",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 数据载入与处理
def load_cases():
    metadata_path = os.path.join(PROJECT_ROOT, "dataset", "metadata.csv")
    if os.path.exists(metadata_path):
        data = pd.read_csv(metadata_path)
        if "label" in data.columns:
            data["label"] = data["label"].astype(int)
        if "priority" not in data.columns:
            data["priority"] = range(len(data))
        if "featured" not in data.columns:
            data["featured"] = 0
        if "source" not in data.columns:
            data["source"] = "自建案例"
        if "title" not in data.columns:
            data["title"] = ""
        data = data.sort_values(["priority", "image_path"]).reset_index(drop=True)
        for idx, row in data.iterrows():
            img_path = row["image_path"]
            if not os.path.isabs(img_path):
                full_path = os.path.join(PROJECT_ROOT, img_path)
                if os.path.exists(full_path):
                    data.at[idx, "image_path"] = full_path
        return data
    return None

df = load_cases()
rumor_df = df[df['label'] == 1] if df is not None else pd.DataFrame()
real_df = df[df['label'] == 0] if df is not None else pd.DataFrame()

CASE_NAMES = {
    "real1.jpg": "捷龙三号卫星发射 (真实)",
    "real2.jpg": "苏翊鸣举国旗 (真实)",
    "real3.jpg": "榆中遭遇特大暴雨 (真实)",
    "rumor1.jpg": "重庆铜梁地震灾情 (谣言)",
    "rumor2.jpg": "环江车辆坠河事故 (谣言)",
    "rumor3.jpg": "三峡景区游船倒扣 (谣言)",
}


def row_title(row):
    title = str(row.get("title", "")).strip()
    if title and title.lower() != "nan":
        return title
    img_name = os.path.basename(row["image_path"])
    return CASE_NAMES.get(img_name, f"示例: {img_name}")


rumor_options = []
rumor_paths = []
if not rumor_df.empty:
    for idx, row in rumor_df.iterrows():
        display_name = row_title(row)
        rumor_options.append(display_name)
        rumor_paths.append(row['image_path'])

real_options = []
real_paths = []
if not real_df.empty:
    for idx, row in real_df.iterrows():
        display_name = row_title(row)
        real_options.append(display_name)
        real_paths.append(row['image_path'])

# 回调函数定义
def on_category_change():
    new_cat = st.session_state.category
    if new_cat == "谣言案例" and len(rumor_paths) > 0:
        first_path = rumor_paths[0]
        row = rumor_df[rumor_df['image_path'] == first_path].iloc[0]
        st.session_state.img_path = row['image_path']
        st.session_state.text = row['text']
        st.session_state.score = None
        st.session_state.highlight_img = None
        st.session_state.explanation = ""
    elif new_cat == "真实案例" and len(real_paths) > 0:
        first_path = real_paths[0]
        row = real_df[real_df['image_path'] == first_path].iloc[0]
        st.session_state.img_path = row['image_path']
        st.session_state.text = row['text']
        st.session_state.score = None
        st.session_state.highlight_img = None
        st.session_state.explanation = ""
    elif new_cat == "自定义上传":
        temp_upload_path = os.path.join(PROJECT_ROOT, "temp_upload.jpg")
        if os.path.exists(temp_upload_path):
            st.session_state.img_path = temp_upload_path
        else:
            st.session_state.img_path = None
            st.session_state.text = ""
        st.session_state.score = None
        st.session_state.highlight_img = None
        st.session_state.explanation = ""

# 2. 注入极其精美、意境非凡的 SaaS 风格深色/亮色玻璃拟态 (Glassmorphism) CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Outfit:wght@400;500;600;700;800&display=swap');

    :root {
        --ink-950: oklch(20% 0.012 235);
        --ink-900: oklch(24% 0.012 235);
        --ink-800: oklch(31% 0.012 235);
        --ink-700: oklch(39% 0.012 235);
        --muted-500: oklch(58% 0.014 235);
        --line-200: oklch(88% 0.012 235);
        --line-300: oklch(82% 0.014 235);
        --paper-50: oklch(97% 0.006 235);
        --paper-100: oklch(94% 0.008 235);
        --panel: oklch(98% 0.006 235);
        --lab: oklch(17% 0.012 235);
        --accent: oklch(69% 0.15 232);
        --accent-strong: oklch(61% 0.16 232);
        --accent-soft: oklch(92% 0.035 232);
        --danger: oklch(58% 0.21 27);
        --warning: oklch(70% 0.16 72);
        --success: oklch(62% 0.13 154);
        --shadow: 0 12px 30px oklch(20% 0.012 235 / 0.08);
    }

    .stApp {
        background: var(--paper-100) !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", system-ui, sans-serif !important;
        color: var(--ink-900) !important;
    }

    [data-testid="stHeader"] {
        background: var(--lab) !important;
        border-bottom: 1px solid oklch(35% 0.018 235 / 0.85) !important;
        height: 42px !important;
    }

    footer {
        display: none !important;
    }

    .block-container {
        max-width: 1180px !important;
        padding-top: 1.25rem !important;
        padding-bottom: 2rem !important;
    }

    ::-webkit-scrollbar {
        width: 6px;
        height: 6px;
    }

    ::-webkit-scrollbar-track {
        background: var(--paper-100);
    }

    ::-webkit-scrollbar-thumb {
        background: var(--line-300);
        border-radius: 3px;
    }

    ::-webkit-scrollbar-thumb:hover {
        background: var(--muted-500);
    }

    section[data-testid="stSidebar"] {
        background: oklch(92% 0.01 235) !important;
        border-right: 1px solid var(--line-300) !important;
        box-shadow: 6px 0 24px oklch(20% 0.012 235 / 0.05) !important;
    }

    [data-testid="stSidebarUserContent"] {
        padding: 1.15rem 1rem 1.5rem !important;
    }

    .sidebar-logo {
        background: var(--lab);
        color: oklch(91% 0.03 232);
        border: 1px solid oklch(35% 0.018 235);
        border-radius: 8px;
        padding: 13px 12px;
        margin: 0 0 18px;
        font-size: 18px;
        font-weight: 800;
        letter-spacing: 0;
        text-align: left;
    }

    .sidebar-logo small {
        display: block;
        margin-top: 4px;
        color: oklch(74% 0.04 232);
        font-size: 11px;
        font-weight: 600;
        letter-spacing: 0.06em;
    }

    .sidebar-section-title {
        color: var(--ink-700);
        font-size: 11px;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin: 18px 0 8px;
        padding-left: 2px;
    }

    .st-key-navuploadactive button,
    .st-key-navrumoractive button,
    .st-key-navrealactive button {
        background: var(--accent) !important;
        color: oklch(16% 0.012 235) !important;
        border: 1px solid var(--accent-strong) !important;
        border-radius: 8px !important;
        font-weight: 800 !important;
        padding: 10px 12px !important;
        margin-bottom: 8px !important;
        box-shadow: 0 8px 18px oklch(61% 0.16 232 / 0.22) !important;
        text-align: left !important;
        width: 100% !important;
    }

    .st-key-navuploadinactive button,
    .st-key-navrumorinactive button,
    .st-key-navrealinactive button {
        background: oklch(97% 0.006 235) !important;
        color: var(--ink-800) !important;
        border: 1px solid var(--line-300) !important;
        border-radius: 8px !important;
        padding: 10px 12px !important;
        margin-bottom: 8px !important;
        text-align: left !important;
        width: 100% !important;
        transition: background 160ms ease-out, border-color 160ms ease-out, color 160ms ease-out !important;
    }

    .st-key-navuploadinactive button:hover,
    .st-key-navrumorinactive button:hover,
    .st-key-navrealinactive button:hover {
        background: var(--accent-soft) !important;
        border-color: var(--accent-strong) !important;
        color: var(--ink-950) !important;
    }

    [class*="caseactive"] button {
        background: var(--lab) !important;
        color: oklch(91% 0.03 232) !important;
        border: 1px solid oklch(42% 0.04 232) !important;
        border-radius: 8px !important;
        font-weight: 700 !important;
        padding: 10px 11px !important;
        margin-bottom: 8px !important;
        text-align: left !important;
        width: 100% !important;
    }

    [class*="caseinactive"] button {
        background: oklch(96% 0.006 235) !important;
        color: var(--ink-800) !important;
        border: 1px solid var(--line-300) !important;
        border-radius: 8px !important;
        padding: 10px 11px !important;
        margin-bottom: 8px !important;
        text-align: left !important;
        width: 100% !important;
        transition: background 160ms ease-out, border-color 160ms ease-out !important;
    }

    [class*="caseinactive"] button:hover {
        background: var(--accent-soft) !important;
        border-color: var(--accent-strong) !important;
    }

    .header-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        background: var(--lab) !important;
        border: 1px solid oklch(34% 0.018 235) !important;
        border-radius: 8px;
        padding: 12px 16px;
        margin: 0 0 14px;
        box-shadow: var(--shadow);
        gap: 18px;
    }

    .header-left {
        display: flex;
        align-items: center;
        gap: 14px;
        min-width: 0;
    }

    .header-badge {
        background: var(--accent);
        color: var(--lab);
        font-size: 11px;
        font-weight: 900;
        padding: 4px 10px;
        border-radius: 999px;
        text-transform: uppercase;
        letter-spacing: 0.02em;
        white-space: nowrap;
    }

    .header-title {
        color: oklch(93% 0.012 235) !important;
        font-size: 20px !important;
        font-weight: 800 !important;
        margin: 0 !important;
        letter-spacing: 0 !important;
    }

    .header-right {
        display: flex;
        gap: 8px;
        flex-wrap: wrap;
        justify-content: flex-end;
    }

    .status-indicator {
        display: flex;
        align-items: center;
        gap: 8px;
        background: oklch(24% 0.012 235);
        border: 1px solid oklch(38% 0.018 235);
        padding: 6px 9px;
        border-radius: 6px;
    }

    .status-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        display: inline-block;
    }

    .status-dot.green {
        background: var(--success);
        box-shadow: 0 0 9px oklch(62% 0.13 154 / 0.75);
    }

    .status-dot.blue {
        background: var(--accent);
        box-shadow: 0 0 9px oklch(69% 0.15 232 / 0.7);
    }

    .status-text {
        font-size: 12px;
        color: oklch(83% 0.018 235);
        font-weight: 650;
        white-space: nowrap;
    }

    .page-kicker {
        color: var(--muted-500);
        font-size: 13px;
        font-weight: 700;
        margin: 0 0 16px;
    }

    .st-key-cardinput,
    .st-key-cardcompare,
    .st-key-cardreport,
    .st-key-cardguideline,
    .st-key-cardarchitecture,
    .st-key-cardwelcome,
    .st-key-cardverdictgreen,
    .st-key-cardverdictyellow,
    .st-key-cardverdictred {
        background: var(--panel) !important;
        border: 1px solid var(--line-200) !important;
        border-radius: 8px !important;
        padding: 18px !important;
        box-shadow: var(--shadow) !important;
        margin-bottom: 16px;
    }

    .st-key-cardcompare {
        background: oklch(20% 0.012 235) !important;
        border-color: oklch(34% 0.018 235) !important;
    }

    .st-key-cardverdictgreen {
        border-color: oklch(77% 0.09 154) !important;
    }

    .st-key-cardverdictyellow {
        border-color: oklch(80% 0.12 72) !important;
    }

    .st-key-cardverdictred {
        border-color: oklch(72% 0.16 27) !important;
    }

    .st-key-cardreport {
        max-height: 520px;
        overflow-y: auto;
    }

    .card-title {
        color: var(--ink-900) !important;
        font-size: 14px !important;
        font-weight: 800 !important;
        margin: 0 0 14px !important;
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 10px;
        line-height: 1.2 !important;
    }

    .st-key-cardcompare .card-title {
        color: oklch(91% 0.018 235) !important;
    }

    .card-title::before {
        content: "";
        width: 9px;
        height: 9px;
        border: 2px solid var(--accent);
        border-radius: 2px;
        display: inline-block;
        flex: 0 0 auto;
    }

    .card-title.verdict-green::before { border-color: var(--success); }
    .card-title.verdict-yellow::before { border-color: var(--warning); }
    .card-title.verdict-red::before { border-color: var(--danger); }

    .evidence-label {
        color: oklch(78% 0.018 235);
        font-size: 12px;
        font-weight: 800;
        letter-spacing: 0.02em;
        margin: 0 0 10px;
        text-align: left;
        text-transform: uppercase;
    }

    .instruction-list,
    .architecture-list {
        color: var(--ink-700);
        font-size: 13.5px;
        line-height: 1.7;
        padding: 2px 0 0;
    }

    .instruction-list b,
    .architecture-list b {
        color: var(--ink-950);
    }

    .instruction-list .step {
        display: block;
        padding: 7px 0;
        border-bottom: 1px solid var(--line-200);
    }

    .instruction-list .step:last-child {
        border-bottom: 0;
    }

    .architecture-list .row {
        display: block;
        padding: 8px 0 8px 16px;
        border-top: 1px solid var(--line-200);
        position: relative;
    }

    .architecture-list .row::before {
        content: "";
        position: absolute;
        left: 0;
        top: 17px;
        width: 6px;
        height: 6px;
        background: var(--accent);
        border-radius: 2px;
    }

    .empty-system {
        min-height: 320px;
        background: var(--lab);
        border: 1px solid oklch(34% 0.018 235);
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        text-align: center;
        color: oklch(86% 0.02 235);
        padding: 30px;
    }

    .empty-system h3 {
        color: oklch(94% 0.012 235);
        font-size: 24px;
        margin: 0 0 8px;
    }

    .empty-system p {
        color: oklch(76% 0.018 235);
        margin: 0;
        line-height: 1.2 !important;
    }

    div[data-testid="stTextArea"] textarea {
        background: oklch(96% 0.006 235) !important;
        border: 1px solid var(--line-300) !important;
        border-radius: 8px !important;
        color: var(--ink-900) !important;
        font-size: 14px !important;
        line-height: 1.6 !important;
        padding: 14px !important;
        transition: border-color 160ms ease-out, box-shadow 160ms ease-out, background 160ms ease-out !important;
    }

    div[data-testid="stTextArea"] textarea:focus {
        border-color: var(--accent-strong) !important;
        box-shadow: 0 0 0 3px oklch(69% 0.15 232 / 0.18) !important;
        background: var(--panel) !important;
    }

    div[data-testid="stTextInput"] input {
        background: oklch(96% 0.006 235) !important;
        border: 1px solid var(--line-300) !important;
        border-radius: 8px !important;
        color: var(--ink-900) !important;
        padding: 10px 14px !important;
    }

    div[data-testid="stTextInput"] input:focus {
        border-color: var(--accent-strong) !important;
        box-shadow: 0 0 0 3px oklch(69% 0.15 232 / 0.16) !important;
    }

    .st-key-startdetectionmain button {
        background: var(--accent) !important;
        color: var(--lab) !important;
        font-size: 15px !important;
        font-weight: 900 !important;
        padding: 12px 24px !important;
        width: 100% !important;
        border: 1px solid var(--accent-strong) !important;
        border-radius: 8px !important;
        letter-spacing: 0 !important;
        box-shadow: 0 9px 20px oklch(61% 0.16 232 / 0.22) !important;
        transition: background 160ms ease-out, transform 160ms ease-out, box-shadow 160ms ease-out !important;
        margin-top: 10px;
    }

    .st-key-startdetectionmain button:hover {
        background: oklch(75% 0.14 232) !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 12px 24px oklch(61% 0.16 232 / 0.3) !important;
    }

    .st-key-resetdetectionmain button {
        background: oklch(95% 0.006 235) !important;
        color: var(--ink-800) !important;
        border: 1px solid var(--line-300) !important;
        font-size: 14px !important;
        font-weight: 750 !important;
        padding: 12px 0 !important;
        border-radius: 8px !important;
        box-shadow: none !important;
        transition: background 160ms ease-out, border-color 160ms ease-out !important;
        margin-top: 10px;
        width: 100% !important;
    }

    .st-key-resetdetectionmain button:hover {
        background: var(--paper-100) !important;
        border-color: var(--muted-500) !important;
    }

    div[data-testid="element-container"]:has(> div[data-testid="stImage"]) img {
        border-radius: 6px !important;
        border: 1px solid oklch(36% 0.018 235) !important;
        box-shadow: 0 10px 24px oklch(12% 0.012 235 / 0.25) !important;
        background: oklch(15% 0.012 235);
    }

    .image-scanner-wrapper {
        position: relative;
        overflow: hidden;
        border-radius: 6px;
        display: inline-block;
        width: 100%;
        border: 1px solid oklch(36% 0.018 235);
        background: oklch(14% 0.012 235);
        box-shadow: 0 10px 24px oklch(12% 0.012 235 / 0.25);
    }

    .image-scanner-line {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 3px;
        background: linear-gradient(90deg, transparent, var(--accent), transparent);
        box-shadow: 0 0 12px 2px oklch(69% 0.15 232 / 0.75);
        animation: scanVertical 2.8s linear infinite;
        pointer-events: none;
        z-index: 5;
    }

    [data-testid="stFileUploader"] {
        background: oklch(96% 0.006 235) !important;
        border: 1px dashed var(--line-300) !important;
        border-radius: 8px !important;
        padding: 12px !important;
        transition: background 160ms ease-out, border-color 160ms ease-out;
    }

    [data-testid="stFileUploader"]:hover {
        border-color: var(--accent-strong) !important;
        background: var(--accent-soft) !important;
    }

    [data-testid="stFileUploader"] label {
        color: var(--ink-700) !important;
        font-size: 13px !important;
        font-weight: 700 !important;
    }

    [data-testid="stFileUploader"] section button span {
        display: none !important;
    }

    [data-testid="stFileUploader"] section button::after {
        content: "选择图片" !important;
        font-size: 14px !important;
        font-family: inherit !important;
    }

    [data-testid="stFileUploader"] section [data-testid="stMarkdownContainer"] p {
        font-size: 0 !important;
    }

    [data-testid="stFileUploader"] section [data-testid="stMarkdownContainer"] p::after {
        content: "拖拽图片到此处上传" !important;
        font-size: 14px !important;
        color: var(--muted-500) !important;
    }

    [data-testid="stFileUploader"] section div:nth-child(3),
    [data-testid="stFileUploader"] section div:nth-child(4),
    [data-testid="stFileUploader"] section small {
        display: none !important;
    }

    [data-testid="stFileUploader"] section::after {
        content: "支持 JPG, PNG 格式，单个文件不超过 200MB" !important;
        font-size: 11px !important;
        color: var(--muted-500) !important;
        display: block !important;
        margin-top: 8px !important;
        text-align: center !important;
    }

    .report-content {
        font-size: 14px !important;
        line-height: 1.75 !important;
        color: var(--ink-800) !important;
    }

    .report-content h3 {
        font-size: 16px !important;
        font-weight: 800 !important;
        color: var(--ink-950) !important;
        margin-top: 22px !important;
        margin-bottom: 12px !important;
        border-bottom: 1px solid var(--line-200) !important;
        padding-bottom: 6px !important;
    }

    .report-content ul, .report-content ol {
        padding-left: 20px !important;
        margin-bottom: 16px !important;
    }

    .report-content li {
        margin-bottom: 8px !important;
    }

    .report-content strong {
        color: var(--ink-950) !important;
        font-weight: 800;
    }

    @keyframes scanVertical {
        0% { transform: translateY(-100%); }
        100% { transform: translateY(100%); }
    }

    @keyframes rotateSweep {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }

    @keyframes pulseRadar {
        0% { opacity: 0.2; transform: scale(0.96); }
        50% { opacity: 0.55; transform: scale(1); }
        100% { opacity: 0.2; transform: scale(0.96); }
    }

    .radar-screen {
        position: relative;
        width: 100%;
        aspect-ratio: 1.15/1;
        background: oklch(14% 0.012 235) !important;
        border: 1px solid oklch(36% 0.018 235) !important;
        border-radius: 6px;
        overflow: hidden;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
        padding: 20px;
    }

    .radar-grid {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-size: 20px 20px;
        background-image: 
            linear-gradient(to right, oklch(69% 0.15 232 / 0.08) 1px, transparent 1px),
            linear-gradient(to bottom, oklch(69% 0.15 232 / 0.08) 1px, transparent 1px);
        pointer-events: none;
    }

    .radar-sweep {
        position: absolute;
        width: 200%;
        height: 200%;
        background: conic-gradient(from 0deg, oklch(69% 0.15 232 / 0.18) 0deg, transparent 85deg);
        opacity: 0.75;
        border-radius: 50%;
        animation: rotateSweep 4s linear infinite;
        transform-origin: center;
        pointer-events: none;
        z-index: 2;
    }

    .radar-laser {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 3px;
        background: linear-gradient(90deg, transparent, var(--accent), transparent);
        box-shadow: 0 0 12px 2px oklch(69% 0.15 232 / 0.7);
        animation: scanVertical 4s linear infinite;
        pointer-events: none;
        z-index: 3;
    }

    .radar-signal {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        border: 2px solid oklch(69% 0.15 232 / 0.45);
        animation: pulseRadar 2s infinite ease-in-out;
        margin-bottom: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 4;
    }

    .radar-dot {
        width: 10px;
        height: 10px;
        background: var(--accent);
        border-radius: 50%;
        box-shadow: 0 0 12px oklch(69% 0.15 232 / 0.9);
    }

    .radar-text {
        font-size: 13px;
        color: oklch(78% 0.018 235);
        line-height: 1.6;
        z-index: 4;
    }

    .radar-text-title {
        font-size: 14.5px;
        font-weight: 800;
        color: oklch(92% 0.018 235);
        margin-bottom: 6px;
    }

    @keyframes drawGauge {
        from { stroke-dashoffset: 251.3; }
        to { stroke-dashoffset: var(--gauge-offset, 0); }
    }

    @keyframes fadeInText {
        from { opacity: 0; transform: scale(0.9); }
        to { opacity: 1; transform: scale(1); }
    }

    .gauge-card-content {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        width: 100%;
        margin-top: 10px;
    }

    .gauge-container {
        position: relative;
        width: 150px;
        height: 150px;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-bottom: 16px;
    }

    .gauge-score-val {
        font-size: 38px;
        font-weight: 800;
        color: var(--ink-950) !important;
        line-height: 1;
        animation: fadeInText 0.8s ease forwards;
    }

    .gauge-score-lbl {
        font-size: 10px;
        color: var(--muted-500) !important;
        margin-top: 4px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        animation: fadeInText 0.8s ease forwards;
    }

    .gauge-verdict-badge-box {
        margin-bottom: 12px;
        display: flex;
        justify-content: center;
        animation: fadeInText 1s ease forwards;
    }

    .gauge-verdict-desc-box {
        font-size: 13.5px;
        color: var(--ink-700) !important;
        line-height: 1.6;
        text-align: center;
        max-width: 280px;
        animation: fadeInText 1.2s ease forwards;
    }

    /* 恢复到改版前的紫蓝玻璃拟态视觉 */
    .stApp {
        background: radial-gradient(circle at 50% 0%,
            color-mix(in srgb, var(--background-color, #ffffff) 94%, var(--primary-color, #4f46e5)) 0%,
            var(--background-color, #ffffff) 65%,
            color-mix(in srgb, var(--background-color, #ffffff) 97%, #000000) 100%) !important;
        font-family: 'Inter', -apple-system, "PingFang SC", "Microsoft YaHei", sans-serif !important;
        color: var(--text-color, #31333f) !important;
    }

    [data-testid="stHeader"] {
        background: transparent !important;
        border-bottom: 0 !important;
        height: auto !important;
    }

    section[data-testid="stSidebar"] {
        background-color: rgba(248, 250, 252, 0.95) !important;
        backdrop-filter: blur(12px) !important;
        -webkit-backdrop-filter: blur(12px) !important;
        border-right: 1px solid rgba(226, 232, 240, 0.8) !important;
        box-shadow: 4px 0 15px rgba(0, 0, 0, 0.02) !important;
    }

    [data-testid="stSidebarUserContent"] {
        padding-top: 2rem !important;
    }

    .sidebar-logo {
        font-family: 'Outfit', sans-serif;
        font-size: 24px;
        font-weight: 800;
        text-align: center;
        color: #4f46e5;
        background: linear-gradient(135deg, #4f46e5 0%, #8b5cf6 100%);
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
        background-clip: text !important;
        padding: 15px 0 25px 0;
        border: 0;
        border-bottom: 1px solid rgba(226, 232, 240, 0.8);
        margin-bottom: 25px;
        letter-spacing: 0;
    }

    .sidebar-logo small {
        display: none;
    }

    .sidebar-section-title {
        font-family: 'Outfit', sans-serif;
        font-size: 13px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1px;
        color: #4f46e5;
        margin-top: 20px;
        margin-bottom: 12px;
        border-left: 3px solid #4f46e5;
        padding-left: 10px;
    }

    .st-key-navuploadactive button,
    .st-key-navrumoractive button,
    .st-key-navrealactive button {
        background: linear-gradient(135deg, #4f46e5 0%, #6366f1 100%) !important;
        color: #ffffff !important;
        font-weight: 600 !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 12px 16px !important;
        margin-bottom: 10px !important;
        box-shadow: 0 4px 15px rgba(99, 102, 241, 0.35) !important;
    }

    .st-key-navuploadinactive button,
    .st-key-navrumorinactive button,
    .st-key-navrealinactive button {
        background: rgba(255, 255, 255, 0.6) !important;
        color: color-mix(in srgb, var(--text-color, #31333f) 70%, transparent) !important;
        border: 1px solid rgba(226, 232, 240, 0.8) !important;
        border-radius: 12px !important;
        padding: 12px 16px !important;
        margin-bottom: 10px !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }

    .st-key-navuploadinactive button:hover,
    .st-key-navrumorinactive button:hover,
    .st-key-navrealinactive button:hover {
        background: rgba(99, 102, 241, 0.08) !important;
        border-color: #4f46e5 !important;
        color: #4f46e5 !important;
        transform: translateX(6px) !important;
        box-shadow: 0 4px 10px rgba(99, 102, 241, 0.05) !important;
    }

    [class*="caseactive"] button {
        background: rgba(99, 102, 241, 0.08) !important;
        color: #4f46e5 !important;
        border: 1px solid #4f46e5 !important;
        border-left: 4px solid #4f46e5 !important;
        font-weight: 600 !important;
        border-radius: 8px !important;
        padding: 10px 14px !important;
    }

    [class*="caseinactive"] button {
        background: rgba(255, 255, 255, 0.4) !important;
        color: color-mix(in srgb, var(--text-color, #31333f) 85%, transparent) !important;
        border: 1px solid rgba(226, 232, 240, 0.8) !important;
        border-radius: 8px !important;
        padding: 10px 14px !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }

    [class*="caseinactive"] button:hover {
        background: rgba(99, 102, 241, 0.04) !important;
        border-color: color-mix(in srgb, #4f46e5 45%, transparent) !important;
        color: #4f46e5 !important;
        transform: translateX(4px) !important;
    }

    .header-container {
        background: rgba(255, 255, 255, 0.7) !important;
        backdrop-filter: blur(12px) !important;
        -webkit-backdrop-filter: blur(12px) !important;
        border: 1px solid rgba(226, 232, 240, 0.8) !important;
        border-radius: 16px;
        padding: 16px 28px;
        margin-bottom: 25px;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.02) !important;
    }

    .header-badge {
        background: linear-gradient(135deg, #4f46e5 0%, #3b82f6 100%);
        color: white;
        font-weight: 700;
        border-radius: 20px;
    }

    .header-title {
        font-family: 'Outfit', sans-serif !important;
        font-size: 22px !important;
        font-weight: 800 !important;
        color: var(--text-color, #31333f) !important;
    }

    .status-indicator {
        background: rgba(255, 255, 255, 0.5);
        border: 1px solid rgba(226, 232, 240, 0.6);
        padding: 6px 12px;
        border-radius: 8px;
    }

    .status-dot.green {
        background-color: #10b981;
        box-shadow: 0 0 8px #10b981;
    }

    .status-dot.blue {
        background-color: #3b82f6;
        box-shadow: 0 0 8px #3b82f6;
    }

    .status-text {
        font-size: 12px;
        color: color-mix(in srgb, var(--text-color, #31333f) 70%, transparent);
        font-weight: 500;
    }

    .page-kicker {
        display: none;
    }

    .st-key-cardinput,
    .st-key-cardcompare,
    .st-key-cardreport,
    .st-key-cardguideline,
    .st-key-cardarchitecture,
    .st-key-cardwelcome,
    .st-key-cardverdictgreen,
    .st-key-cardverdictyellow,
    .st-key-cardverdictred {
        background: rgba(255, 255, 255, 0.65) !important;
        backdrop-filter: blur(20px) saturate(180%) !important;
        -webkit-backdrop-filter: blur(20px) saturate(180%) !important;
        border: 1px solid rgba(226, 232, 240, 0.8) !important;
        border-radius: 20px !important;
        padding: 24px !important;
        box-shadow: 0 15px 35px rgba(0, 0, 0, 0.03) !important;
        margin-bottom: 20px;
    }

    .st-key-cardinput:hover,
    .st-key-cardcompare:hover,
    .st-key-cardreport:hover,
    .st-key-cardguideline:hover,
    .st-key-cardarchitecture:hover,
    .st-key-cardwelcome:hover {
        border-color: rgba(99, 102, 241, 0.25) !important;
        box-shadow: 0 20px 45px rgba(99, 102, 241, 0.08) !important;
        transform: translateY(-4px) !important;
    }

    .card-title {
        font-family: 'Outfit', sans-serif !important;
        font-size: 16px !important;
        font-weight: 700 !important;
        color: var(--text-color, #31333f) !important;
        margin-bottom: 20px !important;
        justify-content: flex-start;
        border-left: 4px solid #4f46e5;
        padding-left: 10px;
    }

    .card-title::before {
        content: none !important;
    }

    .st-key-cardcompare .card-title {
        color: var(--text-color, #31333f) !important;
    }

    div[data-testid="stTextArea"] textarea,
    div[data-testid="stTextInput"] input {
        background: rgba(255, 255, 255, 0.8) !important;
        border: 1px solid rgba(226, 232, 240, 0.8) !important;
        border-radius: 12px !important;
        color: var(--text-color, #31333f) !important;
    }

    div[data-testid="stTextArea"] textarea:focus,
    div[data-testid="stTextInput"] input:focus {
        border-color: #4f46e5 !important;
        box-shadow: 0 0 15px rgba(99, 102, 241, 0.2) !important;
        background: #ffffff !important;
    }

    .st-key-startdetectionmain button {
        background: linear-gradient(135deg, #4f46e5 0%, #6366f1 50%, #8b5cf6 100%) !important;
        color: #ffffff !important;
        font-size: 16px !important;
        font-weight: 600 !important;
        border: none !important;
        border-radius: 12px !important;
        letter-spacing: 1px !important;
        box-shadow: 0 4px 20px rgba(99, 102, 241, 0.3) !important;
    }

    .st-key-resetdetectionmain button {
        background: rgba(255, 255, 255, 0.5) !important;
        color: var(--text-color, #31333f) !important;
        border: 1px solid rgba(226, 232, 240, 0.8) !important;
        border-radius: 12px !important;
    }

    div[data-testid="element-container"]:has(> div[data-testid="stImage"]) img,
    .image-scanner-wrapper {
        border-radius: 12px !important;
        border: 1px solid rgba(226, 232, 240, 0.8) !important;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08) !important;
        background: rgba(0, 0, 0, 0.02);
    }

    .image-scanner-line,
    .radar-laser {
        background: linear-gradient(90deg, transparent, #4f46e5, transparent);
        box-shadow: 0 0 10px 2px #4f46e5;
    }

    [data-testid="stFileUploader"] {
        background: rgba(255, 255, 255, 0.5) !important;
        border: 1px dashed rgba(226, 232, 240, 0.9) !important;
        border-radius: 12px !important;
    }

    .report-content {
        color: color-mix(in srgb, var(--text-color, #31333f) 85%, transparent) !important;
    }

    .radar-screen {
        background: radial-gradient(circle, rgba(99, 102, 241, 0.06) 0%, rgba(255, 255, 255, 0.8) 100%) !important;
        border: 1px dashed rgba(99, 102, 241, 0.25) !important;
        border-radius: 12px;
    }

    .radar-grid {
        background-image:
            linear-gradient(to right, rgba(99, 102, 241, 0.03) 1px, transparent 1px),
            linear-gradient(to bottom, rgba(99, 102, 241, 0.03) 1px, transparent 1px);
    }

    .radar-sweep {
        background: conic-gradient(from 0deg, rgba(99, 102, 241, 0.15) 0deg, transparent 90deg);
    }

    .radar-signal {
        border: 2px solid rgba(99, 102, 241, 0.3);
    }

    .radar-dot {
        background-color: #4f46e5;
        box-shadow: 0 0 10px #4f46e5;
    }

    .radar-text {
        color: color-mix(in srgb, var(--text-color, #31333f) 70%, transparent);
    }

    .radar-text-title,
    .gauge-score-val {
        color: var(--text-color, #31333f) !important;
    }

    .gauge-score-lbl {
        color: color-mix(in srgb, var(--text-color, #31333f) 50%, transparent) !important;
    }

    .gauge-verdict-desc-box {
        color: color-mix(in srgb, var(--text-color, #31333f) 80%, transparent) !important;
    }

    @media (max-width: 860px) {
        .block-container {
            padding-left: 0.85rem !important;
            padding-right: 0.85rem !important;
        }

        .header-container {
            align-items: flex-start;
            flex-direction: column;
        }

        .header-title {
            font-size: 17px !important;
        }

        .header-right {
            justify-content: flex-start;
        }
    }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
    [data-testid="stDecoration"],
    [data-testid="stStatusWidget"],
    section[data-testid="stSidebar"] {
        display: none !important;
        visibility: hidden !important;
        width: 0 !important;
        height: 0 !important;
        min-width: 0 !important;
        min-height: 0 !important;
        opacity: 0 !important;
        pointer-events: none !important;
    }

    [data-testid="stHeader"] {
        height: 58px !important;
        background: rgba(255, 255, 255, 0.92) !important;
        border-bottom: 1px solid rgba(226, 232, 240, 0.92) !important;
        box-shadow: 0 10px 28px rgba(15, 23, 42, 0.045) !important;
        backdrop-filter: blur(16px) !important;
        -webkit-backdrop-filter: blur(16px) !important;
    }

    .header-container {
        display: none !important;
    }

    .block-container {
        max-width: min(1600px, calc(100vw - 80px)) !important;
        padding-top: 0.9rem !important;
        padding-left: 2.5rem !important;
        padding-right: 2.5rem !important;
    }

    .app-topbar {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        z-index: 999990;
        pointer-events: none;
        margin: 0;
        height: 58px;
        padding: 0 184px 0 max(20px, calc((100vw - 1600px) / 2 + 40px));
        display: grid;
        grid-template-columns: auto auto 1fr;
        align-items: center;
        gap: 28px;
        overflow: visible;
    }

    .app-brand {
        pointer-events: auto;
        display: inline-flex;
        align-items: center;
        gap: 10px;
        min-width: 0;
        color: #4f46e5;
        font-size: 15px;
        font-weight: 800;
        text-decoration: none !important;
        white-space: nowrap;
    }

    .app-brand-mark {
        width: 9px;
        height: 9px;
        border-radius: 999px;
        background: #4f46e5;
        box-shadow: 0 0 0 5px rgba(79, 70, 229, 0.12);
        flex: 0 0 auto;
    }

    .app-navlinks {
        pointer-events: auto;
        display: inline-flex;
        align-items: center;
        justify-content: flex-start;
        gap: 22px;
        height: 58px;
    }

    .app-navlink {
        min-width: auto;
        height: 58px;
        padding: 0;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        color: color-mix(in srgb, var(--text-color, #31333f) 72%, transparent);
        font-size: 14px;
        font-weight: 700;
        line-height: 1;
        text-decoration: none !important;
        border-bottom: 2px solid transparent;
        transition: color 160ms ease, border-color 160ms ease;
    }

    .app-navlink:hover {
        color: #4f46e5;
    }

    .app-navlink.is-active {
        color: #4f46e5;
        border-bottom-color: #4f46e5;
    }

    .app-actions {
        display: inline-flex;
        align-items: center;
        justify-content: flex-end;
        justify-self: end;
        gap: 8px;
        min-width: max-content;
        position: relative;
        z-index: 80;
    }

    @media (max-width: 820px) {
        .app-topbar {
            height: 112px;
            grid-template-columns: 1fr;
            justify-items: stretch;
            gap: 0;
            padding: 58px 16px 10px;
        }

        [data-testid="stHeader"] {
            height: 112px !important;
        }

        .block-container {
            padding-top: 0.9rem !important;
        }

        .app-navlinks,
        .app-actions {
            width: 100%;
        }

        .app-navlinks {
            height: 34px;
            gap: 18px;
        }

        .app-navlink {
            flex: 1 1 0;
            min-width: 0;
            height: 34px;
        }
    }

    .filter-row {
        display: flex;
        gap: 8px;
        margin: 16px 0 18px;
    }

    .case-library-head {
        margin: 0 0 18px;
    }

    .case-library-head h2 {
        font-family: 'Outfit', sans-serif;
        font-size: 36px;
        line-height: 1.1;
        font-weight: 800;
        color: color-mix(in srgb, var(--text-color, #31333f) 16%, transparent);
        margin: 0 0 8px;
    }

    .case-library-head p {
        margin: 0;
        color: color-mix(in srgb, var(--text-color, #31333f) 48%, transparent);
        font-size: 14px;
    }

    [class*="st-key-casecard"] {
        background: rgba(255, 255, 255, 0.58) !important;
        border: 1px solid rgba(226, 232, 240, 0.72) !important;
        border-radius: 14px !important;
        padding: 10px !important;
        margin-bottom: 16px;
        min-height: 366px;
        box-shadow: 0 16px 36px rgba(15, 23, 42, 0.035) !important;
    }

    .case-card-fixed-content {
        height: 302px;
    }

    .case-thumb {
        position: relative;
        overflow: hidden;
        border-radius: 10px;
        border: 1px solid rgba(15, 23, 42, 0.1);
        background: rgba(15, 23, 42, 0.94);
    }

    .case-thumb img {
        width: 100%;
        height: 168px;
        object-fit: cover;
        display: block;
        filter: saturate(0.82) contrast(1.05) brightness(0.82);
    }

    .case-badge,
    .case-id {
        position: absolute;
        top: 10px;
        z-index: 2;
        border-radius: 5px;
        padding: 4px 8px;
        font-size: 11px;
        font-weight: 800;
        line-height: 1;
        color: #ffffff;
        backdrop-filter: blur(10px);
    }

    .case-badge {
        left: 10px;
        background: rgba(239, 68, 68, 0.86);
    }

    .case-badge.real {
        background: rgba(245, 158, 11, 0.72);
    }

    .case-id {
        right: 10px;
        background: rgba(15, 23, 42, 0.72);
    }

    .case-card-title {
        color: color-mix(in srgb, var(--text-color, #31333f) 30%, transparent);
        font-size: 16px;
        font-weight: 800;
        line-height: 1.35;
        margin: 12px 4px 7px;
        height: 43px;
        overflow: hidden;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
    }

    .case-card-source {
        margin: 0 4px 8px;
        color: var(--primary-color, #4f46e5);
        font-size: 12px;
        font-weight: 850;
    }

    .case-card-desc {
        color: color-mix(in srgb, var(--text-color, #31333f) 42%, transparent);
        font-size: 12.8px;
        line-height: 1.55;
        height: 76px;
        margin: 0 4px 12px;
        overflow: hidden;
        display: -webkit-box;
        -webkit-line-clamp: 4;
        -webkit-box-orient: vertical;
    }

    .case-page-summary {
        margin: 12px 0 14px;
        color: var(--app-muted);
        font-size: 13px;
        font-weight: 750;
    }

    .case-page-indicator {
        height: 38px;
        display: grid;
        place-items: center;
        color: color-mix(in srgb, var(--text-color, #31333f) 72%, transparent);
        font-size: 13px;
        font-weight: 850;
    }

    [class*="st-key-casepagination"] button {
        border-radius: 8px !important;
        min-height: 38px !important;
        font-weight: 850 !important;
    }

    [class*="st-key-casechoosewrap"] {
        margin: 0 4px;
    }

    [class*="st-key-casechoose"] button {
        background: #111827 !important;
        color: #7dd3fc !important;
        border: 1px solid rgba(125, 211, 252, 0.28) !important;
        border-radius: 6px !important;
        min-height: 34px !important;
        font-size: 13px !important;
        font-weight: 800 !important;
        padding: 7px 14px !important;
        box-shadow: none !important;
    }

    [class*="st-key-casechoose"] button:hover {
        background: #0f172a !important;
        border-color: rgba(125, 211, 252, 0.58) !important;
    }

    .st-key-topuploadpanel {
        background: rgba(255, 255, 255, 0.65) !important;
        border: 1px solid rgba(226, 232, 240, 0.78) !important;
        border-radius: 16px !important;
        padding: 18px !important;
        margin-bottom: 18px;
        box-shadow: 0 15px 35px rgba(0, 0, 0, 0.03) !important;
    }

    .console-preview {
        background: rgba(255, 255, 255, 0.65);
        border: 1px solid rgba(226, 232, 240, 0.78);
        border-radius: 16px;
        padding: 18px;
        min-height: 360px;
        box-shadow: 0 15px 35px rgba(0, 0, 0, 0.03);
    }

    .preview-placeholder {
        height: 230px;
        border: 1px dashed rgba(99, 102, 241, 0.28);
        border-radius: 14px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: color-mix(in srgb, var(--text-color, #31333f) 42%, transparent);
        background: rgba(99, 102, 241, 0.04);
        text-align: center;
        font-weight: 700;
    }

    .console-hero {
        display: grid;
        grid-template-columns: minmax(0, 1fr) auto;
        gap: 18px;
        align-items: end;
        margin: 0 0 18px;
    }

    .console-hero h2 {
        margin: 0 0 8px;
        color: color-mix(in srgb, var(--text-color, #31333f) 88%, transparent);
        font-size: 34px;
        line-height: 1.12;
        font-weight: 850;
    }

    .console-hero p {
        max-width: 68ch;
        margin: 0;
        color: var(--app-muted);
        font-size: 14px;
        line-height: 1.7;
    }

    .console-status-strip {
        display: grid;
        grid-template-columns: repeat(3, minmax(120px, 1fr));
        gap: 8px;
        min-width: 430px;
    }

    .console-status-item {
        border: 1px solid var(--app-border);
        border-radius: 8px;
        padding: 10px 12px;
        background: var(--app-surface);
        box-shadow: var(--app-shadow);
    }

    .console-status-item b {
        display: block;
        color: color-mix(in srgb, var(--text-color, #31333f) 86%, transparent);
        font-size: 13px;
        line-height: 1.2;
    }

    .console-status-item span {
        display: block;
        margin-top: 5px;
        color: var(--app-muted);
        font-size: 12px;
    }

    .console-panel-head {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 12px;
        margin: 0 0 16px;
    }

    .console-panel-head h3 {
        margin: 0;
        color: color-mix(in srgb, var(--text-color, #31333f) 86%, transparent);
        font-size: 16px;
        font-weight: 850;
    }

    .console-panel-head span {
        color: var(--app-muted);
        font-size: 12px;
        font-weight: 800;
    }

    .console-input-hint,
    .console-text-status {
        margin-top: 14px;
        border: 1px solid var(--app-border);
        border-radius: 8px;
        padding: 12px 14px;
        background: var(--app-surface-soft);
        color: var(--app-muted);
        font-size: 13px;
        line-height: 1.6;
    }

    .console-text-status {
        display: flex;
        justify-content: space-between;
        gap: 12px;
        font-weight: 750;
    }

    .console-preview {
        min-height: 520px;
        padding: 0;
        overflow: hidden;
    }

    .console-preview-shell {
        min-height: 520px;
        display: grid;
        grid-template-rows: auto 1fr auto;
        background:
            linear-gradient(90deg, rgba(99, 102, 241, 0.08) 1px, transparent 1px),
            linear-gradient(0deg, rgba(99, 102, 241, 0.08) 1px, transparent 1px),
            var(--app-surface);
        background-size: 44px 44px;
    }

    .console-preview-top {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 14px;
        padding: 16px 18px;
        border-bottom: 1px solid var(--app-border);
        background: color-mix(in srgb, var(--app-surface) 90%, var(--primary-color, #4f46e5) 6%);
    }

    .console-preview-top b {
        color: color-mix(in srgb, var(--text-color, #31333f) 86%, transparent);
        font-size: 15px;
    }

    .console-preview-top span {
        color: var(--app-muted);
        font-size: 12px;
        font-weight: 800;
    }

    .console-preview-stage {
        display: grid;
        place-items: center;
        padding: 26px;
    }

    .console-empty-card {
        width: min(520px, 100%);
        border: 1px solid var(--app-border);
        border-radius: 8px;
        padding: 22px;
        background: color-mix(in srgb, var(--app-surface) 92%, transparent);
        box-shadow: var(--app-shadow);
    }

    .console-empty-card h3 {
        margin: 0;
        color: color-mix(in srgb, var(--text-color, #31333f) 88%, transparent);
        font-size: 18px;
        font-weight: 850;
    }

    .console-empty-card p {
        margin: 10px 0 0;
        color: var(--app-muted);
        font-size: 13px;
        line-height: 1.65;
    }

    .console-scan-rail {
        height: 8px;
        margin: 18px 0 0;
        overflow: hidden;
        border-radius: 99px;
        background: color-mix(in srgb, var(--text-color, #31333f) 8%, transparent);
    }

    .console-scan-rail span {
        display: block;
        width: 38%;
        height: 100%;
        border-radius: inherit;
        background: linear-gradient(90deg, var(--primary-color, #4f46e5), #22c55e);
    }

    .console-preview-checks {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 1px;
        border-top: 1px solid var(--app-border);
        background: var(--app-border);
    }

    .console-preview-checks div {
        min-height: 72px;
        padding: 14px 16px;
        background: var(--app-surface);
    }

    .console-preview-checks b {
        display: block;
        color: color-mix(in srgb, var(--text-color, #31333f) 82%, transparent);
        font-size: 13px;
    }

    .console-preview-checks span {
        display: block;
        margin-top: 6px;
        color: var(--app-muted);
        font-size: 12px;
        line-height: 1.45;
    }

    @media (max-width: 1100px) {
        .console-hero {
            grid-template-columns: 1fr;
        }

        .console-status-strip {
            min-width: 0;
        }
    }

    @media (max-width: 720px) {
        .console-status-strip,
        .console-preview-checks {
            grid-template-columns: 1fr;
        }
    }

    .home-panel,
    .settings-panel {
        background: var(--app-surface);
        border: 1px solid var(--app-border);
        border-radius: 8px;
        padding: 24px;
        box-shadow: var(--app-shadow);
    }

    .home-panel h2,
    .settings-panel h2 {
        margin: 0 0 10px;
        color: color-mix(in srgb, var(--text-color, #31333f) 86%, transparent);
        font-size: 30px;
        line-height: 1.18;
        font-weight: 850;
    }

    .home-panel p,
    .settings-panel p {
        color: color-mix(in srgb, var(--text-color, #31333f) 60%, transparent);
        line-height: 1.72;
        margin: 0;
    }

    .home-dashboard {
        display: grid;
        gap: 16px;
    }

    .home-hero {
        display: grid;
        grid-template-columns: minmax(0, 1.1fr) 360px;
        gap: 28px;
        align-items: stretch;
        padding: 30px;
    }

    .home-hero-main {
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        min-height: 232px;
    }

    .home-eyebrow {
        margin: 0 0 12px;
        color: var(--primary-color, #4f46e5);
        font-size: 12px;
        font-weight: 850;
        letter-spacing: 0.06em;
        text-transform: uppercase;
    }

    .home-title {
        max-width: 740px;
        margin: 0;
        color: color-mix(in srgb, var(--text-color, #31333f) 90%, transparent);
        font-size: 32px;
        line-height: 1.22;
        font-weight: 850;
    }

    .home-copy {
        max-width: 66ch;
        margin: 16px 0 0;
        color: color-mix(in srgb, var(--text-color, #31333f) 62%, transparent);
        font-size: 15px;
        line-height: 1.75;
    }

    .home-actions {
        margin-top: 24px;
        display: flex;
        gap: 10px;
        flex-wrap: wrap;
    }

    .home-action {
        min-height: 40px;
        padding: 0 16px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        border-radius: 8px;
        border: 1px solid var(--app-border);
        background: var(--app-surface-soft);
        color: color-mix(in srgb, var(--text-color, #31333f) 74%, transparent) !important;
        font-size: 14px;
        font-weight: 800;
        text-decoration: none !important;
        transition: background 160ms ease, border-color 160ms ease, color 160ms ease, transform 160ms ease;
    }

    .home-action:hover {
        background: var(--app-surface-hover);
        border-color: var(--app-border-strong);
        transform: translateY(-1px);
    }

    .home-action.primary {
        background: var(--primary-color, #4f46e5);
        border-color: var(--primary-color, #4f46e5);
        color: #f8f7ff !important;
    }

    .home-inspector {
        display: grid;
        gap: 12px;
        align-content: start;
        border: 1px solid var(--app-border);
        border-radius: 8px;
        padding: 16px;
        background: color-mix(in srgb, var(--app-surface-soft) 88%, var(--primary-color, #4f46e5) 5%);
    }

    .home-inspector-title {
        color: color-mix(in srgb, var(--text-color, #31333f) 82%, transparent);
        font-size: 13px;
        font-weight: 850;
    }

    .home-inspector-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 12px;
        padding-top: 10px;
        border-top: 1px solid var(--app-border);
        color: var(--app-muted);
        font-size: 13px;
        line-height: 1.45;
    }

    .home-status-pill {
        display: inline-flex;
        align-items: center;
        gap: 7px;
        color: color-mix(in srgb, var(--text-color, #31333f) 78%, transparent);
        font-weight: 800;
        white-space: nowrap;
    }

    .home-status-pill::before {
        content: "";
        width: 8px;
        height: 8px;
        border-radius: 99px;
        background: #22c55e;
        box-shadow: 0 0 0 3px rgba(34, 197, 94, 0.14);
    }

    .home-stats,
    .home-flow,
    .home-capabilities {
        display: grid;
        gap: 12px;
    }

    .home-stats {
        grid-template-columns: repeat(4, minmax(0, 1fr));
    }

    .home-flow {
        grid-template-columns: repeat(3, minmax(0, 1fr));
    }

    .home-capabilities {
        grid-template-columns: repeat(4, minmax(0, 1fr));
    }

    .home-card {
        position: relative;
        overflow: hidden;
        background: var(--app-surface);
        border: 1px solid var(--app-border);
        border-radius: 8px;
        padding: 16px;
        box-shadow: var(--app-shadow);
    }

    a.home-card {
        color: inherit !important;
        text-decoration: none !important;
    }

    .home-card.interactive {
        min-height: 118px;
        transition: border-color 160ms ease, background 160ms ease, transform 160ms ease;
    }

    .home-card.interactive:hover {
        border-color: color-mix(in srgb, var(--primary-color, #4f46e5) 42%, var(--app-border));
        background: var(--app-surface-hover);
        transform: translateY(-1px);
    }

    .home-stat-value {
        color: color-mix(in srgb, var(--text-color, #31333f) 90%, transparent);
        font-size: 26px;
        line-height: 1;
        font-weight: 850;
    }

    .home-stat-label,
    .home-card p {
        margin: 8px 0 0;
        color: var(--app-muted);
        font-size: 13px;
        line-height: 1.58;
    }

    .home-stat-note {
        margin-top: 10px;
        height: 4px;
        overflow: hidden;
        border-radius: 99px;
        background: color-mix(in srgb, var(--text-color, #31333f) 10%, transparent);
    }

    .home-stat-note span {
        display: block;
        height: 100%;
        border-radius: inherit;
        background: color-mix(in srgb, var(--primary-color, #4f46e5) 72%, #22c55e 28%);
    }

    .home-card h3 {
        margin: 0;
        color: color-mix(in srgb, var(--text-color, #31333f) 86%, transparent);
        font-size: 15px;
        font-weight: 850;
    }

    .home-step {
        width: 28px;
        height: 28px;
        margin-bottom: 14px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        border-radius: 8px;
        background: color-mix(in srgb, var(--primary-color, #4f46e5) 14%, transparent);
        color: var(--primary-color, #4f46e5);
        font-size: 13px;
        font-weight: 850;
    }

    .home-card-meta {
        margin-top: 14px;
        display: inline-flex;
        align-items: center;
        min-height: 24px;
        padding: 0 8px;
        border-radius: 6px;
        background: color-mix(in srgb, var(--text-color, #31333f) 7%, transparent);
        color: color-mix(in srgb, var(--text-color, #31333f) 62%, transparent);
        font-size: 12px;
        font-weight: 800;
    }

    .home-section-title {
        margin: 12px 0 -2px;
        color: color-mix(in srgb, var(--text-color, #31333f) 78%, transparent);
        font-size: 14px;
        font-weight: 850;
    }

    @media (max-width: 1100px) {
        .home-hero,
        .home-stats,
        .home-flow,
        .home-capabilities {
            grid-template-columns: repeat(2, minmax(0, 1fr));
        }

        .home-actions {
            justify-content: flex-start;
        }
    }

    @media (max-width: 720px) {
        .home-hero,
        .home-stats,
        .home-flow,
        .home-capabilities {
            grid-template-columns: 1fr;
        }

        .home-title {
            font-size: 28px;
        }
    }

    :root {
        --app-surface: color-mix(in srgb, var(--background-color, #ffffff) 88%, var(--text-color, #31333f) 8%);
        --app-surface-soft: color-mix(in srgb, var(--background-color, #ffffff) 94%, var(--text-color, #31333f) 4%);
        --app-surface-hover: color-mix(in srgb, var(--background-color, #ffffff) 84%, var(--primary-color, #4f46e5) 10%);
        --app-border: color-mix(in srgb, var(--text-color, #31333f) 18%, transparent);
        --app-border-strong: color-mix(in srgb, var(--text-color, #31333f) 28%, transparent);
        --app-muted: color-mix(in srgb, var(--text-color, #31333f) 58%, transparent);
        --app-faint: color-mix(in srgb, var(--text-color, #31333f) 38%, transparent);
        --app-shadow: 0 16px 36px color-mix(in srgb, var(--text-color, #31333f) 8%, transparent);
    }

    html,
    body,
    .stApp,
    [data-testid="stAppViewContainer"],
    main[data-testid="stMain"] {
        background: var(--background-color, #ffffff) !important;
        color: var(--text-color, #31333f) !important;
        transition: background-color 220ms ease, background 220ms ease, color 180ms ease !important;
    }

    [data-testid="stHeader"] {
        background: color-mix(in srgb, var(--background-color, #ffffff) 92%, transparent) !important;
        border-bottom: 1px solid var(--app-border) !important;
        box-shadow: 0 10px 28px color-mix(in srgb, var(--text-color, #31333f) 6%, transparent) !important;
    }

    .app-brand,
    .app-navlink:hover,
    .app-navlink.is-active {
        color: var(--primary-color, #4f46e5) !important;
    }

    .app-brand-mark {
        background: var(--primary-color, #4f46e5) !important;
        box-shadow: 0 0 0 5px color-mix(in srgb, var(--primary-color, #4f46e5) 18%, transparent) !important;
    }

    .app-navlink {
        color: var(--app-muted) !important;
    }

    .app-navlink.is-active {
        border-bottom-color: var(--primary-color, #4f46e5) !important;
    }

    .home-panel,
    .settings-panel,
    .home-card,
    .st-key-topuploadpanel,
    .console-preview,
    [class*="st-key-casecard"],
    .st-key-cardinput,
    .st-key-cardcompare,
    .st-key-cardreport,
    .st-key-cardguideline,
    .st-key-cardarchitecture,
    .st-key-cardwelcome,
    .st-key-cardverdictgreen,
    .st-key-cardverdictyellow,
    .st-key-cardverdictred {
        background: var(--app-surface) !important;
        border-color: var(--app-border) !important;
        box-shadow: var(--app-shadow) !important;
    }

    .home-panel h2,
    .settings-panel h2,
    .case-library-head h2,
    .card-title,
    .case-card-title,
    .radar-text-title,
    .gauge-score-val {
        color: color-mix(in srgb, var(--text-color, #31333f) 88%, transparent) !important;
    }

    .home-panel p,
    .settings-panel p,
    .case-library-head p,
    .case-card-desc,
    .report-content,
    .radar-text,
    .gauge-score-lbl,
    .gauge-verdict-desc-box {
        color: var(--app-muted) !important;
    }

    .preview-placeholder,
    [data-testid="stFileUploader"],
    div[data-testid="stTextArea"] textarea,
    div[data-testid="stTextInput"] input,
    div[data-testid="stSelectbox"] div[data-baseweb="select"] > div,
    div[data-testid="stSlider"] [data-baseweb="slider"] {
        background: var(--app-surface-soft) !important;
        border-color: var(--app-border) !important;
        color: var(--text-color, #31333f) !important;
    }

    div[data-testid="stTextArea"] textarea:focus,
    div[data-testid="stTextInput"] input:focus {
        background: var(--app-surface-hover) !important;
        border-color: var(--primary-color, #4f46e5) !important;
        box-shadow: 0 0 0 3px color-mix(in srgb, var(--primary-color, #4f46e5) 22%, transparent) !important;
    }

    .st-key-resetdetectionmain button,
    .st-key-navuploadinactive button,
    .st-key-navrumorinactive button,
    .st-key-navrealinactive button,
    [class*="caseinactive"] button {
        background: var(--app-surface-soft) !important;
        border-color: var(--app-border) !important;
        color: var(--app-muted) !important;
    }

    .st-key-resetdetectionmain button:hover,
    .st-key-navuploadinactive button:hover,
    .st-key-navrumorinactive button:hover,
    .st-key-navrealinactive button:hover,
    [class*="caseinactive"] button:hover {
        background: var(--app-surface-hover) !important;
        border-color: var(--primary-color, #4f46e5) !important;
        color: var(--primary-color, #4f46e5) !important;
    }

    div[data-testid="element-container"]:has(> div[data-testid="stImage"]) img,
    .image-scanner-wrapper,
    .case-thumb {
        border-color: var(--app-border) !important;
        background: var(--app-surface-soft) !important;
    }

    .radar-screen {
        background: radial-gradient(circle,
            color-mix(in srgb, var(--primary-color, #4f46e5) 10%, transparent) 0%,
            var(--app-surface-soft) 100%) !important;
        border-color: color-mix(in srgb, var(--primary-color, #4f46e5) 32%, transparent) !important;
    }

    html[data-app-theme="dark"],
    body[data-app-theme="dark"] {
        --app-bg: #0b1020;
        --app-bg-soft: #101827;
        --app-surface: rgba(17, 24, 39, 0.94);
        --app-surface-soft: rgba(15, 23, 42, 0.92);
        --app-surface-hover: rgba(30, 41, 59, 0.96);
        --app-border: rgba(148, 163, 184, 0.24);
        --app-border-strong: rgba(148, 163, 184, 0.38);
        --app-text: #e5e7eb;
        --app-muted: #a3adc2;
        --app-faint: #7b869c;
        --app-primary: #8b8cff;
        --app-shadow: 0 18px 42px rgba(0, 0, 0, 0.34);
    }

    html[data-app-theme="dark"],
    html[data-app-theme="dark"] body,
    html[data-app-theme="dark"] .stApp,
    html[data-app-theme="dark"] [data-testid="stAppViewContainer"],
    html[data-app-theme="dark"] main[data-testid="stMain"] {
        background: var(--app-bg) !important;
        color: var(--app-text) !important;
    }

    html[data-app-theme="dark"] [data-testid="stHeader"] {
        background: rgba(11, 16, 32, 0.94) !important;
        border-bottom-color: rgba(148, 163, 184, 0.18) !important;
        box-shadow: 0 10px 28px rgba(0, 0, 0, 0.26) !important;
    }

    html[data-app-theme="dark"] .app-brand,
    html[data-app-theme="dark"] .app-navlink:hover,
    html[data-app-theme="dark"] .app-navlink.is-active {
        color: var(--app-primary) !important;
    }

    html[data-app-theme="dark"] .app-brand-mark {
        background: var(--app-primary) !important;
        box-shadow: 0 0 0 5px rgba(139, 140, 255, 0.2) !important;
    }

    html[data-app-theme="dark"] .app-navlink {
        color: var(--app-muted) !important;
    }

    html[data-app-theme="dark"] .app-navlink.is-active {
        border-bottom-color: var(--app-primary) !important;
    }

    html[data-app-theme="dark"] .home-panel,
    html[data-app-theme="dark"] .settings-panel,
    html[data-app-theme="dark"] .home-card,
    html[data-app-theme="dark"] .st-key-topuploadpanel,
    html[data-app-theme="dark"] .console-preview,
    html[data-app-theme="dark"] [class*="st-key-casecard"],
    html[data-app-theme="dark"] .st-key-cardinput,
    html[data-app-theme="dark"] .st-key-cardcompare,
    html[data-app-theme="dark"] .st-key-cardreport,
    html[data-app-theme="dark"] .st-key-cardguideline,
    html[data-app-theme="dark"] .st-key-cardarchitecture,
    html[data-app-theme="dark"] .st-key-cardwelcome,
    html[data-app-theme="dark"] .st-key-cardverdictgreen,
    html[data-app-theme="dark"] .st-key-cardverdictyellow,
    html[data-app-theme="dark"] .st-key-cardverdictred {
        background: var(--app-surface) !important;
        border: 1px solid var(--app-border) !important;
        box-shadow: var(--app-shadow) !important;
    }

    html[data-app-theme="dark"] .home-panel h2,
    html[data-app-theme="dark"] .settings-panel h2,
    html[data-app-theme="dark"] .home-title,
    html[data-app-theme="dark"] .home-card h3,
    html[data-app-theme="dark"] .home-stat-value,
    html[data-app-theme="dark"] .home-section-title,
    html[data-app-theme="dark"] .case-library-head h2,
    html[data-app-theme="dark"] .card-title,
    html[data-app-theme="dark"] .case-card-title,
    html[data-app-theme="dark"] .radar-text-title,
    html[data-app-theme="dark"] .gauge-score-val,
    html[data-app-theme="dark"] label,
    html[data-app-theme="dark"] p,
    html[data-app-theme="dark"] span,
    html[data-app-theme="dark"] div[data-testid="stMarkdownContainer"] {
        color: var(--app-text) !important;
    }

    html[data-app-theme="dark"] .home-panel p,
    html[data-app-theme="dark"] .settings-panel p,
    html[data-app-theme="dark"] .home-copy,
    html[data-app-theme="dark"] .home-stat-label,
    html[data-app-theme="dark"] .home-card p,
    html[data-app-theme="dark"] .case-library-head p,
    html[data-app-theme="dark"] .case-card-desc,
    html[data-app-theme="dark"] .report-content,
    html[data-app-theme="dark"] .radar-text,
    html[data-app-theme="dark"] .gauge-score-lbl,
    html[data-app-theme="dark"] .gauge-verdict-desc-box,
    html[data-app-theme="dark"] .preview-placeholder {
        color: var(--app-muted) !important;
    }

    html[data-app-theme="dark"] .preview-placeholder,
    html[data-app-theme="dark"] [data-testid="stFileUploader"],
    html[data-app-theme="dark"] [data-testid="stFileUploader"] section,
    html[data-app-theme="dark"] [data-testid="stFileUploader"] section > div,
    html[data-app-theme="dark"] div[data-testid="stTextArea"] textarea,
    html[data-app-theme="dark"] div[data-testid="stTextInput"] input,
    html[data-app-theme="dark"] div[data-testid="stSelectbox"] div[data-baseweb="select"] > div {
        background: var(--app-surface-soft) !important;
        border-color: var(--app-border) !important;
        color: var(--app-text) !important;
    }

    html[data-app-theme="dark"] div[data-testid="stTextArea"] textarea::placeholder,
    html[data-app-theme="dark"] div[data-testid="stTextInput"] input::placeholder {
        color: var(--app-faint) !important;
    }

    html[data-app-theme="dark"] div[data-testid="stTextArea"] textarea:focus,
    html[data-app-theme="dark"] div[data-testid="stTextInput"] input:focus {
        background: #111a2c !important;
        border-color: var(--app-primary) !important;
        box-shadow: 0 0 0 3px rgba(139, 140, 255, 0.2) !important;
    }

    html[data-app-theme="dark"] .st-key-resetdetectionmain button,
    html[data-app-theme="dark"] [class*="caseinactive"] button,
    html[data-app-theme="dark"] [data-testid="stFileUploader"] button {
        background: var(--app-surface-hover) !important;
        border-color: var(--app-border-strong) !important;
        color: var(--app-text) !important;
    }

    html[data-app-theme="dark"] .image-scanner-wrapper,
    html[data-app-theme="dark"] .case-thumb,
    html[data-app-theme="dark"] div[data-testid="element-container"]:has(> div[data-testid="stImage"]) img {
        background: var(--app-surface-soft) !important;
        border-color: var(--app-border) !important;
    }

    html[data-app-theme="dark"] .radar-screen {
        background: radial-gradient(circle,
            rgba(139, 140, 255, 0.12) 0%,
            var(--app-surface-soft) 100%) !important;
        border-color: rgba(139, 140, 255, 0.32) !important;
    }

    [data-testid="stHeader"],
    .app-brand,
    .app-brand-mark,
    .app-navlink,
    .home-panel,
    .settings-panel,
    .home-card,
    .st-key-topuploadpanel,
    .console-preview,
    [class*="st-key-casecard"],
    .st-key-cardinput,
    .st-key-cardcompare,
    .st-key-cardreport,
    .st-key-cardguideline,
    .st-key-cardarchitecture,
    .st-key-cardwelcome,
    .st-key-cardverdictgreen,
    .st-key-cardverdictyellow,
    .st-key-cardverdictred,
    .preview-placeholder,
    [data-testid="stFileUploader"],
    [data-testid="stFileUploader"] section,
    [data-testid="stFileUploader"] section > div,
    div[data-testid="stTextArea"] textarea,
    div[data-testid="stTextInput"] input,
    div[data-testid="stSelectbox"] div[data-baseweb="select"] > div,
    button,
    label,
    p,
    span,
    h1,
    h2,
    h3,
    div[data-testid="stMarkdownContainer"] {
        transition:
            background-color 220ms ease,
            background 220ms ease,
            border-color 220ms ease,
            color 180ms ease,
            box-shadow 220ms ease,
            opacity 180ms ease !important;
    }

    @media (max-width: 900px) {
        .top-nav-shell {
            align-items: stretch;
            flex-direction: column;
        }

        .block-container {
            max-width: 100% !important;
            padding-left: 1rem !important;
            padding-right: 1rem !important;
        }

        .case-thumb img {
            height: 220px;
        }
    }

    .block-container {
        padding-top: 0.9rem !important;
    }

    .case-library-head,
    .console-hero {
        margin-top: 0 !important;
    }
</style>
""", unsafe_allow_html=True)

# 3. 初始化 Session State
# 使用 setdefault 确保只在第一次访问时设置默认值，不会覆盖已有的设置
st.session_state.setdefault("img_path", None)
st.session_state.setdefault("text", "")
st.session_state.setdefault("score", None)
st.session_state.setdefault("highlight_img", None)
st.session_state.setdefault("explanation", "")
st.session_state.setdefault("is_detecting", False)
st.session_state.setdefault("category", "全部案例")
st.session_state.setdefault("app_page", "案例")
st.session_state.setdefault("case_page", 1)
# 默认使用 Qwen-Max 多模态文本分析，与 selectbox 的第一个选项对应
st.session_state.setdefault("modelsetting", "Qwen-Max 多模态文本分析")
st.session_state.setdefault("thresholdsetting", 45)
st.session_state.setdefault("exportsetting", "PDF")
st.session_state.setdefault("apikeyinput", "")  # 初始化 API Key 输入

# 调试：打印当前 modelsetting 的值
current_model = st.session_state.get("modelsetting", "NOT SET")
print(f"[INIT] 当前模型设置: {current_model}")
print(f"[INIT] session_state 中 modelsetting 存在: {'modelsetting' in st.session_state}")

# 自动加载第一个案例（如果数据集不为空）
if df is not None and not df.empty and st.session_state.img_path is None:
    first_row = df.iloc[0]
    st.session_state.img_path = first_row["image_path"]
    st.session_state.text = first_row["text"]

PAGE_TO_ROUTE = {
    "首页": "home",
    "控制台": "console",
    "案例": "cases",
    "系统设置": "settings",
}
ROUTE_TO_PAGE = {route: page for page, route in PAGE_TO_ROUTE.items()}


def reset_detection_state(clear_image=True):
    if clear_image:
        st.session_state.img_path = None
        st.session_state.text = ""
    st.session_state.score = None
    st.session_state.highlight_img = None
    st.session_state.explanation = ""
    st.session_state.is_detecting = False


def switch_category(category):
    st.session_state.category = category
    st.session_state.case_page = 1


def switch_page(page, update_query=True):
    st.session_state.app_page = page
    if page == "控制台":
        st.session_state.category = "自定义上传"
    elif page == "案例" and st.session_state.category not in ["全部案例", "谣言案例", "真实案例"]:
        st.session_state.category = "全部案例"
    if update_query and page in PAGE_TO_ROUTE:
        st.query_params["page"] = PAGE_TO_ROUTE[page]


def sync_page_from_query():
    route = st.query_params.get("page")
    if isinstance(route, list):
        route = route[0] if route else None
    page = ROUTE_TO_PAGE.get(route)
    if page and page != st.session_state.app_page:
        switch_page(page, update_query=False)


def select_case(row):
    # 调试：查看选择案例前的模型设置
    print(f"[select_case] 选择案例前 modelsetting: {st.session_state.get('modelsetting', 'NOT SET')}")
    
    st.session_state.img_path = row["image_path"]
    st.session_state.text = row["text"]
    switch_page("控制台")
    reset_detection_state(clear_image=False)
    
    # 调试：查看选择案例后的模型设置
    print(f"[select_case] 选择案例后 modelsetting: {st.session_state.get('modelsetting', 'NOT SET')}")


def render_top_navigation():
    # 创建一个包含导航按钮的容器
    col1, col2, col3, col4 = st.columns([1.5, 1, 1, 1])
    
    with col1:
        # Logo/品牌
        st.markdown(f"""
        <div class="app-brand" aria-label="返回案例页">
            <span class="app-brand-mark"></span>
            <span>多模态谣言检测</span>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        if st.button("首页", key="nav_home", use_container_width=True):
            switch_page("首页")
    
    with col3:
        if st.button("控制台", key="nav_console", use_container_width=True):
            switch_page("控制台")
    
    with col4:
        if st.button("案例", key="nav_cases", use_container_width=True):
            switch_page("案例")


def render_streamlit_toolbar_i18n():
    components.html(
        """
        <script>
        (() => {
            let manualThemeChoice = null;
            let manualThemeUntil = 0;

            const translations = new Map([
                ["Deploy", "部署"],
                ["Deploy this app using...", "选择部署方式"],
                ["Streamlit Community Cloud", "Streamlit 社区云"],
                ["For community, always free", "面向社区，永久免费"],
                ["For personal hobbies and learning", "适合个人兴趣和学习"],
                ["Deploy unlimited public apps", "部署不限数量的公开应用"],
                ["Explore and learn from Streamlit’s community and popular apps", "浏览并学习 Streamlit 社区与热门应用"],
                ["Deploy now", "立即部署"],
                ["Snowflake", "Snowflake"],
                ["For enterprise", "面向企业"],
                ["Enterprise-level security, support, and fully managed infrastructure", "企业级安全、支持和全托管基础设施"],
                ["Deploy unlimited private apps with role-based sharing", "部署不限数量的私有应用，并支持按角色共享"],
                ["Integrate with Snowflake’s full data stack", "与 Snowflake 完整数据栈集成"],
                ["Start trial", "开始试用"],
                ["Other platforms", "其他平台"],
                ["For custom deployment", "自定义部署"],
                ["Deploy on your own hardware or cloud service", "部署到自己的硬件或云服务"],
                ["Set up and maintain your own authentication, resources, and costs", "自行配置和维护认证、资源与成本"],
                ["Learn more", "了解更多"],
                ["System", "系统"],
                ["Light", "浅色"],
                ["Dark", "深色"],
                ["Rerun", "重新运行"],
                ["Auto rerun", "自动重新运行"],
                ["Clear cache", "清除缓存"],
                ["Print", "打印"],
                ["Record screen", "录制屏幕"],
                ["Settings", "设置"],
                ["About", "关于"],
            ]);

            const translateValue = (value) => {
                if (!value) return value;
                const trimmed = value.trim();
                if (translations.has(trimmed)) {
                    return value.replace(trimmed, translations.get(trimmed));
                }
                if (trimmed.startsWith("Made with Streamlit")) {
                    return value.replace(trimmed, trimmed.replace("Made with Streamlit", "基于 Streamlit"));
                }
                return value;
            };

            const translateNode = (node) => {
                const nextValue = translateValue(node.nodeValue);
                if (nextValue !== node.nodeValue) node.nodeValue = nextValue;
            };

            const resolveSystemTheme = () => (
                window.parent.matchMedia &&
                window.parent.matchMedia("(prefers-color-scheme: dark)").matches
            ) ? "dark" : "light";

            const setAppTheme = (mode) => {
                const doc = window.parent.document;
                const choice = mode || "light";
                const resolved = choice === "system" ? resolveSystemTheme() : choice;
                doc.documentElement.dataset.appTheme = resolved;
                doc.body.dataset.appTheme = resolved;
                doc.documentElement.dataset.appThemeChoice = choice;
            };

            const getStoredTheme = () => {
                try {
                    const storage = window.parent.localStorage;
                    for (let i = 0; i < storage.length; i += 1) {
                        const key = storage.key(i);
                        const value = String(storage.getItem(key) || "").toLowerCase();
                        if (!key || !key.toLowerCase().includes("theme")) continue;
                        if (value.includes("dark")) return "dark";
                        if (value.includes("light")) return "light";
                        if (value.includes("system")) return "system";
                    }
                } catch (error) {
                    return null;
                }
                return null;
            };

            const normalizeThemeLabel = (value) => {
                const text = value.replace(/\\s+/g, " ").trim();
                if (text === "Dark" || text === "深色") return "dark";
                if (text === "Light" || text === "浅色") return "light";
                if (text === "System" || text === "系统") return "system";
                return null;
            };

            const themeFromEventPath = (event) => {
                const path = event.composedPath ? event.composedPath() : [];
                const nodes = path.length ? path : (() => {
                    const result = [];
                    let node = event.target;
                    while (node) {
                        result.push(node);
                        node = node.parentElement;
                    }
                    return result;
                })();

                for (const node of nodes.slice(0, 8)) {
                    if (!node || !node.textContent) continue;
                    const mode = normalizeThemeLabel(node.textContent || "");
                    if (mode) return mode;
                }
                return null;
            };

            const applyThemeSoon = (mode) => {
                manualThemeChoice = mode;
                manualThemeUntil = Date.now() + 900;
                [0, 90, 260].forEach((delay) => {
                    window.parent.setTimeout(() => setAppTheme(mode), delay);
                });
            };

            const selectedThemeFromMenu = () => {
                const doc = window.parent.document;
                const candidates = [];
                doc.querySelectorAll("button, [role='button'], label, div, span").forEach((element) => {
                    const mode = normalizeThemeLabel(element.textContent || "");
                    if (!mode) return;
                    let node = element;
                    for (let depth = 0; node && depth < 4; depth += 1, node = node.parentElement) {
                        const style = window.parent.getComputedStyle(node);
                        const bg = style.backgroundColor;
                        const rect = node.getBoundingClientRect();
                        const isVisible = rect.width > 28 && rect.height > 24;
                        const hasSelectedBg = bg && bg !== "rgba(0, 0, 0, 0)" && bg !== "transparent";
                        const hasSelectedState =
                            node.getAttribute("aria-selected") === "true" ||
                            node.getAttribute("aria-pressed") === "true";
                        if (isVisible && (hasSelectedBg || hasSelectedState)) {
                            candidates.push({ mode, width: rect.width, height: rect.height, bg });
                            break;
                        }
                    }
                });
                if (!candidates.length) return null;
                candidates.sort((a, b) => (a.width * a.height) - (b.width * b.height));
                return candidates[0].mode;
            };

            const syncTheme = () => {
                if (manualThemeChoice && Date.now() < manualThemeUntil) {
                    setAppTheme(manualThemeChoice);
                    return;
                }
                manualThemeChoice = null;
                const selected = selectedThemeFromMenu();
                const stored = getStoredTheme();
                if (selected) setAppTheme(selected);
                else if (stored) setAppTheme(stored);
            };

            const watchThemeClicks = () => {
                const doc = window.parent.document;
                if (doc.documentElement.dataset.appThemeWatcher === "ready") return;
                doc.documentElement.dataset.appThemeWatcher = "ready";
                const handleThemeIntent = (event) => {
                    const mode = themeFromEventPath(event);
                    if (mode) {
                        applyThemeSoon(mode);
                    }
                };

                doc.addEventListener("pointerdown", handleThemeIntent, true);
                doc.addEventListener("mousedown", handleThemeIntent, true);
                doc.addEventListener("click", handleThemeIntent, true);
                doc.addEventListener("keyup", handleThemeIntent, true);

                try {
                    const storage = window.parent.localStorage;
                    const originalSetItem = storage.setItem.bind(storage);
                    storage.setItem = (key, value) => {
                        const result = originalSetItem(key, value);
                        const keyText = String(key || "").toLowerCase();
                        const valueText = String(value || "").toLowerCase();
                        if (keyText.includes("theme")) {
                            if (valueText.includes("dark")) applyThemeSoon("dark");
                            else if (valueText.includes("light")) applyThemeSoon("light");
                            else if (valueText.includes("system")) applyThemeSoon("system");
                        }
                        return result;
                    };
                } catch (error) {
                    // Some browsers disallow patching Storage. Click listeners still cover the UI.
                }

                if (window.parent.matchMedia) {
                    window.parent.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", () => {
                        if (doc.documentElement.dataset.appThemeChoice === "system") setAppTheme("system");
                    });
                }
            };

            const translatePage = () => {
                const doc = window.parent.document;
                const walker = doc.createTreeWalker(
                    doc.body,
                    doc.defaultView.NodeFilter.SHOW_TEXT
                );
                const textNodes = [];
                while (walker.nextNode()) textNodes.push(walker.currentNode);
                textNodes.forEach(translateNode);

                doc.querySelectorAll("[aria-label], [title]").forEach((element) => {
                    ["aria-label", "title"].forEach((attr) => {
                        const current = element.getAttribute(attr);
                        const next = translateValue(current);
                        if (next !== current) element.setAttribute(attr, next);
                    });
                });
                syncTheme();
            };

            setAppTheme(getStoredTheme() || "light");
            watchThemeClicks();
            translatePage();
            new MutationObserver(translatePage).observe(window.parent.document.body, {
                childList: true,
                subtree: true,
                characterData: true,
                attributes: true,
                attributeFilter: ["class", "style", "aria-selected", "aria-pressed"],
            });
            window.parent.setInterval(syncTheme, 1200);
        })();
        </script>
        """,
        height=0,
        width=0,
    )


def shorten_text(value, limit=78):
    value = str(value).replace("\n", " ").replace("“", "").replace("”", "").strip()
    return value if len(value) <= limit else value[:limit].rstrip() + "..."


def case_code(img_name, label, idx):
    prefix = "RF" if int(label) == 0 else "RM"
    return f"{prefix}-{idx + 1:03d}"


def get_case_rows():
    if df is None or df.empty:
        return pd.DataFrame()
    if st.session_state.category == "谣言案例":
        return rumor_df
    if st.session_state.category == "真实案例":
        return real_df
    return df


def render_case_library():
    current_cases = get_case_rows()
    st.markdown("""
    <div class="case-library-head">
        <h2>案例库</h2>
        <p>浏览预分析的取证调查案例，选择一个案例进行深度对比分析。</p>
    </div>
    """, unsafe_allow_html=True)

    if current_cases.empty:
        st.info("暂无可用案例。")
        return

    filter_cols = st.columns([1, 1, 1, 6])
    filter_items = [("全部案例", "全部案例"), ("谣言案例", "谣言"), ("真实案例", "真实信息")]
    for i, (category, label) in enumerate(filter_items):
        with filter_cols[i]:
            is_active = st.session_state.category == category
            with st.container(key=f"topnavactivefilter{i}" if is_active else f"topnavinactivefilter{i}"):
                if st.button(label, key=f"casefilter{i}", use_container_width=True):
                    switch_category(category)
                    st.rerun()

    current_cases = current_cases.sort_values(["priority", "image_path"]).reset_index(drop=True)
    page_size = 12
    total_cases = len(current_cases)
    total_pages = max(1, math.ceil(total_cases / page_size))
    st.session_state.case_page = max(1, min(st.session_state.case_page, total_pages))
    page = st.session_state.case_page
    start_idx = (page - 1) * page_size
    page_cases = current_cases.iloc[start_idx:start_idx + page_size]

    st.markdown(
        f"<div class='case-page-summary'>共 {total_cases} 条案例 · 第 {page} / {total_pages} 页 · 每页 {page_size} 条</div>",
        unsafe_allow_html=True,
    )

    rows = list(page_cases.iterrows())
    for start in range(0, len(rows), 4):
        cols = st.columns(4)
        for col, (idx, row) in zip(cols, rows[start:start + 4]):
            img_path = row["image_path"]
            img_name = os.path.basename(img_path)
            label = int(row["label"])
            title = row_title(row)
            status_text = "真实信息" if label == 0 else "谣言"
            status_class = "real" if label == 0 else "rumor"
            source = str(row.get("source", "")).strip()

            with col:
                with st.container(key=f"casecard{idx}"):
                    if os.path.exists(img_path):
                        with open(img_path, "rb") as f:
                            data = base64.b64encode(f.read()).decode("utf-8")
                        ext = os.path.splitext(img_path)[1].replace(".", "")
                        img_src = f"data:image/{ext};base64,{data}"
                    else:
                        img_src = ""

                    st.markdown(f"""
                    <div class="case-card-fixed-content">
                        <div class="case-thumb">
                            <span class="case-badge {status_class}">{status_text}</span>
                            <span class="case-id">ID: {case_code(img_name, label, idx)}</span>
                            <img src="{img_src}" alt="{title}">
                        </div>
                        <div class="case-card-title">{title}</div>
                        <div class="case-card-source">{source}</div>
                        <div class="case-card-desc">{shorten_text(row["text"])}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    with st.container(key=f"casechoosewrap{idx}"):
                        if st.button("选择并分析", key=f"casechoose{idx}", use_container_width=True):
                            select_case(row)
                            st.rerun()

    prev_col, page_col, next_col, spacer_col = st.columns([1, 1.2, 1, 5])
    with prev_col:
        with st.container(key="casepaginationprev"):
            if st.button("上一页", disabled=page <= 1, use_container_width=True):
                st.session_state.case_page = page - 1
                st.rerun()
    with page_col:
        st.markdown(f"<div class='case-page-indicator'>{page} / {total_pages}</div>", unsafe_allow_html=True)
    with next_col:
        with st.container(key="casepaginationnext"):
            if st.button("下一页", disabled=page >= total_pages, use_container_width=True):
                st.session_state.case_page = page + 1
                st.rerun()


def render_home_page():
    case_count = 0 if df is None else len(df)
    rumor_count = len(rumor_df)
    real_count = len(real_df)
    home_html = dedent(f"""
    <div class="home-dashboard">
        <section class="home-panel home-hero">
            <div class="home-hero-main">
                <div>
                    <p class="home-eyebrow">多模态核验工作台</p>
                    <h2 class="home-title">把新闻图片、正文和视觉证据放在同一个核验流程里</h2>
                    <p class="home-copy">首页保留最短路径：上传待检材料、复盘预置案例、进入控制台查看冲突高亮。适合课堂演示、样本对比和单条新闻的快速研判。</p>
                </div>
                <div class="home-actions">
                    <a class="home-action primary" href="?page=console" target="_self">进入控制台</a>
                    <a class="home-action" href="?page=cases" target="_self">打开案例库</a>
                </div>
            </div>
            <aside class="home-inspector">
                <div class="home-inspector-title">当前核验配置</div>
                <div class="home-inspector-row">
                    <span>视觉一致性引擎</span>
                    <span class="home-status-pill">就绪</span>
                </div>
                <div class="home-inspector-row">
                    <span>语义研判报告</span>
                    <span class="home-status-pill">可生成</span>
                </div>
                <div class="home-inspector-row">
                    <span>样本库规模</span>
                    <strong>{case_count} 条</strong>
                </div>
            </aside>
        </section>
        <div class="home-stats">
            <div class="home-card">
                <div class="home-stat-value">{case_count}</div>
                <div class="home-stat-label">预置案例总量</div>
                <div class="home-stat-note"><span style="width: 100%;"></span></div>
            </div>
            <div class="home-card">
                <div class="home-stat-value">{rumor_count}</div>
                <div class="home-stat-label">谣言样本</div>
                <div class="home-stat-note"><span style="width: 50%;"></span></div>
            </div>
            <div class="home-card">
                <div class="home-stat-value">{real_count}</div>
                <div class="home-stat-label">真实样本</div>
                <div class="home-stat-note"><span style="width: 50%;"></span></div>
            </div>
            <div class="home-card">
                <div class="home-stat-value">3</div>
                <div class="home-stat-label">研判步骤</div>
                <div class="home-stat-note"><span style="width: 75%;"></span></div>
            </div>
        </div>
        <div class="home-section-title">推荐核验路径</div>
        <div class="home-flow">
            <div class="home-card">
                <div class="home-step">1</div>
                <h3>导入材料</h3>
                <p>上传新闻配图，粘贴正文，或直接从案例库选择一条预置样本。</p>
                <div class="home-card-meta">输入层</div>
            </div>
            <div class="home-card">
                <div class="home-step">2</div>
                <h3>计算一致性</h3>
                <p>系统给出图文一致性得分，并定位可能造成误导的视觉区域。</p>
                <div class="home-card-meta">模型层</div>
            </div>
            <div class="home-card">
                <div class="home-step">3</div>
                <h3>复核结论</h3>
                <p>对照原图、冲突高亮和语言模型说明，形成可解释的研判结论。</p>
                <div class="home-card-meta">报告层</div>
            </div>
        </div>
        <div class="home-section-title">常用入口</div>
        <div class="home-capabilities">
            <a class="home-card interactive" href="?page=console" target="_self">
                <h3>快速上传</h3>
                <p>临时新闻图片与正文的单条检测入口。</p>
                <div class="home-card-meta">开始检测</div>
            </a>
            <a class="home-card interactive" href="?page=cases" target="_self">
                <h3>案例复盘</h3>
                <p>在真实样本和谣言样本之间横向对比。</p>
                <div class="home-card-meta">查看样本</div>
            </a>
            <a class="home-card interactive" href="?page=settings" target="_self">
                <h3>阈值设置</h3>
                <p>调整研判阈值、模型偏好和报告导出格式。</p>
                <div class="home-card-meta">配置系统</div>
            </a>
            <a class="home-card interactive" href="?page=console" target="_self">
                <h3>证据对比</h3>
                <p>查看原始图片、冲突高亮和解释报告。</p>
                <div class="home-card-meta">进入工作区</div>
            </a>
        </div>
    </div>
    """)
    home_html = "\n".join(line for line in home_html.splitlines() if line.strip())
    st.markdown(home_html, unsafe_allow_html=True)


def render_settings_page():
    st.markdown("""
    <div class="settings-panel">
        <h2>系统设置</h2>
        <p>配置推理模型、检测阈值与输出偏好。设置会保存在当前会话中。</p>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
    col_api, col_model = st.columns(2)
    with col_api:
        st.text_input(
            "接口密钥 (DashScope)",
            value="",
            type="password",
            key="apikeyinput",
            help="不填则使用系统默认内置密钥执行大模型研判。"
        )
    with col_model:
        # 定义模型选项列表
        model_options = ["Qwen-Max 多模态文本分析", "Qwen-Plus 快速研判", "本地规则兜底"]
        
        # 获取当前模型设置，并确定对应的索引
        current_model = st.session_state.get("modelsetting", "Qwen-Max 多模态文本分析")
        current_index = model_options.index(current_model) if current_model in model_options else 0
        
        def on_model_change():
            # 确保模型设置被正确保存
            selected_model = st.session_state.get("modelsetting_select", "Qwen-Max 多模态文本分析")
            st.session_state["modelsetting"] = selected_model
            print(f"[模型切换] 已切换到: {selected_model}")
        
        # 使用独立的 key 绑定 selectbox，并通过回调更新 modelsetting
        st.selectbox(
            "主推理模型",
            model_options,
            index=current_index,
            key="modelsetting_select",
            on_change=on_model_change
        )
    # 同步显示当前实际使用的模型设置
    st.info(f"当前模型设置值: `{st.session_state.get('modelsetting', '未设置')}`")
    col_threshold, col_export = st.columns(2)
    with col_threshold:
        st.slider("疑似谣言阈值", min_value=0, max_value=100, value=45, key="thresholdsetting")
    with col_export:
        st.selectbox("报告导出格式", ["Markdown", "PDF", "JSON"], index=1, key="exportsetting")


def render_console_empty():
    st.markdown("""
    <div class="console-hero">
        <div>
            <h2>控制台</h2>
            <p>把图片和正文放进同一条核验流水线。左侧负责输入材料，右侧会在上传后形成待检预览，并在检测后展示证据对比。</p>
        </div>
        <div class="console-status-strip">
            <div class="console-status-item"><b>图片输入</b><span>等待上传</span></div>
            <div class="console-status-item"><b>正文解析</b><span>等待录入</span></div>
            <div class="console-status-item"><b>证据面板</b><span>实时同步</span></div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    col_upload, col_preview = st.columns([5, 7])
    with col_upload:
        with st.container(key="topuploadpanel"):
            st.markdown("""
            <div class="console-panel-head">
                <h3>待检测材料</h3>
                <span>JPG / PNG + 新闻正文</span>
            </div>
            """, unsafe_allow_html=True)
            uploaded = st.file_uploader("上传待检图片", type=["jpg", "png", "jpeg"], key="fileuploader")
            st.markdown("""
            <div class="console-input-hint">
                建议上传新闻原图或截图，并保留标题、地点、人物、时间等关键信息。正文越完整，语义研判越稳定。
            </div>
            """, unsafe_allow_html=True)
            text_value = st.text_area(
                "新闻正文输入",
                value=st.session_state.text,
                height=220,
                key="consoletextinput"
            )
            if text_value != st.session_state.text:
                st.session_state.text = text_value
                st.session_state.score = None
                st.session_state.highlight_img = None
                st.session_state.explanation = ""
                st.session_state.is_detecting = False
            if uploaded:
                temp_file = os.path.join(PROJECT_ROOT, "temp_upload.jpg")
                with open(temp_file, "wb") as f:
                    f.write(uploaded.getbuffer())
                if st.session_state.img_path != temp_file:
                    st.session_state.img_path = temp_file
                    st.session_state.score = None
                    st.session_state.highlight_img = None
                    st.session_state.explanation = ""
                    st.session_state.is_detecting = False
                    st.rerun()
            text_count = len(st.session_state.text.strip())
            image_state = "已选择图片" if st.session_state.img_path else "尚未上传图片"
            st.markdown(f"""
            <div class="console-text-status">
                <span>{image_state}</span>
                <span>正文 {text_count} 字</span>
            </div>
            """, unsafe_allow_html=True)
    with col_preview:
        st.markdown("""
        <div class="console-preview">
            <div class="console-preview-shell">
                <div class="console-preview-top">
                    <b>待检预览</b>
                    <span>空闲状态</span>
                </div>
                <div class="console-preview-stage">
                    <div class="console-empty-card">
                        <h3>等待材料进入核验队列</h3>
                        <p>上传图片并填写正文后，这里会展示原图预览、文本摘要和后续的冲突高亮入口。</p>
                        <div class="console-scan-rail"><span></span></div>
                    </div>
                </div>
                <div class="console-preview-checks">
                    <div><b>图像区域</b><span>检测主体、场景和显著视觉元素</span></div>
                    <div><b>文本事实</b><span>抽取时间、地点、对象和事件关系</span></div>
                    <div><b>冲突定位</b><span>对齐图文语义并标记可疑区域</span></div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.session_state.text.strip():
            st.markdown(f"<p style='margin-top:14px; color: color-mix(in srgb, var(--text-color, #31333f) 70%, transparent); line-height:1.7;'>{shorten_text(st.session_state.text, 140)}</p>", unsafe_allow_html=True)

sync_page_from_query()

# 5. 主界面头部 (SaaS 顶栏状态指示栏)
st.markdown("""
<div class="header-container">
    <div class="header-left">
        <span class="header-badge">多模态智能校验</span>
        <h1 class="header-title">图文一致性多模态谣言检测系统</h1>
    </div>
    <div class="header-right">
        <div class="status-indicator">
            <span class="status-dot green"></span>
            <span class="status-text">视觉对齐引擎: 就绪</span>
        </div>
        <div class="status-indicator">
            <span class="status-dot green"></span>
            <span class="status-text">大语言模型内核: 通义千问已连接</span>
        </div>
        <div class="status-indicator">
            <span class="status-dot blue"></span>
            <span class="status-text">系统版本: v2.5 专业版</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

render_top_navigation()
render_streamlit_toolbar_i18n()

api_key_input = st.session_state.get("apikeyinput", "")

# 6. 核心工作区 (左右双列布局)
if st.session_state.app_page == "控制台" and st.session_state.img_path and os.path.exists(st.session_state.img_path):
    col_left, col_right = st.columns([5, 7])
    
    # 6.1 左列：控制面板
    with col_left:
        with st.container(key="cardinput"):
            st.markdown('<div class="card-title">待检测新闻正文</div>', unsafe_allow_html=True)
            
            user_text = st.text_area(
                "新闻正文输入",
                value=st.session_state.text,
                height=260,
                label_visibility="collapsed"
            )
            if user_text != st.session_state.text:
                st.session_state.text = user_text
                st.session_state.score = None
                st.session_state.highlight_img = None
                st.session_state.explanation = ""
                st.session_state.is_detecting = False
                
            col_btn1, col_btn2 = st.columns([7, 3])
            with col_btn1:
                start_btn = st.button("开始智能检测", key="startdetectionmain", use_container_width=True)
            with col_btn2:
                reset_btn = st.button("重置检测", key="resetdetectionmain", use_container_width=True)
                
            if reset_btn:
                st.session_state.img_path = None
                st.session_state.text = ""
                st.session_state.score = None
                st.session_state.highlight_img = None
                st.session_state.explanation = ""
                st.session_state.is_detecting = False
                st.session_state.category = "自定义上传"
                switch_page("控制台")
                st.rerun()
                
            if start_btn:
                if not st.session_state.text.strip():
                    st.warning("请先在输入框中填入待研判的新闻正文。")
                else:
                    st.session_state.is_detecting = True
                    st.rerun()
            
        # 6.2 左列下方：智能研判结论 (检测后展示)
        if st.session_state.score is not None:
            score_val = st.session_state.score
            if score_val >= 70:
                verdict_class = "verdict-green"
                verdict_key = "cardverdictgreen"
                stroke_color = "#10b981"
                grad_start = "#059669"
                grad_end = "#34d399"
                shadow_color = "rgba(16, 185, 129, 0.4)"
                verdict_badge = "<span style='padding: 6px 16px; border-radius: 20px; font-weight: 700; background: rgba(16, 185, 129, 0.15); color: #10b981; border: 1px solid rgba(16, 185, 129, 0.3); font-size: 14px;'>高度可信</span>"
                verdict_desc = "经多模态交叉对齐与语义校验，未发现图文间存在事实违和，信息高度可信。"
            elif score_val >= 45:
                verdict_class = "verdict-yellow"
                verdict_key = "cardverdictyellow"
                stroke_color = "#f59e0b"
                grad_start = "#d97706"
                grad_end = "#fbbf24"
                shadow_color = "rgba(245, 158, 11, 0.4)"
                verdict_badge = "<span style='padding: 6px 16px; border-radius: 20px; font-weight: 700; background: rgba(245, 158, 11, 0.15); color: #f59e0b; border: 1px solid rgba(245, 158, 11, 0.3); font-size: 14px;'>内容存疑</span>"
                verdict_desc = "图文间存在一定程度的描述偏差或局部冲突，右侧高亮区域可能存在违和事实。"
            else:
                verdict_class = "verdict-red"
                verdict_key = "cardverdictred"
                stroke_color = "#ef4444"
                grad_start = "#dc2626"
                grad_end = "#f87171"
                shadow_color = "rgba(239, 68, 68, 0.4)"
                verdict_badge = "<span style='padding: 6px 16px; border-radius: 20px; font-weight: 700; background: rgba(239, 68, 68, 0.15); color: #ef4444; border: 1px solid rgba(239, 68, 68, 0.3); font-size: 14px;'>疑似谣言</span>"
                verdict_desc = "图像特征与文本事实存在严重语义背离或恶意剪切拼接，存在极高的舆情误导风险。"

            # 计算圆环周长与偏移 (r = 40, cx = 55, cy = 55)
            r = 40
            circ = 2 * 3.14159 * r # 251.3
            stroke_offset = circ * (1.0 - (score_val / 100.0))
            
            with st.container(key=verdict_key):
                st.markdown(f'<div class="card-title {verdict_class}">智能研判结论</div>', unsafe_allow_html=True)
                
                gauge_html = (
                    f'<style>'
                    f'@keyframes drawGauge_{int(score_val)} {{'
                    f'  from {{ stroke-dashoffset: 251.3; }}'
                    f'  to {{ stroke-dashoffset: {stroke_offset}; }}'
                    f'}}'
                    f'</style>'
                    f'<div class="gauge-card-content">'
                    f'<div class="gauge-container">'
                    f'<svg width="150" height="150" viewBox="0 0 110 110" style="position: absolute;">'
                    f'<defs>'
                    f'<linearGradient id="gaugeGrad" x1="0%" y1="100%" x2="100%" y2="0%">'
                    f'<stop offset="0%" stop-color="{grad_start}" />'
                    f'<stop offset="100%" stop-color="{grad_end}" />'
                    f'</linearGradient>'
                    f'</defs>'
                    f'<circle cx="55" cy="55" r="{r}" stroke="color-mix(in srgb, var(--text-color, #31333f) 6%, transparent)" stroke-width="8" fill="transparent" />'
                    f'<circle cx="55" cy="55" r="{r}" stroke="url(#gaugeGrad)" stroke-width="8" fill="transparent" '
                    f'stroke-dasharray="{circ}" stroke-dashoffset="{circ}" stroke-linecap="round" '
                    f'style="transform: rotate(-90deg); transform-origin: 55px 55px; filter: drop-shadow(0 0 6px {shadow_color}); '
                    f'animation: drawGauge_{int(score_val)} 1.5s cubic-bezier(0.4, 0, 0.2, 1) forwards;" />'
                    f'</svg>'
                    f'<div style="text-align: center; z-index: 10;">'
                    f'<div class="gauge-score-val">{score_val:.1f}</div>'
                    f'<div class="gauge-score-lbl">一致性得分</div>'
                    f'</div>'
                    f'</div>'
                    f'<div class="gauge-verdict-badge-box">{verdict_badge}</div>'
                    f'<div class="gauge-verdict-desc-box">{verdict_desc}</div>'
                    f'</div>'
                )
                st.markdown(gauge_html, unsafe_allow_html=True)
        elif not st.session_state.is_detecting:
            # 待命状态时的系统工作指引
            with st.container(key="cardguideline"):
                st.markdown('<div class="card-title">系统工作指引</div>', unsafe_allow_html=True)
                st.markdown("""
                <div style="font-size: 13.5px; color: color-mix(in srgb, var(--text-color, #31333f) 60%, transparent); line-height: 1.7; padding: 10px 0;">
                    1. <b>选择/上传样本</b>：在顶部导航中进入案例库，或上传自定义新闻图片；<br/>
                    2. <b>核对新闻文本</b>：在“待检测新闻正文”文本框中确认或输入待检文本信息；<br/>
                    3. <b>启动AI检测</b>：点击“开始智能检测”按钮，系统将自动进行多模态空间对齐与特征提取；<br/>
                    4. <b>查看双重校验结果</b>：检测完成后，系统将输出交叉对齐矛盾定位图以及大模型生成的深度逻辑研判报告。
                </div>
                """, unsafe_allow_html=True)

    # 6.3 右列：视觉证据
    with col_right:
        with st.container(key="cardcompare"):
            st.markdown('<div class="card-title">视觉证据双屏比对</div>', unsafe_allow_html=True)
            
            col_img1, col_img2 = st.columns(2)
            with col_img1:
                st.markdown("<p style='text-align: center; color: color-mix(in srgb, var(--text-color, #31333f) 60%, transparent); font-size: 13px; font-weight: 600; margin-bottom: 12px;'>原始发布图谱</p>", unsafe_allow_html=True)
                if st.session_state.img_path and os.path.exists(st.session_state.img_path):
                    with open(st.session_state.img_path, "rb") as f:
                        data = base64.b64encode(f.read()).decode("utf-8")
                    ext = os.path.splitext(st.session_state.img_path)[1].replace(".", "")
                    img_src = f"data:image/{ext};base64,{data}"
                    
                    if st.session_state.is_detecting:
                        html = f'<div class="image-scanner-wrapper"><div class="image-scanner-line"></div><img src="{img_src}" style="width: 100%; display: block; border-radius: 12px;"/></div>'
                    else:
                        html = f'<div class="image-scanner-wrapper"><img src="{img_src}" style="width: 100%; display: block; border-radius: 12px;"/></div>'
                    st.markdown(html, unsafe_allow_html=True)
                else:
                    st.markdown("<div style='text-align: center; padding: 20px; color: color-mix(in srgb, var(--text-color, #31333f) 40%, transparent);'>暂无图像</div>", unsafe_allow_html=True)
                
            with col_img2:
                if st.session_state.highlight_img is not None:
                    st.markdown("<p style='text-align: center; color: #f43f5e; font-size: 13px; font-weight: 600; margin-bottom: 12px;'>矛盾冲突高亮</p>", unsafe_allow_html=True)
                    st.image(st.session_state.highlight_img, use_container_width=True)
                else:
                    st.markdown("<p style='text-align: center; color: color-mix(in srgb, var(--text-color, #31333f) 50%, transparent); font-size: 13px; font-weight: 600; margin-bottom: 12px;'>矛盾研判扫描</p>", unsafe_allow_html=True)
                    
                    if st.session_state.is_detecting:
                        radar_title = "正在提取特征..."
                        radar_desc = "正在运行交叉对齐空间扫描<br/>实时比对图像区域与文本特征..."
                    else:
                        radar_title = "检测内核待命"
                        radar_desc = "请点击“开始智能检测”<br/>实时生成并高亮矛盾冲突区域"
                        
                    st.markdown(f"""
                    <div class="radar-screen">
                        <div class="radar-grid"></div>
                        <div class="radar-sweep"></div>
                        <div class="radar-laser"></div>
                        <div class="radar-signal">
                            <div class="radar-dot"></div>
                        </div>
                        <div class="radar-text">
                            <div class="radar-text-title">{radar_title}</div>
                            {radar_desc}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
        # 6.4 右列下方：智能多模态研判报告 (检测后展示)
        if st.session_state.score is not None:
            with st.container(key="cardreport"):
                st.markdown('<div class="card-title">智能多模态研判报告</div>', unsafe_allow_html=True)
                
                # 清理报告内容
                cleaned_explanation = clean_report_content(st.session_state.explanation)
                
                st.markdown('<div class="report-content">', unsafe_allow_html=True)
                st.markdown(cleaned_explanation)
                st.markdown('</div>', unsafe_allow_html=True)
                
                # 报告导出功能 - 根据系统设置选择格式
                export_format = st.session_state.get("exportsetting", "PDF")
                
                if export_format == "Markdown":
                    export_data = get_report_markdown()
                    file_name = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
                    mime_type = "text/markdown"
                    button_label = "导出报告"
                elif export_format == "PDF":
                    # 真正的PDF导出
                    export_data = get_report_pdf()
                    file_name = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                    mime_type = "application/pdf"
                    button_label = "导出报告"
                else:  # JSON
                    export_data = get_report_json()
                    file_name = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                    mime_type = "application/json"
                    button_label = "导出报告"
                
                st.download_button(
                    button_label,
                    data=export_data,
                    file_name=file_name,
                    mime=mime_type,
                    use_container_width=True
                )
        elif not st.session_state.is_detecting:
            # 待命状态时的系统架构规范
            with st.container(key="cardarchitecture"):
                st.markdown('<div class="card-title">系统架构规范</div>', unsafe_allow_html=True)
                st.markdown("""
                <div style="font-size: 13.5px; color: color-mix(in srgb, var(--text-color, #31333f) 60%, transparent); line-height: 1.7; padding: 10px 0;">
                    本系统采用<b>双重校验决策框架</b>：<br/>
                    - <b>视觉-语言交叉特征层</b>：利用对比式语言-图像预训练（CLIP）对齐技术，深度分析图像内各个物体与文本关键词 of 校验，锁定信息冲突的核心网格并以发光红框标注。<br/>
                    - <b>认知大模型推理层</b>：集成先进的通义千问大模型进行高阶多模态事实校验，多维度撰写严谨的辟谣与逻辑研判报告。
                </div>
                """, unsafe_allow_html=True)

    # 6.5 检测执行触发逻辑
    if st.session_state.is_detecting:
        model_setting = st.session_state.get("modelsetting", "Qwen-Max 多模态文本分析")
        
        # 阶段1：特征提取（快速）
        with st.spinner("正在提取多模态交叉对齐特征并计算一致性得分..."):
            score = get_consistency_score(st.session_state.img_path, st.session_state.text)
            st.session_state.score = score
            
            # 获取高亮冲突区域（所有模型都支持）
            highlight_img, _ = highlight_conflict(st.session_state.img_path, st.session_state.text)
            if highlight_img is not None:
                if isinstance(highlight_img, np.ndarray):
                    st.session_state.highlight_img = Image.fromarray(highlight_img)
                else:
                    st.session_state.highlight_img = highlight_img
    
        # 阶段2：生成研判报告（根据模型选择）
        if model_setting == "本地规则兜底":
            # 快速模式：跳过LLM，使用本地规则生成报告
            st.session_state.explanation = generate_fast_report(score, st.session_state.text)
        else:
            # 大模型模式：检查API Key是否可用
            api_key = api_key_input.strip() if api_key_input else os.environ.get('DASHSCOPE_API_KEY')
            
            if api_key:
                # API Key 可用，使用大模型
                with st.spinner("大模型正在进行多模态语义逻辑比对与研判报告生成..."):
                    from llm_reason import generate_explanation
                    model_name = 'qwen-max' if "Max" in model_setting else 'qwen-plus'
                    explanation = generate_explanation(score, st.session_state.text, api_key=api_key, model_name=model_name)
                    st.session_state.explanation = explanation
            else:
                # 没有API Key，自动降级为本地规则兜底
                st.warning("未配置 API Key，已自动降级为本地规则模式。请在系统设置中配置API Key以使用大模型。")
                st.session_state.explanation = generate_fast_report(score, st.session_state.text)
        
        st.session_state.is_detecting = False
        st.rerun()

elif st.session_state.app_page == "控制台":
    render_console_empty()

elif st.session_state.app_page == "案例":
    render_case_library()

elif st.session_state.app_page == "系统设置":
    render_settings_page()

else:
    render_home_page()
