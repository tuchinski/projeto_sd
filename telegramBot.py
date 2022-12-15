from dotenv import load_dotenv
import os
import logging
import requests
from datetime import date 
from cryptography.fernet import Fernet

from typing import Dict
from telegram import __version__ as TG_VER

# carregando dados do .env
load_dotenv()

TOKEN = os.getenv("API_KEY")
BASE_URL = os.getenv("base_url")

try:
    from telegram import __version_info__
except ImportError:
    __version_info__ = (0, 0, 0, 0, 0)  # type: ignore[assignment]

if __version_info__ < (20, 0, 0, "alpha", 1):
    raise RuntimeError(
        f"This example is not compatible with your current PTB version {TG_VER}. To view the "
        f"{TG_VER} version of this example, "
        f"visit https://docs.python-telegram-bot.org/en/v{TG_VER}/examples.html"
    )
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# estados do Bot
OPTIONS, RA, PASSWD, CHECK = range(4)

# Teclado com as opções do bot
reply_keyboard = [
    ["Boletim", "Disciplinas Matriculadas"],
    ["Disciplinas do dia"],
    ["Encerrar sessão"],
]
markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)


def decript_senha(senha_encript:bytes)->str:
    """Descriptografa a senha"""
    fernet = Fernet(os.getenv("key_bot"))
    return fernet.decrypt(senha_encript).decode()

def encript_senha(senha:str) -> bytes:
    """Encripta a senha"""
    fernet = Fernet(os.getenv("key_bot"))
    return fernet.encrypt(senha.encode())

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Inicia a conversa com o aluno"""
    await update.message.reply_text(
        "Olá!! Sou o bot da UTFPR Campus Campo Mourão. "
        "Primeiramente, digite seu RA com a letra 'a'. Ex: a12345.",
        reply_markup=ReplyKeyboardRemove()
    )
    return RA

async def recebendo_ra(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Método que trata quando o aluno envia os RA"""
    
    # Recebe o RA e guarda no user_data
    text = update.message.text
    context.user_data["ra"] = text
    
    await update.message.reply_text(f"Ok!. Agora digite sua senha")

    return PASSWD

def credenciais(context: ContextTypes.DEFAULT_TYPE):
    """Retorna as credenciais do usuário, salvas no user_data"""
    # return context.user_data["ra"], context.user_data["senha"]
    return context.user_data["ra"], decript_senha(context.user_data["senha"])



async def recebendo_senha(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Recebendo a senha do usuário, e armazenando no user_data"""
    # Guardando a senha do usuário no user_data
    text = update.message.text
    context.user_data["senha"] = encript_senha(text)
    
    # Buscando RA e senha para fazer a validação das credenciais
    ra = context.user_data["ra"]
    senha = text
    await update.message.reply_text(f"aguarde um pouco enquanto verifico seus dados no servidor")
    url = f"{BASE_URL}/validaCredenciais"
    requestHeaders = {
        "user": ra,
        "password": senha
    }
    # Realizando a request para validar as credenciais
    try:
        response = requests.get(url, headers=requestHeaders, verify=False, timeout=10)
    except Exception as e:
        print("Erro ao realizar a request")
        print(e)
        await update.message.reply_text("Ops.. Não deu pra fazer sua requisição, tente novamente.")
        await update.message.reply_text("Primeiramente, digite seu RA.")
        return RA


    if response.status_code == 200:
        # Caso sucesso, informa o aluno e vai para o estado OPTIONS
        await update.message.reply_text("Login efetuado com sucesso")
        await update.message.reply_text("Selecione qual opção você deseja", reply_markup=markup)
        return OPTIONS
    else:
        # Caso erro, informa o aluno e volta para o estado RA, para digitar novamente o RA e senha
        responseBody = response.json()
        await update.message.reply_text(responseBody["mensagem"])
        await update.message.reply_text("Tente fazer o login novamente")
        await update.message.reply_text("Primeiramente, digite seu RA.")
        return RA

async def buscando_disciplina_dia(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Método que responde a solicitação de busca das disciplinas do dia"""
    
    # Descobrindo qual dia da semana é hoje
    dia_semana = date.today().weekday()
    ra,senha = credenciais(context)

    # realizando a request para buscar as disciplinas do dia
    url = f"{BASE_URL}/disciplinas/{dia_semana}"
    requestHeaders = {
        "user": ra,
        "password": senha
    }
    try:
        response = requests.get(url, headers= requestHeaders, verify=False, timeout=10)
    except Exception as e:
        print("Erro ao realizar a request")
        print(e)
        await update.message.reply_text("Ops.. Não deu pra fazer sua requisição, tente novamente.")
        return OPTIONS

    # Caso o aluno não tenha aula, o retorno será um array vazio
    responseBody = response.json()
    if not responseBody:
        await update.message.reply_text("Hoje você não tem aula")
    else:
        # Formatando os dados para retornar para o aluno
        responseAluno = "Aqui está sua aula do dia\n"

        for disciplina in responseBody:
            responseAluno = responseAluno + "\n=========================\n"
            responseAluno = responseAluno + "Disciplina: {}\n".format(disciplina["nome"])
            responseAluno = responseAluno + "Sala: {}\n".format(disciplina["sala"])
            responseAluno = responseAluno + "Início da aula: {}\n".format(disciplina["inicio_aula"])
            responseAluno = responseAluno + "Final da aula: {}\n".format(disciplina["final_aula"])

        await update.message.reply_text(responseAluno)  

    return OPTIONS

async def buscando_dados_boletim(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Método que responde a solicitação de busca de dados do boletim"""

    # Realizando a request
    ra,senha = credenciais(context)
    url = f"{BASE_URL}/boletim"
    requestHeaders = {
        "user": ra,
        "password": senha
    }
    try:
        response = requests.get(url, headers= requestHeaders, verify=False, timeout=10)
    except Exception as e:
        print("Erro ao realizar a request")
        print(e)
        await update.message.reply_text("Ops.. Não deu pra fazer sua requisição, tente novamente.")
        return OPTIONS

    responseBody = response.json()
    responseAluno = "Aqui está seu boletim\n"

    for boletim in responseBody:
        # Formatando os dados
        responseAluno = responseAluno + "\n=========================\n"
        responseAluno = responseAluno + "Campus: {}\n".format(boletim["campus"])
        responseAluno = responseAluno + "Disciplina: {}\n".format(boletim["nome"])
        responseAluno = responseAluno + "Código: {}\n".format(boletim["codigo"])
        responseAluno = responseAluno + "turma: {}\n".format(boletim["turma"])
        responseAluno = responseAluno + "Faltas: {}\n".format(boletim["faltas"])
        responseAluno = responseAluno + "Percentual de frequência: {}\n".format(boletim["percentual_presenca"])
        responseAluno = responseAluno + "Limite de faltas: {}\n".format(boletim["limite_faltas"])
        responseAluno = responseAluno + "Média final: {}\n".format(boletim["media_final"])
        responseAluno = responseAluno + "Média parcial: {}\n".format(boletim["media_parcial"])
        
    await update.message.reply_text(responseAluno)

    return OPTIONS

async def buscando_dados_disciplinas(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Método que responde a solicitação de busca dados das disciplinas"""
    
    # Realizando a request
    ra,senha = credenciais(context)
    url = f"{BASE_URL}/disciplinas"
    requestHeaders = {
        "user": ra,
        "password": senha
    }

    try:
        response = requests.get(url, headers= requestHeaders, timeout=10, verify=False)
    except Exception as e:
        print("Erro ao realizar a request")
        print(e)
        await update.message.reply_text("Ops.. Não deu pra fazer sua requisição, tente novamente.")
        return OPTIONS
    responseBody = response.json()
    responseAluno = "Aqui está suas disciplinas\n"

    for materia in responseBody:
        # Formatando os dados
        responseAluno = responseAluno + "\n=========================\n"
        responseAluno = responseAluno + "Disciplina: {}\n".format(responseBody[materia]["nome"])

        for horarios in responseBody[materia]["horarios"]:
            responseAluno = responseAluno + "{} -> {} - {} sala {}\n".format(horarios["dia_semana"], horarios["inicio_aula"],horarios["final_aula"], horarios["sala_aula"])

    await update.message.reply_text(responseAluno)    


    return OPTIONS

async def done(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Metodo que finaliza a conversa do bot com o aluno"""
    user_data = context.user_data

    await update.message.reply_text(
        "Fazendo logout...",
        reply_markup=ReplyKeyboardRemove(),
    )

    user_data.clear()
    return ConversationHandler.END


def main() -> None:
    """Run the bot."""
    # Cria a aplicação e passa o token do bot como parâmetro
    application = Application.builder().token(TOKEN).build()

    # Adiciona os handlers para as mensagens recebidas
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            OPTIONS: [
                MessageHandler(
                    filters.Regex("^(Boletim)$"), buscando_dados_boletim
                ),
                MessageHandler(
                    filters.Regex("^(Disciplinas Matriculadas)$"), buscando_dados_disciplinas
                ), 
                MessageHandler(
                    filters.Regex("^(Disciplinas do dia)$"), buscando_disciplina_dia
                ),
            ],
            RA: [
                MessageHandler(
                    filters.TEXT, recebendo_ra
                )
            ],
            PASSWD: [
                MessageHandler(
                    filters.TEXT, recebendo_senha
                )
            ],
        },
        fallbacks=[MessageHandler(filters.Regex("^Encerrar sessão$"), done)],
    )

    application.add_handler(conv_handler)

    # Run the bot until the user presses Ctrl-C
    application.run_polling()


if __name__ == "__main__":
    main()



