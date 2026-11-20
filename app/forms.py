import re

from flask_wtf import FlaskForm
from wtforms import (
    StringField, IntegerField, DecimalField, SelectField, TextAreaField,
    BooleanField, SubmitField, PasswordField,
)
from wtforms.validators import (
    DataRequired, Length, NumberRange, Optional, Email, ValidationError,
)


class DecimalCommaField(DecimalField):
    def process_formdata(self, valuelist):
        if valuelist and isinstance(valuelist[0], str) and ',' in valuelist[0]:
            valuelist = [valuelist[0].replace('.', '').replace(',', '.')]
        super().process_formdata(valuelist)


def _validate_document_digits(_, field):
    if field.data:
        digit_count = len(re.sub(r'\D', '', field.data))
        if digit_count not in (11, 14):
            raise ValidationError('Informe um CPF com 11 dígitos ou CNPJ com 14 dígitos.')


def _validate_cpf_digits(_, field):
    if field.data and len(re.sub(r'\D', '', field.data)) != 11:
        raise ValidationError('Informe um CPF com 11 dígitos.')


def _validate_phone_digits(_, field):
    if field.data and len(re.sub(r'\D', '', field.data)) not in (10, 11, 12, 13):
        raise ValidationError('Informe um telefone com DDD e número válidos.')


def _validate_brazilian_plate(_, field):
    if field.data and not re.fullmatch(r'[A-Z]{3}-?[0-9][A-Z0-9][0-9]{2}', field.data):
        raise ValidationError('Informe uma placa válida (ABC1234 ou ABC1D23).')


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
    nome = StringField(
        'Nome',
        filters=[lambda value: value.strip() if value else value],
        validators=[DataRequired(), Length(max=100)],
    )
    cpf_cnpj = StringField(
        'CPF/CNPJ',
        filters=[lambda value: value.strip() if value else value],
        validators=[Optional(), Length(max=20), _validate_document_digits],
    )
    telefone = StringField(
        'Telefone',
        filters=[lambda value: value.strip() if value else value],
        validators=[Optional(), Length(max=20), _validate_phone_digits],
    )
    email = StringField(
        'E-mail',
        filters=[lambda value: value.strip().lower() if value else value],
        validators=[Optional(), Email(), Length(max=100)],
    )
    endereco = TextAreaField(
        'Endereço',
        filters=[lambda value: value.strip() if value else value],
        validators=[Optional()],
    )
    submit = SubmitField('Salvar')


class VeiculoForm(FlaskForm):
    cliente_id = SelectField('Cliente', coerce=int, validators=[DataRequired()])
    placa = StringField(
        'Placa',
        filters=[lambda value: value.strip().upper() if value else value],
        validators=[DataRequired(), Length(max=8), _validate_brazilian_plate],
    )
    modelo = StringField(
        'Modelo',
        filters=[lambda value: value.strip() if value else value],
        validators=[DataRequired(), Length(max=50)],
    )
    marca = StringField(
        'Marca',
        filters=[lambda value: value.strip() if value else value],
        validators=[DataRequired(), Length(max=50)],
    )
    ano = IntegerField('Ano', validators=[Optional(), NumberRange(min=1886, max=2100)])
    quilometragem = IntegerField(
        'Quilometragem',
        validators=[Optional(), NumberRange(min=0)],
    )
    submit = SubmitField('Salvar')


class MecanicoForm(FlaskForm):
    nome = StringField(
        'Nome',
        filters=[lambda value: value.strip() if value else value],
        validators=[DataRequired(), Length(max=100)],
    )
    cpf = StringField(
        'CPF',
        filters=[lambda value: value.strip() if value else value],
        validators=[Optional(), Length(max=14), _validate_cpf_digits],
    )
    telefone = StringField(
        'Telefone',
        filters=[lambda value: value.strip() if value else value],
        validators=[Optional(), Length(max=20), _validate_phone_digits],
    )
    especialidade = StringField(
        'Especialidade',
        filters=[lambda value: value.strip() if value else value],
        validators=[Optional(), Length(max=80)],
    )
    ativo = BooleanField('Ativo', default=True)
    submit = SubmitField('Salvar')


class PecaForm(FlaskForm):
    codigo = StringField(
        'Código',
        filters=[lambda value: value.strip().upper() if value else value],
        validators=[Optional(), Length(max=50)],
    )
    descricao = StringField(
        'Descrição',
        filters=[lambda value: value.strip() if value else value],
        validators=[DataRequired(), Length(max=150)],
    )
    preco_custo = DecimalCommaField(
        'Preço de Custo',
        places=2,
        validators=[Optional(), NumberRange(min=0)],
    )
    preco_venda = DecimalCommaField(
        'Preço de Venda',
        places=2,
        validators=[DataRequired(), NumberRange(min=0)],
    )
    estoque_atual = IntegerField('Estoque Atual', validators=[Optional(), NumberRange(min=0)])
    estoque_minimo = IntegerField('Estoque Mínimo', validators=[Optional(), NumberRange(min=0)])
    submit = SubmitField('Salvar')


class ServicoForm(FlaskForm):
    nome = StringField(
        'Nome',
        filters=[lambda value: value.strip() if value else value],
        validators=[DataRequired(), Length(max=100)],
    )
    descricao = TextAreaField(
        'Descrição',
        filters=[lambda value: value.strip() if value else value],
        validators=[Optional()],
    )
    preco_base = DecimalCommaField(
        'Preço Base',
        places=2,
        validators=[DataRequired(), NumberRange(min=0)],
    )
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


class DiagnosticoForm(FlaskForm):
    diagnostico = TextAreaField(
        'Diagnóstico técnico',
        validators=[Optional(), Length(max=5000)]
    )


class FinanceiroForm(FlaskForm):
    tipo = SelectField('Tipo', choices=[('Entrada', 'Entrada'), ('Saida', 'Saída')], validators=[DataRequired()])
    descricao = StringField('Descrição', validators=[DataRequired(), Length(max=255)])
    valor = DecimalField('Valor', places=2, validators=[DataRequired()])
    categoria = StringField('Categoria', validators=[Optional(), Length(max=80)])
    forma_pagamento = StringField('Forma de Pagamento', validators=[Optional(), Length(max=50)])
    submit = SubmitField('Salvar')