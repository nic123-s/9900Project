# web_search_tool.py - 使用DuckDuckGo的网络搜索工具

import requests
from langchain.tools import BaseTool
from bs4 import BeautifulSoup
import json
from typing import Optional, Type, List, Dict, Any
import re
import urllib.parse

class WebSearchTool(BaseTool):
    name: str = "WebSearcher"
    description: str = "Searches the web for up-to-date information about clean energy industry trends, technologies, and latest news. Use this tool when you need current information not available in your knowledge base."
    
    def __init__(self):
        """初始化网络搜索工具，使用DuckDuckGo不需要API密钥"""
        super().__init__()
        
    def _run(self, query: str) -> str:
        """执行网络搜索
        
        Args:
            query: 搜索查询
            
        Returns:
            str: 搜索结果摘要
        """
        try:
            # 使用DuckDuckGo进行搜索
            search_results = self._search_with_duckduckgo(query)
            
            # 提取和格式化搜索结果
            formatted_results = self._format_search_results(search_results)
            
            return formatted_results
        except Exception as e:
            return f"Error performing web search: {str(e)}"
    
    def _search_with_duckduckgo(self, query: str) -> List[Dict]:
        """使用DuckDuckGo执行搜索
        
        Args:
            query: 搜索查询
            
        Returns:
            List[Dict]: 搜索结果列表
        """
        # 添加领域限定
        full_query = urllib.parse.quote(query + " clean energy industry")
        
        # DuckDuckGo搜索URL
        url = f"https://html.duckduckgo.com/html/?q={full_query}"
        
        # 设置请求头
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        # 发送请求
        response = requests.get(url, headers=headers)
        
        # 检查响应状态
        if response.status_code != 200:
            raise Exception(f"Search returned status code {response.status_code}")
        
        # 解析HTML
        soup = BeautifulSoup(response.text, "html.parser")
        
        # 提取搜索结果
        results = []
        
        # DuckDuckGo的结果通常在class为"result"的div中
        for result_div in soup.select(".result"):
            try:
                # 获取标题
                title_elem = result_div.select_one(".result__title")
                title = title_elem.get_text(strip=True) if title_elem else "No Title"
                
                # 获取链接
                link_elem = result_div.select_one(".result__url")
                link = link_elem.get_text(strip=True) if link_elem else "No Link"
                if link and not link.startswith(('http://', 'https://')):
                    link = "https://" + link
                
                # 获取摘要
                snippet_elem = result_div.select_one(".result__snippet")
                snippet = snippet_elem.get_text(strip=True) if snippet_elem else "No Snippet"
                
                # 将结果添加到列表
                results.append({
                    "title": title,
                    "link": link,
                    "snippet": snippet
                })
                
                # 只获取前5个结果
                if len(results) >= 5:
                    break
            except Exception as e:
                print(f"Error parsing result: {e}")
                continue
        
        return results
    
    def _format_search_results(self, results: List[Dict]) -> str:
        """格式化搜索结果
        
        Args:
            results: 搜索结果列表
            
        Returns:
            str: 格式化的搜索结果
        """
        formatted_output = "Web Search Results:\n\n"
        
        if results:
            for i, result in enumerate(results, 1):
                title = result.get("title", "No Title")
                link = result.get("link", "No Link")
                snippet = result.get("snippet", "No Snippet")
                
                formatted_output += f"[Result {i}]\n"
                formatted_output += f"Title: {title}\n"
                formatted_output += f"Snippet: {snippet}\n"
                formatted_output += f"URL: {link}\n\n"
        else:
            formatted_output += "No relevant search results found.\n"
        
        return formatted_output
    
    def _extract_content(self, url: str) -> str:
        """从URL提取内容
        
        Args:
            url: 网页URL
            
        Returns:
            str: 提取的内容
        """
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code != 200:
                return f"Failed to fetch the page. Status code: {response.status_code}"
            
            # 解析HTML
            soup = BeautifulSoup(response.text, "html.parser")
            
            # 移除脚本和样式元素
            for script in soup(["script", "style"]):
                script.extract()
            
            # 获取文本
            text = soup.get_text(separator="\n", strip=True)
            
            # 简单处理文本(删除多余空行等)
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            text = "\n".join(lines)
            
            # 限制文本长度
            return text[:8000] + ("..." if len(text) > 8000 else "")
        except Exception as e:
            return f"Error extracting content: {str(e)}"

def create_web_search_tool():
    """创建网络搜索工具实例"""
    return WebSearchTool()

# 测试代码
if __name__ == "__main__":
    print("=== Testing Web Search Tool (DuckDuckGo) ===\n")
    
    # 创建搜索工具实例
    search_tool = create_web_search_tool()
    
    test_queries = [
        "latest trends in solar energy technology",
        "clean energy industry growth 2023",
        "emerging battery technologies for renewable energy",
        "green hydrogen production advancements"
    ]
    
    # 选择一个查询进行测试
    print("Available test queries:")
    for i, query in enumerate(test_queries, 1):
        print(f"{i}. {query}")
    
    selection = input("\nSelect a query number or enter a custom query: ")
    
    # 处理选择
    if selection.isdigit() and 1 <= int(selection) <= len(test_queries):
        query = test_queries[int(selection) - 1]
    else:
        query = selection
    
    print(f"\nSearching for: '{query}'")
    print("\n" + "="*50 + "\n")
    
    # 执行搜索
    try:
        results = search_tool._run(query)
        print(results)
    except Exception as e:
        print(f"Error during search: {str(e)}")
        
    print("\n" + "="*50)
    print("\nTest completed.")