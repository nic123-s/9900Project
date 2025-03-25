import os
import json
import re
from langchain.chat_models import ChatOpenAI
from langchain.schema import (
    AIMessage,
    HumanMessage,
    SystemMessage
)

# Import template module at the top of the main file
from user_template import get_templates, select_template_for_user

def get_user_profile_collection_llm(streaming=True):
    """Initialize chat language model"""
    llm = ChatOpenAI(
        model_name="gpt-3.5-turbo",
        temperature=0.7,
        max_tokens=512,
        timeout=None,
        max_retries=2,
        streaming=streaming,
        openai_api_key=os.environ.get("OPENAI_API_KEY")
    )
    return llm

def interactive_user_profile_collection(llm):
    """Interactive user information collection, focusing on clean energy career experience"""
    # Initialize data storage
    slots = {
        "age": None,
        "education_background": None,
        "working_experience": None,
        "occupation_status": None  # 0: student, 1: sector shifters, 2: returning/retired workforce, 3: experienced professionals
    }
    conversation_history = []
    corrections_log = []  # Track all corrections made

    # Define correction commands
    correction_commands = {
        "correct age": "age",
        "modify age": "age",
        "change age": "age",
        "correct education": "education_background",
        "modify education": "education_background",
        "change education": "education_background",
        "correct occupation": "occupation_status",
        "modify occupation": "occupation_status",
        "change occupation": "occupation_status",
        "correct experience": "working_experience",
        "modify experience": "working_experience",
        "change experience": "working_experience"
    }

    # Initial greeting
    initial_message = (
        "Hi! I'm your Clean Energy Career Guidance Assistant 😊.\n"
        "Before we begin our formal consultation today, I need to gather some of your personal information. This will help me provide you with more professional career guidance and planning!"
    )
    print("💬 Chatbot:", initial_message)
    conversation_history.append({"role": "assistant", "content": initial_message})

    # Correction handling function
    def handle_correction(user_input):
        """Handle user information correction"""
        # Check for correction command
        for cmd, slot in correction_commands.items():
            if user_input.lower().startswith(cmd):
                # Extract new value
                new_value = user_input[len(cmd):].strip()
                
                # Log the correction
                correction_entry = {
                    "slot": slot,
                    "old_value": slots[slot],
                    "new_value": new_value,
                    "timestamp": len(conversation_history)
                }
                corrections_log.append(correction_entry)
                
                # Reset specific slots based on correction
                if slot == "occupation_status":
                    # If occupation status changes, reset working experience
                    slots["working_experience"] = None
                
                # Return processed correction
                return slot, new_value
        
        return None, None

    # Function to check if all required information is collected properly
    def is_information_complete():
        """Check if all required information is properly collected"""
        # Age must be an integer
        if not isinstance(slots["age"], int):
            return False
        
        # Education background must be a non-empty string
        if not (isinstance(slots["education_background"], str) and slots["education_background"].strip()):
            return False
        
        # Occupation status must be one of 0, 1, 2, 3
        if slots["occupation_status"] not in [0, 1, 2, 3]:
            return False
        
        # Working experience handling depends on occupation status
        if slots["occupation_status"] in [0, 1]:
            # For students and sector shifters, working experience should be 0
            return slots["working_experience"] == 0
        else:
            # For returning workforce and experienced professionals, 
            # working experience must be explicitly provided and not "Not provided"
            return (isinstance(slots["working_experience"], str) and 
                   slots["working_experience"].strip() and 
                   slots["working_experience"] != "Not provided" and
                   slots["working_experience"] != "unknown")
    
    # Conversation loop
    while not is_information_complete():
        user_input = input("🧑‍💻 You: ")
        
        # Exit mechanism
        if user_input.lower() in ["exit", "end", "bye", "goodbye"]:
            print("💬 Chatbot: No worries! Feel free to come back anytime. Take care!")
            break

        # Check for correction
        correction_slot, correction_value = handle_correction(user_input)
        if correction_slot:
            user_input = f"I want to update my {correction_slot} to {correction_value}"
            print(f"💬 Chatbot: I see you want to change your {correction_slot}. Let me help you with that.")

        conversation_history.append({"role": "user", "content": user_input})
        
        # Comprehensive prompt template focusing on occupation status understanding
        prompt_template = (
        "You are a professional clean energy career planning analyst who collects user information through precise, structured conversations to provide personalized career guidance.\n\n"
        
        "【Information Collection Objective】\n"
        "Before the formal consultation, we need to collect some basic information to provide targeted advice. Please note:\n"
        "1. The information must be collected in the following order: Age, Education Background, Occupation Status, Working Experience (conditional).\n"
        "2. Occupation Status is strictly limited to the following four categories:\n"
        "   - 0: Student – Full-time enrolled student\n"
        "   - 1: Sector Shifter – Transitioning from another industry to clean energy\n"
        "   - 2: Returning or Retired Workforce – Previously worked but now seeking reemployment\n"
        "   - 3: Experienced Professional – Currently employed in clean energy industry\n\n"
        
        "【Dialogue Guidance Logic】\n"
        "1. Opening Statement:\n"
        "   \"Hello, I am the Clean Energy Awareness and Employment Guidance Assistant. Before we begin the consultation, I need to collect some of your personal information to better provide professional guidance.\"\n\n"
        
        "2. Basic Information Collection (Age and Education Background):\n"
        "   Example: \"May I ask how old you are? What is your highest level of education?\"\n\n"
        "   !!!You cannot base on user's age and education background to infer user's occupational status or working expeience!\n"
        "   !!!You just can fill the age and education background, you cannot fill the user's occupational status or working expeience information!\n"

        "3. Occupation Status Confirmation:\n"
        "   - You should provide the format and provide current occupational status like the following example, beacuse it can help users to make choice quickly\n"
        "   Example: \"Could you please tell me which of the following best describes your current occupational status?\n"
        "           0 - Student (full-time enrolled),\n"
        "           1 - Sector Shifter (transitioning from another industry to clean energy),\n"
        "           2 - Returning or Retired Workforce (previously worked but seeking reemployment),\n"
        "           3 - Experienced Professional (currently employed in clean energy industry).\"\n"
        "   - Follow the conversation flow strictly and avoid asking questions beyond the target scope.\n"
        "   - Precisely determine the user's Occupation Status from their responses and ensure classification as 0, 1, 2, or 3.\n"
        "   - For ambiguous descriptions (e.g., 'I am a lawyer', 'I have not worked for many years', 'I work part-time', or 'I am considering a career change'), use semantic understanding and follow-up questions to guide the user to confirm the correct category. Specifically:\n"
        "   - If the user says 'I am a lawyer' or similar, prompt: \"A lawyer falls under Sector Shifter. Please confirm if you belong to option 1.\"\n"
        "   - If the user states 'I haven't worked for many years' or 'I have been out of work for a long time', prompt: \"If you have not worked for a long period and are seeking to re-enter the workforce, please choose option 2.\"\n"
        "   - For mixed cases (e.g., part-time, internship, or considering a change), ask about their primary source of income and main work focus. If their primary focus is not in the clean energy field, classify as Sector Shifter (1); if they have already taken steps to transition, classify as Sector Shifter (1); if full-time student, classify as Student (0).\n"
        "   - For freelancers or temporary workers, confirm whether their work involves the clean energy field. If not, classify as option 1; if transitioning, classify as option 1.\n"
        "   - For retirees who still occasionally consult, prompt that their core status is retired and recommend classifying as option 2.\n\n"
        
        "4. Working Experience Collection (Only for Occupation Status 2 or 3):\n"
        "For Returning or Retired Workforce (Option 2):\n"
        "    Follow these steps to respond and guide:\n"
        "    - If the user hasn't mentioned clean energy experience → Ask:\n"
        "    For example:\"Do you have any work experience or relevant working experience in the clean energy sector? like in solar, wind, or energy storage industries?\"\n"
        "    - If the user answers \"no\" or comes from another uncorrelated industry → use 0 to express no experience\n"
        "    - If the user answers \"yes\" → Follow up:\n"
        "    For example:\"How long have you worked in the clean energy sector before? Please specify in years or months, e.g., 2 years or 6 months.\n\n"
        "    - If the user provide a specific time range → Record the specific \"xx years or xx months\"\n"
        "    - If the user's response is vague → Clarify:\n"
        "    For example:\"If you don't remember how long you worked in this field before ,you also can provide a approximate figure? like maybe more than 2 years or 6 months.It can help you to get more professional guide\"\n"
        "    - If the user provide a vague time range → Record the vague \"about xx years or xx months\"\n"

        "For Experienced Professional (Option 3):\n"
        "    Follow these steps to respond and guide:\n"
        "    - If the user hasn't mentioned clean energy experience → Ask:\n"
        "    For example:\"How long have you worked in the clean energy sector now? Please specify in years or months, e.g., 2 years or 6 months.\n\n"
        "    - If the user provide a specific time range → Record the specific \"xx years or xx months\"\n"
        "    - If the user's response is vague → Clarify:\n"
        "    For example:\"If you don't remember how long you worked in this field before ,you also can provide a approximate figure? like maybe more than 2 years or 6 months.It can help you to get more professional guide\"\n"
        "    - If the user provide a vague time range → Record the vague \"about xx years or xx months\"\n"
        "    - If user proivde too vague time range, like \"many years\" → Please keep asking user and give some guide like \"more than 5 years or 10 years\"\n"
        "【Correction Context】\n"
        "CORRECTION CONTEXT:\n"
        "Corrections Made: {corrections}\n\n"
        
        "【Current Collected Information】\n"
        "CURRENT COLLECTED INFORMATION:\n"
        "- Age: {age}\n"
        "- Education Background: {education_background}\n"
        "- Occupation Status: {occupation_status}\n"
        "- Working Experience: {working_experience}\n\n"
        
        "【Conversation History】\n"
        "CONVERSATION HISTORY:\n{dialogue}\n\n"
        
        "【Latest User Input】\n"
        "LATEST USER INPUT: \"{user_input}\"\n\n"
        
        "【Return JSON Format Requirements】\n"
        "Your output must strictly conform to the following JSON format:\n"
        "{{\n"
        "  \"extracted_info\": {{\n"
        "    \"age\": <extracted age as a number>,\n"
        "    \"education_background\": \"standardized education background\",\n"
        "    \"occupation_status\": \"one of 0, 1, 2, or 3\",\n"
        "    \"working_experience\": \"specific or vague time range or 0 to express no experience\"\n"
        "  }},\n"
        "  \"response\": \"a precise response based on the user's situation\",\n"
        "  \"next_step\": \"a clear prompt for the next step\"\n"
        "}}\n\n"
        
        "【Note】\n"
        "- Strictly limit the conversation to the information mentioned above; do not ask questions beyond these details.\n"
        "- Each stage of questioning and judgment must be precise and clearly guided.\n"
        "- Ensure that each field's data is accurate, especially for the determination of Occupation Status.\n"
        "- IMPORTANT: DO NOT infer occupation_status or working_experience based on age or education. You must ONLY include these fields in your JSON response if the user has EXPLICITLY responded to a direct question about them.\n"
        "- For each field in your JSON response, ONLY include fields that have been directly addressed by the user's responses to specific questions.\n"
        "- Maintain a sequential information collection process: first collect age and education, then explicitly ask about occupation status with all 4 options, and only then (if needed) ask about working experience.\n"
        "- Never skip steps in the information collection process, even if you think you can infer information from context.\n"
        "- For users with occupation status 2 or 3, NEVER set working_experience to 'Not provided' in your JSON response.\n"
        "- Each stage of questioning should sound natural and conversational while remaining precise.\n"
        "- Respond directly to user questions before continuing with your information collection process.\n"
        "- Avoid robotic-sounding repeated phrases or unnecessary formality.\n"
        "- When asking about working experience, prefer natural phrasing like 'Yes, I'm asking about how long you've worked in the clean energy sector. Could you share that information?'\n"
    )

        # Prepare corrections display
        corrections_display = "\n".join([
            f"- Changed {c['slot']} from {c['old_value']} to {c['new_value']}"
            for c in corrections_log
        ]) or "No corrections made"

        # Prepare slot values for display only
        slot_values = {
            "age": "Not provided" if slots["age"] is None else slots["age"],
            "education_background": "Not provided" if slots["education_background"] is None else slots["education_background"],
            "occupation_status": "Not provided" if slots["occupation_status"] is None else slots["occupation_status"],
            "working_experience": "Not provided" if slots["working_experience"] is None else slots["working_experience"]
        }
        
        # Dialogue history
        dialogue_text = "\n".join([f"{'User' if msg['role'] == 'user' else 'Assistant'}: {msg['content']}" for msg in conversation_history])
        
        # Construct prompt
        prompt = prompt_template.format(
            age=slot_values["age"],
            education_background=slot_values["education_background"],
            occupation_status=slot_values["occupation_status"],
            working_experience=slot_values["working_experience"],
            dialogue=dialogue_text,
            user_input=user_input,
            corrections=corrections_display
        )

        # System message
        system_message = (
        "You are a friendly, conversational Clean Energy Career Guidance Assistant. "
        "Your goal is to understand the user's professional context with both precision and natural dialogue flow. "
        "Maintain a warm, helpful tone like a real human career counselor. "
        "When users ask questions, answer them directly first before continuing information collection. "
        "Be concise and avoid unnecessary formality or repetitive phrasing. "
        
        "IMPORTANT: You MUST ALWAYS respond with valid JSON format for ALL user inputs, including greetings, "
        "questions, or unclear messages. Your response must ALWAYS follow this exact structure:\n"
        "{\n"
        "  \"extracted_info\": {\n"
        "    // Include any fields with information you can extract\n"
        "    // Leave this as an empty object if no information is provided\n"
        "  },\n"
        "  \"response\": \"Your natural conversational response here\"\n"
        "}\n"
        
        "Even for simple inputs like 'hi' or 'what', always return this JSON format with appropriate response. "
        "This is critical for the system to function properly."
        )
        
        messages = [
            SystemMessage(content=system_message),
            HumanMessage(content=prompt)
        ]
        
        try:
            response = llm.invoke(messages)
            
            # JSON parsing
            try:
                json_str = re.search(r'({.*})', response.content, re.DOTALL)
                if json_str:
                    result = json.loads(json_str.group(1))
                else:
                    result = json.loads(response.content)
            except Exception:
                print("💬 Chatbot: I'm having trouble understanding. Could you rephrase that?")
                continue
            
            # Process extracted information
            extracted_info = result.get("extracted_info", {})
            
            # Debug information
            #print(f"DEBUG - Extracted info: {extracted_info}")
            #print(f"DEBUG - Current slots before update: {slots}")
            
            for key in slots.keys():
                new_value = extracted_info.get(key)
                
                if new_value is not None:
                    # Age handling
                    if key == "age":
                        try:
                            age = int(new_value)
                            if 0 < age < 120:
                                slots[key] = age
                        except (ValueError, TypeError):
                            pass
                    
                    # Education background handling
                    elif key == "education_background":
                        if isinstance(new_value, str) and new_value.strip():
                            slots[key] = new_value.strip()
                    
                    # Occupation status handling
                    elif key == "occupation_status":
                        try:
                            status = int(new_value)
                            if status in [0, 1, 2, 3]:
                                slots[key] = status
                                # Automatic working experience ONLY for students and sector shifters
                                if status in [0, 1]:
                                    slots["working_experience"] = 0
                                # For status 2 and 3, explicitly reset working experience to ensure it's asked
                                elif status in [2, 3] and slots["working_experience"] in [None, "Not provided", "unknown"]:
                                    slots["working_experience"] = None
                        except (ValueError, TypeError):
                            pass
                    
                    # Working experience handling
                    elif key == "working_experience":
                        # Only auto-set for status 0 and 1
                        if slots.get("occupation_status") in [0, 1]:
                            slots[key] = 0
                        # For status 2 and 3, require explicit valid input
                        elif (slots.get("occupation_status") in [2, 3] and 
                              isinstance(new_value, str) and 
                              new_value.strip() and 
                              new_value != "Not provided" and 
                              new_value != "unknown"):
                            slots[key] = new_value.strip()
            
            # Debug information
            #print(f"DEBUG - Current slots after update: {slots}")
           # print(f"DEBUG - Is information complete: {is_information_complete()}")
            
            # ===== 修改这部分代码 =====
            # 检查是否所有信息都已完成收集
            if is_information_complete():
                # 如果信息收集完成，只显示最终消息
                final_message = "Thank you for sharing your information! We'll now match you with a professional clean energy career advisor 😊."
                print("💬 Chatbot:", final_message)
                conversation_history.append({"role": "assistant", "content": final_message})
                # 退出对话循环
                break
            else:
                # 否则显示模型生成的回应
                natural_response = result.get("response", "Could you tell me more?")
                next_step = result.get("next_step", "")
                
                if next_step:
                    natural_response += f" {next_step}"
                
                print("💬 Chatbot:", natural_response)
                conversation_history.append({"role": "assistant", "content": natural_response})
            # ===== 修改结束 =====
            
        except Exception as e:
            #print(f"DEBUG - Exception: {str(e)}")
            fallback_response = "I'm listening carefully. Could you help me understand more about your background?"
            print("💬 Chatbot:", fallback_response)
            conversation_history.append({"role": "assistant", "content": fallback_response})
    
    
    return slots, conversation_history, corrections_log


if __name__ == '__main__':
    llm = get_user_profile_collection_llm(streaming=True)
    user_profile, history, corrections = interactive_user_profile_collection(llm)
    print("\n===== Final User Profile =====")
    print(json.dumps(user_profile, ensure_ascii=False, indent=2))
    
    print("\n===== Corrections Log =====")
    print(json.dumps(corrections, ensure_ascii=False, indent=2))

    # Get all templates
    # Use imported function to select template
    selected_template = select_template_for_user(user_profile)

    # Print selected template
    print("\n===== Matched Template =====")
    print(f"Template ID: {selected_template['id']}")
    print(f"Template Name: {selected_template['name']}")
    print(f"Description: {selected_template['description']}")