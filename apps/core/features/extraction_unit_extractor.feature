# language: pt

Funcionalidade: Extrator de Unidade de Extração
  Como um administrador do sistema
  Eu quero vincular extratores às unidades de extração
  Para gerenciar quem trabalha em cada unidade

  Contexto:
    Dado que existe um usuário "Admin" com email "admin@example.com"
    E que existe uma agência de extração "PCCE"
    E que existe uma unidade de extração "UEXF"
    E que existe um usuário "João Perito" com email "joao.perito@pcce.ce.gov.br"
    E que existe um usuário extrator para "João Perito" na agência "PCCE"

  Cenário: Vincular extrator à unidade de extração
    Quando eu vinculo o extrator "João Perito" à unidade "UEXF"
    Então o vínculo deve ser criado com sucesso
    E o extrator deve estar associado à unidade

  Cenário: Representação string do vínculo
    Dado que o extrator "João Perito" está vinculado à unidade "UEXF"
    Então a representação string deve conter o nome do extrator
    E deve conter a sigla da unidade

  Cenário: Unicidade do vínculo extrator-unidade
    Dado que o extrator "João Perito" está vinculado à unidade "UEXF"
    Quando eu tento vincular novamente o mesmo extrator à mesma unidade
    Então deve gerar um erro de integridade

  Cenário: Múltiplos extratores na mesma unidade
    Dado que existe um usuário "Maria Perita" com email "maria.perita@pcce.ce.gov.br"
    E que existe um usuário extrator para "Maria Perita" na agência "PCCE"
    E que o extrator "João Perito" está vinculado à unidade "UEXF"
    Quando eu vinculo o extrator "Maria Perita" à unidade "UEXF"
    Então ambos os extratores devem estar vinculados à unidade

  Cenário: Extrator vinculado a múltiplas unidades
    Dado que existe uma unidade de extração "UEXF2"
    E que o extrator "João Perito" está vinculado à unidade "UEXF"
    Quando eu vinculo o extrator "João Perito" à unidade "UEXF2"
    Então o extrator deve estar vinculado a ambas as unidades
