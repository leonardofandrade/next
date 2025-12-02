# language: pt

Funcionalidade: Configurações de Unidade de Extração
  Como um administrador do sistema
  Eu quero gerenciar configurações específicas de cada unidade de extração
  Para personalizar o comportamento de cada unidade

  Contexto:
    Dado que existe um usuário "Admin" com email "admin@example.com"
    E que existe uma agência de extração "PCCE"
    E que existe uma unidade de extração "UEXF"

  Cenário: Criar configurações de unidade de extração
    Quando eu crio configurações de unidade de extração com os dados:
      | campo                 | valor                                          |
      | reply_email_template  | Prezado {autoridade}, sua solicitação...       |
      | reply_email_subject   | Resposta à Solicitação de Extração #{numero}   |
    Então as configurações devem ser criadas com sucesso
    E devem estar vinculadas à unidade "UEXF"

  Cenário: Configurar template de email de resposta personalizado
    Dado que existem configurações da unidade "UEXF"
    Quando eu configuro o template de email com:
      | campo                 | valor                                                   |
      | reply_email_template  | Prezado(a) {nome_autoridade},\n\nSua solicitação...    |
      | reply_email_subject   | [PCCE-UEXF] Resposta à Solicitação #{protocolo}        |
    Então o template deve estar salvo
    E o assunto deve estar salvo

  Cenário: Atualizar template de email existente
    Dado que existem configurações da unidade "UEXF" com template definido
    Quando eu atualizo o template de email para:
      """
      Prezado(a) {nome_autoridade},

      Informamos que sua solicitação de extração de dados foi recebida e está sendo processada.
      
      Protocolo: {protocolo}
      Data: {data}
      
      Atenciosamente,
      Equipe UEXF
      """
    Então o template atualizado deve estar salvo

  Cenário: Template de email com variáveis
    Dado que existem configurações da unidade "UEXF"
    Quando eu configuro um template com as variáveis:
      | variável           |
      | {nome_autoridade}  |
      | {protocolo}        |
      | {data}             |
      | {unidade}          |
    Então todas as variáveis devem estar presentes no template

  Cenário: Configurações específicas por unidade
    Dado que existe uma unidade de extração "UEXF2"
    E que existem configurações da unidade "UEXF"
    Quando eu crio configurações diferentes para "UEXF2"
    Então cada unidade deve ter suas próprias configurações
    E as configurações não devem se sobrepor

  Cenário: Relacionamento OneToOne com unidade
    Dado que existem configurações da unidade "UEXF"
    Quando eu tento criar outras configurações para a mesma unidade
    Então deve gerar um erro de integridade
