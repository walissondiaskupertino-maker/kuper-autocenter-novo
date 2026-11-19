import os
import click
from flask import Flask, request
from flask_login import current_user
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash
from .config import Config
from .extensions import db, csrf, login_manager

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    os.makedirs(app.instance_path, exist_ok=True)

    db.init_app(app)
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

    @app.before_request
    def protect_application_routes():
        public_endpoints = {'auth.login', 'auth.cadastro', 'static'}
        if request.endpoint is None or request.endpoint in public_endpoints:
            return None
        if not current_user.is_authenticated:
            return login_manager.unauthorized()
        return None

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