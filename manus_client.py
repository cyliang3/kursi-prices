# Kursi Trades - Manus API 客户端
# ==========================================

import time
import json
import requests
from typing import Optional, Dict, Any
from config import MANUS_API_KEY, MANUS_API_BASE, TASK_TIMEOUT, TASK_CHECK_INTERVAL


class ManusClient:
    """Manus API 客户端封装"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or MANUS_API_KEY
        self.base_url = MANUS_API_BASE
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "API_KEY": self.api_key  # 有些版本用这个
        }
    
    def create_task(self, prompt: str, task_mode: str = "agent") -> str:
        """
        创建一个 Manus 任务
        
        Args:
            prompt: 任务描述/指令
            task_mode: 任务模式，默认 "agent"
            
        Returns:
            task_id: 任务ID
        """
        url = f"{self.base_url}/v1/tasks"
        
        payload = {
            "prompt": prompt,
            "task_mode": task_mode,
        }
        
        response = requests.post(url, headers=self.headers, json=payload)
        
        if response.status_code != 200:
            raise Exception(f"创建任务失败: {response.status_code} - {response.text}")
        
        result = response.json()
        task_id = result.get("id") or result.get("task_id")
        
        print(f"✅ 任务已创建: {task_id}")
        return task_id
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """
        获取任务状态
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务状态信息
        """
        url = f"{self.base_url}/v1/tasks/{task_id}"
        response = requests.get(url, headers=self.headers)
        
        if response.status_code != 200:
            raise Exception(f"获取任务状态失败: {response.status_code} - {response.text}")
        
        return response.json()
    
    def wait_for_task(self, task_id: str, timeout: int = None, interval: int = None) -> Dict[str, Any]:
        """
        等待任务完成并获取结果
        
        Args:
            task_id: 任务ID
            timeout: 超时时间（秒）
            interval: 检查间隔（秒）
            
        Returns:
            任务结果
        """
        timeout = timeout or TASK_TIMEOUT
        interval = interval or TASK_CHECK_INTERVAL
        
        start_time = time.time()
        
        print(f"⏳ 等待任务完成...")
        
        while time.time() - start_time < timeout:
            result = self.get_task_status(task_id)
            status = result.get("status", "").lower()
            
            if status == "completed" or status == "success":
                print(f"✅ 任务完成!")
                
                # Manus API 返回的是消息列表格式
                output = result.get("output", [])
                
                if isinstance(output, list):
                    # 遍历所有消息，找到包含 output_file 的
                    for msg in output:
                        if isinstance(msg, dict):
                            # 检查消息的 content 字段
                            content = msg.get("content", [])
                            if isinstance(content, list):
                                for item in content:
                                    if isinstance(item, dict) and item.get("type") == "output_file":
                                        file_url = item.get("fileUrl")
                                        file_name = item.get("fileName", "result.json")
                                        print(f"📁 发现输出文件: {file_name}")
                                        
                                        # 下载文件内容
                                        if file_url:
                                            try:
                                                file_response = requests.get(file_url, timeout=60)
                                                if file_response.status_code == 200:
                                                    file_content = file_response.text
                                                    print(f"📥 文件下载成功 ({len(file_content)} 字节)")
                                                    return file_content
                                                else:
                                                    print(f"⚠️ 文件下载失败: HTTP {file_response.status_code}")
                                            except Exception as e:
                                                print(f"⚠️ 文件下载异常: {e}")
                            
                            # 直接检查消息本身是否有 output_file
                            if msg.get("type") == "output_file":
                                file_url = msg.get("fileUrl")
                                file_name = msg.get("fileName", "result.json")
                                print(f"📁 发现输出文件: {file_name}")
                                if file_url:
                                    try:
                                        file_response = requests.get(file_url, timeout=60)
                                        if file_response.status_code == 200:
                                            return file_response.text
                                    except Exception as e:
                                        print(f"⚠️ 文件下载异常: {e}")
                    
                    # 如果没找到文件，查找文本中的JSON
                    for msg in output:
                        if isinstance(msg, dict):
                            content = msg.get("content", [])
                            if isinstance(content, list):
                                for item in content:
                                    if isinstance(item, dict) and item.get("type") == "output_text":
                                        text = item.get("text", "")
                                        if text and "{" in text and "prices" in text:
                                            return text
                    
                    # 返回整个output以便调试
                    return output
                
                return output
            
            elif status in ["error", "failed"]:
                error_msg = result.get("error") or result.get("message") or str(result)
                raise Exception(f"任务执行失败: {error_msg}")
            
            # 显示进度
            elapsed = int(time.time() - start_time)
            print(f"   状态: {status} | 已等待: {elapsed}秒")
            
            time.sleep(interval)
        
        raise TimeoutError(f"任务超时（{timeout}秒）未完成")
    
    def run_task(self, prompt: str) -> Dict[str, Any]:
        """
        创建任务并等待完成（一站式方法）
        
        Args:
            prompt: 任务描述
            
        Returns:
            任务结果
        """
        task_id = self.create_task(prompt)
        return self.wait_for_task(task_id)


# 使用 OpenAI 兼容模式的客户端（如果 Manus 支持）
class ManusOpenAIClient:
    """使用 OpenAI SDK 兼容模式的 Manus 客户端"""
    
    def __init__(self, api_key: str = None):
        try:
            from openai import OpenAI
            self.client = OpenAI(
                base_url=MANUS_API_BASE,
                api_key=api_key or MANUS_API_KEY,
                default_headers={"API_KEY": api_key or MANUS_API_KEY}
            )
            self.use_openai = True
        except ImportError:
            print("⚠️ OpenAI SDK 未安装，使用 REST API 模式")
            self.use_openai = False
            self.rest_client = ManusClient(api_key)
    
    def run_task(self, prompt: str) -> str:
        """运行任务并返回结果"""
        if self.use_openai:
            response = self.client.chat.completions.create(
                model="manus-1",
                messages=[{"role": "user", "content": prompt}],
                extra_body={"task_mode": "agent"}
            )
            return response.choices[0].message.content
        else:
            return self.rest_client.run_task(prompt)
