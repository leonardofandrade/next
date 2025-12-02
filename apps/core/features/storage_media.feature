# language: pt

Funcionalidade: Meio de Armazenamento
  Como um administrador do sistema
  Eu quero gerenciar meios de armazenamento
  Para controlar onde o material extraído é guardado

  Contexto:
    Dado que existe um usuário "Admin" com email "admin@example.com"
    E que existe uma agência de extração "PCCE"
    E que existe uma unidade de extração "UEXF"

  Cenário: Criar meio de armazenamento
    Quando eu crio um meio de armazenamento com os dados:
      | campo       | valor                                    |
      | acronym     | HD001                                    |
      | name        | HD Externo 001                           |
      | description | HD externo de 2TB para arquivos de casos |
    Então o meio de armazenamento deve ser criado com sucesso
    E deve estar vinculado à unidade "UEXF"

  Cenário: Representação string do meio de armazenamento
    Dado que existe um meio de armazenamento com:
      | acronym | HD001              |
      | name    | HD Externo 001     |
    Então a representação string deve ser "HD Externo 001"

  Cenário: Unicidade por unidade, sigla e nome
    Dado que existe um meio de armazenamento "HD001" na unidade "UEXF"
    Quando eu tento criar outro meio com os mesmos dados na mesma unidade
    Então deve gerar um erro de integridade

  Cenário: Múltiplos meios de armazenamento na mesma unidade
    Dado que existe um meio de armazenamento "HD001" na unidade "UEXF"
    Quando eu crio um meio de armazenamento "HD002" na unidade "UEXF"
    Então ambos os meios devem estar disponíveis para a unidade

  Cenário: Mesmo nome/sigla em unidades diferentes
    Dado que existe uma unidade de extração "UEXF2"
    E que existe um meio de armazenamento "HD001" na unidade "UEXF"
    Quando eu crio um meio de armazenamento "HD001" na unidade "UEXF2"
    Então ambos devem existir sem conflito
    E cada um deve estar vinculado à sua respectiva unidade
