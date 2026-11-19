from flask import Blueprint, render_template, redirect, url_for, flash
from app.extensions import db
from app.models import Cliente
from app.forms import ClienteForm
from sqlalchemy.exc import IntegrityError

clientes_bp = Blueprint('clientes', __name__)

@clientes_bp.route('/')
def lista():
    clientes = Cliente.query.order_by(Cliente.nome).all()
    return render_template('clientes/lista.html', clientes=clientes)

@clientes_bp.route('/novo', methods=['GET', 'POST'])
def novo():
    form = ClienteForm()
    if form.validate_on_submit():
        cliente = Cliente(
            nome=form.nome.data, cpf_cnpj=form.cpf_cnpj.data,
            telefone=form.telefone.data, email=form.email.data, endereco=form.endereco.data
        )
        db.session.add(cliente)
        db.session.commit()
        flash('Cliente cadastrado com sucesso!', 'success')
        return redirect(url_for('clientes.lista'))
    return render_template('clientes/form.html', form=form, titulo='Novo Cliente')

@clientes_bp.route('/<int:id>/editar', methods=['GET', 'POST'])
def editar(id):
    cliente = Cliente.query.get_or_404(id)
    form = ClienteForm(obj=cliente)
    if form.validate_on_submit():
        cliente.nome = form.nome.data
        cliente.cpf_cnpj = form.cpf_cnpj.data
        cliente.telefone = form.telefone.data
        cliente.email = form.email.data
        cliente.endereco = form.endereco.data
        db.session.commit()
        flash('Cliente atualizado com sucesso!', 'success')
        return redirect(url_for('clientes.lista'))
    return render_template('clientes/form.html', form=form, titulo='Editar Cliente')

@clientes_bp.route('/<int:id>/excluir', methods=['POST'])
def excluir(id):
    cliente = Cliente.query.get_or_404(id)
    db.session.delete(cliente)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        flash(
            'Não é possível excluir um cliente que possui veículos vinculados.',
            'danger'
        )
        return redirect(url_for('clientes.lista'))
    flash('Cliente excluído com sucesso!', 'success')
    return redirect(url_for('clientes.lista'))