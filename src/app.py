from dotenv import load_dotenv
import sys

import gradio.route_utils

import os
import logging
from fastapi import FastAPI

from starlette.middleware.sessions import SessionMiddleware
import uvicorn
import fastapi

sys.path.append("..")
load_dotenv(".env")

from utils.log_config import setup_logging

from base_app import mount_base_app
from chat_app import mount_chat_app


# Override the get_root_url function to add the ROOT_PATH of the nginx proxy
def get_root_url(request: fastapi.Request, route_path: str, root_path: str | None):
    return ROOT_PATH + root_path if ENVIRONMENT != "Local" else root_path


gradio.route_utils.get_root_url = get_root_url


# Automatically configure the root logger when this module is imported
setup_logging()

# Log a message using the custom logger
logging.info("Logging initialized.")

ENVIRONMENT = os.getenv("ENVIRONMENT", "Local")

# Get the host name and root_path from the environment variables
HOST_NAME = os.environ.get("", None)
ROOT_PATH = None if ENVIRONMENT == "Local" else "/chat"
ROOT_PATH_URL = None if ENVIRONMENT == "Local" else f"https://{HOST_NAME}{ROOT_PATH}"

# Log the host name and root path
logging.info(f"host_name: {HOST_NAME}")
logging.info(f"root_path: {ROOT_PATH}")

# Start the FastAPI app
app = FastAPI(root_path=ROOT_PATH, root_path_in_servers=False, redirect_slashes=True)

SECRET_KEY = os.environ.get("") or "a_very_secret_key"
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

# Log a message using the custom logger
logging.info("FastAPI app started.")

app = mount_base_app(app)
app = mount_chat_app(app)

logging.info(app.root_path)
logging.info(app.routes)

if __name__ == "__main__":

    logging.info("Starting Gradio app with Uvicorn...")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=5000,
        log_level="info",
        proxy_headers=True,
    )
