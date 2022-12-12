from dotenv import load_dotenv
import os
import logging
import requests
import json

from typing import Dict
from telegram import __version__ as TG_VER

load_dotenv()

TOKEN = os.getenv("API_KEY")

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

OPTIONS, TYPING_REPLY, TYPING_CHOICE, RA, SENHA, CHECK = range(6)

reply_keyboard = [
    ["Boletim", "Disciplinas Matriculadas"],
    # ["Number of siblings", "Something else..."],
    ["Done"],
]
markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)


def facts_to_str(user_data: Dict[str, str]) -> str:
    """Helper function for formatting the gathered user info."""
    facts = [f"{key} - {value}" for key, value in user_data.items()]
    return "\n".join(facts).join(["\n", "\n"])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the conversation and ask user for input."""
    await update.message.reply_text(
        "Oi, Sou o bot da UTF! "
        "Primeiramente, digite seu RA.",
        reply_markup=ReplyKeyboardRemove()
    )
    return RA

async def recebendo_ra(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    context.user_data["ra"] = text
    
    await update.message.reply_text(f"Ok!. Agora digite sua senha")

    return SENHA

def credenciais(context: ContextTypes.DEFAULT_TYPE):
    return context.user_data["ra"], context.user_data["senha"]


async def recebendo_senha(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    context.user_data["senha"] = text
    ra = context.user_data["ra"]
    senha = context.user_data["senha"]
    # await update.message.reply_text(f"Ok, o RA informado foi {ra} e a senha foi {senha}",reply_markup=markup)
    await update.message.reply_text(f"aguarde um pouco enquanto verifico seus dados no servidor")
    url = "http://localhost:8080/validaCredenciais"
    requestHeaders = {
        "user": ra,
        "password": senha
    }
    response = requests.get(url, headers= requestHeaders)
    if response.status_code == 200:
        await update.message.reply_text("Login efetuado com sucesso")
        await update.message.reply_text("Selecione qual opção você deseja", reply_markup=markup)
        return OPTIONS
    else:
        responseBody = response.json()
        await update.message.reply_text(responseBody["mensagem"])
        await update.message.reply_text("Tente fazer o login novamente")
        await update.message.reply_text("Primeiramente, digite seu RA.")
        return RA

    
async def analisando_credenciais(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Login efetuado com sucesso")

    return OPTIONS

async def selecionando_opcao(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Selecione qual opção você deseja")

    return OPTIONS

async def buscando_dados_boletim(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    ra,senha = credenciais(context)
    url = "http://localhost:8080/boletim"
    requestHeaders = {
        "user": ra,
        "password": senha
    }
    response = requests.get(url, headers= requestHeaders)
    responseBody = response.json()
    responseAluno = "Aqui está seu boletim\n"

    for boletim in responseBody:
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
    ra,senha = credenciais(context)
    url = "http://localhost:8080/disciplinas"
    requestHeaders = {
        "user": ra,
        "password": senha
    }

    response = requests.get(url, headers= requestHeaders, timeout=10)
    responseBody = response.json()
    responseAluno = "Aqui está suas disciplinas\n"

    for materia in responseBody:
        responseAluno = responseAluno + "\n=========================\n"
        responseAluno = responseAluno + "Disciplina: {}\n".format(responseBody[materia]["nome"])

        for horarios in responseBody[materia]["horarios"]:
            responseAluno = responseAluno + "{} - {} sala {}\n".format(horarios["inicio_aula"],horarios["final_aula"], horarios["sala_aula"])

    await update.message.reply_text(responseAluno)    


    return OPTIONS

async def done(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Display the gathered info and end the conversation."""
    user_data = context.user_data
    if "choice" in user_data:
        del user_data["choice"]

    await update.message.reply_text(
        f"I learned these facts about you: {facts_to_str(user_data)}Until next time!",
        reply_markup=ReplyKeyboardRemove(),
    )

    user_data.clear()
    return ConversationHandler.END


def main() -> None:
    """Run the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TOKEN).build()

    # Add conversation handler with the states CHOOSING, TYPING_CHOICE and TYPING_REPLY
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
            ],
            # TYPING_CHOICE: [
            #     MessageHandler(
            #         filters.TEXT & ~(filters.COMMAND | filters.Regex("^Done$")), regular_choice
            #     )
            # ],
            # TYPING_REPLY: [
            #     MessageHandler(
            #         filters.TEXT & ~(filters.COMMAND | filters.Regex("^Done$")),
            #         received_information,
            #     )
            # ],
            RA: [
                MessageHandler(
                    filters.TEXT, recebendo_ra
                )
            ],
            SENHA: [
                MessageHandler(
                    filters.TEXT, recebendo_senha
                )
            ],
            CHECK: [
                MessageHandler(
                    filters.TEXT, selecionando_opcao
                )
            ]
        },
        fallbacks=[MessageHandler(filters.Regex("^Done$"), done)],
    )

    application.add_handler(conv_handler)

    # Run the bot until the user presses Ctrl-C
    application.run_polling()


if __name__ == "__main__":
    main()



