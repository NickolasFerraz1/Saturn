import os
from openai import OpenAI
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
import tiktoken
import re

# Configurar a chave da API da OpenAI
client = OpenAI(api_key="sk-proj-2z8UhJtQ1fxwidNX852lT3BlbkFJbPwFk6JFnORpaJsuQgmn")

# Tamanho máximo do segmento
tamanho_maximo_segmento = 1536

# Conectar ao Elasticsearch
es = Elasticsearch([{'host': 'localhost', 'port': 9200, 'scheme': 'http'}])
if not es.indices.exists(index="teste_busca3"):
    es.indices.create(index="teste_busca3", ignore=400)

# Função para gerar embeddings
def gerar_embeddings(texto, id_arquivo):
    # Segmentar o texto em partes menores
    segmentos = segmentar_texto_por_tokens(texto, id_arquivo)

    # Gerar embeddings para cada segmento
    embeddings = []
    posicao_segmento = 0
    for segmento in segmentos:
        embedding = gerar_embedding_segmento(segmento)
        embeddings.append({
            "_index": "teste_busca3",
            "_source": {
                "id_arquivo": id_arquivo,
                "posicao_trecho": posicao_segmento,
                "embedding": embedding,
                "texto": segmento  # Armazenar o segmento de texto original
            }
        })
        posicao_segmento += 1

    return embeddings

# Função para gerar embedding de um segmento de texto
def gerar_embedding_segmento(segmento):

    # Gerar embedding
    resposta = client.embeddings.create(input=segmento,
                                        model="text-embedding-3-small")  # Escolha o modelo apropriado
    return resposta.data[0].embedding

# Função para segmentar o texto em partes menores
def segmentar_texto_por_tokens(texto, id_arquivo):
    tokenizer = tiktoken.encoding_for_model("text-embedding-3-small")  # Escolha o modelo adequado
    
    # Dividimos o texto em sentenças, garantindo que não vamos quebrar frases
    sentencas = re.split(r'(?<=[.!?]) +', texto)
    
    segmentos = []
    segmento_atual = []
    tokens_no_segmento = 0
    tamanho_maximo_com_nome = tamanho_maximo_segmento - 50  # Assumindo que o identificador usa cerca de 50 tokens
    
    for sentenca in sentencas:
        # Gerar os tokens para a sentença atual
        tokens_na_sentenca = len(tokenizer.encode(sentenca))
        
        # Se a sentença sozinha já excede o tamanho máximo do segmento, quebrá-la
        if tokens_na_sentenca > tamanho_maximo_com_nome:
            print(f"Sentença excede o tamanho máximo: {tokens_na_sentenca} tokens. Quebrando a sentença.")
            palavras = sentenca.split()
            sub_segmento = []
            sub_tokens_no_segmento = 0
            for palavra in palavras:
                tokens_na_palavra = len(tokenizer.encode(palavra))
                if sub_tokens_no_segmento + tokens_na_palavra > tamanho_maximo_com_nome:
                    segmentos.append(f"{id_arquivo}: {' '.join(sub_segmento)}")
                    sub_segmento = []
                    sub_tokens_no_segmento = 0
                sub_segmento.append(palavra)
                sub_tokens_no_segmento += tokens_na_palavra
            
            # Adiciona o último sub-segmento, se houver
            if sub_segmento:
                segmentos.append(f"{id_arquivo}: {' '.join(sub_segmento)}")
            continue
        
        # Verificar se adicionar essa sentença ultrapassaria o limite de tokens
        if tokens_no_segmento + tokens_na_sentenca > tamanho_maximo_com_nome:
            if segmento_atual:
                # Decodificar os tokens do segmento atual e adicionar ao resultado final
                segmento_texto = " ".join(segmento_atual)
                segmento_com_nome = f"{id_arquivo}: {segmento_texto}"
                segmentos.append(segmento_com_nome)
                
                # Limpar o segmento atual para o próximo
                segmento_atual = []
                tokens_no_segmento = 0
        
        # Adicionar a sentença atual ao segmento
        segmento_atual.append(sentenca)
        tokens_no_segmento += tokens_na_sentenca

    # Adicionar o último segmento, caso tenha sobrado algum
    if segmento_atual:
        segmento_texto = " ".join(segmento_atual)
        segmento_com_nome = f"{id_arquivo}: {segmento_texto}"  # Adicionando o id_arquivo no último segmento
        segmentos.append(segmento_com_nome)

    return segmentos

# Obter o diretório atual
diretorio_atual = os.getcwd()

# Construir o caminho para a pasta "textos"
caminho_pasta = os.path.join(diretorio_atual, 'textos')

# Verificar se a pasta existe
if not os.path.exists(caminho_pasta):
    raise FileNotFoundError(f"A pasta 'textos' não foi encontrada no diretório atual: {diretorio_atual}")

# Preparar a lista de documentos para indexação
documentos = []

# Iterar sobre os arquivos na pasta "textos"
for nome_arquivo in os.listdir(caminho_pasta):
    caminho_arquivo = os.path.join(caminho_pasta, nome_arquivo)
    if os.path.isfile(caminho_arquivo):
        with open(caminho_arquivo, 'r', encoding='utf-8') as arquivo:
            conteudo = arquivo.read()
            embeddings = gerar_embeddings(conteudo, nome_arquivo)
            documentos.extend(embeddings)

# Indexar embeddings no Elasticsearch
bulk(es, documentos)
