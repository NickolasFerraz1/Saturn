from openai import OpenAI
from config import API_KEY
from collections import deque
from openai import OpenAIError

class Chatbot:
    def __init__(self, API_KEY: str):
        try:
            self.cliente = OpenAI(api_key=API_KEY)
            self.historico_conversa = deque([{"role": "system", "content": "Você é um assistente de investimentos que responde consultas com base em contexto extraído de documentos relevantes."}])
            self.contexto_adicional = None
        except OpenAIError as e:
            print(f"Erro ao inicializar o cliente OpenAI: {e}")

    def criar_lista_mensagens(self, nova_mensagem: str) -> deque:
        """Adicionar uma nova mensagem ao histórico da conversa"""
        self.historico_conversa.append({"role": "user", "content": nova_mensagem})
        return self.historico_conversa

    def chamar_modelo_gpt(self, mensagens: deque) -> str:
        """Chamar o modelo GPT com o histórico da conversa"""
        try:
            print(mensagens)
            mensagens_temp = list(mensagens)  # Converta para lista, pois deque não é aceito diretamente
            if self.contexto_adicional:
                #mensagens_temp.append({"role": "user", "content": self.contexto_adicional})
                mensagens_temp.append(self.contexto_adicional)
                print(mensagens_temp)
                self.contexto_adicional = None  # Limpa o contexto adicional após usá-lo
            resposta = self.cliente.chat.completions.create(
                model="gpt-4o-mini",
                messages=mensagens_temp,
                max_tokens=2048,
                n=1,
                stop=None,
                temperature=0.7
            )
            if resposta.choices:
                #print(mensagens_temp)
                return resposta.choices[0].message.content
            else:
                return "Nenhuma resposta do modelo GPT"
        except OpenAIError as e:
            print(f"Erro ao chamar o modelo GPT: {e}")

    def continuar_conversa(self, nova_mensagem: str) -> str:
        """Continuar a conversa com uma nova mensagem"""
        # Adicione a nova mensagem ao histórico
        self.criar_lista_mensagens(nova_mensagem)
        # Chame o modelo GPT com o histórico atualizado
        resposta = self.chamar_modelo_gpt(self.historico_conversa)
        # Adicione a resposta ao histórico
        self.historico_conversa.append({"role": "assistant", "content": resposta})
        return resposta
    
    def adicionar_contexto(self, contexto: str):
        """Adicionar ou substituir o contexto adicional"""
        contexto_completo = "Contexto relevante: " + contexto
        contexto_obj = {"role": "user", "content": contexto_completo}
        self.contexto_adicional = contexto_obj
