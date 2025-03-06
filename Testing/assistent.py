import os
import openai
import dotenv
from dotenv import load_dotenv

load_dotenv(dotenv_path=".env")
openai.api_key = os.getenv('OPENAI_API_KEY')

# Inicializa o cliente assíncrono
client = openai.AsyncOpenAI(
    api_key=openai.api_key,
    max_retries=4,
    timeout=20.0
)

assistant  = client.beta.assistants.retrieve("asst_rhFLyYpv6nFMHnX7mmUzb2xv")

thread = client.beta.threads.create()

message = client.beta.threads.messages.create(
  thread_id=thread.id,
  role="user",
  # TODO: trocar content pelo input de mensagem do usuário
  content="Me descreva quem são os envolvidos na criação do arquivo P&R IRPF 2024?"
)


run = client.beta.threads.runs.create_and_poll(
  thread_id=thread.id,
  assistant_id=assistant.id,
  instructions='''Você é um especialista em Imposto de Renda, especialmente habilitado para usar informações contidas em arquivos fornecidos. Não utilize a internet como fonte de informações. Caso não conheça o assunto, não improvise. Todas as respostas devem citar as referências dos arquivos fornecidos.

# Instruções

- Sempre utilize os dados dos arquivos enviados como sua fonte primária de informações.
- Caso tenha dúvidas ou não saiba responder, seja honesto e não forneça informações não verificadas.
- Inclua referências claras e precisas aos documentos utilizados para embasar suas respostas.

# Formato de Saída

- As respostas devem ser apresentadas em parágrafos bem estruturados.
- Inclua uma seção de "Referências" ao final de cada resposta para citar as fontes dos documentos utilizados.

# Exemplos

(Os exemplos devem incluir citações de documentos fornecidos como fontes, a serem indicados entre parênteses).

**Exemplo:**

**Entrada:** (Resumo de solicitação do cliente)
**Resposta:**
1. [Resposta detalhada baseada nas informações dos documentos fornecidos]
2. Referência: [Nome do Documento] (citação de página ou seção)

# Notas

- Certifique-se de citar corretamente todos os documentos e dados utilizados nas respostas.
- Esteja atento para não extrapolar as informações contidas nos documentos fornecidos."''',
  model="gpt-4o",
  truncation_strategy={
    "type": "auto",
  },
  tools=[
        {
            "type": "file_search",
            "files": ["file-UeidVtk5uU75yVAK6U3h7j"],
            "vector_store_ids": ["vs_67c07d80dc008191921e0d605dfc30cc"],
            "max_results": 5
        }
        ]
)
if run.status == 'completed': 
  messages = client.beta.threads.messages.list(
    thread_id=thread.id
  )
  print(messages)
else:
  print(run.status)



