"""
FDE Knowledge Hub - Interview Preparation System
智能面试准备系统，支持问题生成、模拟面试和答案评估
"""

import json
import os
import re
from typing import List, Dict, Any
from dataclasses import dataclass, asdict
from pathlib import Path
from datetime import datetime

try:
    from openai import OpenAI as _OpenAIClient
except ImportError:
    print("请安装依赖: pip install openai")


@dataclass
class InterviewQuestion:
    """面试问题"""
    id: str
    question: str
    category: str
    difficulty: str
    type: str  # technical, behavioral, case_study
    context: str
    hint: str
    reference_answer: str
    evaluation_criteria: List[str]
    time_limit_minutes: int
    follow_up_questions: List[str]


class FDEMockInterview:
    """FDE 模拟面试系统"""

    def __init__(self, config: Dict[str, Any], role: str = "FDE", level: str = "senior"):
        self.config = config
        self.role = role
        self.level = level
        self.project_root = Path(__file__).parent.parent

        # AI client
        minimax_key = config.get('MINIMAX_API_KEY')
        if minimax_key:
            self._client = _OpenAIClient(
                api_key=minimax_key,
                base_url=config.get('MINIMAX_BASE_URL', 'https://api.minimaxi.chat/v1'),
            )
            self._chat_model = config.get('MINIMAX_CHAT_MODEL', 'MiniMax-M2.7')
        else:
            self._client = _OpenAIClient(api_key=config.get('OPENAI_API_KEY'))
            self._chat_model = 'gpt-4o-mini'

        # Knowledge ingester
        self._ingester = self._create_knowledge_ingester()
        self.current_session = None

    def _create_knowledge_ingester(self):
        """延迟初始化知识检索器"""
        try:
            from automation.knowledge_ingestion import FDEKnowledgeIngester
            return FDEKnowledgeIngester(self.config)
        except Exception as e:
            print(f"[WARNING] Cannot init knowledge ingester: {e}")
            return None

    # ── 题目生成 ────────────────────────────────────────────────────

    def generate_interview_questions(
        self,
        count: int = 5,
        categories: List[str] = None,
        difficulty: str = None,
        role_requirement: str = None,
    ) -> List[InterviewQuestion]:
        """基于岗位要求检索知识库并由 AI 动态生成面试题"""
        return self._generate_questions_by_ai(count, role_requirement, categories, difficulty)

    def _build_knowledge_summary(self, role_requirement: str) -> str:
        """检索本地知识库，返回摘要文本用于 prompt"""
        if self._ingester is None:
            return "（知识库不可用，请基于通用 FDE 经验生成题目）"

        try:
            results = self._ingester.search_knowledge(role_requirement, top_k=20)
        except Exception as e:
            print(f"[WARNING] Knowledge search failed: {e}")
            return "（知识库检索失败，请基于通用 FDE 经验生成题目）"

        if not results:
            return "（未检索到相关内容，请基于通用 FDE 经验生成题目）"

        chunks = []
        for r in results:
            src = Path(r['source']).name
            chunks.append(f"[Source: {src}]{r['text']}")

        return "\n\n---\n\n".join(chunks)

    def _generate_questions_by_ai(
        self,
        count: int,
        role_requirement: str,
        categories: List[str],
        difficulty: str,
    ) -> List[InterviewQuestion]:
        """调用 AI 基于知识库摘要动态生成面试题"""
        knowledge_summary = self._build_knowledge_summary(role_requirement)

        category_hint = ""
        if categories:
            category_hint = f"重点考察以下领域：{', '.join(categories)}。"

        difficulty_hint = ""
        if difficulty:
            dm = {'junior': '初级', 'mid': '中级', 'senior': '高级', 'expert': '专家'}
            difficulty_hint = f"难度等级：{dm.get(difficulty, difficulty)}。"

        prompt = f"""You are an FDE (Forward Deployed Engineer) interviewer. Generate interview questions based on the role requirements and knowledge base.

## Role Requirements
{role_requirement}

## Knowledge Base Summary
{knowledge_summary}

## Requirements
- Generate exactly {count} questions
- Type distribution: 40% technical, 30% case study, 30% behavioral
- Each question must include: id, question, category, difficulty, type, context, hint, reference_answer, evaluation_criteria (3-5 items), time_limit_minutes, follow_up_questions (2-3 items)
- Questions should be based on the knowledge base and reflect real FDE client scenarios
- Answers should demonstrate engineering thinking and practical experience

{category_hint}
{difficulty_hint}

Return ONLY valid JSON array, no other text. Each element: id, question, category, difficulty, type, context, hint, reference_answer, evaluation_criteria, time_limit_minutes, follow_up_questions"""

        try:
            response = self._client.chat.completions.create(
                model=self._chat_model,
                max_tokens=4000,
                messages=[{"role": "user", "content": prompt}]
            )
            raw = response.choices[0].message.content
            # Strip thinking tags
            raw = re.sub(r'<think>.*?', '', raw, flags=re.DOTALL).strip()

            json_match = re.search(r'\[.*\]', raw, re.DOTALL)
            if not json_match:
                try:
                    questions_data = json.loads(raw)
                except Exception:
                    print(f"[ERROR] Cannot parse AI response: {raw[:200]}")
                    return []
            else:
                questions_data = json.loads(json_match.group())
        except Exception as e:
            print(f"[ERROR] AI call failed: {e}")
            return []

        questions = []
        for i, q in enumerate(questions_data):
            try:
                q.setdefault('id', f"ai_gen_{i}")
                q.setdefault('category', q.get('category', 'AI Engineering'))
                q.setdefault('difficulty', difficulty or 'senior')
                q.setdefault('type', q.get('type', 'technical'))
                q.setdefault('context', q.get('context', ''))
                q.setdefault('hint', q.get('hint', ''))
                q.setdefault('reference_answer', q.get('reference_answer', ''))
                q.setdefault('evaluation_criteria', q.get('evaluation_criteria', []))
                q.setdefault('time_limit_minutes', q.get('time_limit_minutes', 10))
                q.setdefault('follow_up_questions', q.get('follow_up_questions', []))
                questions.append(InterviewQuestion(**q))
            except Exception as ex:
                print(f"[WARNING] Skipping invalid question: {ex}")
                continue

        if not questions:
            raise ValueError("Failed to generate any valid questions")

        return questions

    # ── 面试流程 ────────────────────────────────────────────────────

    def start_interview_session(self, questions: List[InterviewQuestion]) -> str:
        session_id = f"interview_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.current_session = {
            'session_id': session_id,
            'questions': questions,
            'responses': {},
            'feedback': {},
            'started_at': datetime.now().isoformat()
        }
        return session_id

    def record_response(self, question_id: str, response: str,
                       time_used_minutes: int) -> Dict[str, Any]:
        if not self.current_session:
            raise ValueError("No active interview session")

        question = None
        for q in self.current_session.get('questions', []):
            if q.id == question_id:
                question = q
                break

        if not question:
            raise ValueError(f"Question not found: {question_id}")

        evaluation = self._evaluate_response(question, response, time_used_minutes)

        self.current_session['responses'][question_id] = {
            'response': response,
            'time_used_minutes': time_used_minutes,
            'evaluation': evaluation
        }
        return evaluation

    def _evaluate_response(self, question: InterviewQuestion,
                          response: str, time_used: int) -> Dict[str, Any]:
        eval_prompt = f"""As an FDE interviewer, evaluate this answer:

## Question
{question.question}

## Evaluation Criteria
{chr(10).join(f"- {c}" for c in question.evaluation_criteria)}

## Answer
{response}

## Time
Required: {question.time_limit_minutes} min, Used: {time_used} min

Score (1-10) on: content_quality, logic_clarity, practical_relevance, communication, time_management.
Return JSON with these fields and improvement_suggestions array."""

        try:
            ai_resp = self._client.chat.completions.create(
                model=self._chat_model,
                max_tokens=1000,
                messages=[{"role": "user", "content": eval_prompt}]
            )
            text = ai_resp.choices[0].message.content
            text = re.sub(r'<think>.*?', '', text, flags=re.DOTALL).strip()

            m = re.search(r'\{.*\}', text, re.DOTALL)
            if m:
                raw = json.loads(m.group())
                ev = {
                    'content_quality': raw.get('content_quality', 5),
                    'logic_clarity': raw.get('logic_clarity', raw.get('logical_clarity', 5)),
                    'practical_relevance': raw.get('practical_relevance', 5),
                    'communication': raw.get('communication', 5),
                    'time_management': raw.get('time_management', 5),
                    'improvement_suggestions': raw.get('improvement_suggestions', raw.get('suggestions', [])),
                }
                ev['total_score'] = (ev['content_quality'] + ev['logic_clarity'] +
                                      ev['practical_relevance'] + ev['communication'] +
                                      ev['time_management']) / 5
            else:
                ev = self._generate_default_evaluation(question, response, time_used)
        except Exception as e:
            print(f"[WARNING] AI evaluation failed: {e}")
            ev = self._generate_default_evaluation(question, response, time_used)

        return ev

    def _generate_default_evaluation(self, question, response, time_used):
        l = len(response)
        cq = min(10, max(1, int(l / 50)))
        lc = min(10, max(1, int(response.count('\n') / 3)))
        pr = min(10, max(1, int((response.count('implement') + response.count('deploy')) / 2)))
        com = min(10, max(1, int((response.count('because') + response.count('therefore')))))
        tm = min(10, max(1, int((question.time_limit_minutes / time_used) * 5)))
        total = (cq + lc + pr + com + tm) / 5
        return {
            'content_quality': cq, 'logic_clarity': lc,
            'practical_relevance': pr, 'communication': com,
            'time_management': tm, 'total_score': total,
            'improvement_suggestions': ['Add more practical examples', 'Improve answer structure', 'Connect more with business scenarios']
        }

    # ── 报告生成 ────────────────────────────────────────────────────

    def generate_interview_report(self) -> Dict[str, Any]:
        if not self.current_session:
            raise ValueError("No active interview session")

        all_evals = list(self.current_session['responses'].values())
        if not all_evals:
            return {'error': 'No responses recorded'}

        avg = {
            'content_quality': sum(e['evaluation'].get('content_quality', 0) for e in all_evals) / len(all_evals),
            'logic_clarity': sum(e['evaluation'].get('logic_clarity', 0) for e in all_evals) / len(all_evals),
            'practical_relevance': sum(e['evaluation'].get('practical_relevance', 0) for e in all_evals) / len(all_evals),
            'communication': sum(e['evaluation'].get('communication', 0) for e in all_evals) / len(all_evals),
            'time_management': sum(e['evaluation'].get('time_management', 0) for e in all_evals) / len(all_evals),
        }
        avg['total'] = sum(avg.values()) / len(avg)

        suggestions = self._generate_improvement_suggestions(avg)

        self.current_session['completed_at'] = datetime.now().isoformat()
        self.current_session['overall_performance'] = avg
        self.current_session['improvement_suggestions'] = suggestions

        self._save_interview_report()

        return {
            'session_id': self.current_session['session_id'],
            'overall_performance': avg,
            'improvement_suggestions': suggestions,
            'detailed_responses': self.current_session['responses']
        }

    def _generate_improvement_suggestions(self, scores: Dict[str, float]) -> List[str]:
        s = []
        if scores['content_quality'] < 7:
            s.append('建议深入阅读相关技术文档，增加知识深度')
            s.append('可以多参与实际项目，积累实战经验')
        if scores['logic_clarity'] < 7:
            s.append('建议练习结构化表达，使用 STAR 方法组织回答')
            s.append('可以多做思维导图，提升逻辑思维能力')
        if scores['practical_relevance'] < 7:
            s.append('建议多关注行业案例和最佳实践')
            s.append('可以尝试将理论知识应用到实际项目中')
        if scores['communication'] < 7:
            s.append('建议多练习口头表达，提升沟通能力')
            s.append('可以学习商务沟通技巧和演示技能')
        if scores['time_management'] < 7:
            s.append('建议在练习时严格控制时间')
            s.append('可以学会快速抓住问题核心，避免过度展开')
        if not s:
            s.append('整体表现优秀，继续保持')
            s.append('可以尝试更有挑战性的题目')
        return s

    def _save_interview_report(self):
        reports_dir = self.project_root / "docs" / "interview_reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        report_file = reports_dir / f"{self.current_session['session_id']}.json"

        session_data = {**self.current_session}
        session_data['questions'] = [
            asdict(q) if hasattr(q, '__dataclass_fields__') else q
            for q in self.current_session.get('questions', [])
        ]

        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, ensure_ascii=False, indent=2)
        print(f"[OK] Report saved: {report_file}")

    def export_to_obsidian(self, report: Dict[str, Any]) -> str:
        obsidian_path = self.project_root / "templates" / "interview_reports"
        obsidian_path.mkdir(parents=True, exist_ok=True)
        report_file = obsidian_path / f"{report['session_id']}.md"

        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(self._generate_obsidian_report(report))
        print(f"[OK] Exported to Obsidian: {report_file}")
        return str(report_file)

    def _generate_obsidian_report(self, report: Dict[str, Any]) -> str:
        session = report['session_id']
        perf = report['overall_performance']
        suggestions = report['improvement_suggestions']

        # Build question map
        qmap = {}
        if self.current_session:
            for q in self.current_session.get('questions', []):
                qmap[q.id] = q

        content = f"""# FDE Interview Report

**Session ID**: {session}
**Role**: {self.role}
**Level**: {self.level}

## Overall Performance

| Dimension | Score | Rating |
|-----------|-------|--------|
| Content Quality | {perf['content_quality']:.1f}/10 | {"Excellent" if perf['content_quality'] >= 8 else "Good" if perf['content_quality'] >= 6 else "Needs Improvement"} |
| Logic Clarity | {perf['logic_clarity']:.1f}/10 | {"Excellent" if perf['logic_clarity'] >= 8 else "Good" if perf['logic_clarity'] >= 6 else "Needs Improvement"} |
| Practical Relevance | {perf['practical_relevance']:.1f}/10 | {"Excellent" if perf['practical_relevance'] >= 8 else "Good" if perf['practical_relevance'] >= 6 else "Needs Improvement"} |
| Communication | {perf['communication']:.1f}/10 | {"Excellent" if perf['communication'] >= 8 else "Good" if perf['communication'] >= 6 else "Needs Improvement"} |
| Time Management | {perf['time_management']:.1f}/10 | {"Excellent" if perf['time_management'] >= 8 else "Good" if perf['time_management'] >= 6 else "Needs Improvement"} |

**Total Score**: {perf['total']:.1f}/10

## Improvement Suggestions

"""
        for i, sug in enumerate(suggestions, 1):
            content += f"{i}. {sug}\n"

        content += "\n## Detailed Responses\n\n"

        for qid, resp_data in report['detailed_responses'].items():
            q = qmap.get(qid)
            if not q:
                continue
            ev = resp_data['evaluation']
            content += f"""### {q.question}

**Category**: {q.category} | **Difficulty**: {q.difficulty} | **Type**: {q.type}

**Time**: {resp_data['time_used_minutes']} min (required: {q.time_limit_minutes} min)

**Score**: {ev.get('total_score', 0):.1f}/10

#### Answer
> {resp_data['response']}

#### Evaluation
- Content Quality: {ev.get('content_quality', 0)}/10
- Logic Clarity: {ev.get('logic_clarity', 0)}/10
- Practical Relevance: {ev.get('practical_relevance', 0)}/10
- Communication: {ev.get('communication', 0)}/10
- Time Management: {ev.get('time_management', 0)}/10

#### Suggestions
"""
            for sug in ev.get('improvement_suggestions', []):
                content += f"- {sug}\n"

            if q.follow_up_questions:
                content += "\n#### Follow-up Questions\n"
                for fu in q.follow_up_questions:
                    content += f"- {fu}\n"

            content += "\n---\n\n"

        content += f"""
## Next Steps

Based on this interview, focus on improving:

1. **Short-term (1-2 weeks)**: Practice {self._get_weakest_area(perf)} specifically
2. **Medium-term (1 month)**: Deepen domain knowledge and apply to projects
3. **Long-term (3 months)**: Achieve 8+ in all dimensions consistently

---
**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**FDE Knowledge Hub - Interview System**
"""
        return content

    def _get_weakest_area(self, scores: Dict[str, float]) -> str:
        areas = {k: v for k, v in scores.items() if k != 'total'}
        weakest = min(areas, key=areas.get)
        names = {
            'content_quality': 'Content Quality',
            'logic_clarity': 'Logic Clarity',
            'practical_relevance': 'Practical Relevance',
            'communication': 'Communication',
            'time_management': 'Time Management'
        }
        return names.get(weakest, weakest)


# ── CLI ────────────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(description='FDE Interview Preparation System')
    parser.add_argument('--role', '-r', default='FDE')
    parser.add_argument('--level', '-l', default='senior')
    parser.add_argument('--count', '-n', type=int, default=5)
    parser.add_argument('--interactive', '-i', action='store_true')
    parser.add_argument('--role-requirement', required=True, help='Role requirements (required)')

    args = parser.parse_args()

    from dotenv import load_dotenv
    load_dotenv()
    config = os.environ

    interviewer = FDEMockInterview(config, role=args.role, level=args.level)

    print(f"\n[AI] Question Generation Mode")
    print(f"Role Requirements: {args.role_requirement}\n")

    questions = interviewer.generate_interview_questions(
        count=args.count,
        role_requirement=args.role_requirement,
    )
    print(f"[OK] Generated {len(questions)} questions\n")

    if args.interactive:
        session_id = interviewer.start_interview_session(questions)

        for i, q in enumerate(questions, 1):
            print(f"[{i}/{len(questions)}] {q.question}")
            print(f"[Category: {q.category}] [Difficulty: {q.difficulty}]")
            print(f"[Time Limit: {q.time_limit_minutes} min]")
            if q.hint:
                print(f"[Hint: {q.hint}]")
            print("\nPlease begin your answer...")

            import time
            start = time.time()
            response = input("Your answer: ")
            end = time.time()
            time_used = (end - start) / 60

            evaluation = interviewer.record_response(q.id, response, time_used)

            print(f"\n[Evaluation] Total Score: {evaluation['total_score']:.1f}/10")
            for crit, score in evaluation.items():
                if crit not in ('total_score', 'improvement_suggestions'):
                    print(f"  {crit}: {score}/10")

            if evaluation.get('improvement_suggestions'):
                print(f"\n[Suggestions]")
                for s in evaluation['improvement_suggestions']:
                    print(f"  - {s}")

            print("\n" + "="*50 + "\n")

        print("[Report] Generating interview report...")
        report = interviewer.generate_interview_report()

        print(f"\nOverall Score: {report['overall_performance']['total']:.1f}/10")
        print("\nImprovement Suggestions:")
        for s in report['improvement_suggestions']:
            print(f"- {s}")

        if input("\nExport to Obsidian? (y/n): ").strip().lower() == 'y':
            path = interviewer.export_to_obsidian(report)
            print(f"[OK] Report exported: {path}")
    else:
        for i, q in enumerate(questions, 1):
            print(f"[{i}/{len(questions)}] {q.question}")
            print(f"Category: {q.category} | Difficulty: {q.difficulty} | Type: {q.type}")
            if q.hint:
                print(f"Hint: {q.hint}")
            print()


if __name__ == '__main__':
    main()