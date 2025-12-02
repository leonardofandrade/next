# language: pt

Funcionalidade: Agência de Extração de Dados
  Como um administrador do sistema
  Eu quero gerenciar agências de extração de dados
  Para organizar as unidades de extração

  Contexto:
    Dado que existe um usuário "Admin" com email "admin@example.com"

  Cenário: Criar agência de extração
    Quando eu crio uma agência de extração com os dados:
      | campo              | valor                              |
      | acronym            | PCCE                               |
      | name               | Perícia Forense do Ceará           |
      | incharge_name      | Dr. João Silva                     |
      | incharge_position  | Perito Criminal                    |
    Então a agência deve ser criada com sucesso
    E o campo "created_by" deve ser preenchido
    E o campo "created_at" deve ser preenchido

  Cenário: Agência com logo principal
    Dado que existe uma agência de extração "PCCE"
    Quando eu adiciono um logo principal à agência
    Então o método "has_main_logo" deve retornar True
    E o método "get_main_logo_base64" deve retornar uma string base64 válida

  Cenário: Detectar tipo MIME do logo PNG
    Dado que existe uma agência de extração "PCCE"
    Quando eu adiciono um logo PNG à agência
    Então o método "get_main_logo_mime_type" deve retornar "image/png"

  Cenário: Detectar tipo MIME do logo JPEG
    Dado que existe uma agência de extração "PCCE"
    Quando eu adiciono um logo JPEG à agência
    Então o método "get_main_logo_mime_type" deve retornar "image/jpeg"

  Cenário: Representação string da agência
    Dado que existe uma agência de extração com:
      | acronym | PCCE                      |
      | name    | Perícia Forense do Ceará  |
    Então a representação string deve ser "PCCE"

  Cenário: Unicidade de agência por sigla e nome
    Dado que existe uma agência de extração com:
      | acronym | PCCE                      |
      | name    | Perícia Forense do Ceará  |
    Quando eu tento criar outra agência com os mesmos dados
    Então deve gerar um erro de integridade
