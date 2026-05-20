"""
FDE Knowledge Hub - Web Content Ingestion
网页/文本内容摄入模块，支持粘贴和URL抓取两种方式
"""

import os
import re
import sys
import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict

import click

# Windows GBK terminal encoding fix
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# 确保项目路径可用
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# 知识分类映射
CATEGORY_MAP = {
    'foundation': {
        'name': '技术基础',
        'keywords': ['编程', '算法', '数据结构', '系统设计', '数据库', '网络', '操作系统', '编程基础']
    },
    'ai-engineering': {
        'name': 'AI工程化',
        'keywords': ['机器学习', '深度学习', 'LLM', '大模型', 'RAG', 'Agent', 'AI', '神经网络', 'NLP', 'CV', 'AI工程']
    },
    'product-business': {
        'name': '产品业务',
        'keywords': ['产品', '增长', '运营', '数据分析', '商业', '市场', '用户研究', '产品设计']
    },
    'consulting-delivery': {
        'name': '咨询交付',
        'keywords': ['咨询', '项目管理', '客户管理', '交付', '变革管理', 'ROI', 'FDE']
    }
}

# 难度关键词
DIFFICULTY_KEYWORDS = {
    'beginner': ['入门', '基础', '初学', '新手', 'beginner', 'introduction', 'tutorial'],
    'expert': ['高级', '进阶', '专家', '深入', 'expert', 'advanced', 'deep']
}


def extract_frontmatter(content: str) -> tuple[Dict, str]:
    """从markdown内容中提取并解析front matter"""
    frontmatter = {}
    if content.startswith('---'):
        end = content.find('\n---', 4)
        if end != -1:
            fm_text = content[4:end]
            content = content[end+4:].lstrip('\n')
            for line in fm_text.split('\n'):
                if ':' in line:
                    key, val = line.split(':', 1)
                    val = val.strip().strip('"').strip("'")
                    if val.startswith('['):
                        try:
                            frontmatter[key.strip()] = json.loads(val)
                        except:
                            frontmatter[key.strip()] = [v.strip().strip('"').strip("'") for v in val[1:-1].split(',')]
                    else:
                        frontmatter[key.strip()] = val
    return frontmatter, content


def generate_frontmatter(category: str, difficulty: str, tags: List[str], note_type: str = 'note') -> Dict:
    """生成标准化的front matter"""
    return {
        'type': note_type,
        'category': [category],
        'difficulty': difficulty,
        'tags': tags,
        'source': 'web',
        'created_date': datetime.now().strftime('%Y-%m-%d'),
        'updated_date': datetime.now().strftime('%Y-%m-%d')
    }


def format_frontmatter(fm: Dict) -> str:
    """格式化为markdown front matter字符串"""
    lines = ['---']
    for key, val in fm.items():
        if isinstance(val, list):
            lines.append(f'{key}: {json.dumps(val, ensure_ascii=False)}')
        else:
            lines.append(f'{key}: {val}')
    lines.append('---')
    return '\n'.join(lines)


def detect_category(content: str) -> str:
    """根据内容关键词检测分类"""
    content_lower = content.lower()

    for cat_id, cat_info in CATEGORY_MAP.items():
        for kw in cat_info['keywords']:
            if kw.lower() in content_lower:
                return cat_id

    # 默认返回 foundation
    return 'foundation'


def detect_difficulty(content: str) -> str:
    """根据内容检测难度"""
    content_lower = content.lower()

    for diff, keywords in DIFFICULTY_KEYWORDS.items():
        for kw in keywords:
            if kw.lower() in content_lower:
                return diff

    return 'intermediate'


def extract_title(content: str) -> str:
    """从内容中提取标题"""
    # 优先从 front matter 的 title 获取
    fm, body = extract_frontmatter(content)
    if fm.get('title'):
        return fm['title']

    # 从第一个 # 标题获取
    h1_match = re.search(r'^#\s+(.+)$', body, re.MULTILINE)
    if h1_match:
        return h1_match.group(1).strip()

    # 从文件名或URL提取
    return '未命名'


def clean_content(content: str) -> str:
    """清理内容，移除多余的空白和无效字符"""
    lines = content.split('\n')
    cleaned = []
    prev_empty = False

    for line in lines:
        # 跳过 front matter 重复部分
        if line.strip() == '---' and len(cleaned) > 5:
            continue
        # 移除多余空白行
        if not line.strip():
            if not prev_empty:
                cleaned.append('')
                prev_empty = True
        else:
            cleaned.append(line)
            prev_empty = False

    # 清理到 content
    while cleaned and not cleaned[0]:
        cleaned.pop(0)
    while cleaned and not cleaned[-1]:
        cleaned.pop()

    return '\n'.join(cleaned)


def generate_file_path(title: str, category: str) -> Path:
    """生成标准化的文件路径"""
    # 规范化标题作为文件名
    safe_title = re.sub(r'[<>:"/\\|?*\[\]]', '', title)
    safe_title = re.sub(r'\s+', '-', safe_title.strip())
    safe_title = safe_title[:50]  # 限制长度

    category_path = PROJECT_ROOT / 'core' / category

    # 确保目录存在
    category_path.mkdir(parents=True, exist_ok=True)

    # 生成带时间戳的文件名避免重复
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    filename = f"{safe_title}-{timestamp}.md"

    return category_path / filename


def parse_pasted_content(content: str) -> Dict:
    """解析粘贴的内容"""
    # 提取 front matter
    fm, body = extract_frontmatter(content)

    # 检测分类和难度
    if 'category' not in fm or not fm['category']:
        fm['category'] = [detect_category(body)]

    if 'difficulty' not in fm or not fm['difficulty']:
        fm['difficulty'] = detect_difficulty(body)

    if 'tags' not in fm:
        fm['tags'] = []

    # 清理内容
    body = clean_content(body)

    # 提取标题
    title = extract_title(content)

    return {
        'title': title,
        'content': body,
        'frontmatter': fm
    }


def save_note(parsed: Dict) -> Path:
    """保存笔记到文件"""
    fm = parsed['frontmatter']
    content = parsed['content']

    # 合成完整内容
    full_content = format_frontmatter(fm) + '\n\n' + content

    # 生成文件路径
    filepath = generate_file_path(parsed['title'], fm['category'][0])

    # 写入文件
    filepath.write_text(full_content, encoding='utf-8')

    return filepath


def parse_url(url: str) -> Dict:
    """解析URL获取内容"""
    try:
        import httpx

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        resp = httpx.get(url, headers=headers, timeout=30)
        resp.raise_for_status()

        # 尝试提取文本内容
        html = resp.text

        # 简单提取：移除 script 和 style 标签
        html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
        html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)

        # 将 HTML 转换为 markdown（简化处理）
        text = re.sub(r'<h[1-6][^>]*>', '\n## ', html)
        text = re.sub(r'</h[1-6]>', '\n', text)
        text = re.sub(r'<p[^>]*>', '\n', text)
        text = re.sub(r'</p>', '\n', text)
        text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)
        text = re.sub(r'<[^>]+>', '', text)
        text = re.sub(r'\n+', '\n', text)
        text = text.strip()

        return {
            'title': '',
            'content': text,
            'url': url
        }

    except Exception as e:
        return {'error': str(e), 'url': url}


@click.command()
@click.option('--paste', '-p', is_flag=True, help='从剪贴板粘贴内容')
@click.option('--url', '-u', help='从URL抓取内容')
@click.option('--file', '-f', help='从文件读取内容')
@click.option('--category', '-c', help='指定分类 (foundation/ai-engineering/product-business/consulting-delivery)')
@click.option('--difficulty', '-d', help='指定难度 (beginner/intermediate/expert)')
@click.option('--type', '-t', default='note', help='笔记类型 (note/concept/paper)')
@click.option('--tags', multiple=True, help='添加标签')
@click.option('--title', help='指定标题')
def ingest(paste, url, file, category, difficulty, type, tags, title):
    """
    网页/文本内容摄入到 FDE 知识库

    用法:
      # 粘贴内容
      python -m automation.web_ingest --paste

      # 从URL抓取
      python -m automation.web_ingest --url "https://example.com/article"

      # 从文件读取
      python -m automation.web_ingest --file content.md
    """
    print("📥 FDE Knowledge Hub - Web Ingestion")
    print("=" * 50)

    content = None
    source = None

    if paste:
        # 从剪贴板读取
        try:
            import pyperclip
            content = pyperclip.paste()
            source = 'clipboard'
            print("✓ 已从剪贴板读取内容")
        except ImportError:
            print("⚠️ 需要安装 pyperclip: pip install pyperclip")
            print("  请手动将内容保存到文件后使用 --file 参数")
            return
        except Exception as e:
            print(f"⚠️ 读取剪贴板失败: {e}")
            return

    elif url:
        print(f"🔗 正在抓取: {url}")
        result = parse_url(url)
        if 'error' in result:
            print(f"❌ 抓取失败: {result['error']}")
            return
        content = result['content']
        source = f'url:{url}'
        print("✓ 内容抓取成功")

    elif file:
        filepath = Path(file)
        if not filepath.exists():
            print(f"❌ 文件不存在: {file}")
            return
        content = filepath.read_text(encoding='utf-8')
        source = f'file:{file}'
        print(f"✓ 已从文件读取: {file}")

    else:
        print("❌ 请指定 --paste, --url 或 --file")
        print("  使用 --help 查看更多选项")
        return

    # 解析内容
    print("\n🔄 解析内容...")
    parsed = parse_pasted_content(content)

    # 应用用户指定的覆盖
    if category:
        parsed['frontmatter']['category'] = [category]
    if difficulty:
        parsed['frontmatter']['difficulty'] = difficulty
    if type:
        parsed['frontmatter']['type'] = type
    if tags:
        parsed['frontmatter']['tags'] = list(tags)
    if title:
        parsed['title'] = title

    # 显示解析结果
    print(f"\n📋 解析结果:")
    print(f"   标题: {parsed['title']}")
    print(f"   分类: {parsed['frontmatter']['category']}")
    print(f"   难度: {parsed['frontmatter']['difficulty']}")
    print(f"   类型: {parsed['frontmatter']['type']}")
    print(f"   标签: {parsed['frontmatter'].get('tags', [])}")

    # 保存
    print("\n💾 保存笔记...")
    try:
        filepath = save_note(parsed)
        print(f"✅ 笔记已保存: {filepath}")
        print(f"   源: {source}")
        print(f"   字符数: {len(content)}")
    except Exception as e:
        print(f"❌ 保存失败: {e}")
        raise


if __name__ == '__main__':
    ingest()