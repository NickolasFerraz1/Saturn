import azure.cognitiveservices.speech as speechsdk
import pyaudio
import numpy as np

# Configurações do Microsoft Azure (chave e região)
AZURE_SPEECH_KEY = "sua-chave-de-api"
AZURE_REGION = "sua-regiao"

# Função para ouvir a fala do usuário e convertê-la em texto usando Azure Speech Service (Português)
def ouvir_fala_azure():
    speech_config = speechsdk.SpeechConfig(subscription=AZURE_SPEECH_KEY, region=AZURE_REGION)
    # Define o idioma do reconhecimento de fala para Português do Brasil (pt-BR)
    speech_config.speech_recognition_language = "pt-BR"  
    speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config)

    print("Estou ouvindo...")
    result = speech_recognizer.recognize_once()

    if result.reason == speechsdk.ResultReason.RecognizedSpeech:
        print(f"Você disse: {result.text}")
        return result.text
    elif result.reason == speechsdk.ResultReason.NoMatch:
        print("Desculpe, não consegui reconhecer o que você disse.")
        return ""
    elif result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = result.cancellation_details
        print(f"Reconhecimento de fala cancelado: {cancellation_details.reason}")
        if cancellation_details.reason == speechsdk.CancellationReason.Error:
            print(f"Erro: {cancellation_details.error_details}")
        return ""

# Função para converter texto em fala usando Azure Speech Service (Português)
def falar_azure(texto):
    speech_config = speechsdk.SpeechConfig(subscription=AZURE_SPEECH_KEY, region=AZURE_REGION)
    # Define a voz em Português do Brasil (exemplo: Francisca Neural)
    speech_config.speech_synthesis_voice_name = "pt-BR-FranciscaNeural"  
    speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config)

    result = speech_synthesizer.speak_text_async(texto).get()

    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        print("A resposta foi falada com sucesso.")
    elif result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = result.cancellation_details
        print(f"Sintetização de fala cancelada: {cancellation_details.reason}")
        if cancellation_details.reason == speechsdk.CancellationReason.Error:
            print(f"Erro: {cancellation_details.error_details}")

# Função para detectar ruídos e então ativar o reconhecimento de fala
def detectar_ruido_e_ouvir():
    # Configurações para captura de áudio
    chunk = 1024  # Tamanho do buffer
    formato = pyaudio.paInt16  # Formato de áudio (16 bits)
    canais = 1  # Mono
    taxa_amostragem = 44100  # Taxa de amostragem (em Hz)
    threshold = 500  # Limite de detecção de som (ajuste para calibrar)
    
    p = pyaudio.PyAudio()
    
    # Inicia o fluxo de áudio
    stream = p.open(format=formato,
                    channels=canais,
                    rate=taxa_amostragem,
                    input=True,
                    frames_per_buffer=chunk)
    
    print("Monitorando o som...")
    
    while True:
        data = np.frombuffer(stream.read(chunk), dtype=np.int16)
        volume = np.abs(data).mean()  # Calcula o volume médio do som
        
        if volume > threshold:  # Se o volume capturado exceder o limite, ativamos o reconhecimento de voz
            print(f"Som detectado! Volume: {volume}")
            mensagem_usuario = ouvir_fala_azure()  # Usa reconhecimento de voz do Azure
            return mensagem_usuario
