# FDE Knowledge Hub - 系统架构文档

## 🏗️ 整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        用户交互层                                │
├─────────────────────────────────────────────────────────────────┤
│  Obsidian UI  │  CLI 工具  │  Web 接口  │  AI 对话界面        │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│                       业务逻辑层                                  │
├─────────────────────────────────────────────────────────────────┤
│  知识管理  │  学习路径  │  面试准备  │  智能复习             │
│  模块      │  生成器    │  系统      │  系统                 │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│                       AI 服务层                                  │
├─────────────────────────────────────────────────────────────────┤
│  Claude API  │  NotebookLM  │  本地 LLM  │  混合推理        │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│                       数据存储层                                  │
├─────────────────────────────────────────────────────────────────┤
│  向量数据库  │  文件存储  │  知识图谱        │
│  (Qdrant)   │  (Obsidian)│  (NetworkX)     │
└─────────────────────────────────────────────────────────────────┘
```

## 🔧 技术架构详解

### 1. 知识摄取子系统

```python
class FDEKnowledgeIngester:
    """知识摄取核心类"""
    
    def __init__(self, config):
        self.embeddings = OpenAIEmbeddings()
        self.qdrant_client = QdrantClient()
        self.processors = {
            'pdf': PDFProcessor(),
            'markdown': MarkdownProcessor(),
            'code': CodeProcessor()
        }
    
    def process_source(self, source: Dict) -> List[KnowledgeChunk]:
        """处理单个知识源"""
        processor = self.processors[source['type']]
        chunks = processor.process(source['path'])
        return self._enrich_chunks(chunks, source['metadata'])
    
    def index_knowledge(self, chunks: List[KnowledgeChunk]):
        """索引知识到向量数据库"""
        vectors = [self.embeddings.embed_query(chunk.text) for chunk in chunks]
        points = self._create_points(chunks, vectors)
        self.qdrant_client.upsert("fde_knowledge", points)
```

### 2. 学习路径生成子系统

```python
class FDELearningPathGenerator:
    """学习路径生成核心类"""
    
    def __init__(self, config):
        self.anthropic = Anthropic()
        self.knowledge_graph = self._build_knowledge_graph()
        self.learning_modules = self._load_learning_modules()
    
    def generate_personalized_path(self, user_profile: Dict) -> Dict:
        """生成个性化学习路径"""
        # 1. 分析当前能力
        current_skills = self.analyze_current_skills()
        
        # 2. 识别能力缺口
        skill_gaps = self._identify_skill_gaps(current_skills)
        
        # 3. 拓扑排序学习模块
        ordered_modules = self._topological_sort(skill_gaps)
        
        # 4. AI 增强建议
        ai_suggestions = self._get_ai_suggestions(ordered_modules)
        
        # 5. 生成详细计划
        detailed_plan = self._generate_detailed_plan(ordered_modules, ai_suggestions)
        
        return detailed_plan
```

### 3. 面试准备子系统

```python
class FDEMockInterview:
    """面试准备核心类"""
    
    def __init__(self, config, role: str, level: str):
        self.anthropic = Anthropic()
        self.question_bank = self._load_question_bank()
        self.evaluation_criteria = self._load_evaluation_criteria()
    
    def generate_interview_session(self, count: int) -> List[InterviewQuestion]:
        """生成面试会话"""
        questions = self._select_balanced_questions(count)
        session_id = self._create_session(questions)
        return questions
    
    def evaluate_response(self, question: InterviewQuestion, response: str) -> Dict:
        """评估回答质量"""
        # 使用 AI 进行多维评估
        evaluation = self.anthropic.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=1000,
            messages=[{
                "role": "user",
                "content": self._build_evaluation_prompt(question, response)
            }]
        )
        return self._parse_evaluation(evaluation)
```

### 4. 智能复习子系统

```python
class SpacedRepetitionSystem:
    """间隔重复学习核心类"""
    
    def __init__(self, config):
        self.review_items = self._load_review_data()
        self.sm2_algorithm = SM2Algorithm()
    
    def get_due_reviews(self) -> List[ReviewItem]:
        """获取到期复习项目"""
        now = datetime.now()
        due_items = [
            item for item in self.review_items.values()
            if datetime.fromisoformat(item.next_review) <= now
        ]
        
        # 按重要性和遗忘指数排序
        return sorted(due_items, key=lambda x: (
            self._importance_weight(x.importance),
            x.forgetting_index
        ), reverse=True)
    
    def record_review(self, item_id: str, quality: int):
        """记录复习结果"""
        item = self.review_items[item_id]
        
        # 应用 SM-2 算法
        new_interval = self.sm2_algorithm.calculate_interval(
            item.interval_days,
            item.ease_factor,
            quality,
            item.repetition_count
        )
        
        # 更新项目状态
        item.interval_days = new_interval['interval']
        item.ease_factor = new_interval['ease_factor']
        item.repetition_count += 1
        item.next_review = self._calculate_next_review(new_interval['interval'])
```

## 🗄️ 数据架构

### 知识存储模型

#### 向量数据模型
```python
@dataclass
class VectorDataPoint:
    """向量数据点"""
    id: str                    # 唯一标识符
    vector: List[float]         # 嵌入向量
    text: str                  # 原始文本
    metadata: Dict[str, Any]    # 元数据
    category: str              # 分类标签
    difficulty: str            # 难度等级
    source: str                # 来源文件
    timestamp: str             # 处理时间戳
    hash: str                  # 内容哈希
```

#### 知识图谱模型
```python
@dataclass
class KnowledgeNode:
    """知识图谱节点"""
    id: str                    # 节点ID
    title: str                 # 节点标题
    type: str                  # 节点类型
    category: str              # 分类
    importance: float          # 重要性权重
    created_at: str            # 创建时间
    updated_at: str            # 更新时间

@dataclass
class KnowledgeEdge:
    """知识图谱边"""
    source: str                # 源节点
    target: str                # 目标节点
    relation: str              # 关系类型
    weight: float              # 关系权重
    created_at: str            # 创建时间
```

### 学习进度模型

#### 学习模块模型
```python
@dataclass
class LearningModule:
    """学习模块"""
    id: str                    # 模块ID
    title: str                 # 模块标题
    description: str           # 描述
    category: str              # 分类
    difficulty: str            # 难度
    duration_weeks: int        # 持续时间(周)
    prerequisites: List[str]   # 前置模块
    resources: List[Dict]      # 学习资源
    projects: List[str]        # 实践项目
    objectives: List[str]      # 学习目标
```

#### 学习路径模型
```python
@dataclass
class LearningPath:
    """学习路径"""
    id: str                    # 路径ID
    user_id: str               # 用户ID
    created_at: str            # 创建时间
    phases: Dict[str, List]    # 学习阶段
    timeline: Dict[str, Any]   # 时间线
    milestones: List[Dict]     # 里程碑
    ai_suggestions: Dict[str, Any]  # AI建议
    success_criteria: Dict[str, List[str]]  # 成功标准
```

## 🔌 外部集成架构

### 1. Obsidian 集成

```python
class ObsidianIntegration:
    """Obsidian 集成类"""
    
    def __init__(self, vault_path: Path):
        self.vault_path = vault_path
        self.note_parser = ObsidianNoteParser()
        self.link_analyzer = ObsidianLinkAnalyzer()
    
    def scan_notes(self) -> List[Dict]:
        """扫描所有笔记"""
        notes = list(self.vault_path.rglob("*.md"))
        return [self.note_parser.parse(note) for note in notes]
    
    def analyze_links(self, notes: List[Dict]) -> nx.DiGraph:
        """分析链接关系"""
        graph = nx.DiGraph()
        for note in notes:
            graph.add_node(note['id'], **note['metadata'])
        
        for note in notes:
            links = note['links']
            for link in links:
                graph.add_edge(note['id'], link['target'], 
                              relation=link['type'])
        
        return graph
    
    def export_template(self, template_name: str, data: Dict) -> str:
        """导出模板笔记"""
        template_file = self.vault_path / "templates" / f"{template_name}.md"
        return self._render_template(template_file, data)
```

### 2. NotebookLM 集成

```python
class NotebookLMIntegration:
    """NotebookLM 集成类"""
    
    def __init__(self, api_key: str):
        self.client = NotebookLMClient(api_key=api_key)
        self.sync_state = self._load_sync_state()
    
    def sync_documents(self, documents: List[Dict]) -> bool:
        """同步文档到 NotebookLM"""
        try:
            # 批量上传文档
            batch_results = []
            for doc in documents:
                result = self.client.upload_document(
                    title=doc['title'],
                    content=doc['content'],
                    metadata=doc['metadata']
                )
                batch_results.append(result)
            
            # 更新同步状态
            self._update_sync_state(batch_results)
            return True
            
        except Exception as e:
            print(f"同步失败: {e}")
            return False
    
    def query_knowledge(self, query: str) -> List[Dict]:
        """查询知识库"""
        return self.client.query(query, include_sources=True)
```

### 3. Claude API 集成

```python
class ClaudeIntegration:
    """Claude API 集成类"""
    
    def __init__(self, api_key: str):
        self.client = Anthropic(api_key=api_key)
        self.context_manager = ContextManager()
    
    def analyze_query(self, query: str, context: List[Dict]) -> Dict:
        """分析查询"""
        # 构建上下文
        relevant_context = self.context_manager.select_relevant(
            query, context
        )
        
        # 生成分析
        response = self.client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=2000,
            messages=[{
                "role": "user",
                "content": self._build_analysis_prompt(query, relevant_context)
            }]
        )
        
        return self._parse_analysis_response(response)
    
    def generate_code(self, task: str, language: str) -> str:
        """生成代码"""
        response = self.client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=4000,
            messages=[{
                "role": "user",
                "content": self._build_code_generation_prompt(task, language)
            }]
        )
        
        return response.content[0].text
```

## 🚀 性能优化策略

### 1. 检索优化

#### 混合检索策略
```python
class HybridRetriever:
    """混合检索器"""
    
    def retrieve(self, query: str, top_k: int = 5) -> List[Dict]:
        """混合检索"""
        # 语义检索
        semantic_results = self._semantic_search(query, top_k * 2)
        
        # 关键词检索
        keyword_results = self._keyword_search(query, top_k * 2)
        
        # 结果融合
        fused_results = self._reciprocal_rank_fusion(
            semantic_results,
            keyword_results,
            top_k
        )
        
        # 重排序
        reranked_results = self._rerank_results(query, fused_results)
        
        return reranked_results[:top_k]
```

#### 缓存策略
```python
class KnowledgeCache:
    """知识缓存"""
    
    def __init__(self):
        self.semantic_cache = TTLCache(maxsize=1000, ttl=3600)
        self.embedding_cache = TTLCache(maxsize=5000, ttl=86400)
        self.result_cache = TTLCache(maxsize=2000, ttl=1800)
    
    def get_cached_embedding(self, text: str) -> List[float]:
        """获取缓存的嵌入向量"""
        return self.embedding_cache.get(text)
    
    def cache_embedding(self, text: str, embedding: List[float]):
        """缓存嵌入向量"""
        self.embedding_cache[text] = embedding
```

### 2. 学习路径优化

#### 动态调整算法
```python
class DynamicPathAdjuster:
    """动态路径调整器"""
    
    def adjust_path(self, current_path: Dict, user_performance: Dict) -> Dict:
        """根据用户表现动态调整学习路径"""
        # 分析用户表现
        performance_analysis = self._analyze_performance(user_performance)
        
        # 识别需要调整的模块
        adjustments = self._identify_adjustments(current_path, performance_analysis)
        
        # 应用调整
        adjusted_path = self._apply_adjustments(current_path, adjustments)
        
        # 验证路径有效性
        if self._validate_path(adjusted_path):
            return adjusted_path
        else:
            return current_path  # 保持原路径
```

### 3. 面试系统优化

#### 自适应难度调整
```python
class AdaptiveDifficulty:
    """自适应难度调整"""
    
    def calibrate_difficulty(self, user_history: List[Dict]) -> str:
        """根据历史表现调整难度"""
        # 计算用户能力水平
        ability_level = self._calculate_ability_level(user_history)
        
        # 调整难度
        if ability_level > 0.8:
            return 'expert'
        elif ability_level > 0.6:
            return 'senior'
        elif ability_level > 0.4:
            return 'intermediate'
        else:
            return 'beginner'
```

## 🔐 安全架构

### 1. 数据安全

#### 敏感信息保护
```python
class DataSanitizer:
    """数据清理器"""
    
    def __init__(self, config: Dict):
        self.sensitive_patterns = [
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # 邮箱
            r'\b\d{3}-\d{4}-\d{4}\b',  # 电话号
            r'\b\d{16,19}\b',        # 银行卡号
            r'\b(?:api|token|secret|key)\s*[:=]\s*["\']?[^"\']+\b',  # API密钥
        ]
    
    def sanitize_text(self, text: str) -> str:
        """清理敏感文本"""
        for pattern in self.sensitive_patterns:
            text = re.sub(pattern, '[REDACTED]', text)
        return text
```

#### 访问控制
```python
class AccessController:
    """访问控制器"""
    
    def __init__(self, config: Dict):
        self.roles = config.get('roles', {})
        self.permissions = config.get('permissions', {})
    
    def check_permission(self, user_role: str, action: str, resource: str) -> bool:
        """检查权限"""
        role_permissions = self.roles.get(user_role, [])
        action_permissions = self.permissions.get(action, [])
        
        return (action in role_permissions and 
                resource in action_permissions)
```

### 2. API 安全

#### 请求限流
```python
class RateLimiter:
    """请求限流器"""
    
    def __init__(self, max_requests: int, time_window: int):
        self.max_requests = max_requests
        self.time_window = time_window
        self.request_history = defaultdict(list)
    
    def is_allowed(self, user_id: str) -> bool:
        """检查是否允许请求"""
        now = time.time()
        user_history = self.request_history[user_id]
        
        # 清理过期记录
        user_history = [t for t in user_history if now - t < self.time_window]
        
        if len(user_history) >= self.max_requests:
            return False
        
        user_history.append(now)
        return True
```

## 📊 监控和可观测性

### 1. 性能监控

#### 系统指标收集
```python
class MetricsCollector:
    """指标收集器"""
    
    def __init__(self):
        self.metrics = defaultdict(list)
        self.alerts = []
    
    def record_metric(self, metric_name: str, value: float):
        """记录指标"""
        self.metrics[metric_name].append({
            'value': value,
            'timestamp': datetime.now().isoformat()
        })
        
        # 检查阈值
        self._check_thresholds(metric_name, value)
    
    def _check_thresholds(self, metric_name: str, value: float):
        """检查阈值"""
        thresholds = self._get_thresholds(metric_name)
        
        if 'warning' in thresholds and value > thresholds['warning']:
            self.alerts.append({
                'level': 'warning',
                'metric': metric_name,
                'value': value,
                'threshold': thresholds['warning']
            })
        
        if 'critical' in thresholds and value > thresholds['critical']:
            self.alerts.append({
                'level': 'critical',
                'metric': metric_name,
                'value': value,
                'threshold': thresholds['critical']
            })
```

### 2. 日志系统

#### 结构化日志
```python
class StructuredLogger:
    """结构化日志器"""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        # JSON 格式化器
        formatter = logging.Formatter('{"timestamp": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}')
        
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # 文件处理器
        file_handler = logging.FileHandler('logs/fde_hub.log')
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
    
    def log_event(self, event_type: str, **kwargs):
        """记录事件"""
        log_data = {
            'event_type': event_type,
            **kwargs
        }
        self.logger.info(json.dumps(log_data))
```

## 🔄 扩展性设计

### 1. 插件系统

#### 插件接口
```python
class FDEPlugin:
    """插件基类"""
    
    def __init__(self, config: Dict):
        self.config = config
    
    def initialize(self):
        """初始化插件"""
        pass
    
    def execute(self, **kwargs) -> Any:
        """执行插件功能"""
        raise NotImplementedError
    
    def cleanup(self):
        """清理资源"""
        pass
```

### 2. 数据源扩展

#### 数据源接口
```python
class DataSource(ABC):
    """数据源抽象类"""
    
    @abstractmethod
    def extract(self, source_path: str) -> List[Dict]:
        """提取数据"""
        pass
    
    @abstractmethod
    def validate(self, data: Dict) -> bool:
        """验证数据"""
        pass
    
    @abstractmethod
    def transform(self, data: Dict) -> KnowledgeChunk:
        """转换数据"""
        pass

class PDFDataSource(DataSource):
    """PDF 数据源"""
    
    def extract(self, source_path: str) -> List[Dict]:
        # PDF 提取逻辑
        pass

class MarkdownDataSource(DataSource):
    """Markdown 数据源"""
    
    def extract(self, source_path: str) -> List[Dict]:
        # Markdown 提取逻辑
        pass
```

## 🎯 架构优势

### 1. 模块化设计
- **松耦合**: 各子系统独立运行，便于维护和扩展
- **可替换**: 相同接口的不同实现可以互相替换
- **可测试**: 每个模块都可以独立测试

### 2. 可扩展性
- **插件化**: 支持自定义插件扩展功能
- **数据源**: 支持多种数据源格式
- **AI 模型**: 支持多种 AI 模型和接口

### 3. 性能优化
- **缓存策略**: 多级缓存提升响应速度
- **混合检索**: 结合多种检索算法提升准确性
- **异步处理**: 支持异步处理大量任务

### 4. 用户体验
- **多界面**: 支持 CLI、Web、Obsidian 多种界面
- **智能推荐**: AI 驱动的个性化推荐
- **自适应**: 根据用户表现自动调整

这个架构设计确保了系统的高可维护性、可扩展性和用户体验，为 FDE 面试准备提供了坚实的技术基础。

---

**架构版本**: 1.0.0
**最后更新**: 2026-05-17
**维护者**: 邵炎炎