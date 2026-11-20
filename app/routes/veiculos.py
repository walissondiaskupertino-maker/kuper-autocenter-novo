from flask import Blueprint, render_template, redirect, url_for, flash
from app.extensions import db
from app.models import Cliente, Veiculo
from app.forms import VeiculoForm
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload

veiculos_bp = Blueprint('veiculos', __name__)


@veiculos_bp.route('/')
def lista():
    veiculos = Veiculo.query.options(
        joinedload(Veiculo.cliente)
    ).order_by(Veiculo.placa).all()
    return render_template('veiculos/lista.html', veiculos=veiculos)


@veiculos_bp.route('/novo', methods=['GET', 'POST'])
def novo():
    form = VeiculoForm()
    form.cliente_id.choices = [(c.id, c.nome) for c in Cliente.query.order_by(Cliente.nome).all()]
    if form.validate_on_submit():
        placa = form.placa.data
        veiculo = Veiculo(
            cliente_id=form.cliente_id.data,
            placa=placa,
            modelo=form.modelo.data,
            marca=form.marca.data,
            ano=form.ano.data,
            quilometragem=form.quilometragem.data or 0
        )
        db.session.add(veiculo)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            if Veiculo.query.filter_by(placa=placa).first():
                flash('Já existe um veículo cadastrado com esta placa.', 'danger')
                return render_template('veiculos/form.html', form=form, titulo='Novo Veículo')
            raise
        flash('Veículo cadastrado com sucesso!', 'success')
        return redirect(url_for('veiculos.lista'))
    return render_template('veiculos/form.html', form=form, titulo='Novo Veículo')


@veiculos_bp.route('/<int:id>/editar', methods=['GET', 'POST'])
def editar(id):
    veiculo = Veiculo.query.get_or_404(id)
    form = VeiculoForm(obj=veiculo)
    form.cliente_id.choices = [(c.id, c.nome) for c in Cliente.query.order_by(Cliente.nome).all()]
    if form.validate_on_submit():
        placa = form.placa.data
        veiculo.cliente_id = form.cliente_id.data
        veiculo.placa = placa
        veiculo.modelo = form.modelo.data
        veiculo.marca = form.marca.data
        veiculo.ano = form.ano.data
        veiculo.quilometragem = form.quilometragem.data or 0
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            duplicate = Veiculo.query.filter(
                Veiculo.placa == placa,
                Veiculo.id != veiculo.id,
            ).first()
            if duplicate:
                flash('Já existe um veículo cadastrado com esta placa.', 'danger')
                return render_template('veiculos/form.html', form=form, titulo='Editar Veículo')
            raise
        flash('Veículo atualizado com sucesso!', 'success')
        return redirect(url_for('veiculos.lista'))
    return render_template('veiculos/form.html', form=form, titulo='Editar Veículo')


@veiculos_bp.route('/<int:id>/excluir', methods=['POST'])
def excluir(id):
    veiculo = Veiculo.query.get_or_404(id)
    db.session.delete(veiculo)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        flash(
            'Este veículo possui ordens de serviço vinculadas e não pode ser excluído.',
            'danger'
        )
        return redirect(url_for('veiculos.lista'))
    flash('Veículo excluído com sucesso!', 'success')
    return redirect(url_for('veiculos.lista'))