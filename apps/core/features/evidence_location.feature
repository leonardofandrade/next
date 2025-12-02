# language: pt

Funcionalidade: Local de Armazenamento de Evidências
  Como um administrador do sistema
  Eu quero gerenciar locais de armazenamento de evidências
  Para controlar onde as evidências físicas são guardadas

  Contexto:
    Dado que existe um usuário "Admin" com email "admin@example.com"
    E que existe uma agência de extração "PCCE"
    E que existe uma unidade de extração "UEXF"

  Cenário: Criar local de armazenamento do tipo "Para fazer"
    Quando eu crio um local de armazenamento com os dados:
      | campo       | valor                         |
      | type        | to_do                         |
      | name        | Sala 001                      |
      | description | Sala de recepção de materiais |
      | shelf_name  | Prateleira A                  |
      | slot_name   | Slot 01                       |
    Então o local deve ser criado com sucesso
    E deve ter o tipo "to_do"
    E deve estar vinculado à unidade "UEXF"

  Cenário: Criar local de armazenamento do tipo "Em progresso"
    Quando eu crio um local de armazenamento com os dados:
      | campo       | valor                           |
      | type        | in_progress                     |
      | name        | Sala 002                        |
      | description | Sala de processamento de dados  |
    Então o local deve ser criado com sucesso
    E deve ter o tipo "in_progress"

  Cenário: Criar local de armazenamento do tipo "Finalizado"
    Quando eu crio um local de armazenamento com os dados:
      | campo       | valor                        |
      | type        | done                         |
      | name        | Sala 003                     |
      | description | Sala de armazenamento final  |
    Então o local deve ser criado com sucesso
    E deve ter o tipo "done"

  Cenário: Local com informações de prateleira e slot
    Quando eu crio um local de armazenamento com:
      | campo      | valor        |
      | name       | Armário 001  |
      | shelf_name | Prateleira B |
      | slot_name  | Slot 05      |
    Então o local deve ter prateleira "Prateleira B"
    E deve ter slot "Slot 05"

  Cenário: Unicidade por unidade e nome
    Dado que existe um local de armazenamento "Sala 001" na unidade "UEXF"
    Quando eu tento criar outro local com o mesmo nome na mesma unidade
    Então deve gerar um erro de integridade

  Cenário: Múltiplos locais na mesma unidade
    Dado que existe um local de armazenamento "Sala 001" na unidade "UEXF"
    Quando eu crio um local de armazenamento "Sala 002" na unidade "UEXF"
    Então ambos os locais devem estar disponíveis para a unidade

  Cenário: Filtrar locais por tipo
    Dado que existem locais de armazenamento:
      | name     | type        |
      | Sala 001 | to_do       |
      | Sala 002 | in_progress |
      | Sala 003 | done        |
    Quando eu filtro locais do tipo "to_do"
    Então devo obter apenas "Sala 001"

  Cenário: Mesmo nome em unidades diferentes
    Dado que existe uma unidade de extração "UEXF2"
    E que existe um local de armazenamento "Sala 001" na unidade "UEXF"
    Quando eu crio um local de armazenamento "Sala 001" na unidade "UEXF2"
    Então ambos devem existir sem conflito
    E cada um deve estar vinculado à sua respectiva unidade
