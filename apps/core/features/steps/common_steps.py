"""
Step definitions para os testes BDD do app core.

Este arquivo contém os steps básicos que serão usados nos testes
dos models do app core.
"""

from behave import given, when, then
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.test import TestCase
import pytest


# ==================== Steps Comuns ====================

@given('que existe um usuário "{nome}" com email "{email}"')
def step_criar_usuario(context, nome, email):
    """Cria um usuário para usar nos testes"""
    context.user, created = User.objects.get_or_create(
        email=email,
        defaults={
            'username': email.split('@')[0],
            'first_name': nome.split()[0],
            'last_name': ' '.join(nome.split()[1:]) if len(nome.split()) > 1 else '',
        }
    )
    if created:
        context.user.set_password('senha123')
        context.user.save()


@then('deve gerar um erro de integridade')
def step_verificar_erro_integridade(context):
    """Verifica se foi gerado um erro de integridade"""
    assert hasattr(context, 'exception'), "Nenhuma exceção foi capturada"
    assert isinstance(context.exception, IntegrityError), \
        f"Esperava IntegrityError, mas obteve {type(context.exception)}"


# ==================== Steps para AuditedModel ====================

@when('eu crio uma nova instância de um model que herda de AuditedModel')
def step_criar_instancia_audited_model(context):
    """Cria uma instância de teste de AuditedModel"""
    # Este step será implementado de forma específica em cada teste
    pass


@then('o campo "{campo}" deve ser preenchido automaticamente')
def step_verificar_campo_preenchido(context, campo):
    """Verifica se um campo foi preenchido automaticamente"""
    assert hasattr(context, 'instance'), "Nenhuma instância foi criada"
    valor = getattr(context.instance, campo)
    assert valor is not None, f"O campo {campo} não foi preenchido"


@then('o campo "{campo}" deve ser preenchido com o usuário atual')
def step_verificar_campo_usuario(context, campo):
    """Verifica se um campo foi preenchido com o usuário atual"""
    assert hasattr(context, 'instance'), "Nenhuma instância foi criada"
    assert hasattr(context, 'user'), "Nenhum usuário foi definido no contexto"
    valor = getattr(context.instance, campo)
    assert valor == context.user, f"O campo {campo} não foi preenchido com o usuário correto"


@then('o campo "{campo}" deve ser {valor:d}')
def step_verificar_campo_inteiro(context, campo, valor):
    """Verifica se um campo inteiro tem o valor esperado"""
    assert hasattr(context, 'instance'), "Nenhuma instância foi criada"
    campo_valor = getattr(context.instance, campo)
    assert campo_valor == valor, f"Esperava {valor}, mas obteve {campo_valor}"


# ==================== Steps para verificação de campos ====================

@then('deve ter os campos')
@then('deve ter os campos de informação do dispositivo')
@then('deve ter os campos de status')
@then('deve ter os campos de senha')
@then('deve ter os campos de condição física')
@then('deve ter os campos de acessórios')
@then('deve ter os campos de segurança')
def step_verificar_campos_existem(context):
    """Verifica se os campos especificados existem no model"""
    assert hasattr(context, 'instance'), "Nenhuma instância foi criada"
    for row in context.table:
        campo = row['campo']
        assert hasattr(context.instance, campo), f"O campo {campo} não existe no model"


# ==================== Steps genéricos para criação e verificação ====================

@then('a representação string deve ser "{esperado}"')
def step_verificar_str(context, esperado):
    """Verifica a representação string do objeto"""
    assert hasattr(context, 'instance'), "Nenhuma instância foi criada"
    assert str(context.instance) == esperado, \
        f"Esperava '{esperado}', mas obteve '{str(context.instance)}'"


@then('o campo "{campo}" deve ser {valor}')
def step_verificar_campo_booleano(context, campo, valor):
    """Verifica se um campo booleano tem o valor esperado"""
    assert hasattr(context, 'instance'), "Nenhuma instância foi criada"
    valor_esperado = valor.lower() == 'true'
    campo_valor = getattr(context.instance, campo)
    assert campo_valor == valor_esperado, \
        f"Esperava {valor_esperado}, mas obteve {campo_valor}"


@then('o campo "{campo}" deve ter o valor "{valor}"')
def step_verificar_campo_string(context, campo, valor):
    """Verifica se um campo string tem o valor esperado"""
    assert hasattr(context, 'instance'), "Nenhuma instância foi criada"
    campo_valor = getattr(context.instance, campo)
    assert campo_valor == valor, f"Esperava '{valor}', mas obteve '{campo_valor}'"


# ==================== Steps para testes de métodos ====================

@when('eu chamo o método "{metodo}"')
def step_chamar_metodo(context, metodo):
    """Chama um método do objeto e armazena o resultado"""
    assert hasattr(context, 'instance'), "Nenhuma instância foi criada"
    method = getattr(context.instance, metodo)
    context.result = method() if callable(method) else method


@then('o resultado deve ser "{esperado}"')
def step_verificar_resultado_string(context, esperado):
    """Verifica se o resultado é igual ao esperado"""
    assert hasattr(context, 'result'), "Nenhum resultado foi armazenado"
    assert context.result == esperado, \
        f"Esperava '{esperado}', mas obteve '{context.result}'"


@then('deve retornar {esperado}')
def step_verificar_resultado_none_ou_valor(context, esperado):
    """Verifica se o resultado é None ou outro valor"""
    assert hasattr(context, 'result'), "Nenhum resultado foi armazenado"
    if esperado.lower() == 'none':
        assert context.result is None, f"Esperava None, mas obteve {context.result}"
    elif esperado.lower() == 'true':
        assert context.result is True, f"Esperava True, mas obteve {context.result}"
    elif esperado.lower() == 'false':
        assert context.result is False, f"Esperava False, mas obteve {context.result}"


# Placeholder para implementações específicas que serão adicionadas conforme necessário
