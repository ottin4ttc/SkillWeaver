# 自适应指令执行器 - SkillWeaver扩展

这个文档描述了基于SkillWeaver框架开发的自适应指令执行器，该执行器能够将自然语言指令转换为浏览器自动化脚本，并在运行时自动处理异常。

## 系统概述

自适应指令执行器是SkillWeaver框架的扩展，它结合了以下关键功能：

1. **自然语言指令解析**：将用户的自然语言指令转换为可执行的浏览器自动化脚本
2. **DOM结构分析**：实时读取网页DOM结构，用于生成精确的选择器
3. **异常检测与处理**：在脚本执行过程中检测异常，并自动进行修复
4. **脚本存储与复用**：保存成功执行的脚本，以便在未来遇到类似指令时复用

## 工作原理

### 1. 指令处理流程

```
自然语言指令 → DOM分析 → 脚本生成 → 脚本执行 → 异常检测 → 脚本修复 → 保存成功脚本
```

### 2. 关键组件

- **AdaptiveInstructionExecutor**：核心类，管理整个指令执行过程
- **DOM状态捕获**：通过Playwright获取页面元素和结构信息
- **AI脚本生成**：使用OpenAI API将指令和DOM信息转换为Python脚本
- **异常处理机制**：检测执行错误并生成修复策略
- **脚本存储系统**：管理成功脚本的存储和检索

### 3. 自适应机制

系统的自适应能力体现在以下方面：

- **选择器适应**：根据当前DOM结构动态生成最可靠的选择器
- **错误恢复**：在脚本执行失败时，分析错误原因并自动修复
- **网站变化适应**：当网站结构发生变化时，能够生成新的适应性脚本
- **历史经验学习**：通过保存成功脚本，系统能够从过去的经验中学习

## 使用方法

### 安装依赖

```bash
pip install playwright openai
playwright install
```

### 环境配置

```bash
export OPENAI_API_KEY=your_api_key_here
```

### 基本用法

```python
import asyncio
from adaptive_instruction_executor import AdaptiveInstructionExecutor

async def main():
    executor = AdaptiveInstructionExecutor()
    
    try:
        # 设置浏览器
        await executor.setup_browser()
        
        # 导航到目标网站
        if executor.current_page:
            await executor.current_page.goto("https://maimai.cn/ent/v41/recruit/talents")
            
            # 执行自然语言指令
            result = await executor.execute_instruction("切换到二维码登录")
            print(f"执行结果: {result}")
            
    finally:
        # 关闭浏览器
        await executor.close_browser()

if __name__ == "__main__":
    asyncio.run(main())
```

## 脉脉网站应用示例

以下是在脉脉网站上使用自适应指令执行器的示例：

1. **打开招聘页面**：`"打开脉脉招聘页面"`
2. **切换到二维码登录**：`"切换到二维码登录"`
3. **搜索候选人**：`"搜索Python开发工程师"`
4. **筛选经验**：`"筛选3-5年工作经验的候选人"`

## 系统优势

1. **无需手动编写脚本**：用户只需提供自然语言指令
2. **自动适应网站变化**：当网站结构变化时，系统能够自动调整
3. **持续学习改进**：通过保存成功脚本，系统能够不断改进
4. **可扩展到其他网站**：架构设计允许轻松扩展到其他网站

## 技术实现细节

### DOM状态捕获

系统通过Playwright的JavaScript评估功能获取页面元素信息：

```python
elements_info = await page.evaluate("""
() => {
    const elements = Array.from(document.querySelectorAll('button, a, input, select, textarea, [role="button"]'));
    return elements.map(el => {
        // 提取元素信息
        return {
            tag: el.tagName.toLowerCase(),
            id: el.id,
            className: el.className,
            text: el.textContent?.trim(),
            // 更多属性...
        };
    });
}
""")
```

### AI脚本生成

系统使用OpenAI API生成脚本，提供以下上下文：

1. 自然语言指令
2. 当前页面信息（URL、标题）
3. 可交互元素列表
4. 页面HTML样本

### 异常处理与脚本修复

当脚本执行失败时，系统会：

1. 捕获错误信息和类型
2. 重新获取当前DOM状态
3. 将原始脚本、错误信息和DOM状态发送给AI
4. 生成修复后的脚本
5. 重试执行

### 脚本存储与检索

成功的脚本被保存到本地文件系统：

1. 每个脚本有唯一ID
2. 脚本与原始指令关联
3. 包含执行时间和成功状态
4. 通过指令相似性检索

## 扩展到其他网站

要将系统扩展到其他网站，只需：

1. 更新目标URL
2. 可选：添加网站特定的DOM分析逻辑
3. 可选：调整脚本生成提示以适应网站特性

## 限制与未来改进

1. **性能优化**：减少API调用和DOM分析的开销
2. **更智能的脚本复用**：实现基于语义相似度的脚本检索
3. **多步骤指令支持**：处理复杂的多步骤指令
4. **用户反馈整合**：将用户反馈纳入脚本改进过程
5. **离线能力**：减少对外部API的依赖

## 与SkillWeaver集成

自适应指令执行器与SkillWeaver框架的集成点：

1. 利用SkillWeaver的浏览器环境管理
2. 与SkillWeaver的知识库系统集成
3. 将生成的脚本转换为SkillWeaver API
4. 利用SkillWeaver的评估系统测试生成的脚本

## 结论

自适应指令执行器扩展了SkillWeaver框架，使其能够更灵活地处理自然语言指令，并自动适应网站变化。通过结合AI、DOM分析和异常处理，系统能够生成稳健的浏览器自动化脚本，并在运行时自动修复问题。
