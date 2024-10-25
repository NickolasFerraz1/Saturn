from chatbot import Chatbot
from assistente import Assistente
from buscador import Buscador
from config import API_KEY
from exemplos import exemplos
 
# Inicializa os componentes
conversa_bot = Chatbot(API_KEY)
assistente = Assistente(API_KEY, exemplos)
buscador = Buscador(API_KEY)
 
def processar_conversa(mensagem_usuario):
    """
    Processa a mensagem do usuário e retorna a resposta do chatbot.
    Essa função será usada no código Flask para processar as interações.
    """
    try:
        # Atualiza o histórico com a nova mensagem do usuário
        historico_assistente = conversa_bot.historico_conversa
        assistente.set_histórico(historico_assistente)
 
        # Análise da consulta pelo assistente antes da resposta do chatbot
        resultado_assistente = assistente.analisar_consulta(mensagem_usuario)
 
        # Se a análise do assistente determinar que é necessário buscar informações adicionais, 
        # adiciona o contexto relevante ao histórico do chatbot aqui.
        if resultado_assistente['nova_busca'].lower() == "sim":
            contexto = buscador.responder_consulta(resultado_assistente)
            conversa_bot.adicionar_contexto(contexto)
 
        # Obtém a resposta do chatbot com base no histórico atualizado
        resposta_bot = conversa_bot.continuar_conversa(mensagem_usuario)
        return resposta_bot
 
    except Exception as e:
        return f"Ocorreu um erro: {e}"