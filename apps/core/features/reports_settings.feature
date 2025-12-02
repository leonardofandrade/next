# language: pt

Funcionalidade: Configurações de Relatórios
  Como um administrador do sistema
  Eu quero gerenciar configurações de relatórios
  Para personalizar a aparência e conteúdo dos relatórios

  Contexto:
    Dado que existe um usuário "Admin" com email "admin@example.com"
    E que existe uma agência de extração "PCCE"

  Cenário: Criar configurações de relatórios
    Quando eu crio configurações de relatórios com os dados:
      | campo                       | valor                                    |
      | reports_enabled             | True                                     |
      | report_cover_header_line_1  | POLÍCIA CIVIL DO ESTADO DO CEARÁ         |
      | report_cover_header_line_2  | PERÍCIA FORENSE DO CEARÁ                 |
      | report_cover_header_line_3  | UNIDADE DE EXTRAÇÃO FORENSE              |
      | report_cover_footer_line_1  | www.pcce.ce.gov.br                       |
      | report_cover_footer_line_2  | contato@pcce.ce.gov.br                   |
    Então as configurações de relatórios devem ser criadas com sucesso
    E devem estar vinculadas à agência "PCCE"
    E os relatórios devem estar habilitados

  Cenário: Desabilitar relatórios
    Dado que existem configurações de relatórios com relatórios habilitados
    Quando eu desabilito os relatórios
    Então o campo "reports_enabled" deve ser False

  Cenário: Adicionar logo principal ao relatório
    Dado que existem configurações de relatórios
    Quando eu adiciono um logo principal em formato binário
    Então o campo "default_report_header_logo" deve estar preenchido

  Cenário: Adicionar logo secundário ao relatório
    Dado que existem configurações de relatórios
    Quando eu adiciono um logo secundário em formato binário
    Então o campo "secondary_report_header_logo" deve estar preenchido

  Cenário: Obter logo principal em base64
    Dado que existem configurações de relatórios com logo principal
    Quando eu chamo o método "get_default_logo_base64"
    Então deve retornar uma string base64 válida

  Cenário: Obter logo secundário em base64
    Dado que existem configurações de relatórios com logo secundário
    Quando eu chamo o método "get_secondary_logo_base64"
    Então deve retornar uma string base64 válida

  Cenário: Logo base64 retorna None quando não há logo
    Dado que existem configurações de relatórios sem logos
    Quando eu chamo o método "get_default_logo_base64"
    Então deve retornar None
    E quando eu chamo o método "get_secondary_logo_base64"
    Então deve retornar None

  Cenário: Configurar nota do relatório de distribuição
    Dado que existem configurações de relatórios
    Quando eu defino a nota de distribuição como:
      """
      DISTRIBUIÇÃO RESTRITA
      Este documento é de uso exclusivo das autoridades policiais.
      """
    Então o campo "distribution_report_notes" deve estar preenchido

  Cenário: Configurar linhas do cabeçalho da capa
    Dado que existem configurações de relatórios
    Quando eu configuro as linhas do cabeçalho:
      | linha | valor                            |
      | 1     | GOVERNO DO ESTADO DO CEARÁ       |
      | 2     | SECRETARIA DA SEGURANÇA PÚBLICA  |
      | 3     | PERÍCIA FORENSE                  |
    Então as três linhas do cabeçalho devem estar definidas

  Cenário: Configurar linhas do rodapé da capa
    Dado que existem configurações de relatórios
    Quando eu configuro as linhas do rodapé:
      | linha | valor                              |
      | 1     | Av. Principal, 1234 - Fortaleza/CE |
      | 2     | Tel: (85) 3101-0000                |
    Então as duas linhas do rodapé devem estar definidas

  Cenário: Unicidade de configurações por agência
    Dado que existem configurações de relatórios vinculadas à agência "PCCE"
    Quando eu tento criar outras configurações de relatórios para a mesma agência
    Então deve gerar um erro de integridade

  Cenário: Configurações com valores padrão
    Quando eu crio configurações de relatórios mínimas
    Então o campo "reports_enabled" deve ser True
    E os campos de logo devem estar vazios
    E os campos de cabeçalho e rodapé devem estar vazios
