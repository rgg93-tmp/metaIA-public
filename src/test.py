import logging

from utils.log_config import setup_logging
from utils_chat.agent_chatbot import AgentChatBot

from autogen_agentchat.messages import TextMessage
import asyncio

# Automatically configure the root logger when this module is imported
setup_logging()

# Log a message using the custom logger
logging.info("Gradio app logging initialized.")

# Chatbot demo with multimodal input (text, markdown, LaTeX, code blocks, image, audio, & video). Plus shows support for streaming text.
agent = AgentChatBot()

generated_messages, session_state = asyncio.run(agent.chat(user_message="Hi", team_state=None))

# Filter the text messages from the generated messages
text_messages = [message for message in generated_messages if isinstance(message, TextMessage)]

# Generate the output message
response = text_messages[-1].content

# Remove the T3RM1N4T3: token from the response
response = response.replace("T3RM1N4T3:", "")

print(session_state)
print(response)
