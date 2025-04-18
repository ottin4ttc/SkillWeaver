"""
自适应指令执行器 - 将自然语言指令转换为脚本并自动处理异常

这个模块实现了一个自适应指令执行器，它可以：
1. 接收自然语言指令
2. 分析网页DOM结构
3. 生成执行指令的脚本
4. 在运行时检测异常并自动更新脚本
5. 保存成功的脚本以供将来使用
"""

import asyncio
import json
import os
import time
import traceback
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Union

from openai import AsyncOpenAI
from playwright.async_api import Page, Browser, BrowserContext, async_playwright

client = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

class AdaptiveInstructionExecutor:
    """
    自适应指令执行器类
    
    将自然语言指令转换为可执行脚本，并在运行时自适应处理异常
    """
    
    def __init__(self, script_dir: str = "saved_scripts"):
        """
        初始化自适应指令执行器
        
        Args:
            script_dir: 保存成功脚本的目录
        """
        self.script_dir = script_dir
        self.script_history: Dict[str, List[Dict]] = {}
        self.current_page: Optional[Page] = None
        self.current_browser: Optional[Browser] = None
        self.current_context: Optional[BrowserContext] = None
        
        os.makedirs(script_dir, exist_ok=True)
        
        self._load_saved_scripts()
    
    def _load_saved_scripts(self):
        """加载已保存的脚本"""
        script_index_path = os.path.join(self.script_dir, "script_index.json")
        if os.path.exists(script_index_path):
            try:
                with open(script_index_path, "r", encoding="utf-8") as f:
                    self.script_history = json.load(f)
            except json.JSONDecodeError:
                print("脚本索引文件损坏，创建新索引")
                self.script_history = {}
    
    def _save_script_index(self):
        """保存脚本索引"""
        script_index_path = os.path.join(self.script_dir, "script_index.json")
        with open(script_index_path, "w", encoding="utf-8") as f:
            json.dump(self.script_history, f, ensure_ascii=False, indent=2)
    
    async def setup_browser(self):
        """设置浏览器"""
        playwright = await async_playwright().start()
        self.current_browser = await playwright.chromium.launch(headless=True)  # 使用无头模式
        if self.current_browser:
            self.current_context = await self.current_browser.new_context()
            if self.current_context:
                self.current_page = await self.current_context.new_page()
    
    async def close_browser(self):
        """关闭浏览器"""
        if self.current_context:
            await self.current_context.close()
        if self.current_browser:
            await self.current_browser.close()
    
    async def capture_dom_state(self) -> Dict:
        """
        捕获当前页面的DOM状态
        
        Returns:
            包含页面状态信息的字典
        """
        if not self.current_page:
            raise ValueError("浏览器未初始化")
        
        url = self.current_page.url
        title = await self.current_page.title()
        
        html = await self.current_page.content()
        
        elements_info = await self.current_page.evaluate("""
        () => {
            const elements = Array.from(document.querySelectorAll('button, a, input, select, textarea, [role="button"]'));
            return elements.map(el => {
                const rect = el.getBoundingClientRect();
                return {
                    tag: el.tagName.toLowerCase(),
                    id: el.id,
                    className: el.className,
                    text: el.textContent?.trim(),
                    placeholder: el.placeholder,
                    type: el.type,
                    name: el.name,
                    value: el.value,
                    href: el.href,
                    role: el.getAttribute('role'),
                    ariaLabel: el.getAttribute('aria-label'),
                    visible: rect.width > 0 && rect.height > 0,
                    x: rect.x,
                    y: rect.y,
                    width: rect.width,
                    height: rect.height
                };
            });
        }
        """)
        
        return {
            "url": url,
            "title": title,
            "timestamp": datetime.now().isoformat(),
            "elements": elements_info,
            "html_sample": html[:10000]  # 只保存部分HTML以减小大小
        }
    
    async def generate_script(self, instruction: str, dom_state: Dict) -> str:
        """
        根据自然语言指令和DOM状态生成脚本
        
        Args:
            instruction: 自然语言指令
            dom_state: 页面DOM状态
        
        Returns:
            生成的Python脚本代码
        """
        prompt = f"""
        你是一个专业的网页自动化专家。请根据以下自然语言指令和网页DOM状态，生成一个使用Playwright的Python异步函数。
        
        {instruction}
        
        URL: {dom_state['url']}
        标题: {dom_state['title']}
        
        {json.dumps(dom_state['elements'][:20], ensure_ascii=False, indent=2)}
        
        1. 生成一个名为`execute_instruction`的异步函数，接受一个`page`参数
        2. 使用最可靠的选择器（优先使用文本内容、aria标签、角色等）
        3. 包含适当的等待和错误处理
        4. 只输出Python代码，不要包含任何解释或注释
        5. 确保代码可以直接执行，不需要额外修改
        
        示例代码格式:
        
        async def execute_instruction(page):
            try:
                await page.click("text=登录")
                return {{"success": True, "message": "指令执行成功"}}
            except Exception as e:
                return {{"success": False, "message": str(e), "error_type": type(e).__name__}}
        """
        
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "你是一个专业的网页自动化专家，精通Playwright和Python。"},
                {"role": "user", "content": prompt}
            ]
        )
        
        generated_code = response.choices[0].message.content
        
        if "```python" in generated_code:
            code_start = generated_code.find("```python") + 10
            code_end = generated_code.rfind("```")
            cleaned_code = generated_code[code_start:code_end].strip()
        else:
            cleaned_code = generated_code.strip()
        
        return cleaned_code
    
    async def execute_script(self, script_code: str) -> Dict:
        """
        执行生成的脚本
        
        Args:
            script_code: 要执行的Python脚本代码
        
        Returns:
            执行结果
        """
        if not self.current_page:
            raise ValueError("浏览器未初始化")
        
        try:
            local_namespace = {"page": self.current_page}
            
            exec(script_code, globals(), local_namespace)
            
            execute_instruction = local_namespace.get("execute_instruction")
            
            if not execute_instruction:
                return {"success": False, "message": "脚本中未找到execute_instruction函数"}
            
            start_time = time.time()
            result = await execute_instruction(self.current_page)
            execution_time = time.time() - start_time
            
            if isinstance(result, dict):
                result["execution_time"] = execution_time
            else:
                result = {"success": True, "result": result, "execution_time": execution_time}
            
            return result
        except Exception as e:
            return {
                "success": False, 
                "message": str(e), 
                "error_type": type(e).__name__,
                "traceback": traceback.format_exc()
            }
    
    async def fix_script(self, instruction: str, original_script: str, error_info: Dict, dom_state: Dict) -> str:
        """
        修复失败的脚本
        
        Args:
            instruction: 原始自然语言指令
            original_script: 原始脚本
            error_info: 错误信息
            dom_state: 当前DOM状态
        
        Returns:
            修复后的脚本
        """
        prompt = f"""
        你是一个专业的网页自动化专家。请修复以下失败的脚本。
        
        {instruction}
        
        ```python
        {original_script}
        ```
        
        错误类型: {error_info.get('error_type')}
        错误消息: {error_info.get('message')}
        
        URL: {dom_state['url']}
        标题: {dom_state['title']}
        
        {json.dumps(dom_state['elements'][:20], ensure_ascii=False, indent=2)}
        
        1. 分析错误原因
        2. 修复脚本中的问题
        3. 使用更可靠的选择器或等待策略
        4. 只输出修复后的完整Python代码，不要包含任何解释或注释
        """
        
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "你是一个专业的网页自动化专家，精通Playwright和Python。"},
                {"role": "user", "content": prompt}
            ]
        )
        
        fixed_code = response.choices[0].message.content
        
        if "```python" in fixed_code:
            code_start = fixed_code.find("```python") + 10
            code_end = fixed_code.rfind("```")
            cleaned_code = fixed_code[code_start:code_end].strip()
        else:
            cleaned_code = fixed_code.strip()
        
        return cleaned_code
    
    async def save_successful_script(self, instruction: str, script_code: str, execution_result: Dict):
        """
        保存成功执行的脚本
        
        Args:
            instruction: 自然语言指令
            script_code: 脚本代码
            execution_result: 执行结果
        """
        script_id = f"script_{int(time.time())}"
        
        script_path = os.path.join(self.script_dir, f"{script_id}.py")
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(f"# 指令: {instruction}\n\n")
            f.write(script_code)
        
        instruction_key = instruction.lower().strip()
        if instruction_key not in self.script_history:
            self.script_history[instruction_key] = []
        
        self.script_history[instruction_key].append({
            "script_id": script_id,
            "path": script_path,
            "created_at": datetime.now().isoformat(),
            "execution_time": execution_result.get("execution_time", 0),
            "success": True
        })
        
        self._save_script_index()
    
    async def find_similar_script(self, instruction: str) -> Optional[str]:
        """
        查找类似指令的已保存脚本
        
        Args:
            instruction: 自然语言指令
        
        Returns:
            找到的脚本代码，如果没有找到则返回None
        """
        instruction_key = instruction.lower().strip()
        
        if instruction_key in self.script_history and self.script_history[instruction_key]:
            script_info = next(
                (s for s in reversed(self.script_history[instruction_key]) if s.get("success", False)), 
                None
            )
            
            if script_info:
                script_path = script_info["path"]
                if os.path.exists(script_path):
                    with open(script_path, "r", encoding="utf-8") as f:
                        return f.read()
        
        
        return None
    
    async def execute_instruction(self, instruction: str, max_attempts: int = 3) -> Dict:
        """
        执行自然语言指令
        
        Args:
            instruction: 自然语言指令
            max_attempts: 最大尝试次数
        
        Returns:
            执行结果
        """
        if not self.current_page:
            raise ValueError("浏览器未初始化")
        
        existing_script = await self.find_similar_script(instruction)
        
        if existing_script:
            print(f"找到类似指令的已保存脚本，尝试执行...")
            result = await self.execute_script(existing_script)
            
            if result.get("success", False):
                print(f"已保存脚本执行成功")
                return result
            
            print(f"已保存脚本执行失败，尝试生成新脚本...")
        
        dom_state = await self.capture_dom_state()
        
        script_code = await self.generate_script(instruction, dom_state)
        
        for attempt in range(max_attempts):
            print(f"执行尝试 {attempt + 1}/{max_attempts}...")
            
            result = await self.execute_script(script_code)
            
            if result.get("success", False):
                print(f"脚本执行成功")
                await self.save_successful_script(instruction, script_code, result)
                return result
            
            print(f"脚本执行失败: {result.get('message')}")
            
            if attempt < max_attempts - 1:
                dom_state = await self.capture_dom_state()
                
                script_code = await self.fix_script(instruction, script_code, result, dom_state)
                print(f"脚本已修复，准备重试...")
        
        return {
            "success": False,
            "message": f"在{max_attempts}次尝试后仍然失败",
            "last_error": result
        }

async def main():
    executor = AdaptiveInstructionExecutor()
    
    try:
        await executor.setup_browser()
        
        if executor.current_page:
            await executor.current_page.goto("https://maimai.cn/ent/v41/recruit/talents?pid=&tab=1")
            
            result = await executor.execute_instruction("切换到二维码登录")
            print(f"执行结果: {json.dumps(result, ensure_ascii=False, indent=2)}")
            
            await asyncio.sleep(5)
    finally:
        await executor.close_browser()

if __name__ == "__main__":
    import traceback
    
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"发生错误: {e}")
        print(traceback.format_exc())
