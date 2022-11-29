# Bot Telegram

Bot para consulta de informações no portal do aluno da UTFPR, para matéria de Sistemas Distribuídos.

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