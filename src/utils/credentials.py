import os

from dotenv import load_dotenv

ENVIRONMENT = os.getenv("ENVIRONMENT", "Local")

if ENVIRONMENT == "Local":
    load_dotenv(".env")


def get_credential_oai():
    """
    Retrieves the appropriate Azure authentication credential based on the current environment.

    Returns:
        Credential: An authentication credential object for accessing Azure resources.
    """
    credential = ...
    return credential


def get_credential_aisearch():
    """
    Retrieves the appropriate Azure authentication credential based on the current environment.

    Returns:
        Credential: An authentication credential object for accessing Azure resources.
    """
    credential = ...
    return credential
