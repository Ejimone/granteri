# the agent will be running, make it will be able to make calls and recieve calls
from vapi import Vapi
import os
from dotenv import load_dotenv
from support_assistant import create_support_assistant
from inbound_calls import configure_inbound_calls