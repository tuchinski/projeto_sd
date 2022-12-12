from flask import Flask, request, jsonify, abort
from flask_caching import Cache
import buscador
from cryptography.fernet import Fernet

# Minutos em que o token do cliente vai ficar disponível na cache
TEMPO_LOGIN_CACHE = 30

# Definindo o tipo do cache que será utilizado
cache = Cache(config={'CACHE_TYPE': 'SimpleCache'})

app = Flask(__name__)

# Iniciando o cacha
cache.init_app(app)

# configuração para guardar as senhas na cache de forma criptografada
key = Fernet.generate_key()
fernet = Fernet(key)

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
    
    # Buscando dados na cache para o usuário informado
    dados_cache = cache.get(usuario)

    # Caso encontre o usuário, e a senha seja a mesma, pega o token que já foi
    # previamente informado
    if dados_cache and fernet.decrypt(dados_cache["senha"]).decode() == senha:
        token = dados_cache["token"]
        print(f"Achou na cache o usuário {usuario}")
    else:
        # Caso não ache o usuário na cache, tenta fazer o login no portal do aluno
        try:
            # Tenta realizar o login no portal do aluno, com as informações passadas
            print(f"Não achou o usuário {usuario}, tentando realizar login para obter token")
            token = buscador.login(usuario, senha)
            enc_senha = fernet.encrypt(senha.encode())
            cache.set(usuario, {
                "usuario": usuario,
                "senha": enc_senha,
                "token": token
            },timeout=60*TEMPO_LOGIN_CACHE)
        except buscador.LoginErrorException:
            abort(401)
    
    try:
        retorno = buscador.busca_boletim(usuario,token)
    except buscador.InternalServerErrorException as e:
        return jsonify({
            "erro": e.codigo,
            "mensagem": e.descricao
        }),500
    except Exception:
        return jsonify({
            "erro": 500,
            "mensagem": "Erro interno no servidor"
        }), 500

    return jsonify(retorno)

@app.route("/disciplinas", methods = ["GET"])
def get_disciplinas_matriculadas():
    usuario, senha = get_ra_password(request.headers)
    # Caso não seja passado no header o usuário ou senha do aluno
    # retorna um erro 400(BAD REQUEST)
    if usuario == None or senha == None:
        abort(400)
    
    dados_cache = cache.get(usuario)

    # Caso encontre o usuário, e a senha seja a mesma, pega o token que já foi
    # previamente informado
    if dados_cache and fernet.decrypt(dados_cache["senha"]).decode() == senha:
        token = dados_cache["token"]
        print(f"Achou na cache o usuário {usuario}")
    else:
        # Caso não ache o usuário na cache, tenta fazer o login no portal do aluno
        try:
            # Tenta realizar o login no portal do aluno, com as informações passadas
            print(f"Não achou o usuário {usuario}, tentando realizar login para obter token")
            token = buscador.login(usuario, senha)
            enc_senha = fernet.encrypt(senha.encode())
            cache.set(usuario, {
                "usuario": usuario,
                "senha": enc_senha,
                "token": token
            },timeout=60*TEMPO_LOGIN_CACHE)
        except buscador.LoginErrorException:
            abort(401)
        
    try:
        retorno = buscador.busca_disciplinas_matriculadas(usuario,token)
        return jsonify(retorno)
    except buscador.InternalServerErrorException as e:
        return jsonify({
            "erro": e.codigo,
            "mensagem": e.descricao
        }),500
    except Exception:
        return jsonify({
            "erro": 500,
            "mensagem": "Erro interno no servidor"
        }), 500

    

if __name__ == '__main__':
   app.run("127.0.0.1","8080", True)