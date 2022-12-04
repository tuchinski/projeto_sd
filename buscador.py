import requests
from bs4 import BeautifulSoup
import json


def main():
    print("main")


def login():
    URL_LOGIN = "https://sistemas2.utfpr.edu.br/utfpr-auth/api/v1/"
    
    headers_request = {
        "Content-Type": "application/json",
        "Referer": "https://sistemas2.utfpr.edu.br/login?returnUrl=%2Fdpls%2Fsistema%2Faluno03%2Fmpmenu.inicio"
    }

    request_body = {

    }

    response = requests.post(URL_LOGIN, headers=headers_request, json=request_body)
    response_formt = json.loads(response.text)

    return response_formt["token"]

def busca_boletim(ra: str, token_aluno: str):
    # todo: verificar o tipo de curso
    URL_BOLETIM = f"https://sistemas2.utfpr.edu.br/dpls/sistema/aluno03/mpboletim.inicioAluno?p_pesscodnr={ra}&p_curscodnr=35&p_alcuordemnr=1"

    headers_request = {
        "Cookie": f"testcookie=abc; UTFPRSSO={token_aluno}; style=null"
    }

    response = requests.get(URL_BOLETIM, headers=headers_request)
    soap = BeautifulSoup(response.text, "html.parser")

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

    print(json.dumps(dados_disciplinas, indent=4))

            
        # with open("teste.html", 'w') as file:
        #     file.write(str(dados_linhas))



if __name__ == "__main__":
    token_aluno = login()
    # token_aluno = "eyJraWQiOiJkZW1vaXNlbGxlLXNlY3VyaXR5LWp3dCIsImFsZyI6IlJTNTEyIn0.eyJpc3MiOiJTVE9SRSIsImV4cCI6MTY3MDE3ODk4NSwiYXVkIjoid2ViIiwianRpIjoicnFOWWMtYTNROG1YZndUckVleXhvZyIsImlhdCI6MTY3MDE2NDU4NSwibmJmIjoxNjcwMTY0NTI1LCJpZGVudGl0eSI6IjE3OTIzMyIsIm5hbWUiOiJhMTc5MjMzNCIsInJvbGVzIjpbXSwicGVybWlzc2lvbnMiOnsiYXBwTGlzdCI6WyJzdXBvcnRlLG1vb2RsZSxtYWlsLG51dmVtLHNlaSxwb3J0YWxBbHVubyxtaW5oYUJpYmxpb3RlY2EsbW9vZGxlLG1haWwiXSwiQWRkaXRpb25hbFVzZXJJbmZvIjpbIlczc2lZMjlrYVdkdlZXNXBaR0ZrWlNJNk15d2lZMjlrYVdkdlEzVnljMjhpT2pNMUxDSmpiMlJwWjI5UVpYTnpiMkVpT2pFM09USXpNeXdpYjNKa1pXMGlPakVzSW1Gc2RXNXZRM1Z5YzI5SlpDSTZJamhpS3pFcmRDSXNJbkJsY21sdlpHOGlPamdzSW1OdlpHbG5iMGR5WVdSbElqbzFNQ3dpWVc1dlNXNW5jbVZ6YzI4aU9qSXdNVFlzSW5CbGNtbHZaRzlKYm1keVpYTnpieUk2TVN3aVkyOWthV2R2VTJsMGRXRmpZVzlRYjNOemFYWmxiQ0k2TUgxZCJdfSwicGFyYW1zIjp7InNlcnZlck5hbWUiOiJzaXN0ZW1hczIudXRmcHIuZWR1LmJyOjQ0MyIsInRpcG9Vc3VhcmlvIjoiQUxVTk8iLCJub21lQ29tcGxldG8iOiJMRU9OQVJETyBNRU5ET05DQSBUVUNISU5TS0kiLCJlTWFpbCI6InR1Y2hpbnNraUBhbHVub3MudXRmcHIuZWR1LmJyIn19.cnlQ79FIBQ-SpTUyaASurLaYJztAR-OF2abdXkcgWpav-qgPAk2xJL-OZZI8H9-WKvHEfb2CjZkLVMeKa16K_nxVTs7WtmVqdZBi4TBL-4TTcPwcamKpZc2iOrZLqM3wuVUSnzs2VZaBu_IBifvAP8bX8ek-UIee1ajGBlG00kcWVsiJ7pZjx3U-0WzbqRSdlpWaRemIIfdaoQ2KyyjEr38Wjbe0EJNPQI71mchYleJVCD6hPq4eTH4Pq7NQXdzL6neXiroC_3d-Mmr6U7hV0LZEFOGNGGT3BMokICCVgS90njMz3LzE8vQmILYa37v1doxiwsmD0w3ghlcdpmHlASDyZAoknXJZEknWjVQRzZbWuEcXz5JAMIFCbHKVIMvHi9wwDyuO7NSrOFAA9YgpHwM6rSIuaLNA1WfkCYjXQa6lpzhOsnTFqW1NwaSJWyt_hoJK8ihq7NSTaqtd4uwuDSU_duPrfBttiY3WkKdRhzJjoVNaM0sLIs0wJBKyHBfJaiwNdwZ3A0hFz9eMr9HOPJ5RcHEPoeTY2qtO4IXQVMMHVCqgpvP_ho7DeMuPaLTqDmSYoMH8QSAaMsgaZW2XfDs56JMw7n7ShMHpBRL4UI3tVWEBjL9KLAyRA11xL1yMhjG7AtROV4xT2Gk4_M6tH07Y8s-2JpBGt1GEvxWB8IQ"
    print(token_aluno)
    busca_boletim("1792334", token_aluno)