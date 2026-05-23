from dashscope import Generation
import os

def generate_explanation(score, text, api_key=None, model_name='qwen-max'):
    """生成智能分析报告"""
    # 优先采用传入的 api_key，其次从环境变量读取，最后使用 None（由 dashscope 默认处理）
    if api_key and api_key.strip():
        active_key = api_key
    else:
        active_key = os.environ.get('DASHSCOPE_API_KEY')
    
    # 设置环境变量供 dashscope 使用
    if active_key:
        os.environ['DASHSCOPE_API_KEY'] = active_key
    
    # 根据分数确定置信度描述
    if score >= 80:
        confidence = "极高"
        level = "高度可信"
    elif score >= 70:
        confidence = "高"
        level = "可信"
    elif score >= 55:
        confidence = "中等"
        level = "基本可信"
    elif score >= 45:
        confidence = "较低"
        level = "存疑"
    elif score >= 30:
        confidence = "低"
        level = "疑似谣言"
    else:
        confidence = "极低"
        level = "高度疑似谣言"

    # 根据模型选择不同的提示词
    if model_name == 'qwen-max':
        # Qwen-Max：详细分析报告
        prompt = f"""
你是一名专业的社交媒体谣言检测分析师，拥有丰富的事实核查经验。请根据以下检测数据和文本，进行深度、全面的分析，并输出一份详细、专业、排版精美的 Markdown 格式研判报告。

【检测数据】
- 图文一致性得分：{score:.1f}/100分
- 置信等级：{level}（置信度 {confidence}）

【待分析文本】
{text}

【分析任务与报告结构】
请生成包含以下板块的详细报告，各板块使用 Markdown 标题（如 `###`）：

1. ### 综合判定
   - 给出明确的结论（可信新闻、内容存疑 或 疑似谣言）
   - 详细说明判定依据，包括得分的含义和影响
   - 分析信息来源的可信度和权威性

2. ### 图文一致性深入剖析
   - 结合图文一致性得分，深度分析文本内容与图像特征之间的匹配程度
   - 分析文本中的关键信息点（人物、地点、时间、事件等）
   - 评估文本描述与图像内容的逻辑一致性
   - 分析信息的完整性和合理性

3. ### 风险评估与疑点提示
   - 如果得分较低：
     * 详细分析哪些表述与画面存在明显矛盾
     * 指出可能存在的误导倾向和虚假信息特征
     * 分析谣言可能产生的社会影响
   - 如果得分较高：
     * 详细说明为何该信息可信
     * 分析信息的来源可靠性和证据充分性

4. ### 信息溯源建议
   - 建议如何核实信息的真实性
   - 推荐可靠的信息验证渠道和方法
   - 提供交叉验证的策略建议

5. ### 应对建议
   - 针对不同人群（普通用户、媒体、平台）的具体建议
   - 给出具体且有操作性的下一步行动建议
   - 提供风险防控和信息传播的指导意见

【输出要求】
- 必须使用中文，语言专业、严谨、客观、详细
- 每个板块内容不少于150字，整体报告不少于800字
- 排版格式优雅，使用列表、粗体字和适当的分隔增强可读性
- 直接输出 Markdown 报告，不要闲聊前缀或后缀
- 分析要深入细致，提供充分的论据和推理过程
"""
    else:
        # Qwen-Plus：快速研判报告
        prompt = f"""
你是一名专业的社交媒体谣言检测分析师。请根据以下检测数据和文本，进行快速分析并输出一份简洁、专业的 Markdown 格式研判报告。

【检测数据】
- 图文一致性得分：{score:.1f}/100分
- 置信等级：{level}（置信度 {confidence}）

【待分析文本】
{text}

【分析任务】
请生成包含以下内容的报告：

1. **综合判定**：给出明确结论（可信新闻、内容存疑 或 疑似谣言）
2. **关键分析**：简要分析图文一致性和主要疑点
3. **风险提示**：指出潜在风险等级
4. **建议**：给出简洁的应对建议

【输出要求】
- 必须使用中文，语言专业、严谨、客观
- 报告简洁明了，重点突出
- 使用 Markdown 格式，适当使用粗体和列表
- 直接输出报告内容，无需额外说明
"""
    try:
        response = Generation.call(
            model=model_name,
            api_key=active_key,
            prompt=prompt,
            result_format='message',
            temperature=0.3,
            max_tokens=4096,  # 增加输出长度限制
            top_p=0.8
        )
        if response.status_code == 200:
            content = response.output.choices[0].message.content
            return content
        else:
            return f"**LLM 调用失败（状态码: {response.status_code}）**\n\n请检查 API Key 配置是否正确或网络是否畅通。以下为系统自动生成的备用分析：\n\n- **图文一致性得分**：{score:.1f}/100\n- **判定结果**：{'可信新闻' if score>=70 else '内容存疑' if score>=45 else '疑似谣言'}\n- **建议**：建议人工核对原始出处或等待官方核实。"
    except Exception as e:
        error_msg = str(e)[:100]
        return f"**大模型报告生成异常**\n\n异常信息：`{error_msg}`\n\n以下为系统自动生成的备用分析：\n\n- **图文一致性得分**：{score:.1f}/100\n- **判定结果**：{'可信新闻' if score>=70 else '内容存疑' if score>=45 else '疑似谣言'}\n- **建议**：请人工核查图片和文本的真实发布来源。"
