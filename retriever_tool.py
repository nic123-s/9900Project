# retriever_tool.py - 修改版，移除历史感知功能

from langchain.tools import BaseTool
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from typing import List, Dict, Any, Optional, Type
from pydantic import Field

class HistoryAwareRetrieverTool(BaseTool):
    name: str = "DocumentRetriever"  # 添加类型注解
    description: str = "Retrieves relevant information from the clean energy knowledge base based on the question."  # 修改描述
    
    # 使用 Field 定义这些属性为非必需，或者在初始化时传递
    llm: Any = Field(default=None, exclude=True)  # exclude=True 表示这个不会被序列化
    base_retriever: Any = Field(default=None, exclude=True)

    def __init__(self, llm, pdf_path: str, k: int = 5):
        """初始化检索工具
        
        Args:
            llm: 语言模型（此参数保留但不再使用）
            pdf_path: PDF文档路径
            k: 返回的文档数量
        """
        super().__init__()
        self.llm = llm  # 保留但不使用
        self.base_retriever = self._create_base_retriever(pdf_path, k)
    
    def _create_base_retriever(self, pdf_path: str, k: int):
        """创建基础文档检索器"""
        # 1. 加载文档
        docs = self._load_documents(pdf_path)
        
        # 2. 创建向量存储
        embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        vectorstore = FAISS.from_documents(docs, embeddings)
        
        # 3. 创建检索器
        return vectorstore.as_retriever(search_kwargs={"k": k})
    
    def _load_documents(self, pdf_path: str) -> List[Document]:
        """加载并处理PDF文档"""
        # 加载PDF
        loader = PyPDFLoader(pdf_path)
        documents = loader.load()
        
        # 分块
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=256,
            chunk_overlap=50,
            separators=["\n\n", "\n", " ", ""]
        )
        
        # 分割文本
        texts = text_splitter.split_text("\n".join([doc.page_content for doc in documents]))
        
        # 转换为Document对象
        return [Document(page_content=text) for text in texts]
    
    def _run(self, query: str) -> str:
        """运行检索并返回相关文档内容
        
        Args:
            query: 用户查询
        """
        try:
            # 直接使用原始查询，不再使用历史感知
            docs = self.base_retriever.get_relevant_documents(query)
            
            # 格式化结果
            results = []
            for i, doc in enumerate(docs, 1):
                results.append(f"[Document {i}]\n{doc.page_content.strip()}")
            
            # 返回格式化的结果字符串
            if results:
                return "\n\n".join(results)
            else:
                return "No relevant documents found."
        except Exception as e:
            return f"Error during retrieval: {str(e)}"
    
    def _arun(self, query: str):
        """异步运行 - 不实现"""
        raise NotImplementedError("This tool does not support async")

def create_history_aware_retriever_tool(llm, pdf_path: str, k: int = 5):
    """创建检索工具实例 (不再具有历史感知能力)"""
    return HistoryAwareRetrieverTool(llm, pdf_path, k)