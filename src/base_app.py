from dotenv import load_dotenv
import sys

import gradio as gr
import os
import logging
from fastapi import Depends, Request

from starlette.responses import RedirectResponse
from fastapi.responses import FileResponse

sys.path.append("..")
load_dotenv(".env")

from utils.auth import login_url, acquire_token_by_auth_code, validate_token

ENVIRONMENT = os.getenv("ENVIRONMENT", "Local")

# Get the host name and root_path from the environment variables
HOST_NAME = os.environ.get("", None)
ROOT_PATH = None if ENVIRONMENT == "Local" else "/chat"
ROOT_PATH_URL = None if ENVIRONMENT == "Local" else f"https://{HOST_NAME}{ROOT_PATH}"


###############
###  LOGIN  ###
###############


def get_user(request: Request):
    """Dependency to get the current user from the session."""

    if ENVIRONMENT == "Local":
        return {"name": "local", "oid": "local"}
    user = request.session.get("user")
    if not user or "id_token" not in user:
        return None

    id_token = user[""]
    claims = validate_token(id_token)

    if not claims:
        # Invalid token — maybe tampered or expired
        request.session.pop("user", None)  # Force logout
        return None

    return claims  # Or any field you want to use


async def public(request: Request, user: dict = Depends(get_user)):
    if user:
        return RedirectResponse(url="/classif/" if ROOT_PATH_URL is None else f"{ROOT_PATH_URL}/classif/")
    else:
        try:
            # Case 1: Azure redirected back with ?code=
            if "code" in request.query_params:
                code = request.query_params.get("code")
                # state = request.query_params.get("state")

                result = acquire_token_by_auth_code(code)

                if "error" in result:
                    logging.error(f"Login error: {result['error_description']}")
                    return f"Login error: {result['error_description']}", 401

                # Store user in session
                request.session["user"] = {
                    "id_token": result.get(""),
                    "claims": result.get(""),
                }

                return RedirectResponse(url="/classif/" if ROOT_PATH_URL is None else f"{ROOT_PATH_URL}/classif/")
            else:
                return RedirectResponse(login_url())
        except Exception as e:
            logging.error(f"Error public{str(e)}")
            return RedirectResponse(login_url())


async def login(request: Request):
    return RedirectResponse(login_url())


async def logout(request: Request):
    request.session.pop("user", None)
    return RedirectResponse(url=request.url_for("/login-app/"))


def favicon():
    favicon_path = "themis2.png"
    return FileResponse(favicon_path)


# Gradio Login Page
with gr.Blocks() as login_app:
    gr.Button("Login with Azure", link="/login" if ROOT_PATH is None else f"{ROOT_PATH}/login")


def mount_base_app(app):
    """Mounts the base app with login on top of FastAPI app."""

    logging.info("Gradio base app with login initialized.")

    app.add_api_route("/", public, methods=["GET"])
    app.add_api_route("/login", login, methods=["GET"])
    app.add_api_route("/logout", logout, methods=["GET"])
    app.add_api_route("/favicon.ico", favicon, methods=["GET"])
    app.add_api_route("/login-app/favicon.ico", favicon, methods=["GET"])

    # Mount the Gradio app for the login in the login-app path
    app = gr.mount_gradio_app(app, login_app, path="/login-app", root_path="/login-app")

    logging.info("Gradio base app with login mounted.")

    return app
