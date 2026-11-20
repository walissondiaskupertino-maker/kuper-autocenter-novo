from flask import Blueprint, render_template, redirect, url_for, flash, request
from app.extensions import db
from app.models import Financeiro
from app.forms import FinanceiroForm
from sqlalchemy.sql import func

financeiro_bp = Blueprint('financeiro', __name__)

@financeiro_bp.route('/')
def lista():
    tipo = request.args.get('tipo', '')
    if tipo not in ('Entrada', 'Saida'):
        tipo = ''
    query = Financeiro.query.order_by(Financeiro.data_movimentacao.desc())
    if tipo:
        query = query.filter_by(tipo=tipo)
    lancamentos = query.all()

    total_entradas = float(db.session.query(func.coalesce(func.sum(Financeiro.valor), 0)).filter_by(tipo='Entrada').scalar() or 0)
    total_saidas = float(db.session.query(func.coalesce(func.sum(Financeiro.valor), 0)).filter_by(tipo='Saida').scalar() or 0)

    return render_template('financeiro/lista.html',
                         lancamentos=lancamentos, tipo=tipo,
                         total_entradas=total_entradas, total_saidas=total_saidas,
                         saldo=total_entradas - total_saidas)

@financeiro_bp.route('/novo', methods=['GET', 'POST'])
def novo():
    form = FinanceiroForm()
    if form.validate_on_submit():
        lanc = Financeiro(
            tipo=form.tipo.data,
            descricao=form.descricao.data,
            valor=form.valor.data,
            categoria=form.categoria.data,
            forma_pagamento=form.forma_pagamento.data
        )
        db.session.add(lanc)
        db.session.commit()
        flash('Lançamento registrado com sucesso!', 'success')
        return redirect(url_for('financeiro.lista'))
    return render_template('financeiro/form.html', form=form, titulo='Novo Lançamento')

@financeiro_bp.route('/<int:id>/excluir', methods=['POST'])
def excluir(id):
    lanc = Financeiro.query.get_or_404(id)
    if lanc.venda_id is not None:
        flash('Recebimentos vinculados a vendas não podem ser excluídos.', 'danger')
        return redirect(url_for('financeiro.lista'))
    db.session.delete(lanc)
    db.session.commit()
    flash('Lançamento excluído!', 'success')
    return redirect(url_for('financeiro.lista'))
