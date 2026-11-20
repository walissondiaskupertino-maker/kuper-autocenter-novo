from datetime import datetime
from decimal import Decimal
from app.extensions import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


class Cliente(db.Model):
    __tablename__ = 'clientes'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    cpf_cnpj = db.Column(db.String(20), unique=True)
    telefone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    endereco = db.Column(db.Text)
    created_at = db.Column(db.TIMESTAMP, default=datetime.utcnow)
    updated_at = db.Column(db.TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)

    veiculos = db.relationship(
        'Veiculo',
        backref='cliente',
        lazy=True,
        passive_deletes=True
    )

    def __repr__(self):
        return f"<Cliente {self.nome}>"


class Veiculo(db.Model):
    __tablename__ = 'veiculos'

    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id', ondelete='RESTRICT', onupdate='CASCADE'), nullable=False)
    placa = db.Column(db.String(10), unique=True, nullable=False)
    modelo = db.Column(db.String(50), nullable=False)
    marca = db.Column(db.String(50), nullable=False)
    ano = db.Column(db.Integer)
    quilometragem = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.TIMESTAMP, default=datetime.utcnow)
    updated_at = db.Column(db.TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)

    ordens_servico = db.relationship('OrdemServico', backref='veiculo', lazy=True)

    def __repr__(self):
        return f"<Veiculo {self.marca} {self.modelo} - {self.placa}>"


class Mecanico(db.Model):
    __tablename__ = 'mecanicos'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    cpf = db.Column(db.String(14), unique=True)
    telefone = db.Column(db.String(20))
    especialidade = db.Column(db.String(80))
    ativo = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.TIMESTAMP, default=datetime.utcnow)

    ordens_servico = db.relationship('OrdemServico', backref='mecanico', lazy=True)

    def __repr__(self):
        return f"<Mecanico {self.nome}>"


class Peca(db.Model):
    __tablename__ = 'pecas'

    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(50), unique=True)
    descricao = db.Column(db.String(150), nullable=False)
    preco_custo = db.Column(db.Numeric(10, 2), nullable=False, default=0.00)
    preco_venda = db.Column(db.Numeric(10, 2), nullable=False, default=0.00)
    estoque_atual = db.Column(db.Integer, nullable=False, default=0)
    estoque_minimo = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.TIMESTAMP, default=datetime.utcnow)
    updated_at = db.Column(db.TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)

    movimentacoes = db.relationship('MovimentacaoEstoque', backref='peca', lazy=True)

    def __repr__(self):
        return f"<Peca {self.descricao}>"


class Servico(db.Model):
    __tablename__ = 'servicos'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.Text)
    preco_base = db.Column(db.Numeric(10, 2), nullable=False, default=0.00)
    ativo = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.TIMESTAMP, default=datetime.utcnow)

    def __repr__(self):
        return f"<Servico {self.nome}>"


class OrdemServico(db.Model):
    __tablename__ = 'ordens_servico'

    id = db.Column(db.Integer, primary_key=True)
    veiculo_id = db.Column(db.Integer, db.ForeignKey('veiculos.id', ondelete='RESTRICT', onupdate='CASCADE'), nullable=False)
    mecanico_id = db.Column(db.Integer, db.ForeignKey('mecanicos.id', ondelete='SET NULL', onupdate='CASCADE'), nullable=True)
    status = db.Column(db.Enum('Aberto', 'Em Andamento', 'Aguardando Peças', 'Concluído', 'Cancelado', name='status_os_enum'), nullable=False, default='Aberto')
    defeito_relatado = db.Column(db.Text)
    diagnostico = db.Column(db.Text)
    valor_total = db.Column(db.Numeric(10, 2), nullable=False, default=0.00)
    data_abertura = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    data_conclusao = db.Column(db.DateTime, nullable=True)
    updated_at = db.Column(db.TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)

    servicos = db.relationship('OsServico', backref='ordem_servico', cascade='all, delete-orphan', lazy=True)
    pecas = db.relationship('OsPeca', backref='ordem_servico', cascade='all, delete-orphan', lazy=True)
    movimentacoes = db.relationship('MovimentacaoEstoque', backref='ordem_servico', lazy=True)
    financeiro = db.relationship('Financeiro', backref='ordem_servico', lazy=True)

    def __repr__(self):
        return f"<OrdemServico #{self.id} - Status: {self.status}>"


class OsServico(db.Model):
    __tablename__ = 'os_servicos'

    id = db.Column(db.Integer, primary_key=True)
    os_id = db.Column(db.Integer, db.ForeignKey('ordens_servico.id', ondelete='CASCADE'), nullable=False)
    servico_id = db.Column(db.Integer, db.ForeignKey('servicos.id', ondelete='RESTRICT'), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False, default=1)
    preco_unitario = db.Column(db.Numeric(10, 2), nullable=False)
    subtotal = db.Column(
        db.Numeric(10, 2),
        db.Computed('quantidade * preco_unitario', persisted=True)
    )

    servico = db.relationship('Servico', lazy=True)

    def __repr__(self):
        return f"<OsServico OS #{self.os_id} - Servico #{self.servico_id}>"


class OsPeca(db.Model):
    __tablename__ = 'os_pecas'

    id = db.Column(db.Integer, primary_key=True)
    os_id = db.Column(db.Integer, db.ForeignKey('ordens_servico.id', ondelete='CASCADE'), nullable=False)
    peca_id = db.Column(db.Integer, db.ForeignKey('pecas.id', ondelete='RESTRICT'), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False, default=1)
    preco_unitario = db.Column(db.Numeric(10, 2), nullable=False)
    subtotal = db.Column(
        db.Numeric(10, 2),
        db.Computed('quantidade * preco_unitario', persisted=True)
    )

    peca = db.relationship('Peca', lazy=True)

    def __repr__(self):
        return f"<OsPeca OS #{self.os_id} - Peca #{self.peca_id}>"


class MovimentacaoEstoque(db.Model):
    __tablename__ = 'movimentacoes_estoque'

    id = db.Column(db.Integer, primary_key=True)
    peca_id = db.Column(db.Integer, db.ForeignKey('pecas.id', ondelete='RESTRICT'), nullable=False)
    os_id = db.Column(db.Integer, db.ForeignKey('ordens_servico.id', ondelete='SET NULL'), nullable=True)
    tipo = db.Column(db.Enum('Entrada', 'Saida', 'Ajuste', name='tipo_mov_enum'), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False)
    descricao = db.Column(db.String(255))
    data_movimentacao = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<MovimentacaoEstoque {self.tipo} - Peca #{self.peca_id}>"


class Financeiro(db.Model):
    __tablename__ = 'financeiro'

    id = db.Column(db.Integer, primary_key=True)
    os_id = db.Column(db.Integer, db.ForeignKey('ordens_servico.id', ondelete='SET NULL'), nullable=True)
    venda_id = db.Column(
        db.Integer,
        db.ForeignKey('vendas.id', ondelete='SET NULL'),
        nullable=True,
        index=True,
    )
    tipo = db.Column(db.Enum('Entrada', 'Saida', name='tipo_fin_enum'), nullable=False)
    descricao = db.Column(db.String(255), nullable=False)
    valor = db.Column(db.Numeric(10, 2), nullable=False)
    categoria = db.Column(db.String(80))
    forma_pagamento = db.Column(db.String(50))
    data_movimentacao = db.Column(db.DateTime, default=datetime.utcnow)
    venda = db.relationship('Venda', back_populates='lancamentos_financeiros')

    def __repr__(self):
        return f"<Financeiro {self.tipo} - R$ {self.valor}>"


# ============================================================
# CLASSE USUÁRIO (para sistema de login)
# ============================================================

class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuarios'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    senha = db.Column(db.String(255), nullable=False)
    perfil = db.Column(
        db.Enum('Admin', 'Vendedor', 'Mecanico', 'Recepcionista', name='perfil_enum'),
        nullable=False,
        default='Recepcionista',
    )
    ativo = db.Column(db.Boolean, default=True)
    mecanico_id = db.Column(
        db.Integer,
        db.ForeignKey('mecanicos.id', ondelete='SET NULL', onupdate='CASCADE'),
        unique=True,
        nullable=True
    )
    created_at = db.Column(db.TIMESTAMP, default=datetime.utcnow)
    mecanico = db.relationship(
        'Mecanico',
        backref=db.backref('usuario', uselist=False),
        uselist=False
    )
    vendas = db.relationship('Venda', back_populates='vendedor', lazy=True)
    
    def verificar_senha(self, senha):
        return check_password_hash(self.senha, senha)
    
    def __repr__(self):
        return f"<Usuario {self.email}>"


class Venda(db.Model):
    __tablename__ = 'vendas'
    __table_args__ = (
        db.CheckConstraint('desconto >= 0', name='ck_vendas_desconto_nao_negativo'),
        db.CheckConstraint('total >= 0', name='ck_vendas_total_nao_negativo'),
    )

    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(
        db.Integer,
        db.ForeignKey('clientes.id', ondelete='RESTRICT'),
        nullable=False,
        index=True,
    )
    veiculo_id = db.Column(
        db.Integer,
        db.ForeignKey('veiculos.id', ondelete='RESTRICT'),
        nullable=False,
        index=True,
    )
    vendedor_id = db.Column(
        db.Integer,
        db.ForeignKey('usuarios.id', ondelete='RESTRICT'),
        nullable=False,
        index=True,
    )
    data = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    desconto = db.Column(db.Numeric(10, 2), nullable=False, default=Decimal('0.00'))
    status = db.Column(
        db.Enum('aberta', 'paga', 'cancelada', name='status_venda_enum'),
        nullable=False,
        default='aberta',
    )
    total = db.Column(db.Numeric(10, 2), nullable=False, default=Decimal('0.00'))

    cliente = db.relationship('Cliente')
    veiculo = db.relationship('Veiculo')
    vendedor = db.relationship('Usuario', back_populates='vendas')
    itens = db.relationship(
        'ItemVenda',
        back_populates='venda',
        cascade='all, delete-orphan',
        lazy=True,
    )
    pagamentos = db.relationship(
        'Pagamento',
        back_populates='venda',
        cascade='all, delete-orphan',
        lazy=True,
        order_by='Pagamento.data, Pagamento.id',
    )
    lancamentos_financeiros = db.relationship(
        'Financeiro',
        back_populates='venda',
        lazy=True,
    )

    @property
    def valor_restante(self):
        total_pago = sum(
            (pagamento.valor for pagamento in self.pagamentos),
            start=Decimal('0.00'),
        )
        return max(Decimal('0.00'), (self.total or Decimal('0.00')) - total_pago)

    def __repr__(self):
        return f"<Venda #{self.id} - {self.status}>"


class ItemVenda(db.Model):
    __tablename__ = 'itens_venda'
    __table_args__ = (
        db.CheckConstraint('quantidade > 0', name='ck_itens_venda_quantidade_positiva'),
        db.CheckConstraint(
            'preco_unitario >= 0',
            name='ck_itens_venda_preco_nao_negativo',
        ),
        db.CheckConstraint(
            "(tipo = 'peca' AND peca_id IS NOT NULL AND servico_id IS NULL) OR "
            "(tipo = 'servico' AND servico_id IS NOT NULL AND peca_id IS NULL)",
            name='ck_itens_venda_tipo_referencia',
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    venda_id = db.Column(
        db.Integer,
        db.ForeignKey('vendas.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    tipo = db.Column(db.Enum('peca', 'servico', name='tipo_item_venda_enum'), nullable=False)
    peca_id = db.Column(
        db.Integer,
        db.ForeignKey('pecas.id', ondelete='RESTRICT'),
        nullable=True,
    )
    servico_id = db.Column(
        db.Integer,
        db.ForeignKey('servicos.id', ondelete='RESTRICT'),
        nullable=True,
    )
    quantidade = db.Column(db.Integer, nullable=False)
    preco_unitario = db.Column(db.Numeric(10, 2), nullable=False)

    venda = db.relationship('Venda', back_populates='itens')
    peca = db.relationship('Peca')
    servico = db.relationship('Servico')

    @property
    def subtotal(self):
        return self.quantidade * self.preco_unitario


class Pagamento(db.Model):
    __tablename__ = 'pagamentos'
    __table_args__ = (
        db.CheckConstraint('valor > 0', name='ck_pagamentos_valor_positivo'),
        db.CheckConstraint('parcelas BETWEEN 1 AND 12', name='ck_pagamentos_parcelas'),
    )

    id = db.Column(db.Integer, primary_key=True)
    venda_id = db.Column(
        db.Integer,
        db.ForeignKey('vendas.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    valor = db.Column(db.Numeric(10, 2), nullable=False)
    metodo = db.Column(
        db.Enum(
            'dinheiro',
            'pix',
            'cartao_credito',
            'cartao_debito',
            name='metodo_pagamento_venda_enum',
        ),
        nullable=False,
    )
    parcelas = db.Column(db.Integer, nullable=False, default=1)
    data = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    venda = db.relationship('Venda', back_populates='pagamentos')