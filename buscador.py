import requests
from bs4 import BeautifulSoup
import json

class LoginErrorException(Exception):
    def __init__(self, codigo, descricao):
        self.codigo = codigo
        self.descricao = descricao
        super().__init__(self.descricao)

# Metodo que realiza o login no Portal do aluno
def login(ra, senha):
    URL_LOGIN = "https://sistemas2.utfpr.edu.br/utfpr-auth/api/v1/"
    
    headers_request = {
        "Content-Type": "application/json",
        "Referer": "https://sistemas2.utfpr.edu.br/login?returnUrl=%2Fdpls%2Fsistema%2Faluno03%2Fmpmenu.inicio"
    }

    request_body = {
        "username":ra,
        "password":senha
    }

    response = requests.post(URL_LOGIN, headers=headers_request, json=request_body)
    response_formt = json.loads(response.text)
    if response.status_code == 401:
        raise LoginErrorException(response.status_code, response.text)

    return response_formt["token"]

# Método que realiza a extração de dados do boletim
def busca_boletim(ra: str, token_aluno: str):
    
    URL_BOLETIM = f"https://sistemas2.utfpr.edu.br/dpls/sistema/aluno03/mpboletim.inicioAluno?p_pesscodnr={ra[1:]}&p_curscodnr=35&p_alcuordemnr=1"

    headers_request = {
        "Cookie": f"testcookie=abc; UTFPRSSO={token_aluno}; style=null"
    }

    response = requests.get(URL_BOLETIM, headers=headers_request)
    soap = BeautifulSoup(response.text, "html.parser")

    # Realizando extração dos dados do boletim
    dados_disciplinas = []

    tbody_disciplinas = soap.find_all(class_="destaque")
    for disciplina in tbody_disciplinas:
        dado_disciplina = {}
        dados_linhas = disciplina.find_all("td")
        
        # dado[0] = Campus da disciplina
        dado_disciplina["campus"] = dados_linhas[0].text

        # dado[1] = Código da disciplina
        dado_disciplina["codigo"] = dados_linhas[1].text
        
        # dado[2] = Nome da disciplina
        dado_disciplina["nome"] = dados_linhas[2].text
        
        # dado[3] = Nome da disciplina
        dado_disciplina["turma"] = dados_linhas[3].text
        
        # dado[7] = Limite de faltas previstas
        dado_disciplina["limite_faltas"] = dados_linhas[7].text
        
        # dado[9] = Faltas
        dado_disciplina["faltas"] = dados_linhas[9].text


        # dado[11] = Percentual de presença
        dado_disciplina["percentual_presenca"] = dados_linhas[11].text.strip()

        # dado[12] = Média parcial
        dado_disciplina["media_parcial"] = dados_linhas[12].text.split("\n")[0].strip()

        # dado[13] = Média final
        dado_disciplina["media_final"] = dados_linhas[13].text

        dados_disciplinas.append(dado_disciplina)

    return dados_disciplinas

def remove_bad_characters(string:str):
    return string.replace("\n", "").replace("\t", "")

def busca_disciplinas_matriculadas(ra: str, token_aluno: str):

    # Nota: é necessário tirar o último caractere do RA para realizar a requisição
    URL_DISCIPLINAS = f"https://sistemas2.utfpr.edu.br/dpls/sistema/aluno03/mpconfirmacaomatricula.pcTelaAluno?p_pesscodnr={ra[1:-1]}&p_curscodnr=35&p_alcuordemnr=1"

    headers_request = {
        "Cookie": f"testcookie=abc; UTFPRSSO={token_aluno}; style=null"
    }

    response = requests.get(URL_DISCIPLINAS, headers=headers_request)

    with open("disciplinas.html", "r") as file:
    
        # soap = BeautifulSoup(file.read(), "html.parser")
        soap = BeautifulSoup(response.text, "html.parser")

        # NOTA: As linhas da tabela que contém as matérias começam na posição 1, e vão até a n-3
        # Ex: se o aluno tiver 3 matérias, as linhas que contém os dados das matérias serão as linhas 1,2,3
        # A primeira linha(i=0) contém o cabeçalho da tabela, e as 3 últimas armazenam o total de disciplinas,
        # carga horária total do aluno, e a carga horária máxima, respectivamente.
        linhas_tabela_disciplinas = soap.find_all(class_= "tbl")[1].find_all(class_ = "imprime")[1:-3]
        
        dados_disciplinas_matriculadas = {}

        # Esta primeira parte, extraimos os dados das disciplinas somente
        for linha in linhas_tabela_disciplinas:
            # Limpando os dados recebidos da tabela
            # Esse comando pega todos os filhos da linha e remove somente as posições que tem a string "\n"
            dados_linha = [item for item in linha.contents if item != "\n"]

            dados_disciplina = {}
            dados_disciplina["campus"] = dados_linha[0].text
            dados_disciplina["codigo"] = dados_linha[1].text
            dados_disciplina["nome"] = dados_linha[2].text
            dados_disciplina["turma"] = dados_linha[3].text
            dados_disciplina["enquadramento"] = dados_linha[4].text
            dados_disciplina["horarios"] = []
            dados_disciplinas_matriculadas[dados_disciplina["codigo"]] =  dados_disciplina
        
        # Realizando a busca na tabela de horários

        # Considera todas as linhas da tabela de horário, exceto a primeira, porque ela
        # possui apenas os dados do cabeçalho
        linhas_tabela_horario = soap.find(id = "fshorarios_int").table.find_all("tr")[1:]

        dias_semana = ["segunda", "terca", "quarta", "quinta", "sexta", "sabado"]

        for linha_tabela in linhas_tabela_horario:
            dados_linha = [x for x in linha_tabela.contents if x != "\n"]

            codigo_horario_atual = dados_linha[0].text.strip()
            horario_inicial = dados_linha[1].text.strip()
            horario_final = dados_linha[2].text.strip()

            horarios_aula = linha_tabela.find_all("td") [1:]# array que armazena os horários de aula daquela linha; desconsiderando o primeiro td(é o código da aula. Ex: M1)
            
            i = -1

            for horario in horarios_aula:
                i = i+1
                try:
                    turma,sala = [remove_bad_characters(x) for x in horario.text.split("/")]

                    for materia in dados_disciplinas_matriculadas:
                        # nota: o metodo find retorna a posição de onde a substring começa
                        if turma.find(f"{materia}") >= 0:
                            dados_disciplinas_matriculadas[materia]["horarios"].append({
                                "codigo_horario": codigo_horario_atual,
                                "inicio_aula": horario_inicial,
                                "final_aula": horario_final,
                                "dia_semana": dias_semana[i],
                                "sala_aula": sala
                            })
                except ValueError:
                    # Caso ocorra o ValueError, o campo do horário está vazio, ou seja, o aluno
                    # não tem aula naquele dia e horário
                    continue
        return dados_disciplinas_matriculadas



if __name__ == "__main__":
    # buscando dados para teste
    with open("dados.json", "r") as file:
        dados = json.loads(file.read())

    try:
        token_aluno = login(dados["ra"], dados["senha"])
        print( token_aluno)
        # token_aluno = "eyJraWQiOiJkZW1vaXNlbGxlLXNlY3VyaXR5LWp3dCIsImFsZyI6IlJTNTEyIn0.eyJpc3MiOiJTVE9SRSIsImV4cCI6MTY3MDM3MTc1MywiYXVkIjoid2ViIiwianRpIjoicklyM0ZvR2VOU0RMV1JWUzY1LTNvQSIsImlhdCI6MTY3MDM1NzM1MywibmJmIjoxNjcwMzU3MjkzLCJpZGVudGl0eSI6IjE3OTI5MCIsIm5hbWUiOiJhMTc5MjkwMyIsInJvbGVzIjpbXSwicGVybWlzc2lvbnMiOnsiYXBwTGlzdCI6WyJzdXBvcnRlLG1vb2RsZSxtYWlsLG51dmVtLHNlaSxwb3J0YWxBbHVubyxtaW5oYUJpYmxpb3RlY2EsbW9vZGxlLG1haWwiXSwiQWRkaXRpb25hbFVzZXJJbmZvIjpbIlczc2lZMjlrYVdkdlZXNXBaR0ZrWlNJNk1UTXNJbU52WkdsbmIwTjFjbk52SWpvNExDSmpiMlJwWjI5UVpYTnpiMkVpT2pFM09USTVNQ3dpYjNKa1pXMGlPakVzSW1Gc2RXNXZRM1Z5YzI5SlpDSTZJbVJ6YzNOd1ppSXNJbkJsY21sdlpHOGlPakVzSW1OdlpHbG5iMGR5WVdSbElqb3hNQ3dpWVc1dlNXNW5jbVZ6YzI4aU9qSXdNaklzSW5CbGNtbHZaRzlKYm1keVpYTnpieUk2TWl3aVkyOWthV2R2VTJsMGRXRmpZVzlRYjNOemFYWmxiQ0k2TUgwc2V5SmpiMlJwWjI5VmJtbGtZV1JsSWpvekxDSmpiMlJwWjI5RGRYSnpieUk2TXpVc0ltTnZaR2xuYjFCbGMzTnZZU0k2TVRjNU1qa3dMQ0p2Y21SbGJTSTZNU3dpWVd4MWJtOURkWEp6YjBsa0lqb2llRGQwSzNSM0lpd2ljR1Z5YVc5a2J5STZOaXdpWTI5a2FXZHZSM0poWkdVaU9qVXdMQ0poYm05SmJtZHlaWE56YnlJNk1qQXhOaXdpY0dWeWFXOWtiMGx1WjNKbGMzTnZJam94TENKamIyUnBaMjlUYVhSMVlXTmhiMUJ2YzNOcGRtVnNJam93ZlYwPSJdfSwicGFyYW1zIjp7InNlcnZlck5hbWUiOiJzaXN0ZW1hczIudXRmcHIuZWR1LmJyOjQ0MyIsInRpcG9Vc3VhcmlvIjoiQUxVTk8iLCJub21lQ29tcGxldG8iOiJJTFpJTUFSQSBTSUxWQSBFIFNJTFZBIiwiZU1haWwiOiJpbHppbWFyYXNpbHZhQGFsdW5vcy51dGZwci5lZHUuYnIifX0.cxn_0dsELXbD5yP9FKNaFzkvyGw8MQQ6qw5LGoOORCd8XXf0NZPDPaVQ8kIdq8hDVyDCDJsaWhhGLoXu2xomwCqG-iueyNOd4amt5xNZhRktp4zacvYAyWrSYclWmm459ifOtc5ebZI7Ne9lm2gR9jGWinYRBXoIHFEKLnWGCLATFT6kKerBD2RC5xcR5fuwBBL9PJBArZ5vtDcFrLL7c6dDYLfPe6IsbL95m1l1i5XpRs9so29r0lGDLIPTi4BM9VpaQ-1QXRtOyWqI3aBwRDytFkbV0yJaZ4N9nvVnOrKxkt3cJ9jqD8GBMufFTMYYRVYoWjCCerLaDFYx-HnZp37-nwzbwCVly_DcamrzCC8_hTrbOdq3Xd9bwHRL9zgXTlV19VonKjxC9fKZOB477NhFrKEEqIQBB7GsB8l_rimaDxtjIzqtgY-1hfG5tDR6AiJlqL_JYpIpV-rMJQj7fdAypTgRQypZbkbR9EmyOZ4OqhhR2IJBesy3cX_4Yh0vwXx7WBj4vQdv_w72QaPzrtpKr__gwxb7-mbGcZxZj3uBN9WDEthRkgGAYtK4CJKY4qGkzzgfjWZA-qCw90VnJtYAg6nxvxVdGJbOpy9d5fA4TDtdWflq72_PNX01yrVK6iixMucFllpPku1akib-MsU-vZ3LV_yCmnuo3mAE1KY"
        print(json.dumps(busca_disciplinas_matriculadas(dados["ra"],token_aluno), indent=4))
        print(json.dumps(busca_boletim(dados["ra"],token_aluno), indent=4))
    except LoginErrorException as e:
        print(e)
        exit()
    # print(token_aluno)
    # busca_boletim(dados["ra"], token_aluno)