# 多Agent协同生态修复方案智能决策系统

<p align="center">
  <strong>基于LangGraph的多智能体协同生态修复方案生成系统</strong><br/>
  <em>内网离线部署 · 全流程自动化 · 闭环修正机制</em>
</p>

<p align="center">
  <a href="#-系统架构">系统架构</a> •
  <a href="#-核心特性">核心特性</a> •
  <a href="#-快速开始">快速开始</a> •
  <a href="#-部署指南">部署指南</a> •
  <a href="#-api文档">API文档</a> •
  <a href="#-项目结构">项目结构</a>
</p>

---

## 📋 目录

- [系统概述](#-系统概述)
- [系统架构](#-系统架构)
- [核心特性](#-核心特性)
- [快速开始](#-快速开始)
- [部署指南](#-部署指南)
- [使用说明](#-使用说明)
- [API文档](#-api文档)
- [项目结构](#-项目结构)
- [技术栈](#-技术栈)
- [性能指标](#-性能指标)
- [安全合规](#-安全合规)
- [贡献指南](#-贡献指南)
- [许可证](#-许可证)

---

## 🌟 系统概述

**生态修复方案智能决策系统**是一款面向国土空间生态修复领域的智能化解决方案生成平台。系统采用**多Agent协同架构**，基于**LangGraph状态机**驱动，集成**AgenticRAG知识引擎**和**vLLM大模型推理**，实现从工程文件解析到方案生成的全流程自动化。

### 核心价值

- **全流程自动化**：10步闭环流程，从文件上传到方案输出全自动处理
- **精准知识检索**：双库混合检索（PostgreSQL + Milvus），BGE-Reranker语义重排
- **安全可控**：内网离线部署，Python沙箱运行，AES-256加密存储
- **闭环修正机制**：4维度评分，问题精准定位，定向修正调度

### 适用场景

- 矿山生态修复方案生成
- 边坡防护工程方案设计
- 河道生态修复规划
- 裸地复绿工程设计

---

## 🏗️ 系统架构

### 整体架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                        用户交互层                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │   Web界面    │  │  文件上传    │  │      进度推送(WebSocket) │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        服务接入层                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │  API网关     │  │  身份认证    │  │      限流控制            │  │
│  │ (FastAPI)   │  │  (JWT)      │  │                         │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        智能调度层                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              LangGraph 状态机调度中枢                      │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐    │   │
│  │  │意图感知   │→│文件分析   │→│信息查询   │→│代码解释器 │    │   │
│  │  │Agent     │ │Agent     │ │Agent     │ │Agent     │    │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘    │   │
│  │       │              │              │              │      │   │
│  │       ▼              ▼              ▼              ▼      │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────────────────────┐  │   │
│  │  │报告撰写   │→│结果审查   │→│闭环修正（4维度评分）      │  │   │
│  │  │Agent     │ │Agent     │ │问题定位→定向修正          │  │   │
│  │  └──────────┘ └──────────┘ └──────────────────────────┘  │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        知识引擎层                                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │   AgenticRAG    │  │   双库混合检索    │  │   语义层级分块    │  │
│  │                 │  │                 │  │                 │  │
│  │  ┌───────────┐  │  │  ┌───────────┐  │  │  ┌───────────┐  │  │
│  │  │MinerU解析  │  │  │  │BM25关键词  │  │  │  │规范章-节-条│  │  │
│  │  │PaddleOCR  │  │  │  │向量检索    │  │  │  │植物双模式  │  │  │
│  │  └───────────┘  │  │  └───────────┘  │  │  └───────────┘  │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        模型推理层                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              vLLM推理引擎 + Qwen3-4B模型                   │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐   │   │
│  │  │QLoRA微调    │  │8-bit GPTQ   │  │PagedAttention   │   │   │
│  │  │12类场景     │  │量化         │  │加速推理         │   │   │
│  │  └─────────────┘  └─────────────┘  └─────────────────┘   │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        数据存储层                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌────────┐ │
│  │ PostgreSQL  │  │   Milvus    │  │    Redis    │  │ MinIO  │ │
│  │ 结构化数据   │  │  向量数据库  │  │   状态缓存   │  │对象存储 │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### 核心组件说明

| 组件 | 技术选型 | 功能说明 |
|------|----------|----------|
| **智能体框架** | LangGraph | 6大Agent协同，状态机驱动 |
| **大模型** | Qwen3-4B | QLoRA微调，8-bit GPTQ量化 |
| **推理引擎** | vLLM | PagedAttention加速 |
| **RAG引擎** | AgenticRAG | MinerU解析，语义层级分块 |
| **向量数据库** | Milvus | BGE-large-zh向量化 |
| **图数据库** | Neo4j | 知识图谱存储 |
| **对象存储** | MinIO | 文件分片上传 |
| **API框架** | FastAPI | WebSocket实时推送 |

---

## ✨ 核心特性

### 1. 三级意图识别
- **一级意图**：生成方案 / 调整方案 / 解析文件
- **二级意图**：完整方案 / 专项内容
- **三级意图**：矿山 / 边坡 / 河道场景
- **置信度阈值**：95%，低于阈值自动多轮确认

### 2. 6大智能体协同

| 智能体 | 职责 | 核心能力 |
|--------|------|----------|
| **意图感知Agent** | 系统入口 | 三级意图分类，执行计划生成 |
| **文件分析Agent** | 工程文件解析 | MinerU+OCR，字段提取，交叉校验 |
| **信息查询Agent** | 知识检索 | 双库混合检索，BGE重排，规范有效性校验 |
| **代码解释器Agent** | 量化计算 | Python沙箱，苗木用量计算，图表生成 |
| **报告撰写Agent** | 方案生成 | 溯源绑定，Word/PDF输出 |
| **结果审查Agent** | 质量把控 | 4维度评分，问题定位，修正调度 |

### 3. AgenticRAG知识引擎

#### 语义层级分块
- **规范文档**：章-节-条-款四级分块
- **植物数据**：双模式分块（结构化+描述性）
- **分块校验**：语义完整性检查，不拆完整句子

#### 混合检索策略
```
用户查询 → BM25关键词粗排（Top20）→ Milvus向量检索（Top20）
    → 合并去重 → BGE-Reranker精排（Top5）→ 溯源绑定输出
```

### 4. 闭环修正机制

#### 4维度评分体系
| 维度 | 权重 | 评分标准 |
|------|------|----------|
| **植物合规性** | 40% | 乡土植物匹配度，入侵物种检查 |
| **工艺合规性** | 30% | 规范符合度，技术参数准确性 |
| **数据准确性** | 20% | 量化计算准确性，单位一致性 |
| **内容完整性** | 10% | 章节完整性，必填项检查 |

#### 修正流程
```
评分 < 85分 → 问题定位 → 责任Agent识别 → 定向修正 → 重新评分
```

### 5. 安全合规

- **内网离线部署**：数据不出网，涉密文件本地处理
- **Python沙箱**：禁止网络访问，限制系统调用
- **AES-256加密**：涉密数据加密存储
- **不可篡改审计**：所有操作日志区块链式存储

---

## 🚀 快速开始

### 环境要求

- **操作系统**：Ubuntu 22.04 / CentOS 8 / Windows 10+
- **Docker**：20.10+
- **Docker Compose**：2.0+
- **内存**：16GB+（推荐32GB）
- **磁盘**：100GB+
- **GPU**：NVIDIA GPU（可选，用于模型推理加速）

### 一键启动

```bash
# 1. 克隆项目
cd eco-repair-agent-system

# 2. 复制环境变量配置
cp .env.example .env
# 编辑 .env 文件，配置数据库密码等敏感信息

# 3. 一键启动
./start.sh
```

启动完成后访问：
- **API文档**：http://localhost:8000/docs
- **Web界面**：http://localhost:8000
- **Neo4j Browser**：http://localhost:7474

### 快速体验

```bash
# 生成生态修复方案
curl -X POST http://localhost:8000/api/v1/schemes/generate \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "生成湖北省黄石市大冶铁矿裸地复绿工程完整方案",
    "file_list": ["daye_iron_mine_cad.pdf"]
  }'
```

---

## 📦 部署指南

### 单机部署（Docker Compose）

```bash
# 启动所有服务
./start.sh

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f agent

# 停止服务
./stop.sh

# 重启服务
./restart.sh
```

### Kubernetes集群部署

```bash
# 创建命名空间
kubectl create namespace eco-repair

# 部署所有服务
kubectl apply -f deploy/k8s/

# 查看Pod状态
kubectl get pods -n eco-repair

# 查看服务
kubectl get svc -n eco-repair
```

### 离线部署

```bash
# 构建离线包
./deploy/offline_package/build_offline_package.sh

# 传输到离线服务器
cp output/eco-repair-agent-offline-1.0.0-amd64.tar.gz /path/to/offline/server/

# 在离线服务器上解压安装
tar -xzf eco-repair-agent-offline-1.0.0-amd64.tar.gz
cd eco-repair-agent-offline-1.0.0-amd64
./install.sh
```

---

## 📖 使用说明

### 1. 生成完整方案

```python
import requests

# 1. 上传工程文件
files = {'file': open('daye_iron_mine_cad.pdf', 'rb')}
response = requests.post('http://localhost:8000/api/v1/files/upload', files=files)
file_id = response.json()['data']['file_id']

# 2. 提交方案生成请求
response = requests.post('http://localhost:8000/api/v1/schemes/generate', json={
    'user_input': '生成湖北省黄石市大冶铁矿裸地复绿工程完整方案',
    'file_list': [file_id]
})
scheme_id = response.json()['data']['scheme_id']

# 3. 查询方案状态
response = requests.get(f'http://localhost:8000/api/v1/schemes/{scheme_id}/status')
status = response.json()['data']['status']

# 4. 下载方案
response = requests.get(f'http://localhost:8000/api/v1/schemes/{scheme_id}/download')
with open('scheme.docx', 'wb') as f:
    f.write(response.content)
```

### 2. WebSocket实时进度

```javascript
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log(`进度: ${data.progress}%, 状态: ${data.status}`);
};

ws.send(JSON.stringify({
    action: 'subscribe',
    session_id: 'sess_xxx'
}));
```

### 3. 调整已有方案

```python
# 提交调整请求
response = requests.post('http://localhost:8000/api/v1/schemes/adjust', json={
    'scheme_id': 'scheme_xxx',
    'adjustment': '调整植物配置，增加耐旱品种比例'
})
```

---

## 📚 API文档

### 在线文档

启动服务后访问：http://localhost:8000/docs

### 核心接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/v1/auth/login | 用户登录 |
| POST | /api/v1/sessions | 创建会话 |
| POST | /api/v1/files/upload | 文件上传 |
| POST | /api/v1/schemes/generate | 生成方案 |
| GET | /api/v1/schemes/{id}/status | 查询方案状态 |
| GET | /api/v1/schemes/{id}/download | 下载方案 |
| WS | /ws | WebSocket实时进度 |


---

## 📁 项目结构

```
eco_repair_agent_system/
├── main.py                          # 项目启动入口
├── requirements.txt                 # Python依赖
├── docker-compose.yml               # Docker编排
├── .env.example                     # 环境变量示例
├── .gitignore                       # Git忽略配置
├── start.sh                         # 启动脚本
├── stop.sh                          # 停止脚本
├── restart.sh                       # 重启脚本
│
├── configs/                         # 配置中心
│   ├── system_config.py
│   ├── model_config.py
│   ├── agent_config.py
│   └── ...
│
├── core/                            # 核心调度
│   ├── base_agent.py               # 智能体基类
│   ├── scheduler/                  # 调度引擎
│   │   ├── global_state.py
│   │   ├── graph_build.py
│   │   └── ...
│   ├── agents/                     # 6大智能体
│   │   ├── intent_perceive_agent.py
│   │   ├── file_analyze_agent.py
│   │   ├── info_query_agent.py
│   │   ├── code_interpreter_agent.py
│   │   ├── report_write_agent.py
│   │   └── result_review_agent.py
│   └── review/                     # 闭环修正
│       ├── score_calculator.py
│       └── ...
│
├── agentic_rag/                     # RAG知识引擎
│   ├── data_parse/                 # 文件解析
│   ├── chunk_split/                # 语义分块
│   ├── retrieve/                   # 混合检索
│   └── vector_store/               # 向量库
│
├── model/                           # 模型层
│   ├── finetune/                   # QLoRA微调
│   └── inference/                  # vLLM推理
│
├── service/                         # 服务层
│   ├── api_gateway.py
│   ├── auth_service.py
│   ├── session_service.py
│   ├── file_service.py
│   └── scheme_service.py
│
├── deploy/                          # 部署配置
│   ├── docker/                     # Dockerfile
│   ├── k8s/                        # Kubernetes
│   ├── nginx/                      # Nginx配置
│   └── offline_package/            # 离线包构建
│
├── test/                            # 测试
│   ├── unit_test/                  # 单元测试
│   ├── integration_test/           # 集成测试
│   └── e2e_test/                   # 端到端测试
│
└── docs/                            # 文档
    ├── api_doc.md
    ├── deploy_doc.md
    └── ...
```

---

## 🛠️ 技术栈

### 核心框架
- **LangGraph**: 多Agent协同调度
- **FastAPI**: Web API框架
- **vLLM**: 大模型推理引擎

### 数据库
- **PostgreSQL**: 结构化数据存储
- **Milvus**: 向量数据库
- **Neo4j**: 图数据库
- **Redis**: 缓存与状态管理
- **MinIO**: 对象存储

### 模型
- **Qwen3-4B**: 基础大模型
- **BGE-large-zh-v1.5**: 文本向量化
- **BGE-Reranker**: 语义重排

### 部署
- **Docker**: 容器化
- **Kubernetes**: 容器编排
- **Nginx**: 反向代理

---

## 📊 性能指标

| 指标 | 数值 | 说明 |
|------|------|------|
| **方案生成时间** | 3-5分钟 | 完整方案，含文件解析 |
| **意图识别准确率** | 95%+ | 三级意图分类 |
| **RAG检索准确率** | 90%+ | Top5命中率 |
| **方案合规评分** | 85+ | 4维度加权评分 |
| **并发处理能力** | 10 QPS | 单节点 |
| **知识库规模** | 21762种植物 + 2147份规范 | 持续更新 |

---


---

<p align="center">
  <strong>让生态修复更智能 · 让方案生成更高效</strong>
</p>
