import os

from dotenv import load_dotenv
from azure.identity import get_bearer_token_provider
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient


from typing import List, Dict, Tuple

from autogen_agentchat.conditions import TextMentionTermination
from autogen_agentchat.messages import HandoffMessage
from autogen_agentchat.teams import Swarm
from autogen_agentchat.ui import Console

from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry import trace
import openlit
import mlflow

from .custom_assistant_agent import CustomAssistantAgent
from .tools import invent_data, profile_data

import sys
import base64

sys.path.append("..")

from utils.credentials import get_credential_oai


ENVIRONMENT = os.getenv("ENVIRONMENT", "Local")

if ENVIRONMENT == "Local":
    load_dotenv(".env")


LANGFUSE_PUBLIC_KEY = ""
LANGFUSE_SECRET_KEY = ""
LANGFUSE_AUTH = base64.b64encode(f"{LANGFUSE_PUBLIC_KEY}:{LANGFUSE_SECRET_KEY}".encode()).decode()

os.environ[""] = "http://ip:3000/api/public/otel"  # EU data region
os.environ[""] = f"Authorization=Basic {LANGFUSE_AUTH}"


trace_provider = TracerProvider()
trace_provider.add_span_processor(SimpleSpanProcessor(OTLPSpanExporter()))

# Sets the global default tracer provider

trace.set_tracer_provider(trace_provider)

# Creates a tracer from the global tracer provider
tracer = trace.get_tracer(__name__)

# Initialize OpenLIT instrumentation. The disable_batch flag is set to true to process traces immediately.
openlit.init(tracer=tracer, disable_batch=True)


"""
os.environ[""] = ""
os.environ[""] = ""

# Optional: Set a tracking URI and an experiment
mlflow.set_tracking_uri("http://ip:5003/")
"""
mlflow.set_experiment("AutoGen3")
mlflow.config.enable_async_logging(enable=True)
mlflow.autogen.autolog()


class AgentChatBot:
    """ """

    def __init__(
        self,
        model_client: AzureOpenAIChatCompletionClient,
        log_flag=True,
    ):
        """
        Initializes a ChatBot instance

        Returns:
            None
        """
        self.log_flag = log_flag

        self.planner = CustomAssistantAgent(
            "planner",
            model_client=model_client,
            description="Planner. Given a user message, generate a plan to solve the problem and redirect to the proper agents.",
            handoffs=["chitchat", "data_profiler", "data_generator"],
            system_message=open("src/prompts/planner_system_message.md").read(),
        )

        self.chitchat = CustomAssistantAgent(
            "chitchat",
            model_client=model_client,
            description="Chitchater. For very basic chitchat conversations.",
            handoffs=["planner"],
            system_message=open("src/prompts/chitchat_system_message.md").read(),
        )

        self.data_generator = CustomAssistantAgent(
            "data_generator",
            model_client=model_client,
            handoffs=[],
            description="Data Generator. Generates a dataset of synthetic data.",
            system_message="Generate a synthetic dataset.",
            tools=[invent_data],
        )

        self.data_profiler = CustomAssistantAgent(
            "data_profiler",
            model_client=model_client,
            handoffs=[],
            description="Data Profiler. Given a dataset, generate a data profile report.",
            system_message="Generate a data profile. Only once you are finished with the profile, redirect to planner.",
            tools=[profile_data],
        )

    async def chat(self, user_message: str, team_state: Dict) -> Tuple[List[Dict], List[Dict]]:
        """ """
        with tracer.start_as_current_span("AutoGen3-Trace") as span:
            span.set_attribute("langfuse.user.id", "user-1230")
            span.set_attribute("langfuse.session.id", "1234567890")
            span.set_attribute("langfuse.tags", ["semantic-kernel", "demo"])

            # Define team
            termination = TextMentionTermination(text="T3RM1N4T3:")
            team = Swarm(
                [self.planner, self.chitchat, self.data_profiler, self.data_generator],
                termination_condition=termination,
            )

            # Load state from disk
            if team_state:
                await team.load_state(team_state)

            task = HandoffMessage(source="user", target="planner", content=user_message)

            # Use Console to generate the run
            # task_result = await Console(team.run_stream(task=task))
            task_result = await Console(team.run_stream(task=task))

            # Save the state of the agent team.
            team_state = await team.save_state()

            # Return generated messages and search debug information (if applicable)
            return task_result.messages, team_state


class AgentChatBotInit(AgentChatBot):

    def __init__(self):
        """Initializes a ChatBot instance."""

        # OPENAI
        self.oai_credentials = get_credential_oai()
        self.oai_token = self.oai_credentials.get_token(os.environ.get(""))

        self.model_client = AzureOpenAIChatCompletionClient(
            model=os.environ.get(""),
            api_version=os.environ.get(""),
            azure_endpoint=os.environ.get(""),
            azure_ad_token_provider=get_bearer_token_provider(self.oai_credentials, os.environ.get("")),
            # parallel_tool_calls=False,
        )

        super().__init__(
            model_client=self.model_client,
            log_flag=False,
        )
