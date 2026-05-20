# FDE Knowledge Hub - 项目结构说明

## 📁 项目根目录结构

```
FDE-Knowledge-Hub/
├── README.md                          # 项目说明文档
├── LICENSE                            # MIT 许可证
├── requirements.txt                   # Python 依赖
├── setup.py                           # 项目安装配置
├── .env.example                       # 环境变量示例
├── .gitignore                         # Git 忽略配置
├── .obsidian/                         # Obsidian 配置
│   ├── app.json                      # 应用配置
│   ├── workspace.json                # 工作区配置
│   ├── preferences.json              # 偏好设置
│   ├── community-plugins.json        # 社区插件列表
│   └── appearance.json               # 外观配置
├── core/                             # 核心知识库
│   ├── foundation/                   # 技术基础层
│   │   ├── programming/              # 编程与系统设计
│   │   ├── database/                 # 数据库与数据处理
│   │   ├── network/                  # 网络与安全
│   │   └── cloud/                    # 云原生架构
│   ├── ai-engineering/               # AI工程化层
│   │   ├── ml-basics/                # 机器学习基础
│   │   ├── deep-learning/            # 深度学习
│   │   ├── llm-engineering/          # LLM 工程化
│   │   ├── rag-systems/              # RAG 系统
│   │   └── multi-agent/              # Multi-Agent
│   ├── product-business/             # 产品业务层
│   │   ├── product-thinking/         # 产品思维
│   │   ├── data-analysis/            # 数据分析
│   │   └── market-positioning/       # 市场定位
│   └── consulting-delivery/          # 咨询交付层
│       ├── client-management/        # 客户管理
│       ├── project-delivery/         # 项目交付
│       └── change-management/        # 变革管理
├── templates/                        # 智能模板系统
│   ├── books/                        # 书籍笔记模板
│   ├── concepts/                     # 技术概念模板
│   ├── cases/                        # 案例研究模板
│   ├── interviews/                   # 面试准备模板
│   ├── learning_paths/               # 学习路径模板
│   └── projects/                     # 项目实践模板
├── automation/                       # 自动化工具
│   ├── cli.py                        # 命令行接口
│   ├── knowledge_ingestion.py        # 知识摄取
│   ├── learning_path_generator.py    # 学习路径生成
│   ├── interview_prep.py             # 面试准备
│   ├── spaced_repetition.py          # 间隔重复
│   ├── knowledge_stats.py            # 知识统计
│   └── mock_interview.py             # 模拟面试
├── integration/                      # 外部集成
│   ├── obsidian_notebooklm_sync.py   # Obsidian 同步
│   ├── claude_api_integration.py     # Claude API 集成
│   └── local_llm_integration.py      # 本地 LLM 集成
├── assets/                           # 资源文件
│   ├── books/                        # 电子书
│   ├── papers/                       # 学术论文
│   ├── images/                       # 图片资源
│   ├── code-examples/                # 代码示例
│   └── attachments/                  # 附件
└── docs/                             # 项目文档
    ├── ARCHITECTURE.md               # 系统架构文档
    ├── SETUP_GUIDE.md                # 安装指南
    ├── USAGE_GUIDE.md                # 使用指南
    ├── PLUGINS.md                    # 插件推荐
    ├── LEARNING_MODULES.json         # 学习模块定义
    ├── INTERVIEW_QUESTIONS.json      # 面试题库
    └── interview_reports/            # 面试报告
```

## 🔑 核心设计原则

### 1. 模块化架构
每个层级独立管理，支持按需加载和更新。

### 2. 知识关联
通过 Obsidian 的双链功能建立知识网络。

### 3. 自动化优先
减少手动操作，提高知识管理效率。

### 4. 可扩展性
支持自定义模板、插件和工作流。

### 5. 面试导向
所有功能都围绕 FDE 面试准备设计。

## 📋 文件命名规范

### 知识笔记文件
```
[分类]_[主题]_[难度].md
示例:
- foundation_system-design_intermediate.md
- ai-engineering_rag-systems_advanced.md
- consulting-delivery_client-management_beginner.md
```

### 模板文件
```
template_[类型]_[用途].md
示例:
- template_book_note_standard.md
- template_concept_technical.md
- template_interview_question.md
```

### 自动化脚本
```
[功能]_[描述].py
示例:
- knowledge_ingestion.py (知识摄取)
- learning_path_generator.py (学习路径生成)
- interview_prep.py (面试准备)
```

## 🔧 配置文件说明

### .obsidian/app.json
Obsidian 应用基础配置：
- 字体大小、主题选择
- 界面布局设置
- 显示选项配置

### .obsidian/preferences.json
用户偏好设置：
- 文件创建位置
- 附件存储路径
- 链接格式设置

### .obsidian/community-plugins.json
社区插件列表：
- dataview (数据查询)
- templater (模板系统)
- calendar (日历视图)
- tasks (任务管理)

### .env.example
环境变量配置示例：
- API 密钥配置
- 数据库连接信息
- 自动化设置选项

## 📊 知识分类体系

### 按难度分类
- **beginner**: 入门级别，基础概念
- **intermediate**: 进阶级别，实践应用
- **expert**: 专家级别，深度研究

### 按类型分类
- **concept**: 技术概念和原理
- **practice**: 实践方法和技巧
- **case**: 案例研究和分析
- **tool**: 工具和框架使用
- **trend**: 行业趋势和前沿

### 按应用场景分类
- **interview**: 面试相关
- **project**: 项目实施
- **consulting**: 客户咨询
- **learning**: 学习过程

## 🔄 工作流程

### 知识摄取流程
1. 收集资料 (书籍/论文/代码)
2. 使用摄取工具处理
3. 生成结构化笔记
4. 建立知识关联
5. 索引到向量数据库

### 学习路径流程
1. 分析当前技能水平
2. 识别能力缺口
3. 生成个性化路径
4. 导入 Obsidian
5. 跟踪学习进度

### 面试准备流程
1. 选择面试题类型
2. 模拟面试练习
3. AI 评估回答质量
4. 生成改进建议
5. 跟踪能力提升

## 🚀 快速开始指南

### 1. 初始化项目
```bash
# 克隆项目
git clone https://github.com/yourusername/FDE-Knowledge-Hub.git
cd FDE-Knowledge-Hub

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入你的 API 密钥
```

### 2. 配置 Obsidian
1. 打开 Obsidian
2. 选择 "打开文件夹作为仓库"
3. 选择 FDE-Knowledge-Hub 目录
4. 安装推荐插件 (见 docs/PLUGINS.md)
5. 配置主题和外观

### 3. 开始使用
```bash
# 摄取知识
fde-cli ingest --category ai-engineering --difficulty intermediate

# 生成学习路径
fde-cli path --topic llm-engineering --hours 10

# 面试练习
fde-cli interview --role FDE --difficulty senior

# 同步到 NotebookLM
fde-cli sync
```

## 📈 进阶使用

### 自定义学习模块
编辑 `docs/learning_modules.json` 添加自定义学习模块。

### 扩展面试题库
编辑 `docs/interview_questions.json` 添加新的面试题。

### 开发自定义插件
参考 `integration/` 目录下的示例，开发自定义集成。

### 主题定制
修改 `.obsidian/appearance.json` 和相关 CSS 文件。

## 🤝 贡献指南

欢迎贡献内容、改进建议和代码实现！

### 贡献方式
1. Fork 项目
2. 创建特性分支
3. 提交更改
4. 创建 Pull Request

### 贡献内容
- 新增知识笔记
- 改进现有模板
- 添加自动化功能
- 修复问题和 Bug
- 完善文档

---

**项目版本**: 1.0.0
**最后更新**: 2026-05-17
**维护者**: 邵炎炎