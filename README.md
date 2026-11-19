# Kuper Autocenter

Sistema web para gestão de oficina mecânica desenvolvido com Flask, SQLAlchemy e Bootstrap.

## Recursos

- Dashboard com indicadores operacionais e financeiros
- Cadastro de clientes e veículos
- Gestão de mecânicos, peças e serviços
- Ordens de serviço com serviços e peças
- Controle financeiro e movimentação de estoque
- Relatórios em PDF
- Autenticação com perfis de usuário

## Tecnologias

- Python 3.12
- Flask 3
- SQLAlchemy e PyMySQL
- Flask-Login e Flask-WTF
- Bootstrap 5
- Bootstrap Icons
- Chart.js
- MySQL

## Estrutura

```text
app/
  routes/       Blueprints e regras das páginas
  models/       Entidades e relacionamentos
  templates/    Páginas Jinja
  static/
    css/        Estilos globais
    js/         Comportamentos globais
  forms.py      Formulários WTForms
run.py          Inicialização da aplicação
requirements.txt Dependências Python
```

## Configuração

1. Crie o ambiente virtual e instale as dependências:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. Para desenvolvimento local, o sistema usa SQLite automaticamente; o banco fica em `instance/kuper_autocenter.db`. Para usar MySQL, configure as variáveis de ambiente:

```text
SECRET_KEY=sua-chave-secreta
DB_USER=seu_usuario
DB_PASSWORD=sua_senha
DB_HOST=localhost
DB_PORT=3306
DB_NAME=kuper_autocenter
```

As variáveis podem ser armazenadas em um arquivo `.env` na raiz do projeto.
Em produção, defina `APP_ENV=production` e configure `SECRET_KEY` junto com
`DATABASE_URL` ou `DB_USER` e `DB_PASSWORD`.

Para criar o primeiro administrador, use o comando interativo no terminal:

```powershell
flask --app run create-admin
```

O comando solicita e confirma a senha sem exibi-la. Não há rota web pública
para criar administradores.

3. Crie as tabelas ausentes. O comando preserva tabelas existentes:

```powershell
flask --app run init-db
```

Também é possível importar `app/kuper_autocenter.sql` em uma instalação MySQL nova.

4. Execute a aplicação:

```powershell
python run.py
```

Acesse `http://127.0.0.1:5000`.

As rotas operacionais exigem autenticação. Para criar o primeiro administrador,
execute `flask --app run create-admin` em um terminal local; o comando solicita
e confirma a senha sem exibi-la. O cadastro web permite apenas os perfis
Recepcionista e Mecânico.

## Testes

Instale as dependências do arquivo `requirements.txt` e execute:

```powershell
pytest
```

Os testes usam um banco SQLite temporário e não acessam o banco MySQL de produção.

## Interface

Os estilos globais ficam em `app/static/css/app.css` e o comportamento da navegação móvel em `app/static/js/app.js`. Cada página reutiliza `app/templates/base.html`, que centraliza menu lateral, cabeçalho, perfil do usuário e mensagens de feedback.

Padrões de interface:

- Use `url_for` para links internos.
- Use classes Bootstrap para espaçamento e organização responsiva.
- Use a classe `page-actions` para grupos de botões.
- Use `data-confirm="mensagem"` em ações destrutivas ou de saída.
- Mantenha tabelas dentro de `.table-responsive`.

## Segurança

- Não mantenha credenciais padrão em ambiente de produção.
- Configure `SECRET_KEY` com um valor aleatório.
- Revise a rota de criação do primeiro administrador antes de publicar o sistema.
- Habilite HTTPS em produção.
