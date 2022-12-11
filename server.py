from flask import Flask, request, jsonify, abort
from flask_caching import Cache
import buscador

# Definindo o tipo do cache que será utilizado
cache = Cache(config={'CACHE_TYPE': 'SimpleCache'})

app = Flask(__name__)

# Iniciando o cacha
cache.init_app(app)

# Método responsável por buscar o usuário e a senha do aluno na request
def get_ra_password(headers) -> tuple:
    return (headers.get("user"), headers.get("password"))

# Rota que busca os dados do boletim do aluno
@app.route("/boletim", methods = ["GET"])
def get_dados_boletim():
    usuario, senha = get_ra_password(request.headers)
    # Caso não seja passado no header o usuário ou senha do aluno
    # retorna um erro 400(BAD REQUEST)
    if usuario == None or senha == None:
        abort(400)
    
    dados_cache = cache.get(usuario)

    if dados_cache and dados_cache["senha"] == senha:
        token = dados_cache["token"]
        print(f"Achou na cache o usuário {usuario}")
    else:
        try:
            # Tenta realizar o login no portal do aluno, com as informações passadas
            print(f"Não achou o usuário {usuario}, tentando realizar login para obter token")
            token = buscador.login(usuario, senha)
            cache.set(usuario, {
                "usuario": usuario,
                "senha": senha,
                "token": token
            },timeout=60*10)
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