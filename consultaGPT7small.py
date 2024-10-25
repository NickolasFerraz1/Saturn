from openai import OpenAI
from elasticsearch import Elasticsearch
import logging

# Configurar a chave da API da OpenAI
client = OpenAI(api_key="sk-proj-2z8UhJtQ1fxwidNX852lT3BlbkFJbPwFk6JFnORpaJsuQgmn")

# Conectar ao Elasticsearch
es = Elasticsearch([{'host': 'localhost', 'port': 9200, 'scheme': 'http'}])

# Função para gerar embedding da consulta
def gerar_embedding_consulta(consultasimplificada):
    try:
        resposta = client.embeddings.create(input=consulta, model="text-embedding-3-large")
        return resposta.data[0].embedding
    except Exception as e:
        logging.error(f"Erro ao gerar embedding da consulta: {e}")
        return None

def gerar_embedding_consulta_small(consultasimplificada):
    try:
        resposta = client.embeddings.create(input=consulta, model="text-embedding-3-small")
        return resposta.data[0].embedding
    except Exception as e:
        logging.error(f"Erro ao gerar embedding da consulta: {e}")
        return None

# Função para buscar documentos baseados em embeddings no Elasticsearch
def buscar_documentos_no_elasticsearch(embedding_consulta, es, indice="meu_indice3"):
    try:
        query = {
            "size": 5,  # Número de resultados
            "query": {
                "script_score": {
                    "query": {
                        "match_all": {}
                    },
                    "script": {
                        "source": "cosineSimilarity(params.embedding, 'embedding')",
                        "params": {
                            "embedding": embedding_consulta
                        }
                    }
                }
            },
            "_source": ["texto", "id_arquivo"]  # Garantir que os campos de texto e id_arquivo sejam retornados
        }

        response = es.search(index=indice, body=query)
        return response['hits']['hits']
    except Exception as e:
        logging.error(f"Erro ao buscar documentos no Elasticsearch: {e}")
        return []

# Função para extrair os textos e informações dos documentos retornados
def extrair_informacoes(resultados):
    informacoes = []
    for resultado in resultados:
        if "texto" in resultado["_source"] and "id_arquivo" in resultado["_source"]:
            informacoes.append({
                "texto": resultado["_source"]["texto"],
                "id_arquivo": resultado["_source"]["id_arquivo"],
                "pontuacao_similaridade": resultado["_score"]
            })
        else:
            logging.warning(f"Resultado sem campo 'texto' ou 'id_arquivo': {resultado}")
    return informacoes

# Função para dividir o texto em segmentos de aproximadamente 450 tokens, respeitando os pontos finais
def dividir_texto_em_segmentos(texto, max_tokens=450):
    import re
    sentencas = re.split(r'(?<=[.!?]) +', texto)
    segmentos = []
    segmento_atual = []
    tokens_no_segmento = 0

    for sentenca in sentencas:
        tokens_na_sentenca = len(sentenca.split())
        if tokens_no_segmento + tokens_na_sentenca > max_tokens:
            if segmento_atual:
                segmentos.append(" ".join(segmento_atual))
                segmento_atual = []
                tokens_no_segmento = 0
        segmento_atual.append(sentenca)
        tokens_no_segmento += tokens_na_sentenca

    if segmento_atual:
        segmentos.append(" ".join(segmento_atual))

    return segmentos

# Função para gerar embedding para cada segmento
def gerar_embeddings_segmentos(segmentos):
    embeddings = []
    for segmento in segmentos:
        try:
            resposta = client.embeddings.create(input=segmento, model="text-embedding-3-small")
            embeddings.append(resposta.data[0].embedding)
        except Exception as e:
            logging.error(f"Erro ao gerar embedding para segmento: {e}")
    return embeddings

# Função para calcular similaridade entre embeddings
def calcular_similaridade(embedding1, embedding2):
    from numpy import dot
    from numpy.linalg import norm
    return dot(embedding1, embedding2) / (norm(embedding1) * norm(embedding2))

# Função para limitar os textos a 500 tokens cada
def limitar_texto(texto, max_tokens=500):
    tokens = texto.split()
    if len(tokens) > max_tokens:
        tokens = tokens[:max_tokens]
    return " ".join(tokens)

# Função para combinar trechos em um contexto
def combinar_trechos(informacoes):
    contexto_combinado = []
    for info in informacoes:
        trecho_identificado = f"Fundo: {info['id_arquivo']}\nTrecho: {info['trecho']}\n"
        contexto_combinado.append(trecho_identificado)
    return "\n".join(contexto_combinado)

# Função para responder a consulta usando contexto combinado
def responder_consulta(consulta, es, indice="meu_indice3"):
    # Geração do embedding da consulta
    embedding_consulta = gerar_embedding_consulta(consulta)
    if not embedding_consulta:
        return "Erro ao gerar embedding da consulta."
    
    #geração do embedding small
    embedding_consulta_small = gerar_embedding_consulta_small(consulta)
    if not embedding_consulta_small:
        return "Erro ao gerar embedding da consulta."

    # Busca de documentos no Elasticsearch
    resultados = buscar_documentos_no_elasticsearch(embedding_consulta, es, indice)
    if not resultados:
        logging.warning("Nenhum resultado encontrado no Elasticsearch.")
        return "Nenhum resultado encontrado."

    # Extração de informações dos resultados
    informacoes = extrair_informacoes(resultados)
    if not informacoes:
        logging.warning("Nenhuma informação extraída dos resultados.")
        return "Nenhuma informação extraída dos resultados."

    # Análise de similaridade e seleção de trechos relevantes
    trechos_relevantes = []
    for info in informacoes:
        segmentos = dividir_texto_em_segmentos(info["texto"])
        embeddings_segmentos = gerar_embeddings_segmentos(segmentos)
        similaridades = [calcular_similaridade(embedding_consulta_small, embedding) for embedding in embeddings_segmentos]

        for segmento, similaridade in zip(segmentos, similaridades):
            trechos_relevantes.append({
                "id_arquivo": info["id_arquivo"],
                "trecho": limitar_texto(segmento),
                "similaridade": similaridade
            })

    # Ordenar os trechos por similaridade decrescente
    trechos_relevantes = sorted(trechos_relevantes, key=lambda x: x["similaridade"], reverse=True)

    # Selecionar os 5 trechos mais relevantes
    trechos_selecionados = trechos_relevantes[:5]

    # Combinar trechos em um contexto
    contexto = combinar_trechos(trechos_selecionados)

    # Preparação das mensagens para o modelo GPT-4-turbo
    messages = [
        {"role": "system", "content": "Você é um assistente que responde consultas com base em contexto extraído de documentos relevantes."},
        {"role": "user", "content": f"Consulta: {consulta}\n\nContexto relevante:\n{contexto}\n\nResposta:"}
    ]
    print(messages)

    # Chamada ao modelo GPT-4-turbo
    resposta = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        #max_tokens=400
    )

    # Retorno da resposta gerada pelo modelo
    return resposta.choices[0].message.content.strip()

def transformar_consulta(consulta):
    # Mensagem do sistema que define o comportamento do assistente
    system_message = {"role": "system", "content": "Você é um assistente que transforma consultas de linguagem natural em strings otimizadas para buscas no Elasticsearch. Converta a consulta em uma string de busca eficiente."}

    # Exemplos para ajudar o modelo a entender o padrão desejado
    exemplos = [
        {"role": "user", "content": "Consulta: Estou procurando o melhor fundo de investimento em ouro disponível no mercado."},
        {"role": "assistant", "content": "fundos investimento ouro"},
        {"role": "user", "content": "Consulta: Quais fundos imobiliários oferecem os melhores dividendos atualmente?"},
        {"role": "assistant", "content": "fundos imobiliários melhores dividendos"},
        {"role": "user", "content": "Consulta: Preciso de informações sobre os riscos de investir no fundo de ações ABV11."},
        {"role": "assistant", "content": "riscos fundo ABV11"},
        {"role": "user", "content": "Consulta: Gostaria de saber como foi o desempenho do fundo VGHF11 nos últimos anos."},
        {"role": "assistant", "content": "desempenho fundo VGHF11"},
        {"role": "user", "content": "Consulta: Quais são os melhores fundos de investimento em tecnologia disponíveis?"},
        {"role": "assistant", "content": "fundos investimento tecnologia"},
        {"role": "user", "content": "Consulta: Onde estão localizados os imóveis que fazem parte do fundo BRCR11?"},
        {"role": "assistant", "content": "localização imóveis fundo BRCR11"},
        {"role": "user", "content": "Consulta: Estou procurando informações sobre fundos de investimento sustentáveis. Pode me ajudar?"},
        {"role": "assistant", "content": "fundos investimento sustentáveis"},
        {"role": "user", "content": "Consulta: Quais são as principais características do fundo de investimento KNRI11?"},
        {"role": "assistant", "content": "características fundo KNRI11"},
        {"role": "user", "content": "Consulta: Estou interessado nos informes financeiros mais recentes do fundo GGRC11."},
        {"role": "assistant", "content": "informes financeiros fundo GGRC11"},
        {"role": "user", "content": "Consulta: Qual é o fundo de investimento mais seguro em termos de risco?"},
        {"role": "assistant", "content": "fundo investimento menor risco"}
    ]

    # Mensagem com a consulta do usuário
    user_message = {"role": "user", "content": f"Consulta a ser transformada: {consulta}"}

    # Criação da lista de mensagens para o modelo
    messages = [system_message] + exemplos + [user_message]
    print(messages)

    # Chamada ao modelo GPT-4-turbo
    resposta = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        max_tokens=150
    )

    # Extração e retorno da resposta gerada pelo modelo
    return resposta.choices[0].message.content.strip()


# Exemplo de uso
#consulta = "Quais os riscos do Canal 75 Fundo de Investimento em Direitos Creditórios?"
#consulta = "Qual o patrimônio líquido do fundo NOW MORNINGSTAR US DIGITAL LIFESTYLE FUNDO DE ÍNDICE?"
consulta = "Qual a remuneração proposta pelo FIDC bravano?"

consultasimplificada = transformar_consulta(consulta)
print(f"consultasimplificada é: {consultasimplificada}")

resposta = responder_consulta(consulta, es)
print("Resultado da consulta:")
print(resposta)
