# language: pt

Funcionalidade: Configurações Gerais do Sistema
  Como um administrador do sistema
  Eu quero gerenciar configurações gerais
  Para personalizar o comportamento do sistema

  Contexto:
    Dado que existe um usuário "Admin" com email "admin@example.com"
    E que existe uma agência de extração "PCCE"

  Cenário: Criar configurações gerais do sistema
    Quando eu crio configurações gerais com os dados:
      | campo              | valor                                |
      | system_name        | Sistema de Extração Forense          |
      | system_version     | 1.0.0                                |
      | system_description | Sistema para gestão de extrações     |
      | primary_color      | #1E3A8A                              |
      | secondary_color    | #3B82F6                              |
    Então as configurações devem ser criadas com sucesso
    E devem estar vinculadas à agência "PCCE"

  Cenário: Ativar modo de manutenção
    Dado que existem configurações gerais do sistema
    Quando eu ativo o modo de manutenção com a mensagem:
      """
      Sistema em manutenção programada.
      Retorno previsto para 01/01/2025 às 10:00.
      """
    Então o campo "maintenance_mode" deve ser True
    E a mensagem de manutenção deve estar definida

  Cenário: Desativar modo de manutenção
    Dado que existem configurações gerais com modo de manutenção ativo
    Quando eu desativo o modo de manutenção
    Então o campo "maintenance_mode" deve ser False

  Cenário: Configurar backup automático diário
    Dado que existem configurações gerais do sistema
    Quando eu configuro backup automático com:
      | campo            | valor  |
      | backup_enabled   | True   |
      | backup_frequency | daily  |
    Então o backup automático deve estar ativo
    E a frequência deve ser "daily"

  Cenário: Configurar backup automático semanal
    Dado que existem configurações gerais do sistema
    Quando eu configuro backup automático com:
      | campo            | valor  |
      | backup_enabled   | True   |
      | backup_frequency | weekly |
    Então a frequência deve ser "weekly"

  Cenário: Configurar backup automático mensal
    Dado que existem configurações gerais do sistema
    Quando eu configuro backup automático com:
      | campo            | valor   |
      | backup_enabled   | True    |
      | backup_frequency | monthly |
    Então a frequência deve ser "monthly"

  Cenário: Definir cores do tema
    Dado que existem configurações gerais do sistema
    Quando eu defino as cores:
      | campo           | valor   |
      | primary_color   | #FF0000 |
      | secondary_color | #00FF00 |
    Então as cores devem estar salvas corretamente

  Cenário: Unicidade de configurações por agência
    Dado que existem configurações gerais vinculadas à agência "PCCE"
    Quando eu tento criar outras configurações gerais para a mesma agência
    Então deve gerar um erro de integridade

  Cenário: Configurações com valores padrão
    Quando eu crio configurações gerais mínimas
    Então o campo "maintenance_mode" deve ser False
    E o campo "backup_enabled" deve ser False
    E o campo "backup_frequency" deve ser "daily"
    E deve existir uma mensagem padrão de manutenção
