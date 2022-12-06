import requests
from bs4 import BeautifulSoup
import json

class LoginErrorException(Exception):
    def __init__(self, codigo, descricao):
        self.codigo = codigo
        self.descricao = descricao
        super().__init__(self.descricao)

def main():
    print("main")


def login():
    URL_LOGIN = "https://sistemas2.utfpr.edu.br/utfpr-auth/api/v1/"
    
    headers_request = {
        "Content-Type": "application/json",
        "Referer": "https://sistemas2.utfpr.edu.br/login?returnUrl=%2Fdpls%2Fsistema%2Faluno03%2Fmpmenu.inicio"
    }

    request_body = {
        # "username":"a1792334",
        # "password":"inppyu71"
        "username":"a1792903",
        "password":"joaoma2219938905!"
    }

    response = requests.post(URL_LOGIN, headers=headers_request, json=request_body)
    response_formt = json.loads(response.text)
    if response.status_code == 401:
        raise LoginErrorException(response.status_code, response.text)

    return response_formt["token"]

def busca_boletim(ra: str, token_aluno: str):
    
    URL_BOLETIM = f"https://sistemas2.utfpr.edu.br/dpls/sistema/aluno03/mpboletim.inicioAluno?p_pesscodnr={ra}&p_curscodnr=35&p_alcuordemnr=1"

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

    # print(json.dumps(dados_disciplinas, indent=4))
    return dados_disciplinas

def remove_bad_characters(string:str):
    return string.replace("\n", "").replace("\t", "")

def busca_disciplinas_matriculadas(ra: str, token_aluno: str):

    # Nota: é necessário tirar o último caractere do RA para realizar a requisição
    URL_DISCIPLINAS = f"https://sistemas2.utfpr.edu.br/dpls/sistema/aluno03/mpconfirmacaomatricula.pcTelaAluno?p_pesscodnr={ra[0:-1]}&p_curscodnr=35&p_alcuordemnr=1"

    headers_request = {
        "Cookie": f"testcookie=abc; UTFPRSSO={token_aluno}; style=null"
    }

    # response = requests.get(URL_DISCIPLINAS, headers=headers_request)

    with open("disciplinas.html", "r") as file:
    
        soap = BeautifulSoup(file.read(), "html.parser")
        # soap = BeautifulSoup(response.text, "html.parser")

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
                        if turma == f"{materia}-{dados_disciplinas_matriculadas[materia]['turma']}":
                            dados_disciplinas_matriculadas[materia]["horarios"].append({
                                "codigo_horario": codigo_horario_atual,
                                "inicio_aula": horario_inicial,
                                "final_aula": horario_final,
                                "dia_semana": dias_semana[i]
                            })
                except ValueError:
                    # Caso ocorra o ValueError, o campo do horário está vazio, ou seja, o aluno
                    # não tem aula naquele dia e horário
                    continue
        print(json.dumps(dados_disciplinas_matriculadas, indent=4))       
        return dados_disciplinas_matriculadas
        
        # with open("horario.html", "w") as file2:
        #     file2.write(str(soap.find(id = "fshorarios_int").table.find_all("tr")))
        # print(soap.find(id = "fshorarios_int"))





if __name__ == "__main__":
    # try:
    #     token_aluno = login()
    # except LoginErrorException as e:
    #     print(e)
    token_aluno = "eyJraWQiOiJkZW1vaXNlbGxlLXNlY3VyaXR5LWp3dCIsImFsZyI6IlJTNTEyIn0.eyJpc3MiOiJTVE9SRSIsImV4cCI6MTY3MDI5Njc1MCwiYXVkIjoid2ViIiwianRpIjoiTTZ1RFBoWmNISnRDRzUxX2RWM0tkUSIsImlhdCI6MTY3MDI4MjM1MCwibmJmIjoxNjcwMjgyMjkwLCJpZGVudGl0eSI6IjE3OTIzMyIsIm5hbWUiOiJhMTc5MjMzNCIsInJvbGVzIjpbXSwicGVybWlzc2lvbnMiOnsiYXBwTGlzdCI6WyJzdXBvcnRlLG1vb2RsZSxtYWlsLG51dmVtLHNlaSxwb3J0YWxBbHVubyxtaW5oYUJpYmxpb3RlY2EsbW9vZGxlLG1haWwiXSwiQWRkaXRpb25hbFVzZXJJbmZvIjpbIlczc2lZMjlrYVdkdlZXNXBaR0ZrWlNJNk15d2lZMjlrYVdkdlEzVnljMjhpT2pNMUxDSmpiMlJwWjI5UVpYTnpiMkVpT2pFM09USXpNeXdpYjNKa1pXMGlPakVzSW1Gc2RXNXZRM1Z5YzI5SlpDSTZJamhpS3pFcmRDSXNJbkJsY21sdlpHOGlPamdzSW1OdlpHbG5iMGR5WVdSbElqbzFNQ3dpWVc1dlNXNW5jbVZ6YzI4aU9qSXdNVFlzSW5CbGNtbHZaRzlKYm1keVpYTnpieUk2TVN3aVkyOWthV2R2VTJsMGRXRmpZVzlRYjNOemFYWmxiQ0k2TUgxZCJdfSwicGFyYW1zIjp7InNlcnZlck5hbWUiOiJzaXN0ZW1hczIudXRmcHIuZWR1LmJyOjQ0MyIsInRpcG9Vc3VhcmlvIjoiQUxVTk8iLCJub21lQ29tcGxldG8iOiJMRU9OQVJETyBNRU5ET05DQSBUVUNISU5TS0kiLCJlTWFpbCI6InR1Y2hpbnNraUBhbHVub3MudXRmcHIuZWR1LmJyIn19.sDqzgGCJNNknq4laKy0iXTltIElDx0PqAo91WwMFzG0FXtsyHVxSi_zEEeOn3XkXGO3LiECPtPstQ9Jen1Dnma76WPAZMl5iTF4vtaFRhwGMWqWmWILbOoOixQuE6spTp0jFMDNzYXMSodmFM9oLfFeEBjOsUwqc6CsFtZHaCXgBi2h0BY61TIkl-FN4Z9VNBQoSTE9buAeu89g36mqTDkjvH2exzMJ964crZBrsFNdYRb9E0ZpakOzmdywQTgIk41nvKDOSbJXIfQixla-3WJ6G4mcIv7OjPMPESwujT_8180UF6ZvcdU-NsHF0h6q9elW4EtHc3OHWMAeZ52Obc92I33OWk6tkrVRb6kPe0ZGuJtQ_w58ocNlOX37NtL70ssbWUu2sMXLuEIyfawUtkvgIWG-fQapruUfZiSCuu0_D6DoUDylsPpzZcqlpYPilr96X93KZhQm4uWMfjoB8P6c2EtoOLQ5efq-4x3X1BPt7j9TI_Q6MWYiD7gcRjX8602hZ5OuXa36S6-hl7XKOAP9wwY-GFHDqiPBvbR-vYX-ZiLpQ0BlyS9IoGLWoIPj3yh2OMnaQ_wBplbP_zdW2uBXepg5aM25rOYAutftCq3mCuI21OHtjHOI2HRXebCNbsXn86KPlg6frkaF2yjJn-EQLjxA8qxZKUf2UbYxl76E"
    # print(token_aluno)
    # busca_boletim("1792334", token_aluno)
    busca_disciplinas_matriculadas("1792334",token_aluno)