"""
FDE Knowledge Hub - Learning Path Generator
基于用户背景和目标，智能生成个性化学习路径
"""

import json
from typing import List, Dict, Any
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime, timedelta
import networkx as nx

# MiniMax 提供与 OpenAI Chat Completions 兼容的接口，通过 base_url 切换即可，
# 无需安装 anthropic 包。未配置 MiniMax 时可回退到原生 OpenAI。
try:
    from openai import OpenAI as _OpenAIClient
except ImportError:
    print("请安装依赖: pip install openai")


@dataclass
class LearningModule:
    """学习模块"""
    id: str
    title: str
    description: str
    category: str
    difficulty: str
    duration_weeks: int
    prerequisites: List[str]
    resources: List[Dict]
    projects: List[str]
    learning_objectives: List[str]


class FDELearningPathGenerator:
    """FDE 学习路径生成器"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.project_root = Path(__file__).parent.parent

        # ── AI 客户端初始化 ───────────────────────────────────────────
        # 优先使用 MiniMax；未配置时回退到 OpenAI（需在 .env 填 OPENAI_API_KEY）。
        # MiniMax Chat API 与 OpenAI Chat Completions 格式兼容，仅 base_url 不同。
        minimax_key = config.get('MINIMAX_API_KEY')
        if minimax_key:
            self._client = _OpenAIClient(
                api_key=minimax_key,
                base_url=config.get('MINIMAX_BASE_URL', 'https://api.minimax.chat/v1'),
            )
            self._chat_model = config.get('MINIMAX_CHAT_MODEL', 'MiniMax-Text-01')
        else:
            self._client = _OpenAIClient(api_key=config.get('OPENAI_API_KEY'))
            self._chat_model = 'gpt-4o-mini'

        # 加载预定义的学习模块
        self.learning_modules = self._load_learning_modules()

        # 构建知识依赖图
        self.knowledge_graph = self._build_knowledge_graph()

    def _load_learning_modules(self) -> Dict[str, LearningModule]:
        """加载学习模块"""
        modules_file = self.project_root / "docs" / "learning_modules.json"

        if modules_file.exists():
            with open(modules_file, 'r', encoding='utf-8') as f:
                modules_data = json.load(f)

            return {
                module_id: LearningModule(**module_data)
                for module_id, module_data in modules_data.items()
            }

        # 如果不存在，使用默认模块
        return self._get_default_learning_modules()

    def _get_default_learning_modules(self) -> Dict[str, LearningModule]:
        """获取默认学习模块"""
        return {
            # Phase 1: Foundation
            'programming_basics': LearningModule(
                id='programming_basics',
                title='编程基础与代码质量',
                description='掌握编程语言核心概念和代码质量标准',
                category='foundation',
                difficulty='beginner',
                duration_weeks=4,
                prerequisites=[],
                resources=[
                    {'type': 'book', 'title': '代码整洁之道', 'author': 'Robert Martin'},
                    {'type': 'book', 'title': '重构：改善既有代码的设计', 'author': 'Martin Fowler'},
                ],
                projects=['实现一个简单的文本处理工具', '重构遗留代码'],
                learning_objectives=['理解 SOLID 原则', '掌握重构技巧', '编写可测试代码']
            ),

            'system_design': LearningModule(
                id='system_design',
                title='系统设计原理',
                description='掌握分布式系统设计的基本原理',
                category='foundation',
                difficulty='intermediate',
                duration_weeks=3,
                prerequisites=['programming_basics'],
                resources=[
                    {'type': 'book', 'title': '设计数据密集型应用', 'author': 'Martin Kleppmann'},
                    {'type': 'online', 'title': 'System Design Primer', 'url': 'https://github.com/donnemartin/system-design-primer'},
                ],
                projects=['设计一个高可用 API 网关', '实现分布式缓存系统'],
                learning_objectives=['理解 CAP 定理', '掌握负载均衡策略', '设计容错系统']
            ),

            'database_optimization': LearningModule(
                id='database_optimization',
                title='数据库性能优化',
                description='掌握关系型数据库的设计和优化技巧',
                category='foundation',
                difficulty='intermediate',
                duration_weeks=3,
                prerequisites=['programming_basics'],
                resources=[
                    {'type': 'book', 'title': '高性能 MySQL', 'author': 'Baron Schwartz'},
                    {'type': 'book', 'title': 'SQL 反模式', 'author': 'Bill Karwin'},
                ],
                projects=['优化慢查询', '设计分库分表方案'],
                learning_objectives=['理解索引原理', '掌握查询优化', '设计数据库架构']
            ),

            # Phase 2: AI Engineering
            'ml_basics': LearningModule(
                id='ml_basics',
                title='机器学习基础',
                description='理解机器学习的基本概念和算法',
                category='ai-engineering',
                difficulty='intermediate',
                duration_weeks=4,
                prerequisites=['programming_basics', 'database_optimization'],
                resources=[
                    {'type': 'book', 'title': '机器学习', 'author': 'Tom Mitchell'},
                    {'type': 'course', 'title': 'Andrew Ng ML Specialization', 'platform': 'Coursera'},
                ],
                projects=['实现分类算法', '构建推荐系统原型'],
                learning_objectives=['理解 ML 流程', '掌握常见算法', '评估模型性能']
            ),

            'llm_engineering': LearningModule(
                id='llm_engineering',
                title='LLM 工程化实践',
                description='掌握大语言模型的工程化应用',
                category='ai-engineering',
                difficulty='advanced',
                duration_weeks=6,
                prerequisites=['ml_basics'],
                resources=[
                    {'type': 'book', 'title': 'Build an LLM from Scratch', 'author': 'Sebastian Raschka'},
                    {'type': 'book', 'title': 'AI Engineering', 'author': 'Chip Huyen'},
                ],
                projects=['实现 RAG 系统', '构建 Multi-Agent 应用'],
                learning_objectives=['理解 Transformer 架构', '掌握 RAG 技术', '实现 Agent 系统']
            ),

            'rag_systems': LearningModule(
                id='rag_systems',
                title='RAG 系统设计与优化',
                description='深入掌握检索增强生成技术',
                category='ai-engineering',
                difficulty='advanced',
                duration_weeks=4,
                prerequisites=['llm_engineering'],
                resources=[
                    {'type': 'paper', 'title': 'Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks'},
                    {'type': 'framework', 'title': 'LangChain', 'url': 'https://python.langchain.com/'},
                ],
                projects=['构建企业知识库', '优化检索质量'],
                learning_objectives=['掌握向量检索', '优化上下文构建', '设计混合检索策略']
            ),

            # Phase 3: Product & Business
            'product_thinking': LearningModule(
                id='product_thinking',
                title='产品思维与设计',
                description='理解产品设计原理和用户体验',
                category='product-business',
                difficulty='beginner',
                duration_weeks=3,
                prerequisites=[],
                resources=[
                    {'type': 'book', 'title': '启示录', 'author': 'Marty Cagan'},
                    {'type': 'book', 'title': '用户体验要素', 'author': 'Jesse James Garrett'},
                ],
                projects=['设计 AI 产品原型', '用户调研分析'],
                learning_objectives=['理解用户需求', '掌握产品设计流程', '学习用户体验原则']
            ),

            'data_analysis': LearningModule(
                id='data_analysis',
                title='数据分析与增长',
                description='掌握数据驱动的产品决策方法',
                category='product-business',
                difficulty='intermediate',
                duration_weeks=3,
                prerequisites=[],
                resources=[
                    {'type': 'book', 'title': '精益数据分析', 'author': 'Alistair Croll'},
                    {'type': 'tool', 'title': 'Google Analytics', 'url': 'https://analytics.google.com/'},
                ],
                projects=['设计数据指标体系', 'A/B 测试分析'],
                learning_objectives=['理解数据指标', '掌握增长分析方法', '设计实验框架']
            ),

            'market_positioning': LearningModule(
                id='market_positioning',
                title='市场定位与策略',
                description='理解产品定位和市场竞争策略',
                category='product-business',
                difficulty='intermediate',
                duration_weeks=2,
                prerequisites=['product_thinking'],
                resources=[
                    {'type': 'book', 'title': 'Obvious Awesome', 'author': 'April Dunford'},
                    {'type': 'book', 'title': '跨越鸿沟', 'author': 'Geoffrey Moore'},
                ],
                projects=['竞品分析报告', '定位策略文档'],
                learning_objectives=['理解定位理论', '分析竞争格局', '制定市场策略']
            ),

            # Phase 4: Consulting & Delivery
            'client_management': LearningModule(
                id='client_management',
                title='客户管理与沟通',
                description='掌握客户关系管理和沟通技巧',
                category='consulting-delivery',
                difficulty='beginner',
                duration_weeks=2,
                prerequisites=[],
                resources=[
                    {'type': 'book', 'title': '客户成功', 'author': 'Nick Mehta'},
                    {'type': 'book', 'title': '演说之禅', 'author': 'Garr Reynolds'},
                ],
                projects=['客户需求分析', '演示文稿设计'],
                learning_objectives=['理解客户心理', '掌握沟通技巧', '设计有效演示']
            ),

            'project_delivery': LearningModule(
                id='project_delivery',
                title='项目交付与变革管理',
                description='掌握项目交付和组织变革管理',
                category='consulting-delivery',
                difficulty='intermediate',
                duration_weeks=3,
                prerequisites=['client_management'],
                resources=[
                    {'type': 'standard', 'title': 'PMBOK 指南', 'organization': 'PMI'},
                    {'type': 'book', 'title': '变革之心', 'author': 'John Kotter'},
                ],
                projects=['项目计划制定', '变革策略设计'],
                learning_objectives=['理解项目管理', '掌握变革管理', '设计交付流程']
            ),
        }

    def _build_knowledge_graph(self) -> nx.DiGraph:
        """构建知识依赖图"""
        G = nx.DiGraph()

        # 添加节点
        for module_id, module in self.learning_modules.items():
            G.add_node(module_id, **{
                'title': module.title,
                'category': module.category,
                'difficulty': module.difficulty,
                'duration': module.duration_weeks
            })

        # 添加边（依赖关系）
        for module_id, module in self.learning_modules.items():
            for prereq in module.prerequisites:
                if prereq in self.learning_modules:
                    G.add_edge(prereq, module_id)

        return G

    def analyze_current_skills(self) -> Dict[str, Any]:
        """分析当前技能水平"""
        # 扫描 Obsidian 笔记，分析已掌握的知识
        core_path = self.project_root / "core"

        completed_modules = set()
        skill_levels = {}

        if core_path.exists():
            for note_file in core_path.rglob("*.md"):
                # 从笔记文件名推断已完成的模块
                note_name = note_file.stem
                for module_id in self.learning_modules:
                    if module_id in note_name.lower():
                        completed_modules.add(module_id)
                        skill_levels[module_id] = 'completed'

        # 分析技能覆盖率
        total_modules = len(self.learning_modules)
        completed_count = len(completed_modules)
        coverage_rate = completed_count / total_modules if total_modules > 0 else 0

        return {
            'completed_modules': list(completed_modules),
            'total_modules': total_modules,
            'coverage_rate': coverage_rate,
            'skill_levels': skill_levels
        }

    def generate_personalized_path(self, topic: str = None,
                                  available_hours_per_week: int = 10) -> Dict[str, Any]:
        """生成个性化学习路径"""

        # 分析当前技能
        current_skills = self.analyze_current_skills()
        completed_modules = set(current_skills['completed_modules'])

        # 确定目标模块
        if topic:
            # 基于主题确定相关模块
            target_modules = self._find_modules_by_topic(topic)
        else:
            # 默认完整 FDE 路径
            target_modules = set(self.learning_modules.keys())

        # 找出需要学习的模块
        modules_to_learn = target_modules - completed_modules

        # 拓扑排序，考虑依赖关系
        ordered_modules = self._topological_sort_with_prerequisites(
            modules_to_learn, completed_modules
        )

        # 按阶段分组
        learning_path = self._group_by_phase(ordered_modules)

        # 调整时间安排
        adjusted_path = self._adjust_timeline(learning_path, available_hours_per_week)

        # 生成详细计划
        detailed_plan = self._generate_detailed_plan(adjusted_path, completed_modules)

        # 保存学习路径
        self._save_learning_path(detailed_plan)

        return detailed_plan

    def _find_modules_by_topic(self, topic: str) -> set:
        """根据主题查找相关模块"""
        topic_lower = topic.lower()
        relevant_modules = set()

        for module_id, module in self.learning_modules.items():
            # 检查标题、描述、类别
            if (topic_lower in module.title.lower() or
                topic_lower in module.description.lower() or
                topic_lower in module.category.lower()):
                relevant_modules.add(module_id)

        return relevant_modules if relevant_modules else set(self.learning_modules.keys())

    def _topological_sort_with_prerequisites(self,
                                            modules_to_learn: set,
                                            completed_modules: set) -> List[str]:
        """考虑已学模块的拓扑排序"""

        # 创建子图
        subgraph = self.knowledge_graph.subgraph(modules_to_learn | completed_modules)

        try:
            # 拓扑排序
            sorted_modules = list(nx.topological_sort(subgraph))

            # 过滤出需要学习的模块
            learning_order = [m for m in sorted_modules if m in modules_to_learn]

            return learning_order

        except nx.NetworkXError:
            # 图中有环，返回原始顺序
            return list(modules_to_learn)

    def _group_by_phase(self, modules: List[str]) -> Dict[str, List[Dict]]:
        """按阶段分组学习模块"""
        phases = {
            'Phase 1: 技术基础': [],
            'Phase 2: AI工程化': [],
            'Phase 3: 产品业务': [],
            'Phase 4: 咨询交付': []
        }

        category_mapping = {
            'foundation': 'Phase 1: 技术基础',
            'ai-engineering': 'Phase 2: AI工程化',
            'product-business': 'Phase 3: 产品业务',
            'consulting-delivery': 'Phase 4: 咨询交付'
        }

        for module_id in modules:
            if module_id in self.learning_modules:
                module = self.learning_modules[module_id]
                phase = category_mapping.get(module.category, 'Phase 1: 技术基础')

                phases[phase].append({
                    'id': module_id,
                    'title': module.title,
                    'description': module.description,
                    'duration_weeks': module.duration_weeks,
                    'prerequisites': module.prerequisites,
                    'resources': module.resources,
                    'projects': module.projects,
                    'objectives': module.learning_objectives
                })

        return phases

    def _adjust_timeline(self, phases: Dict[str, List[Dict]],
                        hours_per_week: int) -> Dict[str, Any]:
        """根据可用时间调整时间线"""

        total_weeks = sum(
            sum(module['duration_weeks'] for module in phase_modules)
            for phase_modules in phases.values()
        )

        # 基础时间估计（假设每周20小时为标准）
        base_hours_per_week = 20
        time_factor = base_hours_per_week / hours_per_week

        adjusted_phases = {}
        current_week = 1

        for phase_name, phase_modules in phases.items():
            adjusted_modules = []

            for module in phase_modules:
                adjusted_duration = int(module['duration_weeks'] * time_factor)
                start_week = current_week
                end_week = current_week + adjusted_duration - 1

                adjusted_modules.append({
                    **module,
                    'adjusted_duration_weeks': adjusted_duration,
                    'start_week': start_week,
                    'end_week': end_week,
                    'estimated_hours': adjusted_duration * hours_per_week
                })

                current_week = end_week + 1

            adjusted_phases[phase_name] = adjusted_modules

        return {
            'phases': adjusted_phases,
            'total_weeks': current_week - 1,
            'total_hours': (current_week - 1) * hours_per_week,
            'hours_per_week': hours_per_week
        }

    def _generate_detailed_plan(self, path_data: Dict[str, Any],
                               completed_modules: set) -> Dict[str, Any]:
        """生成详细学习计划"""

        # 使用 AI 生成个性化建议
        ai_suggestions = self._get_ai_suggestions(path_data, completed_modules)

        detailed_plan = {
            'generated_at': datetime.now().isoformat(),
            'summary': {
                'total_phases': len(path_data['phases']),
                'total_weeks': path_data['total_weeks'],
                'total_hours': path_data['total_hours'],
                'hours_per_week': path_data['hours_per_week'],
                'completed_modules': len(completed_modules),
                'remaining_modules': sum(len(modules) for modules in path_data['phases'].values())
            },
            'phases': path_data['phases'],
            'milestones': self._generate_milestones(path_data),
            'weekly_schedule': self._generate_weekly_schedule(path_data),
            'ai_suggestions': ai_suggestions,
            'success_criteria': self._define_success_criteria(path_data)
        }

        return detailed_plan

    def _get_ai_suggestions(self, path_data: Dict[str, Any],
                           completed_modules: set) -> Dict[str, Any]:
        """获取 AI 个性化建议"""

        # 构建提示词
        modules_summary = self._summarize_modules_for_ai(path_data, completed_modules)

        prompt = f"""
        作为 Forward Deployed Engineer 的学习顾问，基于以下信息提供个性化学习建议：

        已完成模块: {', '.join(completed_modules) if completed_modules else '无'}
        学习计划: {json.dumps(modules_summary, ensure_ascii=False, indent=2)}

        请提供以下建议：
        1. 学习重点和优先级
        2. 可能的学习挑战和应对策略
        3. 实践项目建议
        4. 技能验证方法
        5. 职业发展建议

        请以 JSON 格式返回建议，包含上述五个方面。
        """

        try:
            # MiniMax / OpenAI 均遵循 Chat Completions 格式，响应通过 choices[0].message.content 取得。
            response = self._client.chat.completions.create(
                model=self._chat_model,
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )

            # 解析 AI 响应
            suggestions_text = response.choices[0].message.content

            # MiniMax 思考模型会在回答前插入 <think>...</think> 推理过程，需先剥离。
            import re
            suggestions_text = re.sub(r'<think>.*?</think>', '', suggestions_text, flags=re.DOTALL).strip()

            # 提取最外层 JSON 对象（跳过 markdown 代码块标记）
            json_match = re.search(r'\{.*\}', suggestions_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                return {
                    'general_advice': suggestions_text,
                    'focus_areas': [],
                    'challenges': [],
                    'project_suggestions': [],
                    'validation_methods': [],
                    'career_advice': ''
                }

        except Exception as e:
            print(f"AI 建议生成失败: {e}")
            return self._get_default_suggestions()

    def _summarize_modules_for_ai(self, path_data: Dict[str, Any],
                                  completed_modules: set) -> Dict:
        """为 AI 总结模块信息"""
        summary = {}

        for phase_name, phase_modules in path_data['phases'].items():
            summary[phase_name] = [
                {
                    'title': module['title'],
                    'duration_weeks': module['adjusted_duration_weeks'],
                    'objectives': module['objectives'][:3]  # 只取前3个目标
                }
                for module in phase_modules
            ]

        return summary

    def _get_default_suggestions(self) -> Dict[str, Any]:
        """获取默认建议"""
        return {
            'focus_areas': [
                '优先完成技术基础模块',
                'AI 工程化是核心竞争力',
                '产品思维决定项目价值'
            ],
            'challenges': [
                '技术深度与广度的平衡',
                '理论知识向实践转化',
                '快速技术迭代适应'
            ],
            'project_suggestions': [
                '每完成一个模块构建一个实践项目',
                '参与开源项目贡献代码',
                '在个人博客上分享学习心得'
            ],
            'validation_methods': [
                '构建项目演示',
                '参与技术社区讨论',
                '模拟面试练习'
            ],
            'career_advice': '结合个人兴趣和市场需求，选择 FDE 的细分领域深入发展'
        }

    def _generate_milestones(self, path_data: Dict[str, Any]) -> List[Dict]:
        """生成学习里程碑"""
        milestones = []

        week_counter = 0
        for phase_name, phase_modules in path_data['phases'].items():
            # 每个阶段结束是一个里程碑
            phase_end_week = week_counter + max(
                (m['end_week'] for m in phase_modules), default=week_counter
            )

            milestones.append({
                'week': phase_end_week,
                'title': f"{phase_name} 完成",
                'description': f"完成 {phase_name} 的所有学习模块",
                'deliverables': [m['projects'] for m in phase_modules if m['projects']],
                'celebration': '休息一周，回顾学习成果'
            })

            week_counter = phase_end_week

        return milestones

    def _generate_weekly_schedule(self, path_data: Dict[str, Any]) -> List[Dict]:
        """生成周学习计划"""
        weekly_schedule = []

        for week in range(1, path_data['total_weeks'] + 1):
            # 找到当前周正在进行的学习模块
            current_modules = []

            for phase_name, phase_modules in path_data['phases'].items():
                for module in phase_modules:
                    if module['start_week'] <= week <= module['end_week']:
                        # 计算进度
                        total_weeks = module['end_week'] - module['start_week'] + 1
                        current_week_in_module = week - module['start_week'] + 1
                        progress = current_week_in_module / total_weeks

                        current_modules.append({
                            'title': module['title'],
                            'phase': phase_name,
                            'progress': f"{int(progress * 100)}%",
                            'focus_area': self._get_weekly_focus(module, current_week_in_module)
                        })

            weekly_schedule.append({
                'week': week,
                'modules': current_modules,
                'total_study_hours': path_data['hours_per_week'],
                'suggested_breakdown': self._suggest_hour_breakdown(current_modules, path_data['hours_per_week'])
            })

        return weekly_schedule

    def _get_weekly_focus(self, module: Dict, week_in_module: int) -> str:
        """获取本周学习重点"""
        total_weeks = module['end_week'] - module['start_week'] + 1

        if week_in_module == 1:
            return "概念理解和基础学习"
        elif week_in_module == total_weeks:
            return "实践项目总结"
        else:
            return "深入学习和实践应用"

    def _suggest_hour_breakdown(self, modules: List[Dict],
                               total_hours: int) -> Dict[str, int]:
        """建议学时分配"""
        if not modules:
            return {}

        # 简单平均分配，实际可以根据模块重要性调整
        hours_per_module = total_hours // len(modules)

        breakdown = {}
        for module in modules:
            breakdown[module['title']] = hours_per_module

        # 添加复习和实践时间
        breakdown['复习和总结'] = max(2, total_hours // 4)
        breakdown['实践项目'] = max(3, total_hours // 3)

        return breakdown

    def _define_success_criteria(self, path_data: Dict[str, Any]) -> Dict[str, List[str]]:
        """定义成功标准"""
        return {
            'knowledge_acquisition': [
                '完成所有预定的学习模块',
                '通过模块自测题目',
                '能够解释核心概念和原理'
            ],
            'practical_skills': [
                '完成每个模块的实践项目',
                '代码质量达到生产标准',
                '能够独立解决实际问题'
            ],
            'application_ability': [
                '能够将所学知识应用到实际项目',
                '具备技术方案设计能力',
                '能够进行有效的技术沟通'
            ],
            'continuous_learning': [
                '建立个人知识管理系统',
                '养成定期复习习惯',
                '关注技术发展趋势'
            ]
        }

    def _save_learning_path(self, learning_path: Dict[str, Any]):
        """保存学习路径"""
        learning_path_file = self.project_root / "docs" / "current_learning_path.json"

        # 确保目录存在
        learning_path_file.parent.mkdir(parents=True, exist_ok=True)

        # 保存为格式化的 JSON
        with open(learning_path_file, 'w', encoding='utf-8') as f:
            json.dump(learning_path, f, ensure_ascii=False, indent=2)

        print(f"学习路径已保存到: {learning_path_file}")

    def export_to_obsidian(self, learning_path: Dict[str, Any]):
        """导出学习路径到 Obsidian"""
        obsidian_templates_path = self.project_root / "templates" / "learning_paths"
        obsidian_templates_path.mkdir(parents=True, exist_ok=True)

        # 创建学习路径总览
        overview_file = obsidian_templates_path / "学习路径总览.md"
        with open(overview_file, 'w', encoding='utf-8') as f:
            f.write(self._generate_obsidian_overview(learning_path))

        # 为每个阶段创建详细笔记
        for phase_name, phase_modules in learning_path['phases'].items():
            phase_file = obsidian_templates_path / f"{phase_name}.md"
            with open(phase_file, 'w', encoding='utf-8') as f:
                f.write(self._generate_obsidian_phase(phase_name, phase_modules))

        print(f"学习路径已导出到 Obsidian 模板: {obsidian_templates_path}")

    def _generate_obsidian_overview(self, learning_path: Dict[str, Any]) -> str:
        """生成 Obsidian 学习路径总览"""
        overview = f"""# FDE 学习路径总览

> 生成时间: {learning_path['generated_at']}
> 总周期: {learning_path['summary']['total_weeks']} 周
> 总学时: {learning_path['summary']['total_hours']} 小时
> 每周安排: {learning_path['summary']['hours_per_week']} 小时

## 📊 学习概况

- **已完成模块**: {learning_path['summary']['completed_modules']} 个
- **待学习模块**: {learning_path['summary']['remaining_modules']} 个
- **学习阶段**: {learning_path['summary']['total_phases']} 个

## 🎯 学习阶段

"""

        for i, (phase_name, _) in enumerate(learning_path['phases'].items(), 1):
            overview += f"{i}. [[{phase_name}]]\n"

        overview += f"""
## 📅 关键里程碑

"""

        for milestone in learning_path['milestones']:
            overview += f"- **第 {milestone['week']} 周**: {milestone['title']}\n"

        overview += f"""
## 💡 AI 个性化建议

{self._format_ai_suggestions(learning_path['ai_suggestions'])}

## ✅ 成功标准

### 知识获取
{chr(10).join(f"- {criteria}" for criteria in learning_path['success_criteria']['knowledge_acquisition'])}

### 实践技能
{chr(10).join(f"- {criteria}" for criteria in learning_path['success_criteria']['practical_skills'])}

### 应用能力
{chr(10).join(f"- {criteria}" for criteria in learning_path['success_criteria']['application_ability'])}

### 持续学习
{chr(10).join(f"- {criteria}" for criteria in learning_path['success_criteria']['continuous_learning'])}

---

**注意**: 此学习路径根据个人情况和可用时间生成，建议定期回顾和调整。
"""
        return overview

    def _generate_obsidian_phase(self, phase_name: str,
                                 phase_modules: List[Dict]) -> str:
        """生成 Obsidian 阶段笔记"""
        phase_content = f"""# {phase_name}

## 📚 学习模块

"""

        for module in phase_modules:
            phase_content += f"""### {module['title']}

**时间安排**: 第 {module['start_week']}-{module['end_week']} 周 ({module['adjusted_duration_weeks']} 周)
**预计学时**: {module['estimated_hours']} 小时

#### 学习目标
{chr(10).join(f"- {objective}" for objective in module['objectives'])}

#### 学习资源
"""

            for resource in module['resources']:
                if resource['type'] == 'book':
                    phase_content += f"- 📖 《{resource['title']}》- {resource['author']}\n"
                elif resource['type'] == 'course':
                    phase_content += f"- 🎓 {resource['title']} ({resource['platform']})\n"
                elif resource['type'] == 'paper':
                    phase_content += f"- 📄 {resource['title']}\n"
                elif resource['type'] == 'framework':
                    phase_content += f"- 🔧 [{resource['title']}]({resource['url']})\n"
                else:
                    phase_content += f"- 🔗 {resource.get('title', resource.get('name', 'Resource'))}\n"

            phase_content += f"""
#### 实践项目
{chr(10).join(f"- {project}" for project in module['projects'])}

#### 前置要求
{', '.join(module['prerequisites']) if module['prerequisites'] else '无'}

---

"""

        return phase_content

    def _format_ai_suggestions(self, suggestions: Dict[str, Any]) -> str:
        """格式化 AI 建议"""
        if not suggestions:
            return "暂无 AI 建议"

        formatted = ""

        if 'focus_areas' in suggestions:
            formatted += "### 学习重点\n"
            formatted += chr(10).join(f"- {area}" for area in suggestions['focus_areas'])
            formatted += "\n\n"

        if 'challenges' in suggestions:
            formatted += "### 可能的挑战\n"
            formatted += chr(10).join(f"- {challenge}" for challenge in suggestions['challenges'])
            formatted += "\n\n"

        if 'project_suggestions' in suggestions:
            formatted += "### 项目建议\n"
            formatted += chr(10).join(f"- {project}" for project in suggestions['project_suggestions'])
            formatted += "\n\n"

        if 'general_advice' in suggestions:
            formatted += f"### 综合建议\n{suggestions['general_advice']}\n\n"

        return formatted

    def track_learning_progress(self, completed_module_id: str,
                               quality_score: float = None,
                               notes: str = "") -> Dict[str, Any]:
        """跟踪学习进度"""
        progress_file = self.project_root / "docs" / "learning_progress.json"

        # 加载现有进度
        progress_data = {}
        if progress_file.exists():
            with open(progress_file, 'r', encoding='utf-8') as f:
                progress_data = json.load(f)

        # 更新进度
        if 'completed_modules' not in progress_data:
            progress_data['completed_modules'] = {}

        progress_data['completed_modules'][completed_module_id] = {
            'completed_at': datetime.now().isoformat(),
            'quality_score': quality_score,
            'notes': notes
        }

        # 保存进度
        with open(progress_file, 'w', encoding='utf-8') as f:
            json.dump(progress_data, f, ensure_ascii=False, indent=2)

        # 重新生成学习路径
        updated_path = self.generate_personalized_path()

        return {
            'updated_progress': progress_data['completed_modules'][completed_module_id],
            'updated_learning_path': updated_path
        }


def main():
    """主函数，用于命令行调用"""
    import argparse

    parser = argparse.ArgumentParser(description='FDE 学习路径生成器')
    parser.add_argument('--topic', '-t', help='学习主题')
    parser.add_argument('--hours', '-h', type=int, default=10, help='每周可用学习小时数')
    parser.add_argument('--export', '-e', action='store_true', help='导出到 Obsidian')

    args = parser.parse_args()

    # 加载配置
    from dotenv import load_dotenv
    load_dotenv()
    config = os.environ

    generator = FDELearningPathGenerator(config)

    # 生成学习路径
    learning_path = generator.generate_personalized_path(
        topic=args.topic,
        available_hours_per_week=args.hours
    )

    # 显示学习路径
    print(f"\n🎯 FDE 个性化学习路径")
    print(f"📅 总周期: {learning_path['summary']['total_weeks']} 周")
    print(f"⏰ 总学时: {learning_path['summary']['total_hours']} 小时")
    print(f"📚 学习阶段: {learning_path['summary']['total_phases']} 个")

    for phase_name, phase_modules in learning_path['phases'].items():
        print(f"\n{phase_name}:")
        for module in phase_modules:
            print(f"  • {module['title']} ({module['adjusted_duration_weeks']} 周)")

    # 导出到 Obsidian
    if args.export:
        generator.export_to_obsidian(learning_path)


if __name__ == '__main__':
    main()