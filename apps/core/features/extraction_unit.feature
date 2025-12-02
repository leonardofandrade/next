# language: pt

Funcionalidade: Unidade de Extração
  Como um administrador do sistema
  Eu quero gerenciar unidades de extração
  Para organizar as operações de extração de dados

  Contexto:
    Dado que existe um usuário "Admin" com email "admin@example.com"
    E que existe uma agência de extração "PCCE"

  Cenário: Criar unidade de extração
    Quando eu crio uma unidade de extração com os dados:
      | campo            | valor                   |
      | acronym          | UEXF                    |
      | name             | Unidade de Extração     |
      | primary_phone    | (85) 3101-2345          |
      | primary_email    | uexf@pcce.ce.gov.br     |
      | incharge_name    | Dr. Maria Santos        |
      | incharge_position| Perito Chefe            |
    Então a unidade deve ser criada com sucesso
    E deve estar vinculada à agência "PCCE"

  Cenário: Unidade de extração com endereço completo
    Quando eu crio uma unidade de extração com endereço:
      | campo          | valor                    |
      | address_line1  | Rua Teste                |
      | address_number | 123                      |
      | address_line2  | Sala 456                 |
      | neighborhood   | Centro                   |
      | city_name      | Fortaleza                |
      | postal_code    | 60000-000                |
      | state_name     | Ceará                    |
      | country_name   | Brasil                   |
    Então todos os campos de endereço devem estar preenchidos

  Cenário: Configurar template de email de resposta
    Dado que existe uma unidade de extração "UEXF"
    Quando eu configuro o template de email com:
      | campo                 | valor                                |
      | reply_email_template  | Prezado {nome}, sua solicitação...   |
      | reply_email_subject   | Resposta à Solicitação #{numero}     |
    Então os templates devem ser salvos com sucesso

  Cenário: Representação string da unidade
    Dado que existe uma unidade de extração com:
      | acronym | UEXF                |
      | name    | Unidade de Extração |
    Então a representação string deve ser "UEXF"

  Cenário: Contatos secundários da unidade
    Dado que existe uma unidade de extração "UEXF"
    Quando eu adiciono contatos secundários:
      | campo            | valor                      |
      | secondary_phone  | (85) 3101-9999             |
      | secondary_email  | backup@pcce.ce.gov.br      |
    Então os contatos secundários devem estar disponíveis
