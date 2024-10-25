from flask import Flask, render_template, request, jsonify, redirect, url_for
# Removida a importação redundante de main_teste e processar_conversa.
from chatbot import Chatbot
from assistente import Assistente
from buscador import Buscador
from config import API_KEY
from exemplos import exemplos

app = Flask(__name__)

# Inicializa os componentes
conversa_bot = Chatbot(API_KEY)
assistente = Assistente(API_KEY, exemplos)
buscador = Buscador(API_KEY)

# Rota para processar as conversas com o chatbot
@app.route('/api/chatbot', methods=['POST'])
def chatbot_response():
    mensagem_usuario = request.json.get('message')
    resposta = processar_conversa(mensagem_usuario)
    return jsonify({"reply": resposta})

def processar_conversa(mensagem_usuario):
    """
    Processa a mensagem do usuário e retorna a resposta do chatbot.
    Essa função será usada no código Flask para processar as interações.
    """
    try:
        historico_assistente = conversa_bot.historico_conversa
        assistente.set_histórico(historico_assistente)

        resultado_assistente = assistente.analisar_consulta(mensagem_usuario)

        if resultado_assistente['nova_busca'].lower() == "sim":
            contexto = buscador.responder_consulta(resultado_assistente)
            conversa_bot.adicionar_contexto(contexto)

        resposta_bot = conversa_bot.continuar_conversa(mensagem_usuario)
        resposta_bot_limpa = resposta_bot.replace('**', '').replace('###', '').replace('##', '').replace('#', '')
        return resposta_bot_limpa

    except Exception as e:
        return f"Ocorreu um erro: {e}"

# Rota para o index.html
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        user_message = request.form.get('user_message')
        return redirect(url_for('conversa', message=user_message))
    return render_template('index.html')

# Rota para o segundo HTML com a mensagem capturada
@app.route('/conversa')
def conversa():
    user_message = request.args.get('message', '')
    return render_template('index2.html', user_message=user_message)

# Rota para lidar com as mensagens do chat usando uma única rota
@app.route('/send_message', methods=['POST'])
def send_message():
    user_message = request.json.get('message')
    
    # Processa a mensagem do usuário e obtém a resposta do chatbot
    resposta = processar_conversa(user_message)
    
    return jsonify({'response': resposta})

if __name__ == '__main__':
    # Corrigido o host para 127.0.0.1 (ou use 0.0.0.0 para acessar externamente)
    app.run(debug=True, host='127.5.0.1', port=5000)
