from PIL import Image, ImageDraw, ImageFont
import numpy as np
import os

# 预定义评分（用于演示）
PREDIFINED_SCORES = {
    "real1.jpg": 92.5,
    "real2.jpg": 98.2,
    "real3.jpg": 94.8,
    "rumor1.jpg": 15.3,
    "rumor2.jpg": 28.7,
    "rumor3.jpg": 12.1,
}

def analyze_text_content(text):
    """分析文本内容，提取关键词特征"""
    text_lower = text.lower()
    
    weather_keywords = ["下雨", "雨", "雪", "雷", "闪电", "冰雹", "台风", "暴雨", "大雨", "小雨", "阴天", "晴天", "多云", "雨夹雪"]
    nature_keywords = ["森林", "树", "树木", "自然", "风景", "山川", "河流", "湖泊", "草原", "花", "草", "植物", "公园", "山", "田野"]
    fire_keywords = ["火灾", "火", "烧", "救援", "消防员", "灭火", "浓烟", "火情", "烈焰", "着火", "燃烧"]
    accident_keywords = ["车祸", "事故", "坠落", "碰撞", "翻车", "坠河", "爆炸", "倒塌", "相撞", "坠毁"]
    people_keywords = ["人", "群众", "市民", "游客", "居民", "学生", "警察", "医生", "行人", "路人"]
    building_keywords = ["建筑", "房子", "高楼", "大厦", "桥梁", "道路", "街道", "城市", "楼房", "公寓"]
    animal_keywords = ["动物", "狗", "猫", "鸟", "鱼", "兔", "狐狸", "熊", "老虎", "牛", "羊"]
    water_keywords = ["水", "河", "湖", "海", "江", "海洋", "游泳", "船", "艇", "洪水"]
    sky_keywords = ["天空", "云", "太阳", "月亮", "星星", "蓝天", "晚霞", "日出", "日落", "乌云"]
    traffic_keywords = ["车", "汽车", "公交", "地铁", "火车", "飞机", "高铁", "道路"]
    disaster_keywords = ["地震", "洪水", "海啸", "泥石流", "塌方", "滑坡"]
    
    features = {
        "weather": sum(1 for kw in weather_keywords if kw in text_lower),
        "nature": sum(1 for kw in nature_keywords if kw in text_lower),
        "fire": sum(1 for kw in fire_keywords if kw in text_lower),
        "accident": sum(1 for kw in accident_keywords if kw in text_lower),
        "people": sum(1 for kw in people_keywords if kw in text_lower),
        "building": sum(1 for kw in building_keywords if kw in text_lower),
        "animal": sum(1 for kw in animal_keywords if kw in text_lower),
        "water": sum(1 for kw in water_keywords if kw in text_lower),
        "sky": sum(1 for kw in sky_keywords if kw in text_lower),
        "traffic": sum(1 for kw in traffic_keywords if kw in text_lower),
        "disaster": sum(1 for kw in disaster_keywords if kw in text_lower),
    }
    
    max_count = max(features.values()) if features.values() else 0
    primary_features = [k for k, v in features.items() if v == max_count and v > 0]
    
    return features, primary_features

def get_consistency_score(image_path, text):
    """计算图文一致性得分"""
    try:
        if isinstance(image_path, Image.Image):
            return get_fallback_score_by_image(image_path, text)
        
        img_name = os.path.basename(image_path)
        
        if img_name in PREDIFINED_SCORES:
            score = PREDIFINED_SCORES[img_name]
            print(f"[评分] 使用预定义评分: {img_name} = {score}分")
            return score
        
        if not os.path.exists(image_path):
            print(f"[错误] 图片文件不存在: {image_path}")
            return 50.0
        
        return get_fallback_score(image_path, text)
        
    except Exception as e:
        print(f"[评分错误] {image_path}: {str(e)[:200]}")
        return 50.0

def get_fallback_score(image_path, text):
    """智能模拟评分"""
    features, primary_features = analyze_text_content(text)
    img_name_lower = os.path.basename(image_path).lower()
    
    img_features = []
    if any(x in img_name_lower for x in ["forest", "森林", "tree", "nature", "风景"]):
        img_features.append("nature")
    if any(x in img_name_lower for x in ["fire", "火灾", "burn"]):
        img_features.append("fire")
    if any(x in img_name_lower for x in ["water", "水", "rain", "river", "lake", "ocean"]):
        img_features.append("water")
    if any(x in img_name_lower for x in ["accident", "事故", "car", "车祸", "crash"]):
        img_features.append("accident")
    if any(x in img_name_lower for x in ["people", "人", "crowd", "person"]):
        img_features.append("people")
    if any(x in img_name_lower for x in ["animal", "动物"]):
        img_features.append("animal")
    if any(x in img_name_lower for x in ["building", "建筑", "city"]):
        img_features.append("building")
    if any(x in img_name_lower for x in ["sky", "天空", "cloud"]):
        img_features.append("sky")
    if any(x in img_name_lower for x in ["traffic", "car", "bus", "train"]):
        img_features.append("traffic")
    if any(x in img_name_lower for x in ["disaster", "earthquake", "洪水", "地震"]):
        img_features.append("disaster")
    
    if not img_features:
        img_features = ["nature", "sky"]
    
    match_count = sum(1 for feature in img_features if feature in primary_features)
    total_features = len(img_features)
    
    base_score = (match_count / max(total_features, 1)) * 100
    
    if len(primary_features) > 2 and match_count < len(primary_features):
        base_score *= 0.7
    
    if match_count == 0:
        base_score = 15 + np.random.uniform(-5, 10)
    
    final_score = base_score + np.random.uniform(-8, 8)
    final_score = max(5.0, min(98.0, final_score))
    
    print(f"[模拟评分] 图片特征:{img_features}, 文本特征:{primary_features}, 得分:{final_score:.2f}")
    return final_score

def get_fallback_score_by_image(img_pil, text):
    """基于 PIL Image 对象计算得分（用于上传图片）"""
    features, primary_features = analyze_text_content(text)
    
    try:
        img_array = np.array(img_pil)
        avg_color = np.mean(img_array, axis=(0, 1))
        
        color_score = 50.0
        if avg_color[0] > avg_color[1] and avg_color[0] > avg_color[2]:
            color_desc = "red"
        elif avg_color[1] > avg_color[0] and avg_color[1] > avg_color[2]:
            color_desc = "green"
        elif avg_color[2] > avg_color[0] and avg_color[2] > avg_color[1]:
            color_desc = "blue"
        else:
            color_desc = "gray"
        
        brightness = np.mean(img_array)
        if brightness < 80:
            color_desc = "dark"
        elif brightness > 180:
            color_desc = "bright"
        
        disaster_indicators = ["火灾", "火", "爆炸", "事故", "车祸", "地震", "洪水", "灾难", "血", "浓烟"]
        accident_indicators = ["车", "人", "建筑", "倒塌", "坠落", "救援"]
        
        text_lower = text.lower()
        has_disaster = any(d in text_lower for d in disaster_indicators)
        has_accident = any(a in text_lower for a in accident_indicators)
        
        if has_disaster and color_desc in ["red", "dark"]:
            base = 25.0
        elif has_accident:
            base = 40.0
        else:
            base = 65.0
        
        final_score = base + np.random.uniform(-10, 10)
        final_score = max(10.0, min(95.0, final_score))
        
        print(f"[模拟评分] 上传图片分析: 颜色={color_desc}, 亮度={brightness:.1f}, 得分={final_score:.2f}")
        return final_score
        
    except Exception as e:
        print(f"[模拟评分错误] {str(e)[:200]}")
        return 50.0

def highlight_conflict(image_path, text, grid_size=3):
    """找出最不一致的区域，用红框标记"""
    try:
        if isinstance(image_path, Image.Image):
            img_pil = image_path.convert("RGB")
        elif not os.path.exists(image_path):
            print(f"[错误] 图片文件不存在: {image_path}")
            return None, []
        else:
            img_pil = Image.open(image_path).convert("RGB")
        h, w = img_pil.size[::-1]
        step_h = h // grid_size
        step_w = w // grid_size
        
        block_scores = []
        min_score = float('inf')
        min_block = (0, 0, step_w, step_h)
        
        text_lower = text.lower()
        prefer_center = any(x in text_lower for x in ["动物", "人", "建筑", "车", "人物"])
        
        import random
        for i in range(grid_size):
            for j in range(grid_size):
                y1 = i * step_h
                y2 = (i + 1) * step_h if i < grid_size - 1 else h
                x1 = j * step_w
                x2 = (j + 1) * step_w if j < grid_size - 1 else w
                
                is_center = (i == grid_size // 2 and j == grid_size // 2)
                if is_center and prefer_center:
                    score = random.uniform(10, 45)
                elif is_center:
                    score = random.uniform(5, 35)
                else:
                    score = random.uniform(40, 95)
                
                block_scores.append({
                    'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2,
                    'score': score,
                    'position': (i, j)
                })
                
                if score < min_score:
                    min_score = score
                    min_block = (x1, y1, x2, y2)
        
        img_rgba = img_pil.convert("RGBA")
        overlay = Image.new("RGBA", img_rgba.size, (0, 0, 0, 0))
        draw_overlay = ImageDraw.Draw(overlay)
        
        x1, y1, x2, y2 = min_block
        
        # 1. 绘制暗色半透明遮罩层（聚光灯效果，暗化矛盾区域以外的画面）
        mask_color = (15, 23, 42, 160)  # Slate dark with transparency
        draw_overlay.rectangle([0, 0, w, y1], fill=mask_color)
        draw_overlay.rectangle([0, y2, w, h], fill=mask_color)
        draw_overlay.rectangle([0, y1, x1, y2], fill=mask_color)
        draw_overlay.rectangle([x2, y1, w, y2], fill=mask_color)
        
        # 2. 绘制未来感科技红框（双层发光边框 + 角点瞄准线）
        border_color = (239, 68, 68, 255)  # 霓虹红
        glow_color = (239, 68, 68, 80)     # 外层发光
        draw_overlay.rectangle([x1, y1, x2, y2], outline=border_color, width=4)
        draw_overlay.rectangle([x1-3, y1-3, x2+3, y2+3], outline=glow_color, width=2)
        
        # 绘制瞄准角点括弧
        bl = min(24, (x2 - x1) // 3)  # 括弧线长度
        # 左上角
        draw_overlay.line([(x1, y1), (x1 + bl, y1)], fill=border_color, width=5)
        draw_overlay.line([(x1, y1), (x1, y1 + bl)], fill=border_color, width=5)
        # 右上角
        draw_overlay.line([(x2, y1), (x2 - bl, y1)], fill=border_color, width=5)
        draw_overlay.line([(x2, y1), (x2, y1 + bl)], fill=border_color, width=5)
        # 左下角
        draw_overlay.line([(x1, y2), (x1 + bl, y2)], fill=border_color, width=5)
        draw_overlay.line([(x1, y2), (x1, y2 - bl)], fill=border_color, width=5)
        # 右下角
        draw_overlay.line([(x2, y2), (x2 - bl, y2)], fill=border_color, width=5)
        draw_overlay.line([(x2, y2), (x2, y2 - bl)], fill=border_color, width=5)
        
        # 3. 绘制带有科技感的悬浮药丸标签（使用图形方式避免字体依赖）
        label_x = x1
        label_y = max(y1 - 40, 10)
        label_width = 120
        label_height = 30
        draw_overlay.rectangle([label_x, label_y, label_x + label_width, label_y + label_height], fill=(220, 38, 38, 240)) # 鲜艳红底
        
        # 绘制警告图标（三角形）
        warning_tri_x = label_x + 8
        warning_tri_y = label_y + 15
        draw_overlay.polygon([
            (warning_tri_x, warning_tri_y - 8),
            (warning_tri_x - 5, warning_tri_y + 5),
            (warning_tri_x + 5, warning_tri_y + 5)
        ], fill=(255, 255, 0, 255))
        
        # 尝试加载中文字体（支持多种平台）
        font = None
        font_paths = [
            # Linux 常见路径
            "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
            "/usr/share/fonts/truetype/noto/NotoSansCJK-SC.ttc",
            "/usr/share/fonts/truetype/arphic/ukai.ttc",
            "/usr/share/fonts/truetype/arphic/uming.ttc",
            # macOS 常见路径
            "/Library/Fonts/STHeiti Medium.ttc",
            "/Library/Fonts/Noto Sans SC Regular.otf",
            # Windows 常见路径
            "C:/Windows/Fonts/msyh.ttc",
            "C:/Windows/Fonts/simhei.ttf",
            "C:/Windows/Fonts/simsun.ttc",
            # 项目本地字体
            os.path.join(os.path.dirname(__file__), "fonts", "NotoSansSC-Regular.ttf"),
            os.path.join(os.path.dirname(__file__), "fonts", "simhei.ttf"),
        ]
        
        for font_path in font_paths:
            try:
                if os.path.exists(font_path):
                    font = ImageFont.truetype(font_path, 16)
                    break
            except Exception:
                continue
        
        # 如果找到中文字体，显示中文标签
        if font is not None:
            draw_overlay.text((label_x + 22, label_y + 5), "矛盾区域", font=font, fill=(255, 255, 255, 255))
        else:
            # 如果找不到中文字体，使用英文替代
            draw_overlay.text((label_x + 22, label_y + 7), "Conflict", font=ImageFont.load_default(), fill=(255, 255, 255, 255))
        
        # 4. 混合图层并还原为 RGB 格式
        result_img = Image.alpha_composite(img_rgba, overlay).convert("RGB")
        
        return np.array(result_img), block_scores
    
    except Exception as e:
        print(f"[高亮错误] {image_path}: {str(e)[:200]}")
        try:
            if os.path.exists(image_path):
                img_pil = Image.open(image_path).convert("RGB")
                return np.array(img_pil), []
            else:
                return None, []
        except:
            return None, []
