import os
from openai import OpenAI
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
import tiktoken

# Configurar a chave da API da OpenAI
client = OpenAI(api_key="sk-proj-2z8UhJtQ1fxwidNX852lT3BlbkFJbPwFk6JFnORpaJsuQgmn")

# Tamanho máximo do segmento
tamanho_maximo_segmento = 8191

# Conectar ao Elasticsearch
es = Elasticsearch([{'host': 'localhost', 'port': 9200, 'scheme': 'http'}])
if not es.indices.exists(index="meu_indice3"):
    es.indices.create(index="meu_indice3", ignore=400)

# Função para gerar embeddings
def gerar_embeddings(texto, id_arquivo):
    # Segmentar o texto em partes menores
    segmentos = segmentar_texto_por_tokens(texto, tamanho_maximo_segmento, id_arquivo)

    # Gerar embeddings para cada segmento
    embeddings = []
    posicao_segmento = 0
    for segmento in segmentos:
        embedding = gerar_embedding_segmento(segmento)
        embeddings.append({
            "_index": "meu_indice3",
            "_source": {
                "id_arquivo": id_arquivo,
                "posicao_segmento": posicao_segmento,
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
                                        model="text-embedding-3-large")  # Escolha o modelo apropriado
    return resposta.data[0].embedding

# Função para segmentar o texto em partes menores
def segmentar_texto_por_tokens(texto, tamanho_maximo_tokens, id_arquivo):
    tamanho_maximo_com_nome = tamanho_maximo_segmento - 50
    tokenizer = tiktoken.encoding_for_model("text-embedding-3-large")  # Escolha o modelo adequado
    tokens = tokenizer.encode(texto)
    #print(tokens)
    
    segmentos = []
    posicao_inicial = 0
    while posicao_inicial < len(tokens):
        segmento_final = min(posicao_inicial + tamanho_maximo_com_nome, len(tokens))
        segmento_tokens = tokens[posicao_inicial:segmento_final]
        segmento_texto = tokenizer.decode(segmento_tokens)
        # Adicionar o nome do arquivo ao início do segmento
        segmento_com_nome = f"{id_arquivo}: {segmento_texto}"
        segmentos.append(segmento_com_nome)
        posicao_inicial = segmento_final

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
