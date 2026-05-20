# FDE Knowledge Hub - 完整安装指南

本指南将帮助你从零开始搭建完整的 FDE 知识管理系统。

## 🎯 系统要求

### 必需环境
- **Python**: 3.9 或更高版本
- **Obsidian**: 最新版本 (https://obsidian.md/download)
- **Git**: 用于版本控制

### 可选环境
- **Docker**: 用于运行向量数据库
- **Ollama**: 用于本地 LLM 推理
- **Google Account**: 用于使用 NotebookLM

## 📦 安装步骤

### 1. 环境准备

#### 1.1 安装 Python
```bash
# Windows: 从 python.org 下载安装包
# macOS: brew install python@3.9
# Linux: sudo apt install python3.9 python3-pip
```

#### 1.2 安装 Obsidian
1. 访问 https://obsidian.md/download
2. 下载适合你操作系统的版本
3. 安装并打开 Obsidian

#### 1.2 克隆项目
```bash
git clone https://github.com/yourusername/FDE-Knowledge-Hub.git
cd FDE-Knowledge-Hub
```

### 2. Python 环境配置

#### 2.1 创建虚拟环境
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

#### 2.2 安装依赖
```bash
# 安装核心依赖
pip install -r requirements.txt

# 或安装开发版本（包含开发工具）
pip install -e ".[dev]"
```

### 3. 环境变量配置

#### 3.1 复制环境变量模板
```bash
cp .env.example .env
```

#### 3.2 编辑 .env 文件
```bash
# 使用你喜欢的编辑器打开 .env 文件
# Windows: notepad .env
# macOS/Linux: nano .env 或 vim .env
```

#### 3.3 配置 API 密钥
```env
# AI API Keys
ANTHROPIC_API_KEY=your_anthropic_api_key_here
OPENAI_API_KEY=your_openai_api_key_here

# NotebookLM (可选)
GOOGLE_API_KEY=your_google_api_key_here
NOTEBOOKLM_PROJECT_ID=your_project_id_here

# Vector Database (可选)
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=your_qdrant_api_key_here

# 自动化设置
ENABLE_AUTO_SYNC=true
SYNC_INTERVAL_HOURS=6
```

### 4. Obsidian 配置

#### 4.1 打开知识库
1. 打开 Obsidian
2. 点击 "打开文件夹作为仓库"
3. 选择 `FDE-Knowledge-Hub` 目录
4. 点击 "打开"

#### 4.2 安装推荐插件

在 Obsidian 中：
1. 点击 ⚙️ (设置) → 社区插件
2. 关闭安全模式
3. 点击 "浏览" 并搜索以下插件：
   - **Dataview**: 数据查询和展示
   - **Templater**: 模板系统
   - **Calendar**: 日历视图
   - **Tasks**: 任务管理
   - **QuickAdd**: 快速添加内容
   - **Homepage**: 设置首页

#### 4.3 配置插件

**Dataview 配置**:
- 启用 JavaScript 查询
- 设置默认查询视图

**Templater 配置**:
- 设置模板文件夹为 `templates/`
- 启用系统命令执行

**Calendar 配置**:
- 设置笔记文件夹为 `00-Inbox/`
- 配置日期格式

### 5. 可选服务配置

#### 5.1 向量数据库 (Qdrant)

**使用 Docker**:
```bash
# 启动 Qdrant
docker run -p 6333:6333 qdrant/qdrant

# 验证运行
curl http://localhost:6333/
```

**或使用本地安装**:
```bash
# 下载并安装 Qdrant
# 访问: https://qdrant.tech/documentation/guides/installation/
```

#### 5.2 NotebookLM 配置

1. 访问 https://notebooklm.google.com/
2. 创建新项目
3. 获取项目 ID
4. 配置 Google API 密钥
5. 在 `.env` 文件中设置相应变量

#### 5.3 Ollama (本地 LLM)

```bash
# 安装 Ollama
# 访问: https://ollama.ai/download

# 拉取模型
ollama pull llama2
ollama pull mistral

# 验证运行
ollama run llama2 "Hello, world!"
```

## 🚀 快速开始

### 基础功能测试

#### 1. 测试命令行工具
```bash
# 激活虚拟环境
# Windows: venv\Scripts\activate
# macOS/Linux: source venv/bin/activate

# 测试系统状态
fde-cli status

# 测试知识摄取
fde-cli ingest --help

# 测试学习路径生成
fde-cli path --help

# 测试面试准备
fde-cli interview --help
```

#### 2. 创建第一个笔记

在 Obsidian 中：
1. 打开 `core/foundation/programming/` 目录
2. 点击新建文件按钮
3. 选择 "编程基础与代码质量" 模板
4. 开始记录你的学习笔记

#### 3. 生成学习路径

```bash
# 生成完整 FDE 学习路径
fde-cli path --topic fde --hours 10

# 导出到 Obsidian
fde-cli path --topic fde --hours 10 --export
```

#### 4. 开始面试练习

```bash
# 开始模拟面试
fde-cli interview --role FDE --difficulty senior

# 交互式练习模式
fde-cli interview --role FDE --difficulty senior --interactive
```

### 第一次知识摄取

#### 1. 准备学习资料
将你的电子书、论文、代码示例放入相应目录：
```bash
# 书籍
assets/books/AI_Engineering.pdf

# 论文
assets/papers/rag-paper.pdf

# 代码示例
assets/code-examples/rag_system.py
```

#### 2. 执行知识摄取
```bash
# 摄取所有资料
fde-cli ingest

# 摄取特定分类
fde-cli ingest --category ai-engineering

# 摄取特定难度
fde-cli ingest --difficulty intermediate
```

#### 3. 在 Obsidian 中查看
摄取完成后，在 Obsidian 中查看生成的笔记：
1. 打开 `core/` 目录
2. 查看新生成的笔记
3. 建立知识关联
4. 添加个人理解

## 🔧 高级配置

### 自定义学习模块

编辑 `docs/learning_modules.json`：

```json
{
  "custom_module_id": {
    "id": "custom_module_id",
    "title": "自定义学习模块",
    "description": "模块描述",
    "category": "ai-engineering",
    "difficulty": "intermediate",
    "duration_weeks": 4,
    "prerequisites": [],
    "resources": [
      {"type": "book", "title": "书籍名", "author": "作者"}
    ],
    "projects": ["项目一", "项目二"],
    "learning_objectives": ["目标一", "目标二"]
  }
}
```

### 自定义面试题

编辑 `docs/interview_questions.json`：

```json
{
  "questions": [
    {
      "id": "fde_custom_001",
      "question": "自定义面试题",
      "category": "自定义分类",
      "difficulty": "senior",
      "type": "technical",
      "context": "题目背景",
      "hint": "提示信息",
      "reference_answer": "参考答案",
      "evaluation_criteria": ["评估标准"],
      "time_limit_minutes": 15,
      "follow_up_questions": ["追问一", "追问二"]
    }
  ]
}
```

### 自定义模板

在 `templates/` 目录下创建新模板：

```markdown
---
type: custom_template
tags: ["模板"]
---

# 模板标题

模板内容...

## 使用方法
1. 步骤一
2. 步骤二
3. 步骤三

## 注意事项
- 注意事项一
- 注意事项二
```

## 📊 系统监控

### 查看系统状态
```bash
# 查看详细状态
fde-cli status

# 查看知识统计
python automation/knowledge_stats.py
```

### 查看学习进度
```bash
# 查看当前学习路径
cat docs/current_learning_path.json

# 查看学习进度
cat docs/learning_progress.json
```

### 查看面试记录
```bash
# 查看面试报告列表
ls docs/interview_reports/

# 查看特定报告
cat docs/interview_reports/interview_20240517_143022.json
```

## 🐛 故障排除

### 常见问题

#### 1. 依赖安装失败
```bash
# 升级 pip
pip install --upgrade pip

# 使用国内镜像
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

#### 2. API 密钥无效
- 检查 `.env` 文件格式
- 确认 API 密钥有效且有足够额度
- 检查网络连接

#### 3. Obsidian 插件安装失败
- 检查 Obsidian 版本是否最新
- 尝试重启 Obsidian
- 检查网络连接

#### 4. 向量数据库连接失败
```bash
# 检查 Qdrant 是否运行
curl http://localhost:6333/

# 重启 Qdrant
docker restart <qdrant_container_id>
```

#### 5. 知识摄取失败
```bash
# 检查文件格式
# 确认支持 PDF、MD、PY 等格式

# 查看详细错误信息
fde-cli ingest --debug
```

### 获取帮助

如果遇到问题：
1. 查看 GitHub Issues
2. 检查日志文件
3. 运行诊断命令
4. 联系维护者

```bash
# 运行诊断
python automation/diagnostics.py

# 查看日志
cat logs/fde_hub.log
```

## 📈 性能优化

### 系统性能
- 使用向量数据库加速检索
- 启用缓存机制
- 批量处理大量文件

### 学习效率
- 使用间隔重复系统
- 定期回顾学习进度
- 基于反馈调整学习路径

### 存储优化
- 压缩大型文件
- 清理重复内容
- 归档旧的学习记录

## 🔄 系统维护

### 日常维护
```bash
# 每日同步
fde-cli sync

# 每周复习提醒
fde-cli review --review-type weekly

# 每月进度更新
fde-cli status
```

### 定期更新
```bash
# 更新依赖
pip install --upgrade -r requirements.txt

# 更新知识库
fde-cli ingest --update

# 更新学习路径
fde-cli path --update
```

### 备份策略
```bash
# 备份 Obsidian Vault
rsync -av /path/to/FDE-Knowledge-Hub /backup/location/

# 备份学习进度
cp docs/learning_progress.json /backup/location/

# 备份面试报告
cp -r docs/interview_reports/ /backup/location/
```

## 🎓 学习建议

### 新手建议
1. 从技术基础层开始
2. 每个模块完成一个实践项目
3. 定期回顾和总结
4. 积极参与社区讨论

### 进阶建议
1. 选择感兴趣的方向深入
2. 尝试跨领域知识整合
3. 分享学习心得和项目
4. 持续跟踪技术发展

### 专家建议
1. 建立个人知识体系
2. 开发自定义工具和模板
3. 指导和帮助他人学习
4. 推动社区知识共享

---

**下一步**: 开始你的 FDE 学习之旅！

```bash
# 生成你的第一个学习路径
fde-cli path --topic fde --hours 10 --export

# 开始面试练习
fde-cli interview --interactive

# 加入学习社区
# 访问: https://github.com/yourusername/FDE-Knowledge-Hub/discussions
```

祝学习顺利！🚀