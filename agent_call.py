from langchain_core.tools import tool
from service import CalenderService, to_timezone
from datetime import datetime, timedelta

calender_service = CalenderService()

DATE_FORMAT = "%Y-%m-%d %H:%M:%S %Z"


def convert_to_str(slot):
    return f"{slot[0].strftime(DATE_FORMAT)} to {slot[0].strftime(DATE_FORMAT)}"


def convert_back_datetime(slot):
    start, end = slot.split(" to ")
    return (
        to_timezone(datetime.strptime(start, DATE_FORMAT)),
        to_timezone(datetime.strptime(end, DATE_FORMAT)),
    )


@tool
def get_free_slots():
    """Get Free slots list for booking appointment."""
    slots = calender_service.find_free_slots(
        business_hours={
            "start": to_timezone(datetime(2024, 3, 16, 10, 0, 0)),
            "end": to_timezone(datetime(2024, 3, 16, 22, 0, 0)),
        },
        appointment_duration=timedelta(minutes=30),
    )
    slots = [convert_to_str(slot) for slot in slots]
    return slots


@tool
def create_event(data):
    """Create event for the given time slot.
    Args:
        data: slot for appointment
    """

    start, end = convert_back_datetime(data)
    res = calender_service.event_manager.create_event(
        start, end, "summary", description="sample", location=None
    )
    return res["status"]


tools = [get_free_slots, create_event]
from langchain import hub
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate

# Get the prompt to use - you can modify this!
prompt = hub.pull("hwchase17/openai-tools-agent")
prompt.pretty_print()

# Choose the LLM that will drive the agent
# Only certain models support this
model = ChatOpenAI(model="gpt-3.5-turbo-1106", temperature=0)

consent_prompt = (
    "You are assist to help salesman to book appointment of users."
    "Your task is to ask the user to book appointment. If the user says yes, then show the appointment slots to user, return the index number based on his choice from 0 to n"
    "After the slot is choosen, create event by calling relevent function, with choosen slot data"
)

# prompt_template =
from langchain.memory.buffer import ConversationBufferMemory

conversation_memory = ConversationBufferMemory(
    memory_key="chat_history",
    max_len=200,
    return_messages=True,
)
prompt.messages[0].prompt = PromptTemplate(template=consent_prompt, input_variables=[])
# Construct the OpenAI Tools agent
agent = create_openai_tools_agent(model, tools, prompt)

# Create an agent executor by passing in the agent and tools
agent_executor = AgentExecutor(
    agent=agent, tools=tools, verbose=True, memory=conversation_memory
)
output = agent_executor.invoke({"input": "Hi"})
output = agent_executor.invoke({"input": "Book appointment"})
output = agent_executor.invoke({"input": "2nd"})
print(output)
