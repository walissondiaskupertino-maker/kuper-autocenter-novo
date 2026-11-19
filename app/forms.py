from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, DecimalField, SelectField, TextAreaField, BooleanField, SubmitField, PasswordField
from wtforms.validators import DataRequired, Length, NumberRange, Optional, Email


class CadastroForm(FlaskForm):
    nome = StringField(
        'Nome Completo',
        filters=[lambda value: value.strip() if value else value],
        validators=[
            DataRequired(message='Informe seu nome.'),
            Length(max=100, message='O nome deve ter no máximo 100 caracteres.')
        ]
    )
    email = StringField(
        'E-mail',
        filters=[lambda value: value.strip().lower() if value else value],
        validators=[
            DataRequired(message='Informe seu e-mail.'),
            Email(message='Informe um e-mail válido.'),
            Length(max=100, message='O e-mail deve ter no máximo 100 caracteres.')
        ]
    )
    perfil = SelectField(
        'Perfil de Acesso',
        choices=[('Recepcionista', 'Recepcionista'), ('Mecanico', 'Mecânico')],
        validators=[DataRequired(message='Selecione um perfil.')]
    )
    senha = PasswordField(
        'Senha',
        validators=[
            DataRequired(message='Informe uma senha.'),
            Length(
                min=6,
                max=128,
                message='A senha deve ter entre 6 e 128 caracteres.'
            )
        ]
    )


class ClienteForm(FlaskForm):
    nome = StringField('Nome', validators=[DataRequired(), Length(max=100)])
    cpf_cnpj = StringField('CPF/CNPJ', validators=[Optional(), Length(max=20)])
    telefone = StringField('Telefone', validators=[Optional(), Length(max=20)])
    email = StringField('E-mail', validators=[Optional(), Email(), Length(max=100)])
    endereco = TextAreaField('Endereço', validators=[Optional()])
    submit = SubmitField('Salvar')


class VeiculoForm(FlaskForm):
    cliente_id = SelectField('Cliente', coerce=int, validators=[DataRequired()])
    placa = StringField('Placa', validators=[DataRequired(), Length(max=10)])
    modelo = StringField('Modelo', validators=[DataRequired(), Length(max=50)])
    marca = StringField('Marca', validators=[DataRequired(), Length(max=50)])
    ano = IntegerField('Ano', validators=[Optional()])
    quilometragem = IntegerField('Quilometragem', validators=[Optional(), NumberRange(min=0)])
    submit = SubmitField('Salvar')


class MecanicoForm(FlaskForm):
    nome = StringField('Nome', validators=[DataRequired(), Length(max=100)])
    cpf = StringField('CPF', validators=[Optional(), Length(max=14)])
    telefone = StringField('Telefone', validators=[Optional(), Length(max=20)])
    especialidade = StringField('Especialidade', validators=[Optional(), Length(max=80)])
    ativo = BooleanField('Ativo', default=True)
    submit = SubmitField('Salvar')


class PecaForm(FlaskForm):
    codigo = StringField('Código', validators=[Optional(), Length(max=50)])
    descricao = StringField('Descrição', validators=[DataRequired(), Length(max=150)])
    preco_custo = DecimalField('Preço de Custo', places=2, validators=[Optional()])
    preco_venda = DecimalField('Preço de Venda', places=2, validators=[DataRequired()])
    estoque_atual = IntegerField('Estoque Atual', validators=[Optional(), NumberRange(min=0)])
    estoque_minimo = IntegerField('Estoque Mínimo', validators=[Optional(), NumberRange(min=0)])
    submit = SubmitField('Salvar')


class ServicoForm(FlaskForm):
    nome = StringField('Nome', validators=[DataRequired(), Length(max=100)])
    descricao = TextAreaField('Descrição', validators=[Optional()])
    preco_base = DecimalField('Preço Base', places=2, validators=[DataRequired()])
    ativo = BooleanField('Ativo', default=True)
    submit = SubmitField('Salvar')


class OrdemServicoForm(FlaskForm):
    veiculo_id = SelectField('Veículo', coerce=int, validators=[DataRequired()])
    mecanico_id = SelectField('Mecânico', coerce=int, validators=[Optional()])
    status = SelectField('Status', choices=[
        ('Aberto', 'Aberto'),
        ('Em Andamento', 'Em Andamento'),
        ('Aguardando Peças', 'Aguardando Peças'),
        ('Concluído', 'Concluído'),
        ('Cancelado', 'Cancelado')
    ], validators=[DataRequired()])
    defeito_relatado = TextAreaField('Defeito Relatado', validators=[Optional()])
    diagnostico = TextAreaField('Diagnóstico', validators=[Optional()])
    submit = SubmitField('Salvar')


class FinanceiroForm(FlaskForm):
    tipo = SelectField('Tipo', choices=[('Entrada', 'Entrada'), ('Saida', 'Saída')], validators=[DataRequired()])
    descricao = StringField('Descrição', validators=[DataRequired(), Length(max=255)])
    valor = DecimalField('Valor', places=2, validators=[DataRequired()])
    categoria = StringField('Categoria', validators=[Optional(), Length(max=80)])
    forma_pagamento = StringField('Forma de Pagamento', validators=[Optional(), Length(max=50)])
    submit = SubmitField('Salvar')