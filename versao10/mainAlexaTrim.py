from chatbot import Chatbot
from assistente import Assistente
from buscador import Buscador
from config import API_KEY
from exemplos import exemplos
from audio import falar_azure, detectar_ruido_e_ouvir  # Importando as funções de áudio

# Variável de estado para controlar o modo de entrada (inicialmente texto)
modo_entrada = "texto"

if __name__ == "__main__":
    conversa_bot = Chatbot(API_KEY)
    assistente = Assistente(API_KEY, exemplos)
    buscador = Buscador(API_KEY)
    
    while True:
        try:
            # Verifica o modo de entrada atual e coleta a mensagem do usuário
            if modo_entrada == 'voz':
                # Usa o detector de ruído para ativar a escuta
                mensagem_usuario = detectar_ruido_e_ouvir()
            else:
                mensagem_usuario = input("Você (modo texto): ")  # Entrada manual por texto

            if mensagem_usuario.lower() in ["sair", "exit"]:
                falar_azure("Encerrando a conversa.")
                print("Encerrando a conversa.")
                break

            # Atualiza o histórico com a nova mensagem do usuário
            historico_assistente = conversa_bot.historico_conversa
            assistente.set_histórico(historico_assistente)

            # Análise da consulta pelo assistente antes da resposta do chatbot
            resultado_assistente = assistente.analisar_consulta(mensagem_usuario)
            print("Resultado da análise do assistente:", resultado_assistente)

            # Se a análise do assistente determinar que é necessário buscar informações adicionais, 
            if resultado_assistente['nova_busca'].lower() == "sim":
                contexto = buscador.responder_consulta(resultado_assistente)
                conversa_bot.adicionar_contexto(contexto)                 

            # Obtém a resposta do chatbot com base no histórico atualizado
            resposta_bot = conversa_bot.continuar_conversa(mensagem_usuario) 
              
            if modo_entrada == 'texto':
                print("Chatbot:", resposta_bot)
            
            # Falar a resposta do chatbot usando Azure (em Português)
            if modo_entrada == 'voz':
                falar_azure(resposta_bot)

        except Exception as e:
            print(f"Ocorreu um erro: {e}")
