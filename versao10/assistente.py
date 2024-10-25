from openai import OpenAI
from config import API_KEY
from openai import OpenAIError
import logging

class Assistente:
    def __init__(self, API_KEY: str, exemplos: list):
        self.exemplos = exemplos  # Armazena os exemplos como parte da classe
        self.historico = []  # Inicialmente vazio, será preenchido pelo código principal
        try:
            self.cliente = OpenAI(api_key=API_KEY)
        except OpenAIError as e:
            print(f"Erro ao inicializar o cliente OpenAI: {e}")
        
    def set_histórico(self, historico: list):
        self.historico = historico

    def analisar_consulta(self, consulta: str) -> dict:

        system_message_assistente = {
            "role": "system",
            "content": (
                "Você é um assistente de chatbot que vai auxiliar na análise dos prompts feitos a um analista de investimento.\n\n"
                "Exemplos:\n" +
                "\n".join([f"user: {exemplo['content']}" if exemplo['role'] == 'user' else f"assistant: {exemplo['content']}" for exemplo in self.exemplos]) +
                "\n\nHistórico:\n" +
                "\n".join([f"{message['role']}: {message['content']}" for message in self.historico if message['role'] != 'system']) +  # Remover capitalização aqui
                "\n\nConsulta a ser transformada:\n" + consulta
            )
        }

        # Adiciona system_message, exemplos e histórico
        messages = [system_message_assistente]
        print(messages)

        try:
            resposta = self.cliente.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                max_tokens=150
            )
            resposta = resposta.choices[0].message.content.strip()

            # Inicializamos o dicionário de resultado padrão
            resultado = {
                "nova_busca": "",
                "fundo_especifico": "",
                "nome_fundo": "",
                "consulta": ""
            }

            # 1. Verificar se existe "Nova Busca"
            if "Nova Busca:" in resposta:
                partes_nova_busca = resposta.split("Nova Busca:")
                resultado["nova_busca"] = partes_nova_busca[1].split()[0].strip()  # Pegamos o primeiro valor (Sim ou Não)

            # 2. Verificar se existe "Fundo Específico"
            if "Fundo Específico:" in resposta:
                partes_fundo_especifico = resposta.split("Fundo Específico:")
                resultado["fundo_especifico"] = partes_fundo_especifico[1].split()[0].strip()  # Sim ou Não

            # 3. Verificar se existe "nome Fundo"
            if "nome Fundo:" in resposta:
                partes_nome_fundo = resposta.split("nome Fundo:")
                resultado["nome_fundo"] = partes_nome_fundo[1].split("Consulta:")[0].strip()  # Pegamos o nome do fundo antes de "Consulta"

            # 4. Verificar se existe "Consulta"
            if "Consulta:" in resposta:
                partes_consulta = resposta.split("Consulta:")
                resultado["consulta"] = partes_consulta[1].strip()  # Pegamos o restante da frase após "Consulta"

            # Retorna o dicionário preenchido
            return resultado

        except IndexError as e:
            logging.error(f"Erro de índice: {e}")
            return {"erro": "Erro de formatação na resposta do modelo."}
        except Exception as e:
            logging.error(f"Erro ao processar a consulta: {e}")
            return {"erro": "Erro inesperado ao processar a consulta."}