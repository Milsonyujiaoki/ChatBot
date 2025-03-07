import os
from dataclasses import dataclass

from teams.ai.tokenizers import Tokenizer
from teams.ai.data_sources import DataSource
from teams.state.state import TurnContext
from teams.state.memory import Memory

from Assistant import interagir_com_assistente  # Importando a função do outro módulo
import asyncio  # Necessário para chamadas assíncronas
import chardet

@dataclass
class Result:
    output: str
    length: int
    too_long: bool

class MyDataSource(DataSource):
    """
    A data source that searches through a local directory of files for a given query.
    """

    def __init__(self, name):
        """
        Creates a new instance of the LocalDataSource instance.
        Initializes the data source.
        """
        self.name = name
        
        filePath = os.path.join(os.path.dirname(__file__), 'data')
        files = os.listdir(filePath)
        self._data = []
        for file in files:
            file_path = os.path.join(filePath, file)
    
            # Detecta a codificação do arquivo
            with open(file_path, 'rb') as f:
                raw_data = f.read()
                encoding = chardet.detect(raw_data)['encoding']
    
            # Abre o arquivo usando a codificação detectada
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    self._data.append(f.read())
            except Exception as e:
                print(f"Erro ao ler o arquivo {file}: {e}")
        
    def name(self):
        return self.name

    async def render_data(self, context: TurnContext, memory: Memory, tokenizer: Tokenizer, maxTokens: int):
        """
        Renders the data source as a string of text.
        The returned output should be a string of text that will be injected into the prompt at render time.
        """
        query = memory.get('temp.input')
        if not query:
            return Result('', 0, False)
    
        result = ''

        # Obtém resposta do Assistente
        resposta_assistente = await interagir_com_assistente(query)

        # Adiciona a resposta do assistente no resultado
        if resposta_assistente:
            result += f"\nResposta da IA:\n{resposta_assistente}\n"

        # Pesquisa nos arquivos locais
        for data in self._data:
            if query in data:
                result += data

        return Result(self.formatDocument(result), len(result), False) if result != '' else Result('', 0, False)

    def formatDocument(self, result):
        """
        Formats the result string 
        """
        return f"<context>{result}</context>"