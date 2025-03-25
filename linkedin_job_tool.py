# linkedin_job_tool.py
from langchain.tools import Tool
import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Optional, Union, Tuple

class LinkedInJobTool:
    """LinkedIn职位搜索工具类"""
    
    def __init__(self):
        """初始化LinkedIn职位搜索工具"""
        # 创建Tool实例
        self.tool = Tool(
            name="LinkedIn Job Searcher",
            func=self._search_jobs_wrapper,
            description="Search for jobs on LinkedIn. Input format: 'Job Title in Location', for example 'Solar Engineer in California'"
        )
    
    def _search_jobs_wrapper(self, query: str) -> str:
        """Tool接口的包装函数，处理输入query"""
        try:
            # 解析查询字符串
            if " in " in query:
                job_title, location = query.split(" in ", 1)
            else:
                job_title = query
                location = "anywhere"
            
            # 调用主要搜索函数
            return self.search_linkedin_jobs(job_title.strip(), location.strip())
        except Exception as e:
            return f"Error searching for jobs: {str(e)}"
    
    def search_linkedin_jobs(self, job_title: str, location: str) -> str:
        """从LinkedIn搜索职位信息
        
        Args:
            job_title: 职位名称
            location: 位置
            
        Returns:
            str: 格式化的职位列表
        """
        # 构建LinkedIn搜索URL
        url = f"https://www.linkedin.com/jobs/search?keywords={job_title.replace(' ', '%20')}&location={location.replace(' ', '%20')}&pageNum=0"
        
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept-Language": "en-US,en;q=0.5"
        }
        response = requests.get(url, headers=headers)
        
        if response.status_code != 200:
            return f"Failed to fetch job listings (Status code: {response.status_code})."
        
        # 解析HTML
        soup = BeautifulSoup(response.text, "html.parser")
        job_listings = soup.find_all("div", class_="job-search-card")
        
        result_str = ""
        count = 0  # 限制为前5个职位
        for job in job_listings:
            title_elem = job.find("h3", class_="base-search-card__title")
            company_elem = job.find("a", class_="hidden-nested-link")
            location_elem = job.find("span", class_="job-search-card__location")
            anchor_tag = job.find("a", class_="base-card__full-link")
            
            if title_elem and company_elem and location_elem and anchor_tag:
                result_str += (
                    f"Title: {title_elem.text.strip()}\n"
                    f"Company: {company_elem.text.strip()}\n"
                    f"Location: {location_elem.text.strip()}\n"
                    f"Job Link: {anchor_tag['href']}\n\n"
                )
                count += 1
                if count == 5:  # 限制为前5个职位
                    break
        
        if result_str:
            return f"Found {count} job listings for '{job_title}' in '{location}':\n\n{result_str}"
        else:
            return f"No job listings found for '{job_title}' in '{location}'."
    
    def get_tool(self) -> Tool:
        """获取LangChain工具实例
        
        Returns:
            Tool: 可用于LangChain Agent的工具
        """
        return self.tool
    
    def search_jobs(self, query: str) -> str:
        """直接搜索职位的便捷方法
        
        Args:
            query: 查询字符串，格式为"职位 in 地点"
            
        Returns:
            str: 搜索结果
        """
        return self._search_jobs_wrapper(query)

    def parse_job_search_query(self, query: str) -> Tuple[str, str]:
        """解析职位搜索查询
        
        Args:
            query: 查询字符串，格式可以是"search for X in Y"或其他变体
            
        Returns:
            Tuple[str, str]: (职位, 地点)
        """
        # 去除前缀
        clean_query = query
        for prefix in ["search for", "find", "look for", "search"]:
            if query.lower().startswith(prefix):
                clean_query = query[len(prefix):].strip()
                break
        
        # 分割职位和地点
        if " in " in clean_query:
            parts = clean_query.split(" in ", 1)
            job_title = parts[0].strip()
            location = parts[1].strip()
        else:
            # 如果没有明确的地点，默认为"anywhere"
            job_title = clean_query.strip()
            location = "anywhere"
        
        return job_title, location
    
    def is_job_search_request(self, query: str) -> bool:
        """判断查询是否是职位搜索请求
        
        Args:
            query: 用户输入
            
        Returns:
            bool: 是否是职位搜索请求
        """
        search_patterns = [
            "search for",
            "find jobs",
            "look for jobs",
            "job search",
            "find positions",
            "search jobs"
        ]
        
        query_lower = query.lower()
        return any(pattern in query_lower for pattern in search_patterns)


# 用法示例
if __name__ == "__main__":
    # 创建工具实例
    linkedin_tool = LinkedInJobTool()
    
    # 演示搜索功能
    search_query = "Data Scientist in New York"
    result = linkedin_tool.search_jobs(search_query)
    print(f"Search Results for '{search_query}':\n{result}")
    
    # 演示查询解析
    query = "search for Software Engineer in San Francisco"
    job_title, location = linkedin_tool.parse_job_search_query(query)
    print(f"Parsed Query: Job Title='{job_title}', Location='{location}'")
    
    # 演示检测功能
    test_queries = [
        "search for jobs in clean energy",
        "what skills do I need?",
        "find jobs as a solar installer",
        "hello"
    ]
    for q in test_queries:
        is_search = linkedin_tool.is_job_search_request(q)
        print(f"'{q}' is job search request: {is_search}")