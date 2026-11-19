import os
import click
from flask import Flask
from sqlalchemy import event
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash
from .config import Config
from .extensions import db, csrf, login_manager
from .security import protect_application_route

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    os.makedirs(app.instance_path, exist_ok=True)

    db.init_app(app)
    with app.app_context():
        if db.engine.dialect.name == 'sqlite':
            @event.listens_for(db.engine, 'connect')
            def enable_sqlite_foreign_keys(connection, _):
                cursor = connection.cursor()
                cursor.execute('PRAGMA foreign_keys=ON')
                cursor.close()

    csrf.init_app(app)
    login_manager.init_app(app)

    @app.cli.command('init-db')
    def init_db_command():
        """Create database tables that do not exist yet."""
        with app.app_context():
            db.create_all()
        click.echo('Tabelas ausentes criadas (as existentes foram preservadas).')

    @app.cli.command('create-admin')
    @click.option('--email', prompt=True)
    @click.option('--nome', prompt='Nome', default='Administrador')
    @click.password_option('--password', confirmation_prompt=True)
    def create_admin_command(email, nome, password):
        """Create the first administrator from a local terminal."""
        from .models import Usuario

        email = email.strip().lower()
        with app.app_context():
            if Usuario.query.filter_by(perfil='Admin').first():
                raise click.ClickException('Já existe um administrador cadastrado.')
            if Usuario.query.filter_by(email=email).first():
                raise click.ClickException('Este e-mail já está cadastrado.')

            db.session.add(Usuario(
                nome=nome.strip(),
                email=email,
                senha=generate_password_hash(password),
                perfil='Admin',
                ativo=True
            ))
            try:
                db.session.commit()
            except IntegrityError as error:
                db.session.rollback()
                raise click.ClickException(
                    'Não foi possível criar o administrador; verifique os dados e tente novamente.'
                ) from error

        click.echo('Administrador criado com sucesso.')

    @app.cli.command('link-mechanic')
    @click.option('--email', prompt=True)
    @click.option('--mecanico-id', type=click.IntRange(min=1), prompt='ID do mecânico')
    def link_mechanic_command(email, mecanico_id):
        """Link a mechanic account to an existing mechanic record."""
        from .models import Mecanico, Usuario

        email = email.strip().lower()
        with app.app_context():
            usuario = Usuario.query.filter_by(email=email).first()
            if usuario is None:
                raise click.ClickException('Usuário não encontrado.')
            if usuario.perfil != 'Mecanico':
                raise click.ClickException('A conta informada não tem perfil Mecânico.')

            mecanico = db.session.get(Mecanico, mecanico_id)
            if mecanico is None or not mecanico.ativo:
                raise click.ClickException('Mecânico não encontrado ou inativo.')
            if usuario.mecanico_id is not None:
                raise click.ClickException('Esta conta já está vinculada a um mecânico.')
            if Usuario.query.filter_by(mecanico_id=mecanico_id).first():
                raise click.ClickException('Este mecânico já está vinculado a uma conta.')

            usuario.mecanico_id = mecanico.id
            try:
                db.session.commit()
            except IntegrityError as error:
                db.session.rollback()
                raise click.ClickException(
                    'Não foi possível vincular a conta; verifique se a migração foi aplicada.'
                ) from error

        click.echo('Conta vinculada ao mecânico com sucesso.')

    @app.before_request
    def protect_application_routes():
        return protect_application_route()

    # Carregar usuário
    @login_manager.user_loader
    def load_user(user_id):
        from .models import Usuario
        return db.session.get(Usuario, int(user_id))

    # Blueprints
    from .routes.dashboard import dashboard_bp
    from .routes.clientes import clientes_bp
    from .routes.veiculos import veiculos_bp
    from .routes.mecanicos import mecanicos_bp
    from .routes.pecas import pecas_bp
    from .routes.servicos import servicos_bp
    from .routes.ordens_servico import os_bp
    from .routes.financeiro import financeiro_bp
    from .routes.relatorios import relatorios_bp
    from .routes.auth import auth_bp

    app.register_blueprint(dashboard_bp)
    app.register_blueprint(clientes_bp, url_prefix='/clientes')
    app.register_blueprint(veiculos_bp, url_prefix='/veiculos')
    app.register_blueprint(mecanicos_bp, url_prefix='/mecanicos')
    app.register_blueprint(pecas_bp, url_prefix='/pecas')
    app.register_blueprint(servicos_bp, url_prefix='/servicos')
    app.register_blueprint(os_bp, url_prefix='/ordens-servico')
    app.register_blueprint(financeiro_bp, url_prefix='/financeiro')
    app.register_blueprint(relatorios_bp, url_prefix='/relatorios')
    app.register_blueprint(auth_bp, url_prefix='/auth')

    return app