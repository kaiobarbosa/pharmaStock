# PharmaStock

Aplicação desktop construída com Electron, frontend HTML/CSS/JavaScript e API local Flask.

## Preparar o backend local

1. Crie e ative um ambiente virtual Python na raiz do projeto, chamado `venv`.
2. Instale as dependências: `pip install -r backend/requirements.txt`.
3. Crie um arquivo `.env` na raiz com `DB_HOST`, `DB_USER`, `DB_PASSWORD`, `DB_NAME` e `JWT_SECRET_KEY`.
   Gere uma chave forte com `python -c "import secrets; print(secrets.token_urlsafe(48))"` (o backend exige pelo menos 32 bytes).
4. O cadastro do primeiro diretor não requer registro na tabela `filial`: `funcionario.id_filial` deve aceitar `NULL` para esse usuário, que responde pela rede inteira.
5. Inicie a aplicação com `npm start`. O Electron inicia o Flask em `127.0.0.1:5055` junto com a tela inicial escolhida após a checagem do primeiro acesso.

O executável Python pode ser definido pela variável `PHARMASTOCK_PYTHON`. A porta padrão da API é `5055` e pode ser alterada por `FLASK_PORT`.

O login retorna um JWT assinado com HS256. O token leva o nome e o e-mail do usuário e expira em uma hora. Defina `JWT_SECRET_KEY` no `.env` para manter a chave de assinatura entre reinicializações; sem ela, o backend gera uma chave aleatória nova a cada execução e os tokens anteriores deixam de ser aceitos.

## Endpoint de cadastro

`POST /api/create_director_account` recebe JSON com `first_name`, `last_name`, `cpf`, `email`, `password`, `password_confirmation` e `internal_code`. O endpoint responde JSON; uma criação bem-sucedida retorna `201 Created`.

`POST /api/login` recebe `email` e `password`. No sucesso, retorna `access_token` (Bearer JWT) com as claims `nome`, `email` e `exp`; o token dura uma hora. `GET /api/auth/session` valida o token enviado no cabeçalho `Authorization: Bearer <token>`.

`POST /api/create_branch` recebe JSON com `nome`, `cep`, `logradouro`, `numero`, `complemento`, `bairro`, `cidade` e `estado`. O complemento pode ser vazio. No sucesso, cria o endereço e a filial na mesma transação e retorna `201 Created` com os identificadores gerados. `GET /api/branches` retorna as filiais com seus endereços. `PUT /api/branches/<id_filial>` recebe os mesmos campos do cadastro e atualiza filial e endereço na mesma transação.
