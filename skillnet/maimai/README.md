# 脉脉招聘自动化 - SkillWeaver 概念验证

本文档提供了如何使用 SkillWeaver 框架开发脉脉招聘自动化功能的指南。

## 概述

这个概念验证演示了如何使用 SkillWeaver 框架来：
1. 打开脉脉招聘页面
2. 切换到二维码登录界面

## 示例代码说明

`maimai_kb_sample_code.py` 文件包含了与脉脉网站交互的基本功能：

- `navigate_to_maimai_talents_page`: 导航到脉脉人才招聘页面
- `switch_to_qr_code_login`: 切换到二维码登录界面
- `search_candidates_by_keyword`: 使用关键词搜索候选人
- `filter_candidates_by_experience`: 按工作经验筛选候选人
- `extract_candidate_information`: 提取候选人信息

## 如何使用

### 1. 设置环境

确保已按照 SkillWeaver 的主要 README 文件中的说明设置了环境：

```bash
conda create -n skillweaver python=3.10
conda activate skillweaver
pip install -r requirements.txt
playwright install
```

### 2. 配置 API 密钥

```bash
export OPENAI_API_KEY=<your_openai_api_key>
```

### 3. 运行探索脚本

要开始探索脉脉网站并生成 API，可以使用以下命令：

```bash
python -m skillweaver.explore maimai.cn logs/explore-maimai-gpt4o --agent-lm-name gpt-4o --api-synthesis-lm-name gpt-4o --iterations 50
```

### 4. 执行特定任务

一旦生成了知识库，您可以使用以下命令执行特定任务：

```bash
python -m skillweaver.attempt_task "https://maimai.cn/ent/v41/recruit/talents?pid=&tab=1" "打开脉脉招聘页面并切换到二维码登录" --knowledge-base-path-prefix logs/explore-maimai-gpt4o/iter_49/kb_post
```

## 注意事项

1. **选择器更新**: 示例代码中的选择器（如 `.qrcode-login-tab`）需要根据实际网站结构进行调整。

2. **登录限制**: 脉脉可能有登录限制和反爬虫措施，这可能会影响自动化脚本的执行。

3. **合规性考虑**: 确保您的自动化活动符合脉脉的使用条款和相关数据保护法规。

## 扩展功能

示例代码还包含了一些额外功能，可以进一步扩展：

1. **高级搜索**: 实现更复杂的搜索条件，如技能组合、教育背景等。

2. **候选人评估**: 自动评估候选人与职位要求的匹配度。

3. **自动消息发送**: 向符合条件的候选人发送自动消息。

## 故障排除

如果在执行过程中遇到问题：

1. 确保您有有效的脉脉账户和访问权限。
2. 检查网络连接和代理设置。
3. 验证选择器是否仍然有效（网站更新可能会改变元素结构）。
4. 考虑添加更长的等待时间，以适应网络延迟。
