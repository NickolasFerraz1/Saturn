# Saturn
Bem vindo ao nosso robô que realiza consultas em prospectos de fundos de investimento.
Neste projeto, utilizamos as melhores ferramentas de IA e busca do momento. 
Neste projeto foram utilizadas as seguintes tecnologias:
* Python
* Elastic Search
* ChatGPT
* Kibana
* Flask

Para o funcionamento deste projeto, nós utilizamos os seguintes passos:
* Criamos a nossa base de dados local, através de um web scraping do site: https://fnet.bmfbovespa.com.br/fnet/publico/pesquisarGerenciadorDocumentosCVM?tipoFundo=1
* Transformamos nossos arquivos extraídos do web scraping em TXT
* Transformamos esse TXT em embeddings
* Armazenamos estes embeddings no Elastic Search
* Quando o usuário fizer a solicitação de uma informação, transformamos essa busca em um embedding
* Comparamos o embedding dessa consulta com os embeddings que temos em nosso Elastic Search
* Encontramos a maior semelhança nos embeddings dos documentos com o embedding da consulta e enviamos, através de API, pro ChatGPT
* O ChatGPT checa esses embeddings e retorna uma resposta para o usuário
