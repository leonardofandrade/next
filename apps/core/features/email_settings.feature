# language: pt

Funcionalidade: Configurações de E-mail
  Como um administrador do sistema
  Eu quero gerenciar configurações de e-mail
  Para enviar notificações e relatórios

  Contexto:
    Dado que existe um usuário "Admin" com email "admin@example.com"
    E que existe uma agência de extração "PCCE"

  Cenário: Criar configurações de e-mail com TLS
    Quando eu crio configurações de e-mail com os dados:
      | campo              | valor                  |
      | email_host         | smtp.gmail.com         |
      | email_port         | 587                    |
      | email_use_tls      | True                   |
      | email_use_ssl      | False                  |
      | email_host_user    | sistema@pcce.ce.gov.br |
      | email_host_password| senha123               |
      | email_from_name    | Sistema PCCE           |
    Então as configurações de e-mail devem ser criadas com sucesso
    E devem estar vinculadas à agência "PCCE"
    E o TLS deve estar ativo
    E o SSL deve estar inativo

  Cenário: Criar configurações de e-mail com SSL
    Quando eu crio configurações de e-mail com os dados:
      | campo              | valor                  |
      | email_host         | smtp.office365.com     |
      | email_port         | 465                    |
      | email_use_tls      | False                  |
      | email_use_ssl      | True                   |
      | email_host_user    | sistema@pcce.ce.gov.br |
      | email_from_name    | Sistema PCCE           |
    Então o SSL deve estar ativo
    E o TLS deve estar inativo

  Cenário: Configurações de e-mail com valores padrão
    Quando eu crio configurações de e-mail mínimas
    Então o campo "email_host" deve ser "localhost"
    E o campo "email_port" deve ser 587
    E o campo "email_use_tls" deve ser True
    E o campo "email_use_ssl" deve ser False
    E o campo "email_from_name" deve ser "Sistema"

  Cenário: Configurar servidor SMTP Gmail
    Quando eu configuro o servidor SMTP Gmail:
      | campo              | valor              |
      | email_host         | smtp.gmail.com     |
      | email_port         | 587                |
      | email_use_tls      | True               |
      | email_host_user    | user@gmail.com     |
      | email_host_password| app_password       |
    Então as configurações devem estar corretas para Gmail

  Cenário: Configurar servidor SMTP Office365
    Quando eu configuro o servidor SMTP Office365:
      | campo              | valor                  |
      | email_host         | smtp.office365.com     |
      | email_port         | 587                    |
      | email_use_tls      | True                   |
      | email_host_user    | user@office365.com     |
    Então as configurações devem estar corretas para Office365

  Cenário: Unicidade de configurações por agência
    Dado que existem configurações de e-mail vinculadas à agência "PCCE"
    Quando eu tento criar outras configurações de e-mail para a mesma agência
    Então deve gerar um erro de integridade

  Cenário: Configurar nome do remetente personalizado
    Dado que existem configurações de e-mail
    Quando eu altero o nome do remetente para "Perícia Forense - CE"
    Então o campo "email_from_name" deve ser "Perícia Forense - CE"
