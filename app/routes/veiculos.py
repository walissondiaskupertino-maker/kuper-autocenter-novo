from flask import Blueprint, render_template, redirect, url_for, flash
from app.extensions import db
from app.models import Veiculo, Cliente
from app.forms import VeiculoForm

veiculos_bp = Blueprint('veiculos', __name__)


@veiculos_bp.route('/')
def lista():
    veiculos = Veiculo.query.join(Cliente).order_by(Veiculo.placa).all()
    return render_template('veiculos/lista.html', veiculos=veiculos)


@veiculos_bp.route('/novo', methods=['GET', 'POST'])
def novo():
    form = VeiculoForm()
    form.cliente_id.choices = [(c.id, c.nome) for c in Cliente.query.order_by(Cliente.nome).all()]
    if form.validate_on_submit():
        veiculo = Veiculo(
            cliente_id=form.cliente_id.data,
            placa=form.placa.data.upper(),
            modelo=form.modelo.data,
            marca=form.marca.data,
            ano=form.ano.data,
            quilometragem=form.quilometragem.data or 0
        )
        db.session.add(veiculo)
        db.session.commit()
        flash('Veículo cadastrado com sucesso!', 'success')
        return redirect(url_for('veiculos.lista'))
    return render_template('veiculos/form.html', form=form, titulo='Novo Veículo')


@veiculos_bp.route('/<int:id>/editar', methods=['GET', 'POST'])
def editar(id):
    veiculo = Veiculo.query.get_or_404(id)
    form = VeiculoForm(obj=veiculo)
    form.cliente_id.choices = [(c.id, c.nome) for c in Cliente.query.order_by(Cliente.nome).all()]
    if form.validate_on_submit():
        veiculo.cliente_id = form.cliente_id.data
        veiculo.placa = form.placa.data.upper()
        veiculo.modelo = form.modelo.data
        veiculo.marca = form.marca.data
        veiculo.ano = form.ano.data
        veiculo.quilometragem = form.quilometragem.data or 0
        db.session.commit()
        flash('Veículo atualizado com sucesso!', 'success')
        return redirect(url_for('veiculos.lista'))
    return render_template('veiculos/form.html', form=form, titulo='Editar Veículo')


@veiculos_bp.route('/<int:id>/excluir', methods=['POST'])
def excluir(id):
    veiculo = Veiculo.query.get_or_404(id)
    db.session.delete(veiculo)
    db.session.commit()
    flash('Veículo excluído com sucesso!', 'success')
    return redirect(url_for('veiculos.lista'))