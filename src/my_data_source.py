import os
import pdfplumber  
from dataclasses import dataclass
from teams.ai.tokenizers import Tokenizer
from teams.ai.data_sources import DataSource
from teams.state.state import TurnContext
from teams.state.memory import Memory

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
        Initializes the data source and loads files from the 'data' directory.
        """
        self._name = name
        filePath = os.path.join(os.path.dirname(__file__), 'data')
        files = os.listdir(filePath)
        
        print(f"📂 Arquivos encontrados no diretório '{filePath}': {files}")

        self._data = []
        for file in files:
            file_path = os.path.join(filePath, file)
            if file.lower().endswith('.pdf'):
                extracted_text = self.read_pdf_plumber(file_path)
            else:
                extracted_text = self.read_file(file_path)
            
            print(f"\n📄 Conteúdo extraído de {file_path} (primeiras 500 caracteres):")
            print(extracted_text[:500])  # Exibir uma amostra dos dados extraídos

            self._data.append(extracted_text)

    @property
    def name(self):
        """Implementação do método abstrato 'name'."""
        return self._name

    def read_file(self, file_path):
        """Lê arquivos de texto de maneira otimizada."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                text = f.read().strip()
            return text
        except Exception as e:
            print(f"❌ Erro ao ler {file_path}: {e}")
            return ""

    def read_pdf_plumber(self, file_path):
        """Método otimizado para extrair texto de PDFs utilizando pdfplumber."""
        try:
            with pdfplumber.open(file_path) as pdf:
                text = "\n".join(page.extract_text() or "" for page in pdf.pages)  # Handle None
            return text.strip()
        except Exception as e:
            print(f"❌ Erro ao ler PDF {file_path}: {e}")
            return ""

    async def render_data(self, context: TurnContext, memory: Memory, tokenizer: Tokenizer, maxTokens: int):
        """Busca a query nos documentos carregados e retorna os resultados."""
        query = memory.get('temp.input')
        if not query:
            print("⚠️ Nenhuma consulta foi recebida na memória.")
            return Result('', 0, False)

        print(f"\n🔍 Buscando a consulta: '{query}' nos documentos...")

        result = ''
        for data in self._data:
            if query in data:
                result += data
            if 'IRPF' in query.lower() or 'irpf' in query.lower():
                result += self._data[0]  
        
        print(f"\n📊 Resultado da busca para '{query}' (primeiras 500 caracteres):")
        print(result[:500])  # Exibir uma amostra do resultado

        return Result(self.formatDocument(result), len(result), False) if result else Result('', 0, False)

    def formatDocument(self, result):
        """Formata a string de resultado."""
        return f"<context>{result}</context>"
