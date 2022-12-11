import requests
from bs4 import BeautifulSoup
import json

# Exception criada para ser lançada quando ocorre erro de autenticação no login
class LoginErrorException(Exception):
    def __init__(self, codigo, descricao):
        self.codigo = codigo
        self.descricao = descricao
        super().__init__(self.descricao)

# Metodo que realiza o login no Portal do aluno
def login(ra: str, senha: str):
    URL_LOGIN = "https://sistemas2.utfpr.edu.br/utfpr-auth/api/v1/"
    
    headers_request = {
        "Content-Type": "application/json",
        "Referer": "https://sistemas2.utfpr.edu.br/login?returnUrl=%2Fdpls%2Fsistema%2Faluno03%2Fmpmenu.inicio"
    }

    request_body = {
        "username":ra,
        "password":senha
    }
    # realizando o request na URL de login
    response = requests.post(URL_LOGIN, headers=headers_request, json=request_body)

    # transformando o retorno para dict
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

# método para remover os caracteres \n e \t 
def remove_bad_characters(string:str):
    return string.replace("\n", "").replace("\t", "")

# Método que realiza a extração dos dados das disciplinas matriculadas
def busca_disciplinas_matriculadas(ra: str, token_aluno: str):

    # Nota: é necessário tirar o último caractere do RA para realizar a requisição
    URL_DISCIPLINAS = f"https://sistemas2.utfpr.edu.br/dpls/sistema/aluno03/mpconfirmacaomatricula.pcTelaAluno?p_pesscodnr={ra[1:-1]}&p_curscodnr=35&p_alcuordemnr=1"

    headers_request = {
        "Cookie": f"testcookie=abc; UTFPRSSO={token_aluno}; style=null"
    }

    response = requests.get(URL_DISCIPLINAS, headers=headers_request)

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

   # Iterando para cada linha da tabela
    for linha_tabela in linhas_tabela_horario:
        dados_linha = [x for x in linha_tabela.contents if x != "\n"]

        # Armazenando as informações do início da linha
        # Como a iteração é realizada linha a linha, o código da matéria, horário de início e fim das aulas, sempre serão os mesmos
        codigo_horario_atual = dados_linha[0].text.strip()
        horario_inicial = dados_linha[1].text.strip()
        horario_final = dados_linha[2].text.strip()

        # array que armazena os horários de aula daquela linha; desconsiderando o primeiro td(é o código da aula. Ex: M1)
        horarios_aula = linha_tabela.find_all("td") [1:]
        
        i = -1

        for horario_atualizado in horarios_aula:
            i = i+1
            try:
                # tenta splitar o código da matéria e a sala, caso não tenha aula naquele dia, vai gerar o ValueError,
                materia_atual,sala = [remove_bad_characters(x) for x in horario_atualizado.text.split("/")]
                flag_horario_atualizado = False # flag que indica se o horário foi atualizado

                for materia in dados_disciplinas_matriculadas:
                    # nota: o metodo find retorna a posição de onde a substring começa
                    # os seja, é verificado se o código da matéria está na materia_atual
                    if materia_atual.find(materia) >= 0:
                        # Verifica se já foi preenchido algum horário para aquela matéria
                        if dados_disciplinas_matriculadas[materia]['horarios']:

                            # percorrendo o array de horários daquela disciplina
                            for horario_atualizado in dados_disciplinas_matriculadas[materia]['horarios']:

                                # Valida se já existe um horário pra aquele dia da semana
                                if horario_atualizado["dia_semana"] == dias_semana[i]:
                                    # Caso exista um horário pra aquele dia da semana, atualiza o código_horário e 
                                    # o horário do final da aula, e ao final, atualiza o valor da flag de atualização do horário
                                    horario_atualizado["codigo_horario"] = horario_atualizado["codigo_horario"] + "/" + codigo_horario_atual
                                    horario_atualizado["final_aula"] = horario_final
                                    flag_horario_atualizado = True
                                    break
                        
                        # Caso não exista horário daquela matéria pra aquele dia, faz um novo cadastro
                        if not flag_horario_atualizado:
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
