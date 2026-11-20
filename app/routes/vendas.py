from collections import defaultdict
from decimal import Decimal

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user
from app.extensions import db
from app.forms import PagamentoForm, VendaForm
from app.models import (
    Cliente,
    Financeiro,
    ItemVenda,
    MovimentacaoEstoque,
    Pagamento,
    Peca,
    Servico,
    Usuario,
    Veiculo,
    Venda,
)
from app.security import role_required


vendas_bp = Blueprint('vendas', __name__)
CENTAVO = Decimal('0.01')
VALOR_MAXIMO = Decimal('99999999.99')
FORMAS_PAGAMENTO = {
    'dinheiro': 'Dinheiro',
    'pix': 'Pix',
    'cartao_credito': 'Cartão de crédito',
    'cartao_debito': 'Cartão de débito',
}


def _popular_escolhas(form):
    clientes = Cliente.query.order_by(Cliente.nome).all()
    veiculos = Veiculo.query.order_by(Veiculo.placa).all()
    form.cliente_id.choices = [(0, 'Selecione um cliente')] + [
        (cliente.id, cliente.nome) for cliente in clientes
    ]
    form.veiculo_id.choices = [(0, 'Selecione um veículo')] + [
        (veiculo.id, f'{veiculo.placa} - {veiculo.marca} {veiculo.modelo}')
        for veiculo in veiculos
    ]
    return clientes, veiculos


def _render_nova_venda(form):
    clientes, veiculos = _popular_escolhas(form)
    tipos = request.form.getlist('tipo_item[]') if request.method == 'POST' else []
    ids = request.form.getlist('item_id[]') if request.method == 'POST' else []
    quantidades = request.form.getlist('quantidade[]') if request.method == 'POST' else []
    quantidade_linhas = max(len(tipos), len(ids), len(quantidades), 0)
    itens_iniciais = [
        {
            'tipo': tipos[index] if index < len(tipos) else '',
            'id': ids[index] if index < len(ids) else '',
            'quantidade': quantidades[index] if index < len(quantidades) else '1',
        }
        for index in range(quantidade_linhas)
    ]
    return render_template(
        'vendas/nova_venda.html',
        form=form,
        clientes=clientes,
        veiculos=veiculos,
        pecas=Peca.query.order_by(Peca.descricao).all(),
        servicos=Servico.query.filter_by(ativo=True).order_by(Servico.nome).all(),
        itens_iniciais=itens_iniciais,
    )


def _venda_do_usuario(venda_id, bloquear=False):
    query = Venda.query.filter_by(id=venda_id)
    if current_user.perfil == 'Vendedor':
        query = query.filter_by(vendedor_id=current_user.id)
    if bloquear:
        query = query.with_for_update()
    return query.first_or_404()


def _validar_itens():
    tipos = request.form.getlist('tipo_item[]')
    ids = request.form.getlist('item_id[]')
    quantidades = request.form.getlist('quantidade[]')
    if not tipos or len(tipos) != len(ids) or len(tipos) != len(quantidades):
        return None, None, 'Adicione ao menos um item e confira os dados de cada linha.'

    itens = []
    estoque_necessario = defaultdict(int)
    subtotal = Decimal('0.00')
    for tipo, item_id_texto, quantidade_texto in zip(tipos, ids, quantidades):
        try:
            item_id = int(item_id_texto)
            quantidade = int(quantidade_texto)
        except (TypeError, ValueError):
            return None, None, 'Informe um item e uma quantidade inteira válida.'
        if item_id < 1 or quantidade < 1 or quantidade > 999999:
            return None, None, 'A quantidade de cada item deve ser maior que zero.'

        if tipo == 'peca':
            catalogo = db.session.get(Peca, item_id)
            if catalogo is None:
                return None, None, 'Uma das peças selecionadas não existe mais.'
            preco = Decimal(catalogo.preco_venda)
            estoque_necessario[catalogo.id] += quantidade
            item = ItemVenda(
                tipo='peca',
                peca_id=catalogo.id,
                quantidade=quantidade,
                preco_unitario=preco,
            )
        elif tipo == 'servico':
            catalogo = db.session.get(Servico, item_id)
            if catalogo is None or not catalogo.ativo:
                return None, None, 'Um dos serviços selecionados não existe ou está inativo.'
            preco = Decimal(catalogo.preco_base)
            item = ItemVenda(
                tipo='servico',
                servico_id=catalogo.id,
                quantidade=quantidade,
                preco_unitario=preco,
            )
        else:
            return None, None, 'Tipo de item inválido.'

        if preco < 0:
            return None, None, 'O preço cadastrado para um item não pode ser negativo.'
        subtotal += preco * quantidade
        if subtotal > VALOR_MAXIMO:
            return None, None, 'O subtotal excede o limite financeiro permitido.'
        itens.append(item)

    if estoque_necessario:
        pecas = Peca.query.filter(
            Peca.id.in_(sorted(estoque_necessario))
        ).order_by(Peca.id).with_for_update().all()
        for peca in pecas:
            if peca.estoque_atual < estoque_necessario[peca.id]:
                return None, None, (
                    f'Estoque insuficiente para {peca.descricao}. '
                    f'Disponível: {peca.estoque_atual}.'
                )

    return itens, subtotal.quantize(CENTAVO), None


@vendas_bp.route('/')
@role_required('Vendedor', 'Admin')
def lista():
    query = Venda.query
    if current_user.perfil == 'Vendedor':
        query = query.filter_by(vendedor_id=current_user.id)
    vendas = query.order_by(Venda.data.desc(), Venda.id.desc()).all()
    return render_template('vendas/lista.html', vendas=vendas)


@vendas_bp.route('/nova', methods=['GET', 'POST'])
@role_required('Vendedor', 'Admin')
def nova_venda():
    form = VendaForm()
    _popular_escolhas(form)

    if form.validate_on_submit():
        veiculo = db.session.get(Veiculo, form.veiculo_id.data)
        if veiculo is None or veiculo.cliente_id != form.cliente_id.data:
            flash('Selecione um veículo pertencente ao cliente informado.', 'danger')
            return _render_nova_venda(form)

        itens, subtotal, erro = _validar_itens()
        if erro:
            flash(erro, 'danger')
            return _render_nova_venda(form)

        desconto = (form.desconto.data or Decimal('0.00')).quantize(CENTAVO)
        if desconto > subtotal:
            flash('O desconto não pode ser maior que o subtotal.', 'danger')
            return _render_nova_venda(form)
        total = (subtotal - desconto).quantize(CENTAVO)
        if total <= 0:
            flash('O total da venda deve ser maior que zero.', 'danger')
            return _render_nova_venda(form)

        venda = Venda(
            cliente_id=form.cliente_id.data,
            veiculo_id=veiculo.id,
            vendedor_id=current_user.id,
            desconto=desconto,
            status='aberta',
            total=total,
            itens=itens,
        )
        db.session.add(venda)
        db.session.commit()
        flash(f'Venda #{venda.id} criada. Registre o pagamento para concluí-la.', 'success')
        return redirect(url_for('vendas.detalhe', venda_id=venda.id))

    return _render_nova_venda(form)


@vendas_bp.route('/<int:venda_id>')
@role_required('Vendedor', 'Admin')
def detalhe(venda_id):
    venda = _venda_do_usuario(venda_id)
    pagamento_form = PagamentoForm()
    pagamento_form.parcelas.data = 1
    return render_template(
        'vendas/detalhes.html',
        venda=venda,
        pagamento_form=pagamento_form,
    )


@vendas_bp.route('/<int:venda_id>/pagamentos', methods=['POST'])
@role_required('Vendedor', 'Admin')
def registrar_pagamento(venda_id):
    venda = _venda_do_usuario(venda_id, bloquear=True)
    form = PagamentoForm()

    if not form.validate_on_submit():
        flash('Dados de pagamento inválidos. Confira valor, método e parcelas.', 'danger')
        return redirect(url_for('vendas.detalhe', venda_id=venda.id))
    if venda.status != 'aberta':
        flash('Somente vendas abertas podem receber pagamentos.', 'danger')
        return redirect(url_for('vendas.detalhe', venda_id=venda.id))

    valor = form.valor.data.quantize(CENTAVO)
    restante = venda.valor_restante.quantize(CENTAVO)
    if valor <= 0 or valor > restante:
        flash(f'O pagamento deve ser maior que zero e não pode exceder {restante:.2f}.', 'danger')
        return redirect(url_for('vendas.detalhe', venda_id=venda.id))

    metodo = form.metodo.data
    parcelas = form.parcelas.data or 1
    if metodo != 'cartao_credito' and parcelas != 1:
        flash('Parcelamento só está disponível para cartão de crédito.', 'danger')
        return redirect(url_for('vendas.detalhe', venda_id=venda.id))

    quita_venda = valor == restante
    if quita_venda:
        quantidade_por_peca = defaultdict(int)
        for item in venda.itens:
            if item.tipo == 'peca':
                quantidade_por_peca[item.peca_id] += item.quantidade

        if quantidade_por_peca:
            pecas = Peca.query.filter(
                Peca.id.in_(sorted(quantidade_por_peca))
            ).order_by(Peca.id).with_for_update().all()
            pecas_por_id = {peca.id: peca for peca in pecas}
            for peca_id, quantidade in quantidade_por_peca.items():
                peca = pecas_por_id.get(peca_id)
                if peca is None or peca.estoque_atual < quantidade:
                    descricao = peca.descricao if peca else f'ID {peca_id}'
                    disponivel = peca.estoque_atual if peca else 0
                    flash(
                        f'Estoque insuficiente para {descricao}. Disponível: {disponivel}. '
                        'O pagamento não foi registrado.',
                        'danger',
                    )
                    return redirect(url_for('vendas.detalhe', venda_id=venda.id))

            for peca_id, quantidade in quantidade_por_peca.items():
                peca = pecas_por_id[peca_id]
                peca.estoque_atual -= quantidade
                db.session.add(MovimentacaoEstoque(
                    peca_id=peca.id,
                    tipo='Saida',
                    quantidade=quantidade,
                    descricao=f'Venda #{venda.id}',
                ))

    pagamento = Pagamento(
        venda_id=venda.id,
        valor=valor,
        metodo=metodo,
        parcelas=parcelas,
    )
    db.session.add(pagamento)
    db.session.add(Financeiro(
        venda_id=venda.id,
        tipo='Entrada',
        descricao=f'Recebimento da venda #{venda.id}',
        valor=valor,
        categoria='Venda',
        forma_pagamento=FORMAS_PAGAMENTO[metodo],
    ))
    if quita_venda:
        venda.status = 'paga'

    db.session.commit()
    if quita_venda:
        flash('Venda quitada, estoque atualizado e recebimento lançado no financeiro.', 'success')
    else:
        flash('Pagamento registrado e lançado no financeiro.', 'success')
    return redirect(url_for('vendas.detalhe', venda_id=venda.id))
