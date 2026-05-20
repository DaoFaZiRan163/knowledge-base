"""
FDE Knowledge Hub - Knowledge Statistics Module
知识统计分析模块，提供知识库状态和学习进度的统计功能
"""

import json
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime
from collections import Counter
import re


class KnowledgeStats:
    """知识统计器"""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.core_path = project_root / "core"
        self.templates_path = project_root / "templates"
        self.docs_path = project_root / "docs"

    def get_overview_stats(self) -> Dict[str, Any]:
        """获取知识库概览统计"""
        # 扫描所有 Markdown 文件
        all_notes = list(self.project_root.rglob("*.md"))

        # 统计不同类型的笔记
        note_types = Counter()
        note_categories = Counter()
        note_difficulties = Counter()

        total_links = 0
        total_words = 0

        for note_file in all_notes:
            # 跳过系统文件
            if '.obsidian' in str(note_file) or '__pycache__' in str(note_file):
                continue

            # 解析 YAML front matter
            metadata = self._parse_frontmatter(note_file)
            if metadata:
                note_type = metadata.get('type', 'unknown')
                note_types[note_type] += 1

                categories = metadata.get('category', [])
                for category in categories:
                    note_categories[category] += 1

                difficulty = metadata.get('difficulty')
                if difficulty:
                    note_difficulties[difficulty] += 1

            # 统计链接数量
            content = self._read_note_content(note_file)
            links = re.findall(r'\[\[.*?\]\]', content)
            total_links += len(links)

            # 统计字数
            # 移除 Markdown 语法
            clean_text = re.sub(r'[#*`\[\]]', '', content)
            words = len(clean_text.split())
            total_words += words

        # 计算平均值
        avg_links_per_note = total_links / len(all_notes) if all_notes else 0

        return {
            'total_notes': len(all_notes),
            'total_links': total_links,
            'total_words': total_words,
            'avg_links_per_note': avg_links_per_note,
            'note_types': dict(note_types),
            'note_categories': dict(note_categories),
            'note_difficulties': dict(note_difficulties),
            'core_notes': len(list(self.core_path.rglob("*.md"))),
            'template_notes': len(list(self.templates_path.rglob("*.md"))),
            'generated_at': datetime.now().isoformat()
        }

    def get_learning_progress(self) -> Dict[str, Any]:
        """获取学习进度统计"""
        progress_file = self.docs_path / "learning_progress.json"

        if not progress_file.exists():
            return {
                'error': '学习进度文件不存在',
                'suggestion': '请先使用 fde-cli path 生成学习路径'
            }

        with open(progress_file, 'r', encoding='utf-8') as f:
            progress_data = json.load(f)

        # 解析当前学习路径
        current_path_file = self.docs_path / "current_learning_path.json"
        if current_path_file.exists():
            with open(current_path_file, 'r', encoding='utf-8') as f:
                current_path = json.load(f)
        else:
            current_path = {}

        # 计算进度
        completed_modules = set(progress_data.get('completed_modules', {}).keys())
        total_modules = len(current_path.get('phases', {}))

        if 'summary' in current_path:
            total_modules = current_path['summary'].get('remaining_modules', total_modules)
            completed_count = current_path['summary'].get('completed_modules', len(completed_modules))
        else:
            completed_count = len(completed_modules)

        progress_rate = completed_count / total_modules if total_modules > 0 else 0

        # 按分类统计
        category_progress = {}
        for phase_name, phase_modules in current_path.get('phases', {}).items():
            phase_category = self._extract_category_from_phase(phase_name)

            completed_in_phase = sum(
                1 for module in phase_modules
                if module['id'] in completed_modules
            )

            category_progress[phase_category] = {
                'total': len(phase_modules),
                'completed': completed_in_phase,
                'progress_rate': completed_in_phase / len(phase_modules) if phase_modules else 0
            }

        # 学习时间统计
        total_study_hours = 0
        for module_id, module_data in progress_data.get('completed_modules', {}).items():
            # 这里可以根据实际学习时间计算
            total_study_hours += 10  # 假设每个模块10小时

        return {
            'total_modules': total_modules,
            'completed_modules': completed_count,
            'remaining_modules': total_modules - completed_count,
            'progress_rate': progress_rate,
            'total_study_hours': total_study_hours,
            'category_progress': category_progress,
            'last_updated': progress_data.get('last_updated', 'unknown')
        }

    def get_interview_stats(self) -> Dict[str, Any]:
        """获取面试统计"""
        interview_reports_dir = self.docs_path / "interview_reports"

        if not interview_reports_dir.exists():
            return {
                'total_interviews': 0,
                'suggestion': '请先使用 fde-cli interview 进行面试练习'
            }

        # 获取所有面试报告
        report_files = list(interview_reports_dir.glob("*.json"))

        total_interviews = len(report_files)

        if total_interviews == 0:
            return {
                'total_interviews': 0,
                'suggestion': '请先使用 fde-cli interview 进行面试练习'
            }

        # 分析面试表现
        all_scores = []
        category_scores = {}

        for report_file in report_files:
            try:
                with open(report_file, 'r', encoding='utf-8') as f:
                    report_data = json.load(f)

                if 'overall_performance' in report_data:
                    overall_score = report_data['overall_performance'].get('total', 0)
                    all_scores.append(overall_score)

                    # 按分类统计
                    for category, score in report_data['overall_performance'].items():
                        if category != 'total':
                            if category not in category_scores:
                                category_scores[category] = []
                            category_scores[category].append(score)

            except Exception as e:
                print(f"Error reading {report_file}: {e}")
                continue

        # 计算统计数据
        if all_scores:
            avg_score = sum(all_scores) / len(all_scores)
            max_score = max(all_scores)
            min_score = min(all_scores)

            # 计算进步趋势
            progress_trend = self._calculate_progress_trend(all_scores)
        else:
            avg_score = max_score = min_score = 0
            progress_trend = 'stable'

        # 按分类平均分
        category_averages = {}
        for category, scores in category_scores.items():
            category_averages[category] = sum(scores) / len(scores)

        return {
            'total_interviews': total_interviews,
            'average_score': avg_score,
            'max_score': max_score,
            'min_score': min_score,
            'progress_trend': progress_trend,
            'category_averages': category_averages,
            'recent_performance': all_scores[-5:] if len(all_scores) >= 5 else all_scores
        }

    def get_knowledge_network_stats(self) -> Dict[str, Any]:
        """获取知识网络统计"""
        all_notes = list(self.project_root.rglob("*.md"))

        network_stats = {
            'total_nodes': 0,  # 笔记数量
            'total_edges': 0,  # 链接数量
            'connected_components': 0,  # 连通分量
            'avg_connections': 0,  # 平均连接数
            'most_connected_notes': [],  # 连接最多的笔记
            'isolated_notes': [],  # 孤立笔记
            'knowledge_density': 0  # 知识密度
        }

        if not all_notes:
            return network_stats

        network_stats['total_nodes'] = len(all_notes)

        # 统计连接关系
        note_connections = Counter()

        for note_file in all_notes:
            if '.obsidian' in str(note_file) or '__pycache__' in str(note_file):
                continue

            note_name = note_file.stem
            content = self._read_note_content(note_file)

            # 找出所有链接
            links = re.findall(r'\[\[([^\]]+)\]\]', content)

            for linked_note in links:
                note_connections[note_name] += 1

            network_stats['total_edges'] += len(links)

        # 计算平均连接数
        if network_stats['total_nodes'] > 0:
            network_stats['avg_connections'] = network_stats['total_edges'] / network_stats['total_nodes']

        # 找出连接最多的笔记
        most_common = note_connections.most_common(10)
        network_stats['most_connected_notes'] = [
            {'note': note, 'connections': count}
            for note, count in most_common
        ]

        # 找出孤立笔记
        all_note_names = {note.stem for note in all_notes
                          if '.obsidian' not in str(note) and '__pycache__' not in str(note)}

        connected_notes = set(note_connections.keys())
        isolated_notes = all_note_names - connected_notes
        network_stats['isolated_notes'] = list(isolated_notes)

        # 计算知识密度（边的数量除以可能的最大边数）
        max_possible_edges = network_stats['total_nodes'] * (network_stats['total_nodes'] - 1) / 2
        network_stats['knowledge_density'] = network_stats['total_edges'] / max_possible_edges if max_possible_edges > 0 else 0

        return network_stats

    def generate_comprehensive_report(self) -> Dict[str, Any]:
        """生成综合报告"""
        return {
            'knowledge_overview': self.get_overview_stats(),
            'learning_progress': self.get_learning_progress(),
            'interview_performance': self.get_interview_stats(),
            'knowledge_network': self.get_knowledge_network_stats(),
            'generated_at': datetime.now().isoformat()
        }

    def display_stats(self, stats: Dict[str, Any], format: str = 'text'):
        """显示统计信息"""
        if format == 'text':
            self._display_text_stats(stats)
        elif format == 'json':
            print(json.dumps(stats, ensure_ascii=False, indent=2))
        elif format == 'markdown':
            self._display_markdown_stats(stats)

    def _display_text_stats(self, stats: Dict[str, Any]):
        """以文本格式显示统计"""
        print("📊 FDE Knowledge Hub 统计报告")
        print("=" * 50)

        # 知识概览
        if 'knowledge_overview' in stats:
            overview = stats['knowledge_overview']
            print("\n📚 知识库概览:")
            print(f"  总笔记数: {overview['total_notes']}")
            print(f"  总链接数: {overview['total_links']}")
            print(f"  总字数: {overview['total_words']:,}")
            print(f"  平均链接/笔记: {overview['avg_links_per_note']:.1f}")

            print(f"\n  核心笔记: {overview['core_notes']}")
            print(f"  模板笔记: {overview['template_notes']}")

            if overview['note_types']:
                print(f"\n  笔记类型:")
                for note_type, count in overview['note_types'].items():
                    print(f"    {note_type}: {count}")

            if overview['note_difficulties']:
                print(f"\n  难度分布:")
                for difficulty, count in overview['note_difficulties'].items():
                    print(f"    {difficulty}: {count}")

        # 学习进度
        if 'learning_progress' in stats and 'error' not in stats['learning_progress']:
            progress = stats['learning_progress']
            print(f"\n📈 学习进度:")
            print(f"  总模块数: {progress['total_modules']}")
            print(f"  已完成: {progress['completed_modules']}")
            print(f"  剩余: {progress['remaining_modules']}")
            print(f"  进度: {progress['progress_rate']:.1%}")
            print(f"  学习时长: {progress['total_study_hours']} 小时")

        # 面试表现
        if 'interview_performance' in stats and stats['interview_performance']['total_interviews'] > 0:
            interview = stats['interview_performance']
            print(f"\n🎤 面试表现:")
            print(f"  总面试次数: {interview['total_interviews']}")
            print(f"  平均分数: {interview['average_score']:.1f}/10")
            print(f"  最高分: {interview['max_score']:.1f}/10")
            print(f"  最低分: {interview['min_score']:.1f}/10")
            print(f"  进步趋势: {interview['progress_trend']}")

            if interview['category_averages']:
                print(f"\n  各维度平均分:")
                for category, avg_score in interview['category_averages'].items():
                    print(f"    {category}: {avg_score:.1f}/10")

        # 知识网络
        if 'knowledge_network' in stats:
            network = stats['knowledge_network']
            print(f"\n🔗 知识网络:")
            print(f"  节点数: {network['total_nodes']}")
            print(f"  边数: {network['total_edges']}")
            print(f"  平均连接数: {network['avg_connections']:.1f}")
            print(f"  知识密度: {network['knowledge_density']:.3f}")

            if network['isolated_notes']:
                print(f"  孤立笔记: {len(network['isolated_notes'])}")

        print("\n" + "=" * 50)
        print(f"生成时间: {stats.get('generated_at', 'unknown')}")

    def _display_markdown_stats(self, stats: Dict[str, Any]):
        """以 Markdown 格式显示统计"""
        md_content = "# FDE Knowledge Hub 统计报告\n\n"

        # 知识概览
        if 'knowledge_overview' in stats:
            overview = stats['knowledge_overview']
            md_content += "## 📚 知识库概览\n\n"
            md_content += f"- **总笔记数**: {overview['total_notes']}\n"
            md_content += f"- **总链接数**: {overview['total_links']}\n"
            md_content += f"- **总字数**: {overview['total_words']:,}\n"
            md_content += f"- **平均链接/笔记**: {overview['avg_links_per_note']:.1f}\n"
            md_content += f"- **核心笔记**: {overview['core_notes']}\n"
            md_content += f"- **模板笔记**: {overview['template_notes']}\n\n"

        # 学习进度
        if 'learning_progress' in stats and 'error' not in stats['learning_progress']:
            progress = stats['learning_progress']
            md_content += "## 📈 学习进度\n\n"
            md_content += f"- **总模块数**: {progress['total_modules']}\n"
            md_content += f"- **已完成**: {progress['completed_modules']}\n"
            md_content += f"- **剩余**: {progress['remaining_modules']}\n"
            md_content += f"- **进度**: {progress['progress_rate']:.1%}\n"
            md_content += f"- **学习时长**: {progress['total_study_hours']} 小时\n\n"

        # 面试表现
        if 'interview_performance' in stats and stats['interview_performance']['total_interviews'] > 0:
            interview = stats['interview_performance']
            md_content += "## 🎤 面试表现\n\n"
            md_content += f"- **总面试次数**: {interview['total_interviews']}\n"
            md_content += f"- **平均分数**: {interview['average_score']:.1f}/10\n"
            md_content += f"- **最高分**: {interview['max_score']:.1f}/10\n"
            md_content += f"- **最低分**: {interview['min_score']:.1f}/10\n"
            md_content += f"- **进步趋势**: {interview['progress_trend']}\n\n"

        # 知识网络
        if 'knowledge_network' in stats:
            network = stats['knowledge_network']
            md_content += "## 🔗 知识网络\n\n"
            md_content += f"- **节点数**: {network['total_nodes']}\n"
            md_content += f"- **边数**: {network['total_edges']}\n"
            md_content += f"- **平均连接数**: {network['avg_connections']:.1f}\n"
            md_content += f"- **知识密度**: {network['knowledge_density']:.3f}\n\n"

        md_content += f"---\n\n*生成时间: {stats.get('generated_at', 'unknown')}*"

        print(md_content)

    # 辅助方法
    def _parse_frontmatter(self, note_file: Path) -> Dict[str, Any]:
        """解析 YAML front matter"""
        try:
            with open(note_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # 提取 YAML front matter
            yaml_match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
            if yaml_match:
                import yaml
                yaml_data = yaml.safe_load(yaml_match.group(1))
                if isinstance(yaml_data, dict):
                    return yaml_data
        except Exception as e:
            pass

        return {}

    def _read_note_content(self, note_file: Path) -> str:
        """读取笔记内容"""
        try:
            with open(note_file, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            return ""

    def _extract_category_from_phase(self, phase_name: str) -> str:
        """从阶段名称提取分类"""
        if 'Foundation' in phase_name or '基础' in phase_name:
            return '技术基础'
        elif 'AI' in phase_name or 'AI工程化' in phase_name:
            return 'AI工程化'
        elif 'Product' in phase_name or '产品业务' in phase_name:
            return '产品业务'
        elif 'Consulting' in phase_name or '咨询交付' in phase_name:
            return '咨询交付'
        else:
            return '其他'

    def _calculate_progress_trend(self, scores: List[float]) -> str:
        """计算进步趋势"""
        if len(scores) < 3:
            return 'insufficient_data'

        # 计算线性回归斜率
        x = list(range(len(scores)))
        y = scores

        n = len(x)
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(xi * yi for xi, yi in zip(x, y))
        sum_x_squared = sum(xi * xi for xi in x)

        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x_squared - sum_x ** 2)

        if slope > 0.5:
            return 'improving_rapidly'
        elif slope > 0.1:
            return 'improving_steadily'
        elif slope > -0.1:
            return 'stable'
        elif slope > -0.5:
            return 'declining_slowly'
        else:
            return 'declining_rapidly'


def main():
    """主函数，用于命令行调用"""
    import argparse

    parser = argparse.ArgumentParser(description='FDE 知识统计系统')
    parser.add_argument('--format', '-f', choices=['text', 'json', 'markdown'],
                       default='text', help='输出格式')
    parser.add_argument('--report', '-r', action='store_true',
                       help='生成综合报告')
    parser.add_argument('--overview', '-o', action='store_true',
                       help='显示知识概览')
    parser.add_argument('--progress', '-p', action='store_true',
                       help='显示学习进度')
    parser.add_argument('--interview', '-i', action='store_true',
                       help='显示面试表现')
    parser.add_argument('--network', '-n', action='store_true',
                       help='显示知识网络统计')

    args = parser.parse_args()

    # 获取项目根目录
    project_root = Path(__file__).parent.parent
    stats = KnowledgeStats(project_root)

    if args.report:
        # 生成综合报告
        comprehensive_stats = stats.generate_comprehensive_report()
        stats.display_stats(comprehensive_stats, args.format)
    elif args.overview:
        # 显示知识概览
        overview_stats = stats.get_overview_stats()
        stats.display_stats({'knowledge_overview': overview_stats}, args.format)
    elif args.progress:
        # 显示学习进度
        progress_stats = stats.get_learning_progress()
        stats.display_stats({'learning_progress': progress_stats}, args.format)
    elif args.interview:
        # 显示面试表现
        interview_stats = stats.get_interview_stats()
        stats.display_stats({'interview_performance': interview_stats}, args.format)
    elif args.network:
        # 显示知识网络统计
        network_stats = stats.get_knowledge_network_stats()
        stats.display_stats({'knowledge_network': network_stats}, args.format)
    else:
        # 默认显示所有统计
        all_stats = stats.generate_comprehensive_report()
        stats.display_stats(all_stats, args.format)


if __name__ == '__main__':
    main()