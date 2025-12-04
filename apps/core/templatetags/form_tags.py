"""
Template tags para formulários Django com estilização centralizada

Este módulo fornece template tags e filters para adicionar automaticamente
a classe CSS 'form-label' aos labels de campos de formulário Django.

ABORDAGEM RECOMENDADA: Use o filter `form_label_class` que é mais simples e direto.

Exemplo de uso:

    # No template:
    {% load form_tags %}
    
    # Opção 1: Usando o filter (RECOMENDADO)
    {{ form.campo|form_label_class }}
    {{ form.campo }}
    
    # Opção 2: Usando a template tag (para casos mais complexos)
    {% form_label form.campo %}
    {{ form.campo }}
"""
from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag
def form_label(field, attrs=None, label_suffix=None):
    """
    Template tag que renderiza o label_tag de um campo com a classe 'form-label'.
    
    Uso no template:
        {% load form_tags %}
        {% form_label form.campo %}
        
    Com classes adicionais (usando a template tag):
        {% form_label form.campo attrs='class:form-label fw-bold' %}
    
    Nota: Para uso simples, prefira o filter `form_label_class`.
    """
    if not hasattr(field, 'label_tag'):
        return ''
    
    if attrs is None:
        attrs = {}
    
    # Se attrs for uma string, converte para dicionário
    if isinstance(attrs, str):
        attrs_dict = {}
        for attr in attrs.split():
            if ':' in attr:
                key, value = attr.split(':', 1)
                attrs_dict[key] = value
            elif attr.startswith('class:'):
                attrs_dict['class'] = attr.split(':', 1)[1]
            else:
                attrs_dict['class'] = attrs_dict.get('class', '') + ' ' + attr
        attrs = attrs_dict
    
    # Garante que form-label está presente
    if 'class' in attrs:
        classes = attrs['class'].split()
        if 'form-label' not in classes:
            classes.append('form-label')
        attrs['class'] = ' '.join(classes)
    else:
        attrs['class'] = 'form-label'
    
    return mark_safe(field.label_tag(attrs=attrs, label_suffix=label_suffix))


@register.filter
def form_label_class(field):
    """
    Filter que retorna o label_tag de um campo com a classe 'form-label'.
    
    Esta é a abordagem RECOMENDADA para adicionar a classe 'form-label' aos labels.
    
    Uso no template:
        {% load form_tags %}
        {{ form.campo|form_label_class }}
        {{ form.campo }}
    
    Exemplo completo:
        <div class="mb-3">
            {{ form.nome|form_label_class }}
            {{ form.nome }}
            {% if form.nome.errors %}
                <div class="invalid-feedback d-block">
                    {{ form.nome.errors }}
                </div>
            {% endif %}
        </div>
    """
    if not hasattr(field, 'label_tag'):
        return ''
    
    # Renderiza o label_tag com a classe form-label
    attrs = {'class': 'form-label'}
    return mark_safe(field.label_tag(attrs=attrs))

