from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user
from app.extensions import db
from app.models import Usuario
from app.forms import CadastroForm
from werkzeug.security import generate_password_hash
from sqlalchemy.exc import IntegrityError

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = (request.form.get('email') or '').strip().lower()
        senha = request.form.get('senha')
        usuario = Usuario.query.filter_by(email=email).first()
        
        if usuario and usuario.verificar_senha(senha):
            if not usuario.ativo:
                flash('Usuário desativado. Contate o administrador.', 'danger')
                return redirect(url_for('auth.login'))
            if (
                usuario.perfil == 'Mecanico'
                and (
                    usuario.mecanico is None
                    or not usuario.mecanico.ativo
                )
            ):
                flash('Conta de mecânico ainda não vinculada. Contate o administrador.', 'warning')
                return redirect(url_for('auth.login'))
                
            login_user(usuario, remember=True)
            session['usuario_nome'] = usuario.nome
            session['usuario_perfil'] = usuario.perfil
            flash(f'Bem-vindo(a), {usuario.nome}!', 'success')
            home_endpoint = {
                'Admin': 'dashboard.index',
                'Recepcionista': 'clientes.lista',
                'Mecanico': 'ordens_servico.lista',
            }[usuario.perfil]
            return redirect(url_for(home_endpoint))
        
        flash('E-mail ou senha inválidos.', 'danger')
    
    return render_template('auth/login.html')

@auth_bp.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    form = CadastroForm()
    if form.validate_on_submit():
        email = form.email.data
        if Usuario.query.filter_by(email=email).first():
            flash('Este e-mail já está cadastrado no sistema.', 'danger')
            return render_template('auth/cadastro.html', form=form)

        novo_usuario = Usuario(
            nome=form.nome.data,
            email=email,
            senha=generate_password_hash(form.senha.data),
            perfil=form.perfil.data,
            ativo=True
        )
        db.session.add(novo_usuario)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            if Usuario.query.filter_by(email=email).first():
                flash('Este e-mail já está cadastrado no sistema.', 'danger')
                return render_template('auth/cadastro.html', form=form)
            raise
        
        flash('Cadastro realizado com sucesso! Faça login para acessar.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/cadastro.html', form=form)

@auth_bp.route('/logout', methods=['POST'])
def logout():
    logout_user()
    session.clear()
    flash('Você saiu do sistema com sucesso.', 'info')
    return redirect(url_for('auth.login'))
