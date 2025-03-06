import os
import sys
import traceback
import json
import openai
import pdfplumber
from dotenv import load_dotenv
from dataclasses import asdict
from botbuilder.core import MemoryStorage, TurnContext
from teams import Application, ApplicationOptions, TeamsAdapter
from teams.ai import AIOptions
from teams.ai.models import OpenAIModel, OpenAIModelOptions
from teams.ai.planners import ActionPlanner, ActionPlannerOptions
from teams.ai.prompts import PromptManager, PromptManagerOptions
from teams.state import TurnState
from teams.feedback_loop_data import FeedbackLoopData
from teams.ai.tokenizers import Tokenizer
from teams.ai.data_sources import DataSource
from teams.state.memory import Memory

from Testing.my_data_source import MyDataSource
from config import Config

# Carregar variáveis de ambiente
load_dotenv(dotenv_path=".env")

config = Config()

# Inicializa o cliente OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")
client = openai.AsyncOpenAI(
    api_key=openai.api_key,
    max_retries=4,
    timeout=20.0
)

# Inicializa o assistente corretamente
async def get_assistant():
    return await client.beta.assistants.retrieve("asst_rhFLyYpv6nFMHnX7mmUzb2xv")

assistant = None  # Inicializar como None

async def initialize_assistant():
    global assistant
    assistant = await get_assistant()

# Criar componentes de IA
model = OpenAIModel(
    OpenAIModelOptions(
        api_key=config.OPENAI_API_KEY,
        default_model=config.OPENAI_MODEL_NAME,
    )
)

prompts = PromptManager(PromptManagerOptions(prompts_folder=f"{os.getcwd()}/prompts"))

# Adicionar fonte de dados personalizada (descomente se necessário)
my_data_source = MyDataSource('local-search')
prompts.add_data_source(my_data_source)

planner = ActionPlanner(
    ActionPlannerOptions(model=model, prompts=prompts, default_prompt="chat")
)

# Definição do armazenamento e criação da aplicação do bot
storage = MemoryStorage()
bot_app = Application[TurnState](
    ApplicationOptions(
        bot_app_id=config.APP_ID,
        storage=storage,
        adapter=TeamsAdapter(config),
        ai=AIOptions(planner=planner, enable_feedback_loop=True),
    )
)

@bot_app.error
async def on_error(context: TurnContext, error: Exception):
    print(f"\n [on_turn_error] unhandled error: {error}", file=sys.stderr)
    traceback.print_exc()
    await context.send_activity("The bot encountered an error or bug.")

@bot_app.feedback_loop()
async def feedback_loop(_context: TurnContext, _state: TurnState, feedback_loop_data: FeedbackLoopData):
    print(f"Your feedback is:\n{json.dumps(asdict(feedback_loop_data), indent=4)}")

async def process_message(context: TurnContext, state: TurnState):
    user_message = context.activity.text.strip()
    print(f"🔍 Mensagem recebida: {user_message}")

    global assistant
    if assistant is None:
        await initialize_assistant()

    thread = await client.beta.threads.create()
    message = await client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=user_message
    )

    run = await client.beta.threads.runs.create_and_poll(
        thread_id=thread.id,
        assistant_id=assistant.id,
        instructions="Suas instruções aqui...",
        model="gpt-4o",
        truncation_strategy={"type": "auto"},
        tools=[{"type": "file_search", "files": ["file-UeidVtk5uU75yVAK6U3h7j"], "max_results": 5}]
    )

    if run.status == 'completed': 
        messages = await client.beta.threads.messages.list(thread_id=thread.id)
        response_text = messages.data[0].content
        print(f"✅ Resposta do assistente: {response_text}")
        await context.send_activity(response_text)
    else:
        print(f"⚠️ Status da execução: {run.status}")
        await context.send_activity("O assistente está processando sua solicitação.")

@bot_app.message("text")
async def on_message(context: TurnContext, state: TurnState):
    await process_message(context, state)
