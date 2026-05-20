"""
FDE Knowledge Hub - Spaced Repetition System
基于遗忘曲线的智能间隔重复学习系统
"""

import json
import random
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict


@dataclass
class ReviewItem:
    """复习项目"""
    id: str
    title: str
    category: str
    difficulty: str
    last_review: str
    next_review: str
    interval_days: int
    ease_factor: float
    repetition_count: int
    quality_scores: List[float]
    importance: str  # high/medium/low
    forgetting_index: float


class SpacedRepetitionSystem:
    """间隔重复学习系统"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.project_root = Path(__file__).parent.parent
        self.review_data_file = self.project_root / "docs" / "review_data.json"

        # 加载复习数据
        self.review_items = self._load_review_data()

        # SM-2 算法参数
        self.default_ease_factor = 2.5
        self.minimum_ease_factor = 1.3
        self.quality_bounds = {
            'easy': 5,
            'good': 4,
            'hard': 3,
            'again': 0
        }

    def _load_review_data(self) -> Dict[str, ReviewItem]:
        """加载复习数据"""
        if self.review_data_file.exists():
            with open(self.review_data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            return {
                item_id: ReviewItem(**item_data)
                for item_id, item_data in data.items()
            }

        return {}

    def _save_review_data(self):
        """保存复习数据"""
        self.review_data_file.parent.mkdir(parents=True, exist_ok=True)

        with open(self.review_data_file, 'w', encoding='utf-8') as f:
            data = {
                item_id: asdict(item)
                for item_id, item in self.review_items.items()
            }
            json.dump(data, f, ensure_ascii=False, indent=2)

    def add_review_item(self, item_id: str, title: str, category: str,
                       difficulty: str, importance: str = "medium"):
        """添加复习项目"""
        if item_id in self.review_items:
            return

        now = datetime.now()
        next_review = now + timedelta(days=1)  # 第一次复习在明天

        review_item = ReviewItem(
            id=item_id,
            title=title,
            category=category,
            difficulty=difficulty,
            last_review=now.isoformat(),
            next_review=next_review.isoformat(),
            interval_days=1,
            ease_factor=self.default_ease_factor,
            repetition_count=0,
            quality_scores=[],
            importance=importance,
            forgetting_index=1.0  # 初始遗忘指数
        )

        self.review_items[item_id] = review_item
        self._save_review_data()

    def record_review(self, item_id: str, quality: int):
        """记录复习结果"""
        if item_id not in self.review_items:
            raise ValueError(f"复习项目不存在: {item_id}")

        item = self.review_items[item_id]
        now = datetime.now()

        # 更新质量分数
        item.quality_scores.append(quality)

        # SM-2 算法更新
        ease_factor = item.ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
        ease_factor = max(ease_factor, self.minimum_ease_factor)

        if quality >= 3:
            # 记忆成功，增加间隔
            if item.repetition_count == 0:
                interval_days = 1
            elif item.repetition_count == 1:
                interval_days = 6
            else:
                interval_days = round(item.interval_days * ease_factor)

            item.repetition_count += 1
        else:
            # 记忆失败，重置间隔
            item.repetition_count = 0
            interval_days = 1

        # 更新项目数据
        item.last_review = now.isoformat()
        item.next_review = (now + timedelta(days=interval_days)).isoformat()
        item.interval_days = interval_days
        item.ease_factor = ease_factor

        # 更新遗忘指数
        item.forgetting_index = self._calculate_forgetting_index(item)

        self._save_review_data()

    def _calculate_forgetting_index(self, item: ReviewItem) -> float:
        """计算遗忘指数"""
        if not item.quality_scores:
            return 1.0

        # 基于历史质量分数计算
        avg_quality = sum(item.quality_scores) / len(item.quality_scores)
        recent_quality = item.quality_scores[-5:]  # 最近5次

        # 趋势分析
        if len(recent_quality) >= 3:
            trend = sum(recent_quality[-3:]) / 3
        else:
            trend = avg_quality

        # 综合计算
        forgetting_index = (1.0 - (avg_quality / 5.0)) * 0.7 + (1.0 - (trend / 5.0)) * 0.3

        return max(0.0, min(1.0, forgetting_index))

    def get_due_review_items(self) -> List[Dict[str, Any]]:
        """获取到期复习项目"""
        now = datetime.now()
        due_items = []

        for item_id, item in self.review_items.items():
            next_review = datetime.fromisoformat(item.next_review)

            if next_review <= now:
                due_items.append({
                    'id': item_id,
                    'title': item.title,
                    'category': item.category,
                    'difficulty': item.difficulty,
                    'importance': item.importance,
                    'forgetting_index': item.forgetting_index,
                    'last_review': item.last_review,
                    'days_overdue': (now - next_review).days,
                    'repetition_count': item.repetition_count,
                    'interval_days': item.interval_days
                })

        # 按重要性和遗忘指数排序
        due_items.sort(key=lambda x: (
            self._importance_priority[x['importance']],
            x['forgetting_index'],
            x['days_overdue']
        ), reverse=True)

        return due_items

    def get_daily_review_items(self) -> List[Dict[str, Any]]:
        """获取每日复习项目"""
        now = datetime.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)

        daily_items = []

        for item_id, item in self.review_items.items():
            next_review = datetime.fromisoformat(item.next_review)

            if today_start <= next_review < today_end:
                daily_items.append({
                    'id': item_id,
                    'title': item.title,
                    'category': item.category,
                    'difficulty': item.difficulty,
                    'importance': item.importance,
                    'forgetting_index': item.forgetting_index,
                    'scheduled_time': next_review.strftime('%H:%M'),
                    'repetition_count': item.repetition_count,
                    'interval_days': item.interval_days
                })

        # 按预定时间排序
        daily_items.sort(key=lambda x: x['scheduled_time'])

        return daily_items

    def get_weekly_review_items(self) -> List[Dict[str, Any]]:
        """获取每周复习项目"""
        now = datetime.now()
        week_start = now - timedelta(days=now.weekday())
        week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
        week_end = week_start + timedelta(weeks=1)

        weekly_items = []

        for item_id, item in self.review_items.items():
            next_review = datetime.fromisoformat(item.next_review)

            if week_start <= next_review < week_end:
                weekly_items.append({
                    'id': item_id,
                    'title': item.title,
                    'category': item.category,
                    'difficulty': item.difficulty,
                    'importance': item.importance,
                    'forgetting_index': item.forgetting_index,
                    'scheduled_day': next_review.strftime('%A'),
                    'scheduled_date': next_review.strftime('%Y-%m-%d'),
                    'repetition_count': item.repetition_count,
                    'interval_days': item.interval_days
                })

        # 按预定日期排序
        weekly_items.sort(key=lambda x: x['scheduled_date'])

        return weekly_items

    def get_adaptive_review_items(self) -> List[Dict[str, Any]]:
        """获取自适应复习项目"""
        now = datetime.now()

        # 获取到期项目
        due_items = self.get_due_review_items()

        # 如果到期项目太少，添加一些即将到期的项目
        if len(due_items) < 5:
            upcoming_items = []
            tomorrow = now + timedelta(days=1)
            tomorrow_end = tomorrow.replace(hour=23, minute=59, second=59)

            for item_id, item in self.review_items.items():
                next_review = datetime.fromisoformat(item.next_review)

                if now < next_review <= tomorrow_end:
                    upcoming_items.append({
                        'id': item_id,
                        'title': item.title,
                        'category': item.category,
                        'difficulty': item.difficulty,
                        'importance': item.importance,
                        'forgetting_index': item.forgetting_index,
                        'scheduled_time': next_review.strftime('%H:%M'),
                        'type': 'upcoming',
                        'repetition_count': item.repetition_count,
                        'interval_days': item.interval_days
                    })

            # 添加即将到期的项目（按遗忘指数排序）
            upcoming_items.sort(key=lambda x: x['forgetting_index'], reverse=True)
            due_items.extend(upcoming_items[:5])

        # 如果项目仍然太少，添加高重要性的项目
        if len(due_items) < 5:
            high_importance_items = []

            for item_id, item in self.review_items.items():
                if item.importance == 'high' and item.id not in [d['id'] for d in due_items]:
                    high_importance_items.append({
                        'id': item_id,
                        'title': item.title,
                        'category': item.category,
                        'difficulty': item.difficulty,
                        'importance': item.importance,
                        'forgetting_index': item.forgetting_index,
                        'type': 'high_priority',
                        'repetition_count': item.repetition_count,
                        'interval_days': item.interval_days
                    })

            high_importance_items.sort(key=lambda x: x['forgetting_index'], reverse=True)
            due_items.extend(high_importance_items[:5])

        return due_items[:10]  # 最多返回10个项目

    def get_review_statistics(self) -> Dict[str, Any]:
        """获取复习统计"""
        now = datetime.now()

        total_items = len(self.review_items)
        if total_items == 0:
            return {
                'total_items': 0,
                'due_items': 0,
                'suggestion': '请先添加复习项目'
            }

        due_items = self.get_due_review_items()
        overdue_items = [item for item in due_items if item['days_overdue'] > 0]

        # 统计不同间隔的项目数量
        interval_distribution = {}
        for item in self.review_items.values():
            interval_range = self._get_interval_range(item.interval_days)
            interval_distribution[interval_range] = interval_distribution.get(interval_range, 0) + 1

        # 统计重要性分布
        importance_distribution = {}
        for item in self.review_items.values():
            importance_distribution[item.importance] = importance_distribution.get(item.importance, 0) + 1

        # 计算平均遗忘指数
        avg_forgetting_index = sum(item.forgetting_index for item in self.review_items.values()) / total_items

        return {
            'total_items': total_items,
            'due_items': len(due_items),
            'overdue_items': len(overdue_items),
            'completion_rate': (total_items - len(overdue_items)) / total_items if total_items > 0 else 0,
            'avg_forgetting_index': avg_forgetting_index,
            'interval_distribution': interval_distribution,
            'importance_distribution': importance_distribution,
            'most_problematic_items': sorted(
                [asdict(item) for item in self.review_items.values()],
                key=lambda x: x['forgetting_index'],
                reverse=True
            )[:5]
        }

    def generate_review_plan(self, days_ahead: int = 7) -> Dict[str, List]:
        """生成复习计划"""
        now = datetime.now()
        review_plan = {}

        for day in range(days_ahead):
            target_date = now + timedelta(days=day)
            date_str = target_date.strftime('%Y-%m-%d')

            daily_items = []

            for item_id, item in self.review_items.items():
                next_review = datetime.fromisoformat(item.next_review)

                if next_review.date() == target_date.date():
                    daily_items.append({
                        'id': item_id,
                        'title': item.title,
                        'category': item.category,
                        'importance': item.importance,
                        'estimated_time': self._estimate_review_time(item)
                    })

            # 按重要性排序
            daily_items.sort(key=lambda x: self._importance_priority[x['importance']], reverse=True)

            if daily_items:
                review_plan[date_str] = daily_items

        return review_plan

    def optimize_review_schedule(self, available_time_minutes: int = 60) -> List[Dict[str, Any]]:
        """优化复习安排"""
        due_items = self.get_due_review_items()

        if not due_items:
            return []

        # 估算每个项目的复习时间
        for item in due_items:
            review_item = self.review_items[item['id']]
            item['estimated_time'] = self._estimate_review_time(review_item)

        # 按重要性和遗忘指数排序
        due_items.sort(key=lambda x: (
            self._importance_priority[x['importance']],
            x['forgetting_index']
        ), reverse=True)

        # 选择能够在可用时间内完成的项目
        selected_items = []
        total_time = 0

        for item in due_items:
            if total_time + item['estimated_time'] <= available_time_minutes:
                selected_items.append(item)
                total_time += item['estimated_time']
            else:
                break

        return selected_items

    def import_from_obsidian(self, note_ids: List[str]):
        """从 Obsidian 导入复习项目"""
        # 扫描 Obsidian 笔记，自动添加复习项目
        core_path = self.project_root / "core"

        for note_file in core_path.rglob("*.md"):
            note_id = note_file.stem

            # 跳过已存在的项目
            if note_id in self.review_items:
                continue

            # 解析元数据
            metadata = self._parse_note_metadata(note_file)

            if metadata:
                # 添加为复习项目
                self.add_review_item(
                    item_id=note_id,
                    title=metadata.get('title', note_id),
                    category=metadata.get('category', 'foundation'),
                    difficulty=metadata.get('difficulty', 'intermediate'),
                    importance=metadata.get('importance', 'medium')
                )

    def export_to_obsidian(self, review_items: List[Dict[str, Any]]):
        """导出到 Obsidian"""
        review_templates_path = self.project_root / "templates" / "review_notes"
        review_templates_path.mkdir(parents=True, exist_ok=True)

        for item in review_items:
            review_file = review_templates_path / f"复习_{item['id']}.md"

            with open(review_file, 'w', encoding='utf-8') as f:
                f.write(self._generate_review_note(item))

    def _generate_review_note(self, item: Dict[str, Any]) -> str:
        """生成复习笔记"""
        note_content = f"""# 复习: {item['title']}

**ID**: {item['id']}
**分类**: {item['category']}
**难度**: {item['difficulty']}
**重要性**: {item['importance']}
**遗忘指数**: {item['forgetting_index']:.2f}

## 📝 复习内容

### 核心概念
*在这里记录核心概念的理解*

### 实际应用
*在这里记录实际应用场景*

### 个人理解
*在这里记录个人理解和体会*

### 代码示例
```
*在这里记录相关代码*
```

## 🎯 复习检查

### 理解程度
- [ ] 能够清晰解释核心概念
- [ ] 能够举例说明实际应用
- [ ] 能够回答相关问题

### 实践能力
- [ ] 能够独立实现相关功能
- [ ] 能够解决相关问题
- [ ] 能够指导他人学习

### 知识关联
- [ ] 了解前置知识
- [ ] 了解后续学习方向
- [ ] 了解相关领域

## 📊 复习评估

### 本次复习质量
- **理解程度**: 1-5分
- **记忆程度**: 1-5分
- **应用能力**: 1-5分

### 遗忘情况
- **完全遗忘**: 需要重新学习
- **部分遗忘**: 需要重点复习
- **基本记住**: 正常复习即可
- **印象深刻**: 可以延长间隔

### 下次复习计划
- **建议间隔**: X天
- **复习重点**: 重点内容
- **复习方法**: 复习方法

## 🔗 相关知识

### 前置知识
- [[前置知识一]]
- [[前置知识二]]

### 相关概念
- [[相关概念一]]
- [[相关概念二]]

### 实践项目
- [[实践项目一]]
- [[实践项目二]]

---

**复习日期**: {datetime.now().strftime('%Y-%m-%d')}
**下次复习**: 待定
**FDE Knowledge Hub - 智能复习系统**
"""
        return note_content

    # 重要性优先级映射（类级常量，供 lambda 排序直接下标访问）
    _importance_priority = {'high': 3, 'medium': 2, 'low': 1}

    def _get_interval_range(self, interval_days: int) -> str:
        """获取间隔范围"""
        if interval_days == 1:
            return '1天'
        elif interval_days <= 7:
            return '1周内'
        elif interval_days <= 30:
            return '1月内'
        elif interval_days <= 90:
            return '3月内'
        else:
            return '3月以上'

    def _estimate_review_time(self, item: ReviewItem) -> int:
        """估算复习时间（分钟）"""
        base_time = 10  # 基础时间10分钟

        # 根据难度调整
        difficulty_multiplier = {
            'beginner': 1.0,
            'intermediate': 1.5,
            'expert': 2.0
        }
        difficulty_multiplier = difficulty_multiplier.get(item.difficulty, 1.0)

        # 根据重要性调整
        importance_multiplier = {
            'high': 1.5,
            'medium': 1.0,
            'low': 0.8
        }
        importance_multiplier = importance_multiplier.get(item.importance, 1.0)

        # 根据遗忘指数调整
        forgetting_multiplier = 1.0 + item.forgetting_index

        estimated_time = base_time * difficulty_multiplier * importance_multiplier * forgetting_multiplier

        return int(estimated_time)

    def _parse_note_metadata(self, note_file: Path) -> Dict[str, Any]:
        """解析笔记元数据"""
        try:
            with open(note_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # 提取 YAML front matter
            import re
            yaml_match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
            if yaml_match:
                import yaml
                yaml_data = yaml.safe_load(yaml_match.group(1))
                if isinstance(yaml_data, dict):
                    return yaml_data
        except Exception as e:
            pass

        return {}


def main():
    """主函数，用于命令行调用"""
    import argparse

    parser = argparse.ArgumentParser(description='FDE 间隔重复学习系统')
    parser.add_argument('--import-notes', '-i', action='store_true',
                       help='从 Obsidian 导入复习项目')
    parser.add_argument('--add-item', '-a', nargs=4,
                       metavar=('ID', 'TITLE', 'CATEGORY', 'DIFFICULTY'),
                       help='添加复习项目')
    parser.add_argument('--record-review', '-r', nargs=2,
                       metavar=('ID', 'QUALITY'),
                       help='记录复习结果')
    parser.add_argument('--show-due', '-d', action='store_true',
                       help='显示到期复习项目')
    parser.add_argument('--show-daily', action='store_true',
                       help='显示每日复习项目')
    parser.add_argument('--show-weekly', action='store_true',
                       help='显示每周复习项目')
    parser.add_argument('--show-adaptive', action='store_true',
                       help='显示自适应复习项目')
    parser.add_argument('--show-stats', '-s', action='store_true',
                       help='显示复习统计')
    parser.add_argument('--generate-plan', '-p', type=int, default=7,
                       metavar='DAYS', help='生成N天的复习计划')
    parser.add_argument('--optimize-schedule', '-o', type=int, default=60,
                       metavar='MINUTES', help='优化复习安排（可用分钟数）')

    args = parser.parse_args()

    # 加载配置
    from dotenv import load_dotenv
    load_dotenv()
    config = os.environ

    srs = SpacedRepetitionSystem(config)

    if args.import_notes:
        srs.import_from_obsidian()
        print("✅ 已从 Obsidian 导入复习项目")

    elif args.add_item:
        item_id, title, category, difficulty = args.add_item
        srs.add_review_item(item_id, title, category, difficulty)
        print(f"✅ 已添加复习项目: {title}")

    elif args.record_review:
        item_id, quality = args.record_review
        srs.record_review(item_id, int(quality))
        print(f"✅ 已记录复习结果: {item_id}")

    elif args.show_due:
        due_items = srs.get_due_review_items()
        print(f"📝 到期复习项目: {len(due_items)} 个\n")

        for item in due_items:
            print(f"• {item['title']}")
            print(f"  分类: {item['category']} | 重要性: {item['importance']}")
            print(f"  遗忘指数: {item['forgetting_index']:.2f} | 逾期: {item['days_overdue']} 天\n")

    elif args.show_daily:
        daily_items = srs.get_daily_review_items()
        print(f"📅 今日复习项目: {len(daily_items)} 个\n")

        for item in daily_items:
            print(f"• {item['title']} ({item['scheduled_time']})")
            print(f"  分类: {item['category']} | 重要性: {item['importance']}\n")

    elif args.show_weekly:
        weekly_items = srs.get_weekly_review_items()
        print(f"📅 本周复习项目: {len(weekly_items)} 个\n")

        for item in weekly_items:
            print(f"• {item['title']} ({item['scheduled_day']}, {item['scheduled_date']})")
            print(f"  分类: {item['category']} | 重要性: {item['importance']}\n")

    elif args.show_adaptive:
        adaptive_items = srs.get_adaptive_review_items()
        print(f"🎯 自适应复习项目: {len(adaptive_items)} 个\n")

        for item in adaptive_items:
            print(f"• {item['title']}")
            print(f"  分类: {item['category']} | 重要性: {item['importance']}")
            print(f"  遗忘指数: {item['forgetting_index']:.2f}\n")

    elif args.show_stats:
        stats = srs.get_review_statistics()
        print("📊 复习统计\n")

        if 'error' in stats:
            print(stats['suggestion'])
        else:
            print(f"总项目数: {stats['total_items']}")
            print(f"到期项目: {stats['due_items']}")
            print(f"逾期项目: {stats['overdue_items']}")
            print(f"完成率: {stats['completion_rate']:.1%}")
            print(f"平均遗忘指数: {stats['avg_forgetting_index']:.2f}")

            print(f"\n间隔分布:")
            for interval_range, count in stats['interval_distribution'].items():
                print(f"  {interval_range}: {count} 个")

            print(f"\n重要性分布:")
            for importance, count in stats['importance_distribution'].items():
                print(f"  {importance}: {count} 个")

    elif args.generate_plan:
        plan = srs.generate_review_plan(args.generate_plan)
        print(f"📅 未来 {args.generate_plan} 天复习计划\n")

        for date, items in plan.items():
            print(f"{date}: {len(items)} 个项目")
            total_time = sum(item['estimated_time'] for item in items)
            print(f"  预计用时: {total_time} 分钟\n")

    elif args.optimize_schedule:
        optimized_items = srs.optimize_review_schedule(args.optimize_schedule)
        print(f"⚡ 优化的复习安排 ({args.optimize_schedule} 分钟)\n")

        total_time = 0
        for i, item in enumerate(optimized_items, 1):
            print(f"{i}. {item['title']} ({item['estimated_time']} 分钟)")
            print(f"   分类: {item['category']} | 重要性: {item['importance']}")
            print(f"   遗忘指数: {item['forgetting_index']:.2f}\n")
            total_time += item['estimated_time']

        print(f"总计用时: {total_time} 分钟")

    else:
        # 默认显示自适应复习项目
        print("🎯 今日复习建议 (自适应模式)\n")
        adaptive_items = srs.get_adaptive_review_items()

        for item in adaptive_items:
            print(f"• {item['title']}")
            print(f"  分类: {item['category']} | 重要性: {item['importance']}")
            print(f"  遗忘指数: {item['forgetting_index']:.2f}")

            if 'type' in item:
                if item['type'] == 'upcoming':
                    print(f"  ⏰ 预定时间: {item['scheduled_time']}")
                elif item['type'] == 'high_priority':
                    print(f"  🔥 高优先级项目")

            print()


if __name__ == '__main__':
    main()