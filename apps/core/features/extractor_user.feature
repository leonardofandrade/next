# language: pt

Funcionalidade: Usuário Extrator
  Como um administrador do sistema
  Eu quero gerenciar usuários extratores
  Para controlar quem pode realizar extrações

  Contexto:
    Dado que existe um usuário "Admin" com email "admin@example.com"
    E que existe uma agência de extração "PCCE"
    E que existe um usuário "João Perito" com email "joao.perito@pcce.ce.gov.br"

  Cenário: Criar usuário extrator
    Quando eu crio um usuário extrator vinculando:
      | campo              | valor       |
      | user               | João Perito |
      | extraction_agency  | PCCE        |
    Então o usuário extrator deve ser criado com sucesso
    E deve estar vinculado ao usuário "João Perito"
    E deve estar vinculado à agência "PCCE"

  Cenário: Representação string do usuário extrator
    Dado que existe um usuário extrator para "João Perito" na agência "PCCE"
    Então a representação string deve conter o nome completo do usuário
    E deve conter a sigla da agência

  Cenário: Unicidade de usuário extrator por usuário e agência
    Dado que existe um usuário extrator para "João Perito" na agência "PCCE"
    Quando eu tento criar outro usuário extrator com os mesmos dados
    Então deve gerar um erro de integridade

  Cenário: Múltiplos usuários extratores na mesma agência
    Dado que existe um usuário "Maria Perita" com email "maria.perita@pcce.ce.gov.br"
    E que existe um usuário extrator para "João Perito" na agência "PCCE"
    Quando eu crio um usuário extrator para "Maria Perita" na agência "PCCE"
    Então ambos os extratores devem estar ativos
    E devem estar vinculados à mesma agência
