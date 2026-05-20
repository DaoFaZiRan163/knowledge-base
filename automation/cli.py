"""
FDE Knowledge Hub - Command Line Interface
统一的命令行工具，提供知识管理、学习跟踪、面试准备等功能
"""

import click
import os
import sys
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

# Windows GBK terminal doesn't support emoji; force UTF-8 output
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

console = Console()

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent
CONFIG_FILE = PROJECT_ROOT / ".env"

def load_config():
    """加载配置文件"""
    if not CONFIG_FILE.exists():
        console.print("[yellow]⚠️  配置文件不存在，请先复制 .env.example 为 .env[/yellow]")
        return None
    from dotenv import load_dotenv
    load_dotenv(CONFIG_FILE)
    return os.environ

@click.group()
@click.version_option(version="1.0.0", prog_name="fde-cli")
def cli():
    """FDE Knowledge Hub - Forward Deployed Engineer 专业知识管理系统"""
    pass

@cli.command()
@click.option('--category', '-c', help='知识分类')
@click.option('--difficulty', '-d', help='难度等级: beginner/intermediate/expert')
def ingest(category, difficulty):
    """摄取知识到知识库"""
    config = load_config()
    if not config:
        return

    from automation.knowledge_ingestion import FDEKnowledgeIngester

    console.print("[blue]📚 开始摄取知识到 FDE 知识库...[/blue]")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("初始化知识摄取器...", total=None)

        ingester = FDEKnowledgeIngester(config)

        progress.update(task, description="扫描知识源...")
        sources = ingester.scan_knowledge_sources(
            category=category,
            difficulty=difficulty
        )

        progress.update(task, description=f"发现 {len(sources)} 个知识源")

        for i, source in enumerate(sources, 1):
            progress.update(task, description=f"处理 [{i}/{len(sources)}] {source['name']}...")
            ingester.process_source(source)

    console.print("[green]✅ 知识摄取完成！[/green]")

@cli.command()
@click.option('--topic', '-t', help='学习主题')
@click.option('--hours', '-h', type=int, help='每周可用学习小时数')
def path(topic, hours):
    """生成个性化学习路径"""
    config = load_config()
    if not config:
        return

    from automation.learning_path_generator import FDELearningPathGenerator

    console.print("[blue]🎯 生成个性化 FDE 学习路径...[/blue]")

    generator = FDELearningPathGenerator(config)

    # 分析当前能力
    console.print("[yellow]📊 分析当前能力水平...[/yellow]")
    current_skills = generator.analyze_current_skills()

    # 生成学习路径
    console.print("[yellow]🛣️  生成学习路径...[/yellow]")
    learning_path = generator.generate_personalized_path(
        topic=topic,
        available_hours_per_week=hours or 10
    )

    # 展示学习路径
    display_learning_path(learning_path)

@cli.command()
@click.option('--role', '-r', default='FDE', help='面试角色')
@click.option('--difficulty', '-d', default='senior', help='难度等级')
@click.option('--count', '-n', type=int, default=5, help='题目数量')
def interview(role, difficulty, count):
    """模拟面试练习"""
    config = load_config()
    if not config:
        return

    from automation.interview_prep import FDEMockInterview

    console.print(f"[blue]🎤 开始 {role} 面试模拟 ({difficulty} 级别)[/blue]")

    interviewer = FDEMockInterview(config, role=role, level=difficulty)

    # 生成面试题
    questions = interviewer.generate_interview_questions(count=count)

    # 展示面试题
    display_interview_questions(questions)

    # 提供练习模式
    if console.input("\n[yellow]是否开始练习模式？(y/n): [/yellow]").lower() == 'y':
        practice_mode(interviewer, questions)

@cli.command()
@click.option('--review-type', '-r',
              type=click.Choice(['daily', 'weekly', 'adaptive']),
              default='adaptive',
              help='复习类型')
def review(review_type):
    """智能复习提醒"""
    config = load_config()
    if not config:
        return

    from automation.spaced_repetition import SpacedRepetitionSystem

    console.print(f"[blue]🔄 {review_type} 复习提醒[/blue]")

    srs = SpacedRepetitionSystem(config)

    if review_type == 'adaptive':
        due_items = srs.get_adaptive_review_items()
    elif review_type == 'daily':
        due_items = srs.get_daily_review_items()
    else:
        due_items = srs.get_weekly_review_items()

    if due_items:
        display_review_items(due_items)
    else:
        console.print("[green]🎉 没有需要复习的内容！[/green]")

@cli.command()
@click.option('--paste', '-p', is_flag=True, help='从剪贴板粘贴内容')
@click.option('--url', '-u', help='从URL抓取内容')
@click.option('--file', '-f', help='从文件读取内容')
@click.option('--category', '-c', help='指定分类')
@click.option('--difficulty', '-d', help='指定难度')
@click.option('--type', '-t', default='note', help='笔记类型')
@click.option('--tags', multiple=True, help='添加标签')
@click.option('--title', help='指定标题')
def web(paste, url, file, category, difficulty, type, tags, title):
    """从网页/文本摄入知识"""
    from automation.web_ingest import ingest as web_ingest

    ctx = click.Context(web_ingest)
    ctx.params = {
        'paste': paste, 'url': url, 'file': file,
        'category': category, 'difficulty': difficulty,
        'type': type, 'tags': tags, 'title': title
    }
    ctx.invoke(web_ingest)

@cli.command()
def sync():
    """同步 Obsidian 和 NotebookLM"""
    config = load_config()
    if not config:
        return

    from integration.obsidian_notebooklm_sync import ObsidianNotebookLMSync

    console.print("[blue]🔄 同步 Obsidian 到 NotebookLM...[/blue]")

    syncer = ObsidianNotebookLMSync(config)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("扫描 Obsidian 笔记...", total=None)

        # 扫描核心文档
        core_docs = syncer.scan_core_documents()
        progress.update(task, description=f"发现 {len(core_docs)} 个核心文档")

        # 格式转换和上传
        for i, doc in enumerate(core_docs, 1):
            progress.update(task, description=f"同步 [{i}/{len(core_docs)}] {doc['title']}...")
            syncer.sync_document(doc)

    console.print("[green]✅ 同步完成！[/green]")

@cli.command()
def status():
    """显示系统状态"""
    config = load_config()

    console.print("[blue]📊 FDE Knowledge Hub 系统状态[/blue]\n")

    # 基本信息表格
    status_table = Table(title="项目状态")
    status_table.add_column("项目", style="cyan")
    status_table.add_column("状态", style="green")
    status_table.add_column("详细信息")

    status_table.add_row(
        "Obsidian Vault",
        "✅ 正常" if (PROJECT_ROOT / ".obsidian").exists() else "❌ 未配置",
        str(PROJECT_ROOT)
    )

    status_table.add_row(
        "配置文件",
        "✅ 已加载" if config else "❌ 未配置",
        str(CONFIG_FILE)
    )

    # 统计信息
    from automation.knowledge_stats import KnowledgeStats
    stats_obj = KnowledgeStats(PROJECT_ROOT)
    overview = stats_obj.get_overview_stats()

    status_table.add_row(
        "知识条目",
        f"📚 {overview['total_notes']}",
        f"核心: {overview['core_notes']} | 模板: {overview['template_notes']}"
    )

    status_table.add_row(
        "知识关联",
        f"🔗 {overview['total_links']}",
        f"平均每篇: {overview['avg_links_per_note']:.1f} 个链接"
    )

    console.print(status_table)

    # 学习进度
    if config:
        console.print("\n[blue]📈 学习进度[/blue]")
        progress_table = Table()
        progress_table.add_column("阶段", style="cyan")
        progress_table.add_column("进度", style="yellow")
        progress_table.add_column("状态")

        phases = [
            ("技术基础", "15%", "进行中"),
            ("AI工程化", "5%", "刚开始"),
            ("产品业务", "0%", "未开始"),
            ("咨询交付", "0%", "未开始"),
        ]

        for phase, progress, status_text in phases:
            progress_table.add_row(phase, progress, status_text)

        console.print(progress_table)

# 辅助函数
def display_learning_path(learning_path):
    """展示学习路径"""
    summary = learning_path.get('summary', {})
    if summary:
        console.print(f"\n总周期 [yellow]{summary.get('total_weeks', '?')}[/yellow] 周 · "
                      f"总学时 [yellow]{summary.get('total_hours', '?')}[/yellow] 小时 · "
                      f"待学模块 [yellow]{summary.get('remaining_modules', '?')}[/yellow] 个")

    for phase_name, modules in learning_path.get('phases', {}).items():
        console.print(f"\n[bold cyan]{phase_name}[/bold cyan]")
        for i, module in enumerate(modules, 1):
            duration = module.get('adjusted_duration_weeks', module.get('duration_weeks', '?'))
            prereqs = module.get('prerequisites', [])
            console.print(f"  {i}. {module['title']} ({duration} 周)")
            console.print(f"     前置: {', '.join(prereqs) if prereqs else '无'}")

def display_interview_questions(questions):
    """展示面试题（questions 为 InterviewQuestion dataclass 列表）"""
    for i, q in enumerate(questions, 1):
        console.print(f"\n[bold yellow]问题 {i}: {q.question}[/bold yellow]")
        console.print(f"[dim]分类: {q.category} | 难度: {q.difficulty} | 类型: {q.type}[/dim]")
        if q.hint:
            console.print(f"[blue]提示: {q.hint}[/blue]")

def practice_mode(interviewer, questions):
    """练习模式（questions 为 InterviewQuestion dataclass 列表）"""
    console.print("\n[green]🎯 练习模式 - 请回答以下问题:[/green]\n")

    for i, q in enumerate(questions, 1):
        console.print(f"[bold]问题 {i}: {q.question}[/bold]")
        console.print("[dim]按 Enter 显示参考答案...[/dim]")
        console.input()

        console.print(f"[blue]参考答案:[/blue]")
        console.print(q.reference_answer)

        if i < len(questions):
            console.input("\n[dim]按 Enter 继续...[/dim]")

def display_review_items(items):
    """展示复习项目"""
    console.print(f"\n[green]📝 今日复习: {len(items)} 个项目[/green]\n")

    for i, item in enumerate(items, 1):
        # next_review 仅 due 模式返回，adaptive 模式部分条目用 scheduled_time 替代
        next_rev = item.get('next_review') or item.get('scheduled_time', '-')
        console.print(f"{i}. [bold]{item['title']}[/bold]")
        console.print(f"   [dim]上次复习: {item.get('last_review', '-')} | 推荐复习: {next_rev}[/dim]")
        console.print(f"   [blue]重要性: {item['importance']} | 遗忘指数: {item['forgetting_index']:.2f}[/blue]\n")

def main():
    """主函数"""
    cli()

if __name__ == '__main__':
    main()