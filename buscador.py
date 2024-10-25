import logging
from openai import OpenAI
from elasticsearch import Elasticsearch
from config import API_KEY

class Buscador:
    def __init__(self, API_KEY: str, es_host: str = 'localhost', es_port: int = 9200, es_scheme: str = 'http', indice: str = 'meu_indice3'):
        self.client = OpenAI(api_key=API_KEY)
        self.es = Elasticsearch([{'host': es_host, 'port': es_port, 'scheme': es_scheme}])
        self.indice = indice
        
    def gerar_embedding_consulta(self, consulta):
        try:
            resposta = self.client.embeddings.create(input=consulta, model="text-embedding-3-large")
            return resposta.data[0].embedding
        except Exception as e:
            logging.error(f"Erro ao gerar embedding da consulta: {e}")
            return None
        
    def buscar_documentos_no_elasticsearch(self, embedding_consulta, ids_filtrados=None):
        try:
            query = {
                "size": 25,  # Número de resultados
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

            # Se houver ids_filtrados (de uma busca de fundo específico), adicionamos uma filtragem
            if ids_filtrados:
               query["query"]["script_score"]["query"] = { "terms": { "id_arquivo.keyword": ids_filtrados }}
    
            response = self.es.search(index=self.indice, body=query)
            return response['hits']['hits']
        except Exception as e:
            logging.error(f"Erro ao buscar documentos no Elasticsearch: {e}")
            return []
    
    def buscar_fundos_similares(self, nome_fundo):
        try:
            query_mlt = {
                "size": 5,
                "query": {
                    "more_like_this": {
                        "fields": ["id_arquivo"],
                        "like": nome_fundo,
                        "min_term_freq": 1,
                        "max_query_terms": 12
                    }
                },
                "_source": ["id_arquivo"]  # Precisamos apenas dos id_arquivos para usar na próxima busca
            }

            response = self.es.search(index=self.indice, body=query_mlt)
            # Extraímos apenas ids distintos
            ids_filtrados = list(set([hit["_source"]["id_arquivo"] for hit in response['hits']['hits']]))
            print(ids_filtrados)
            return ids_filtrados
        except Exception as e:
            logging.error(f"Erro ao buscar fundos similares no Elasticsearch: {e}")
            return []

    def combinar_trechos(self, informacoes):
        contexto_combinado = []
        for info in informacoes:
            trecho_identificado = f"Fundo: {info['_source']['id_arquivo']}\nTrecho: {info['_source']['texto']}\n"
            contexto_combinado.append(trecho_identificado)
        return "\n".join(contexto_combinado)

    def responder_consulta(self, dicionario):
        fundo_especifico = dicionario['fundo_especifico'].lower()
        nome_fundo = dicionario['nome_fundo']
        consulta = dicionario['consulta']

        # Geração do embedding da consulta (small)
        embedding_consulta = self.gerar_embedding_consulta(consulta)
        if not embedding_consulta:
            return "Erro ao gerar embedding da consulta."

        if fundo_especifico == 'sim':
            # Buscar os arquivos mais similares ao nome do fundo usando "More Like This"
            ids_filtrados = self.buscar_fundos_similares(nome_fundo)
            if not ids_filtrados:
                logging.warning(f"Nenhum fundo similar encontrado para {nome_fundo}.")
                return f"Nenhum fundo similar encontrado para {nome_fundo}."
            
            # Fazer a busca de documentos com restrição aos id_arquivos filtrados
            resultados = self.buscar_documentos_no_elasticsearch(embedding_consulta, ids_filtrados)
        else:
            # Fazer a busca de documentos sem restrição de fundo específico
            resultados = self.buscar_documentos_no_elasticsearch(embedding_consulta)

        if not resultados:
            logging.warning("Nenhum resultado encontrado no Elasticsearch.")
            return "Nenhum resultado encontrado."

        # Combinar trechos em um contexto
        contexto = self.combinar_trechos(resultados)

        return contexto
