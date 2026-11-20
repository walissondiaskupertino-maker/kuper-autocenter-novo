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

As variáveis podem ser armazenadas em um arquivo `.env` na raiz do projeto
(copie `.env.example` e substitua os valores de exemplo). Para compatibilidade
com instalações anteriores, se o arquivo da raiz não existir, o sistema também
procura `app/.env`. A mesma configuração é escolhida independentemente da pasta
de onde o Flask for iniciado; variáveis de ambiente do sistema têm prioridade.
Em produção, defina `APP_ENV=production` e configure `SECRET_KEY` junto com
`DATABASE_URL` ou `DB_USER` e `DB_PASSWORD`.

Para criar o primeiro administrador, use o comando interativo no terminal:

```powershell
flask --app run create-admin
```

O comando solicita e confirma a senha sem exibi-la. Não há rota web pública
para criar administradores.

3. Crie somente as tabelas ausentes. O comando preserva as tabelas e os dados
existentes; execute-o no mesmo ambiente e com a mesma configuração de banco usada
para iniciar o servidor:

```powershell
flask --app run init-db
```

O arquivo `app/kuper_autocenter.sql` é somente para uma instalação MySQL nova:
ele cria e popula tabelas de exemplo e não deve ser executado em um banco existente.

Para instalações existentes, faça backup e aplique uma única vez a migração
correspondente ao banco em `migrations/mysql/` ou `migrations/sqlite/` antes de
atualizar o código. `init-db` cria tabelas ausentes, mas não altera tabelas existentes.

Após cadastrar a conta com perfil Mecânico e criar seu registro no módulo
Mecânicos, vincule ambos pelo terminal local usando o e-mail da conta e o ID do
cadastro:

```powershell
flask --app run link-mechanic --email mecanico@example.com --mecanico-id 1
```

O perfil Mecânico só consegue acessar as OS atribuídas a esse cadastro e atualizar
o diagnóstico. Recepcionistas operam clientes, veículos e abertura/edição básica
de OS; somente Admin acessa financeiro, estoque e cadastros administrativos.

4. Execute a aplicação:

```powershell
python run.py
```

Acesse `http://127.0.0.1:5000`.

As rotas operacionais exigem autenticação. O cadastro web aceita somente os
perfis Recepcionista e Mecânico; contas de mecânico precisam ser vinculadas a
um cadastro ativo antes do primeiro acesso.

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
- Crie administradores somente pelo comando CLI `create-admin`.
- As permissões são verificadas no servidor por perfil; a navegação também oculta módulos não autorizados.
- Aplique a migração de vínculo de mecânicos antes de atualizar uma instalação existente.
- Habilite HTTPS em produção.
