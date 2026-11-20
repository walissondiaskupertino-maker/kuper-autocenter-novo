# Kuper Autocenter

Sistema web para gestão de oficina mecânica desenvolvido com Flask, SQLAlchemy e Bootstrap.

## Recursos

- Dashboard com indicadores operacionais e financeiros
- Cadastro de clientes e veículos
- Gestão de mecânicos, peças e serviços
- Ordens de serviço com serviços e peças
- Controle financeiro e movimentação de estoque
- Vendas com pagamentos parciais integrados ao financeiro
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
Para ativar Vendas, aplique `20261120_add_sales_module.sql` no banco utilizado
pela aplicação. A migração amplia os perfis de usuário e cria as tabelas de vendas,
itens e pagamentos, além do vínculo financeiro; ela não apaga nem recria dados.
Não execute novamente uma migração já aplicada.

O perfil Vendedor é provisionado no terminal, e não pelo cadastro público:

```powershell
flask --app run create-vendedor
```

O vendedor acessa somente as próprias vendas. Cada recebimento, inclusive parcial,
gera uma entrada no Financeiro. O estoque de peças é baixado uma única vez, ao
quitar a venda, após uma nova conferência de disponibilidade. O cadastro manual
do Financeiro permanece disponível apenas para saídas.

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

## Dificuldades encontradas e melhorias implementadas

### Acesso e comunicação com o banco

- O login apresentou erro 500 porque a aplicação consultava `usuarios` em um
  banco no qual essa tabela não existia. A seleção do arquivo `.env` também
  variava conforme a pasta de inicialização, podendo direcionar a aplicação para
  um banco diferente. A configuração passou a localizar o `.env` de forma
  determinística, e `init-db` cria tabelas ausentes sem apagar as existentes.
- `app/extensions.py` inicializa SQLAlchemy, CSRF e Flask-Login; as colunas e os
  perfis de usuário são definidos no modelo `Usuario`, em
  `app/models/models.py`.
- Alterações de esquema em bancos existentes devem ser feitas por migrações
  aditivas, com backup prévio. `init-db` não altera tabelas ou colunas já
  existentes.

### Cadastros e navegação

- No cadastro de veículos, foram corrigidos o carregamento de clientes, o
  botão de envio e o tratamento de placas duplicadas.
- Clientes, veículos, mecânicos, peças e serviços ganharam validação e
  normalização de dados; as listagens também oferecem filtros.
- A autorização é verificada no servidor por perfil. Vendedores veem somente
  as próprias vendas; o cadastro do perfil Vendedor é feito pelo comando CLI,
  não pelo cadastro público.

### Financeiro, vendas e estoque

- O Financeiro oferece relatórios em PDF e Excel que respeitam o filtro de
  entradas e saídas.
- Vendas registram peças e serviços com preços recalculados no servidor.
  Recebimentos parciais criam entradas financeiras; o estoque é conferido e
  baixado uma única vez quando a venda é quitada.
- Recebimentos vinculados a vendas não podem ser excluídos manualmente, para
  manter o histórico financeiro conciliado com os pagamentos.

### Situação da migração de vendas no MySQL

Em consulta de leitura realizada em 20/11/2026, a tabela `usuarios` e a coluna
`perfil` existiam no MySQL configurado para a aplicação. O tipo `ENUM` ainda
permitia somente `Admin`, `Mecanico` e `Recepcionista`; portanto, o perfil
`Vendedor` e o esquema de vendas ainda não estavam habilitados nessa base.

Antes de iniciar uma versão com vendas, faça backup e aplique uma única vez
[`migrations/mysql/20261120_add_sales_module.sql`](migrations/mysql/20261120_add_sales_module.sql).
Essa migração adiciona o perfil e as tabelas necessárias sem recriar as tabelas
ou apagar os registros existentes. Não a execute novamente se já tiver sido
aplicada.

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
- Os cadastros de clientes, veículos, mecânicos, peças e serviços oferecem busca
  e filtros nas listagens; os campos de documento, telefone, placa e valores
  também normalizam a entrada e validam os dados no servidor.
- O módulo Financeiro oferece exportação em PDF e Excel; ambos respeitam o filtro
  de entradas/saídas selecionado na tela.

## Segurança

- Não mantenha credenciais padrão em ambiente de produção.
- Configure `SECRET_KEY` com um valor aleatório.
- Crie administradores somente pelo comando CLI `create-admin`.
- As permissões são verificadas no servidor por perfil; a navegação também oculta módulos não autorizados.
- Aplique a migração de vínculo de mecânicos antes de atualizar uma instalação existente.
- Aplique a migração do módulo de vendas antes de iniciar uma versão que contenha as novas rotas.
- Habilite HTTPS em produção.
