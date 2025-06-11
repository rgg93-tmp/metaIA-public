from dotenv import load_dotenv
import sys

import gradio as gr

import logging

from base_app import get_user
from fastapi.responses import FileResponse

from agents.agent_chatbot import AgentChatBotInit
from autogen_agentchat.messages import TextMessage

sys.path.append("..")
load_dotenv(".env")

from utils.log_config import setup_logging

setup_logging()
logging.info("Logging initialized.")

###############
### CHATBOT ###
###############

# Chatbot demo with multimodal input (text, markdown, LaTeX, code blocks, image, audio, & video). Plus shows support for streaming text.


def add_message(history, message):
    for x in message["files"]:
        history.append({"role": "user", "content": {"path": x}})
    if message["text"] is not None:
        history.append({"role": "user", "content": message["text"]})
    return history, gr.MultimodalTextbox(value=None, interactive=False)


async def bot(history: list, session_state: dict):

    # Init chatbot
    agent = AgentChatBotInit()

    try:
        # Get user message
        user_input = history[-1]["content"]

        # Run team
        print(session_state)
        generated_messages, session_state = await agent.chat(user_message=user_input, team_state=session_state)

        # Filter the text messages from the generated messages
        text_messages = [message for message in generated_messages if isinstance(message, TextMessage)]

        # Generate the output message
        response = text_messages[-1].content

        # Remove the T3RM1N4T3: token from the response
        response = response.replace("T3RM1N4T3:", "")
    except Exception as e:
        response = str("Ha ocurrido un error:\n", e)

    history.append({"role": "assistant", "content": response})
    return history, session_state


def clean_team_state(session_state: dict):
    # Delete state
    return None


with gr.Blocks(title="Chat") as chat_app:
    session_state = gr.State()

    # Chat interface
    chatbot = gr.Chatbot(elem_id="chatbot", label="Chat", bubble_full_width=False, type="messages")

    chat_input = gr.MultimodalTextbox(
        interactive=True, sources=[], placeholder="Escriba su mensaje aquí...", show_label=False
    )

    # Chat interactions
    chat_msg = chat_input.submit(add_message, [chatbot, chat_input], [chatbot, chat_input], queue=False)
    bot_msg = chat_msg.then(bot, [chatbot, session_state], [chatbot, session_state], api_name="bot_response")
    bot_msg.then(lambda: gr.MultimodalTextbox(interactive=True), None, [chat_input])

    # If the user clears the chat, reset the chatbot
    chatbot.clear(clean_team_state, session_state, session_state)


def favicon():
    favicon_path = "themis2.png"
    return FileResponse(favicon_path)


def mount_chat_app(app):
    """Mounts the app with classif page on top of FastAPI app."""

    logging.info("Gradio chat app initialized.")

    # Mount the Gradio app for the classifier in the classif path
    app.add_api_route("/chat/favicon.ico", favicon, methods=["GET"])

    app = gr.mount_gradio_app(
        app,
        chat_app,
        path="/chat",
        root_path="/chat",
        auth_dependency=get_user,
        max_file_size="1mb",
    )

    logging.info("Gradio chat app mounted.")

    return app
