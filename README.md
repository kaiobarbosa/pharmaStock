# PharmaStock

Aplicação desktop construída com Electron, frontend HTML/CSS/JavaScript e API local Flask.

## Preparar o backend local

1. Crie e ative um ambiente virtual Python na raiz do projeto, chamado `venv`.
2. Instale as dependências: `pip install -r backend/requirements.txt`.
3. Crie um arquivo `.env` na raiz com `DB_HOST`, `DB_USER`, `DB_PASSWORD` e `DB_NAME`.
4. O cadastro do primeiro diretor não requer registro na tabela `filial`: `funcionario.id_filial` deve aceitar `NULL` para esse usuário, que responde pela rede inteira.
5. Inicie a aplicação com `npm start`. O Electron inicia o Flask em `127.0.0.1:5000` junto com a tela de cadastro.

O executável Python pode ser definido pela variável `PHARMASTOCK_PYTHON`. A porta da API pode ser alterada por `FLASK_PORT`.

## Endpoint de cadastro

`POST /api/create_director_account` recebe JSON com `first_name`, `last_name`, `cpf`, `email`, `password`, `password_confirmation` e `internal_code`. O endpoint responde JSON; uma criação bem-sucedida retorna `201 Created`.
