# main.py - 主函数部分

from langchain.agents import AgentType, initialize_agent
from langchain.memory import ConversationBufferMemory
from langchain_openai.chat_models import ChatOpenAI
import os
import json
import sys

# 导入您的工具模块（确保这些文件存在于相同目录或已添加到路径中）
from retriever_tool import create_history_aware_retriever_tool
from linkedin_job_tool import LinkedInJobTool
from web_search_tool import create_web_search_tool, WebSearchTool

# 导入用户画像相关模块
from user_profile_collector import get_user_profile_collection_llm, interactive_user_profile_collection
from user_template import select_template_for_user

def get_chat_llm(streaming=True):
    """初始化聊天语言模型"""
    llm = ChatOpenAI(
        model_name="gpt-3.5-turbo",  # 或 "gpt-4"
        temperature=0.3,
        max_tokens=512,
        timeout=None,
        max_retries=2,
        streaming=streaming,
        openai_api_key=os.environ.get("OPENAI_API_KEY")
    )
    return llm

def save_conversation_to_history(memory, conversation_history):
    """将对话历史保存到会话存储"""
    for message in conversation_history:
        if message["role"] == "assistant":
            memory.chat_memory.add_ai_message(message["content"])
        elif message["role"] == "user":
            memory.chat_memory.add_user_message(message["content"])

def main():
   
    # 设置会话ID
    session_id = "user123"
    
    # 初始化LLM
    llm = get_chat_llm()
    get_user_profile_llm = get_user_profile_collection_llm()

    # 创建工具实例
    # 1. 历史感知检索工具
    pdf_path = 'knowledge_database/ED520114.pdf'  # 确保此路径指向您的PDF文件 9900\knowledge_database
    print(os.path.exists(pdf_path))
    retriever_tool = create_history_aware_retriever_tool(llm, pdf_path)
    
    # 2. LinkedIn职位搜索工具
    linkedin_tool = LinkedInJobTool()

    # 3. Web搜索工具
    web_search_tool = create_web_search_tool()
    
    # 收集用户画像
    user_profile, history, corrections= interactive_user_profile_collection(get_user_profile_llm)
    
    # 选择模板
    selected_template = select_template_for_user(user_profile)

    # 提取风格指南和工具使用指南
    style_guide = selected_template.get('style_guide', '')
    tool_usage_guidelines = selected_template.get('Tool_Usage_Guidelines', '')
    
    
    # 创建包含用户信息的自定义系统提示
    custom_prefix = f"""You are a professor specializing in clean energy careers guidance.

    USER PROFILE:
    - Age: {user_profile['age']}
    - Education_level: {user_profile['education_background']}
    - Occupation_status: {selected_template['name']}
    - Clean Energy Working Experience: {user_profile['working_experience']}


    - Carefully consider the user's background information(USER PROFILE) above when crafting your responses. Tailor your advice, explanations, and tool selections to be most relevant and helpful given their specific age, education level, occupation status, and experience in the clean energy sector.
    
    - When responding to the user, carefully incorporate the principles and communication style from the following STYLE GUIDE:
    {style_guide}
    
    - For determining when and how to use available tools, follow these TOOL USAGE GUIDELINES:
    {tool_usage_guidelines}
    
    - Ensure your responses maintain the professional tone, expertise level, and structured approach outlined in the style guide while leveraging tools according to the specified guidelines.
    """

    
    # 将工具组合成工具列表
    tools = [
        retriever_tool,  # 假设这已经是LangChain Tool类型
        linkedin_tool.get_tool(),
        web_search_tool

    ]
    
    # 设置会话记忆
    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
    
    # 保存初始对话历史
    save_conversation_to_history(memory, history)
    

    # 自定义后缀
    suffix = """Begin!

    Previous conversation history:
    {chat_history}

    New human input: {input}
    {agent_scratchpad}"""

    # 配置Agent
    agent = initialize_agent(
        tools=tools,
        llm=llm,
        agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
        verbose=True,  # 设为True可以看到详细的思考过程
        memory=memory,
        handle_parsing_errors=True,
        agent_kwargs={
            "prefix": custom_prefix,
            #"format_instructions": format_instructions,
            "suffix": suffix,
            "ai_prefix": "CleanEnergyExpert"
        }
    )
    
    # 添加欢迎消息
    welcome_message = (
        f"Thank you for sharing your information! "
        f"I'll tailor my guidance to your needs. How can I help with your clean energy career questions today? 😊"
        
    )
    print(f"💬 Chatbot:{welcome_message}")
    
    # 对话循环
    while True:
        user_input = input("🧑‍💻 You:")
        if user_input.lower() == "exit" or user_input.lower() == "end":
            print("💬 Chatbot:Thank you for our conversation. Best of luck with your clean energy career journey!")
            break
        
        # 使用Agent处理用户输入
        try:
            response = agent.run(user_input)
            print(f"💬 Chatbot:{response}")
        except Exception as e:
            print(f"Error: {str(e)}")
            print("💬 Chatbot:I apologize for the error. How else can I assist you?")

if __name__ == "__main__":
    main()