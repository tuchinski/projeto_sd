# Bot Telegram

Bot para consulta de informações no portal do aluno da UTFPR, para matéria de Sistemas Distribuídos.

# Descrição da arquitetura
[Arquitetura do sistema](https://github.com/tuchinski/projeto_sd/blob/main/doc/Diagrama_Bot_Telegram_v2.png "Arquitetura do sistema")

1 - O aluno realiza uma requisição no Telegram, que enviada para o servidor.

2 - O servidor recebe a requisição, identifica e direciona para a aplicação que irá extrair os dados do portal do aluno.

3 - A aplicação responsável pela extração dos dados recebe a requisição e realiza a solicitação para o portal do aluno.

4 - O portal do aluno retorna as informações solicitadas, e a aplicação extrai os dados solicitados.

5 - A aplicação responsável pela extração dos dados, envia os mesmos, formatados, para o servidor responsável pelas requisições do telegram.

6 - A aplicação responsável pelas requisições do telegram retorna as informações solicitadas para o aluno.

# Interfaces de Serviço
## Servidor de extração de dados do portal do aluno
- Este servidor ficará responsável por extrair os dados do portal do aluno, e transformá-los no formato JSON, para que sejam retornados para o servidor que recebe as requisicões do Telegram.

- Login
    - Inicialmente, será necessário realizar a autenticação do usuário no portal do aluno. Isso é realizado através do login e senha do aluno. Esta requisição irá gerar um token, que será utilizado para a realização das demais requisições.

- Buscar disciplinas matriculadas
    - Busca as disciplinas matriculadas do aluno, juntamente com os horários da aula. Utiliza o token gerado na requisição de login para autenticação no portal do aluno.

- Boletim
    - Busca os dados do boletim do aluno, com os seguntes dados: matéria, número de faltas, limite máximo de faltas, porcentagem e frequência. Utiliza o token gerado na requisição de login para autenticação no portal do aluno.

## Servidor de requisições do telegram
- Esta aplicação ficará responsável por tratar as requisições recebidas do telegram, e respondê-las da forma correta.

- Receber, tratar e responder as requisições do telegram.
