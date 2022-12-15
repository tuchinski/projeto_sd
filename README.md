# Bot Telegram

Bot para consulta de informações no portal do aluno da UTFPR, para matéria de Sistemas Distribuídos.

# Descrição da arquitetura

![Arquitetura do sistema](https://github.com/tuchinski/projeto_sd/blob/main/doc/Diagrama_Bot_Telegram_v2.png "Arquitetura do sistema")

1 - O aluno realiza uma requisição no Telegram, que enviada para o servidor.

2 - O servidor recebe a requisição, identifica e direciona para a aplicação que irá extrair os dados do portal do aluno.

3 - A aplicação responsável pela extração dos dados recebe a requisição e realiza a solicitação para o portal do aluno.

4 - O portal do aluno retorna as informações solicitadas, e a aplicação extrai os dados solicitados.

5 - A aplicação responsável pela extração dos dados, envia os mesmos, formatados, para o servidor responsável pelas requisições do telegram.

6 - A aplicação responsável pelas requisições do telegram retorna as informações solicitadas para o aluno.

# Interfaces de Serviço

## Extrator de dados do portal do aluno

- Este servidor ficará responsável por extrair os dados do portal do aluno, e transformá-los no formato JSON, para que sejam retornados para o servidor que recebe as requisicões do Telegram.
- Login
  - Inicialmente, será necessário realizar a autenticação do usuário no portal do aluno. Isso é realizado através do login e senha do aluno. Esta requisição irá gerar um token, que será utilizado para a realização das demais requisições.
- Buscar disciplinas matriculadas
  - Busca as disciplinas matriculadas do aluno, juntamente com os horários da aula. Utiliza o token gerado na requisição de login para autenticação no portal do aluno.
- Boletim
  - Busca os dados do boletim do aluno, com os seguntes dados: matéria, número de faltas, limite máximo de faltas, porcentagem e frequência. Utiliza o token gerado na requisição de login para autenticação no portal do aluno.

##  Servidor de requisições

- Este servidor responde as requisições do servidor, enviando os dados solicitados do aluno. Importante lembrar, que este servidor utiliza o protocolo HTTPS.

  ### `/boletim`

  - Este endpoint traz todos as informações do boletim do aluno, trazendo os dados das disciplinas do aluno, como Campus, código, faltas, média final, média parcial, nome da disciplina, percentual de presença e a turma.

  - Cabeçalho da requisição: 

    - `user`: neste campo, deve ser informado o RA do aluno
    - `password`: neste campo, deve ser informada a senha do aluno

  - Retorno esperado:

    - Status code: 200

    - ```json
      [
          {
              "campus": "Campo Mourão",
              "codigo": "BCC34G",
              "faltas": "4",
              "limite_faltas": "17",
              "media_final": " * ",
              "media_parcial": "0,0",
              "nome": "Sistemas Operacionais",
              "percentual_presenca": "90,0",
              "turma": "IC4A"
          },
          {
              "campus": "Campo Mourão",
              "codigo": "BCC35G",
              "faltas": 0,
              "limite_faltas": "17",
              "media_final": " * ",
              "media_parcial": "0,0",
              "nome": "Inteligencia Artificial",
              "percentual_presenca": "67,9",
              "turma": "IC5A"
          },
          {
              "campus": "Campo Mourão",
              "codigo": "BCC36C",
              "faltas": "2",
              "limite_faltas": "17",
              "media_final": " * ",
              "media_parcial": "0,0",
              "nome": "Sistemas Distribuidos",
              "percentual_presenca": "83,9",
              "turma": "IC6A"
          }
      ]
      ```

      - Erros
        - Caso o RA e/ou senha estiverem incorretos, será retornado um status code 401

  ### `/disciplinas`

  - Este endpoint busca os horários de todas as disciplinas matriculadas do aluno, trazendo o campus, código, enquadramento, lista de horários, nome da disciplina, e turma.

  - Cabeçalho da requisição: 

    - `user`: neste campo, deve ser informado o RA do aluno
    - `password`: neste campo, deve ser informada a senha do aluno

  - Retorno esperado:

    - Status code: 200

    - ```json
      {
          "BCC34G": {
              "campus": "Campo Mourão",
              "codigo": "BCC34G",
              "enquadramento": "Turma 100% Presencial, conforme Resolução 123/2021 - COGEP.",
              "horarios": [
                  {
                      "codigo_horario": "T4/T5",
                      "dia_semana": "quarta",
                      "final_aula": "17h30",
                      "inicio_aula": "15h50",
                      "sala_aula": "F101"
                  },
                  {
                      "codigo_horario": "T4/T5",
                      "dia_semana": "quinta",
                      "final_aula": "17h30",
                      "inicio_aula": "15h50",
                      "sala_aula": "E007"
                  }
              ],
              "nome": "Sistemas Operacionais",
              "turma": "IC4A"
          },
          "BCC36C": {
              "campus": "Campo Mourão",
              "codigo": "BCC36C",
              "enquadramento": "Turma 100% Presencial, conforme Resolução 123/2021 - COGEP.",
              "horarios": [
                  {
                      "codigo_horario": "N2/N3",
                      "dia_semana": "quinta",
                      "final_aula": "21h10",
                      "inicio_aula": "19h30",
                      "sala_aula": "E102"
                  },
                  {
                      "codigo_horario": "N4/N5",
                      "dia_semana": "terca",
                      "final_aula": "23h00",
                      "inicio_aula": "21h20",
                      "sala_aula": "E103"
                  }
              ],
              "nome": "Sistemas Distribuidos",
              "turma": "IC6A"
          }
      }
      ```

      - Erros
        - Caso o RA e/ou senha estiverem incorretos, será retornado um status code 401

  

  ### `/validaCredenciais`

  - Este endpoint valida as credenciais do aluno no portal do aluno.

  - Cabeçalho da requisição: 

    - `user`: neste campo, deve ser informado o RA do aluno
    - `password`: neste campo, deve ser informada a senha do aluno

  - Retorno esperado:

    - Status code: 200

    - ```json
      {
          "codigo": 200,
          "mensagem": "Sucesso ao validar as credenciais"
      }
      ```

    - Erros

      - Caso o RA e/ou senha estiverem incorretos, será retornado um status code 401

        

  ### `disciplinas/<dia_semana>`

  - Este endpoint busca as aulas de um determinado dia da semana

  - Parâmetros da requisição

    - `dia_semana`: dia da semana em que se deseja saber as aulas, sendo um valor inteiro, onde 0 -> segunda, 1-> terça, etc...

  - Cabeçalho da requisição: 

    - `user`: neste campo, deve ser informado o RA do aluno
    - `password`: neste campo, deve ser informada a senha do aluno

  - Retorno esperado:

    - Status code: 200

    - ```json
      [
          {
              "final_aula": "23h00",
              "inicio_aula": "21h20",
              "nome": "Sistemas Distribuidos",
              "sala": "E103"
          },
          {
              "final_aula": "08h20",
              "inicio_aula": "07h30",
              "nome": "Projeto E Desenvolvimento Em Ciência Da Computação",
              "sala": "REMOTA"
          }
      ]
      ```

  - Erros

    - Caso o RA e/ou senha estiverem incorretos, será retornado um status code 401
    - Caso o valor do dia da semana ultrapasse 6, será retornado um erro 400.

## Servidor de requisições do telegram

- Esta aplicação ficará responsável por tratar as requisições recebidas do telegram, e respondê-las da forma correta.

- Receber, tratar e responder as requisições do telegram.