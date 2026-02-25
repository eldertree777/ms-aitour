import azure.functions as func
import logging
from agent_framework.azure import AgentFunctionApp
from agents.master_agent import create_master_agent

app = AgentFunctionApp(
    agents=[create_master_agent()], 
    enable_health_check=True, 
    max_poll_retries=50
)