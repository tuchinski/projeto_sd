from flask import Flask, request, jsonify, abort
import buscador

app = Flask(__name__)

@app.route("/")
def hello():
    return ("hello world")

def get_ra_password(headers) -> tuple:
    return (headers.get("user"), headers.get("password"))

@app.route("/boletim", methods = ["GET"])
def get_dados_boletim():
    usuario, senha = get_ra_password(request.headers)
    if usuario == None or senha == None:
        abort(400)
    try:
        token = buscador.login(usuario, senha)
    except buscador.LoginErrorException:
        abort(401)
    
    retorno = buscador.busca_boletim(usuario,token)

    return jsonify(retorno)

@app.route("/disciplinas", methods = ["GET"])
def get_disciplinas_matriculadas():
    usuario, senha = get_ra_password(request.headers)
    if usuario == None or senha == None:
        abort(400)
    try:
        token = buscador.login(usuario, senha)
    except buscador.LoginErrorException:
        abort(401)
    
    retorno = buscador.busca_disciplinas_matriculadas(usuario,token)

    return jsonify(retorno)
    

if __name__ == '__main__':
   app.run("127.0.0.1","8080", True)