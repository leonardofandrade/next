# 🔍 NEXT - Sistema de Gerenciamento de Extrações de Dados

## 📋 Visão Geral

O **NEXT** é uma plataforma completa para gerenciamento de solicitações, processos e extrações de dados forenses. O sistema permite o controle completo do fluxo de trabalho desde a solicitação inicial até a finalização e coleta do material.

---

## 👥 Tipos de Usuários

### 🔑 Superuser
- **Permissões:** Acesso total ao sistema
- **Pode:** Visualizar, editar, excluir tudo
- **Identificação:** Campo nativo do Django `User.is_superuser`

### 👨‍💼 Staff
- **Permissões:** Apenas visualização (read-only)
- **Pode:** Visualizar todo o conteúdo do sistema
- **NÃO pode:** Editar ou excluir nada
- **Identificação:** Campo nativo do Django `User.is_staff`

### 🔧 Extractor (Extrator)
- **Permissões:** Ações em Cases e Extractions
- **Pode:**
  - Visualizar cases e extractions
  - Editar cases e extractions
  - Criar, atualizar e gerenciar cases e extractions
  - Atribuir casos a si mesmo ou outros extractors
  - Iniciar, pausar e finalizar extrações
- **NÃO pode:** Excluir (apenas superuser pode)
- **Identificação:** Campo `UserProfile.is_extractor`

### 📋 Requester (Solicitante)
- **Permissões:** Ações em Extraction Requests
- **Pode:**
  - Visualizar extraction requests
  - Editar extraction requests
  - Criar e atualizar solicitações de extração
  - Gerenciar informações das solicitações
- **NÃO pode:** Excluir (apenas superuser pode)
- **Identificação:** Campo `UserProfile.is_requester`

### 📊 Manager (Gestor)
- **Permissões:** Consulta de funcionalidades (read-only)
- **Pode:**
  - Visualizar funcionalidades de gestão
  - Acessar relatórios e dashboards
  - Consultar estatísticas e métricas
- **NÃO pode:** Editar ou excluir nada
- **Identificação:** Campo `UserProfile.is_manager`

---

## 🔐 Matriz de Permissões

| Ação | Superuser | Staff | Extractor | Requester | Manager |
|------|-----------|-------|-----------|-----------|---------|
| **Visualizar Cases** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Editar Cases** | ✅ | ❌ | ✅ | ❌ | ❌ |
| **Excluir Cases** | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Visualizar Extractions** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Editar Extractions** | ✅ | ❌ | ✅ | ❌ | ❌ |
| **Excluir Extractions** | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Visualizar Extraction Requests** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Editar Extraction Requests** | ✅ | ❌ | ❌ | ✅ | ❌ |
| **Excluir Extraction Requests** | ✅ | ❌ | ❌ | ❌ | ❌ |

---

## ⚙️ Funcionalidades Principais

### 📝 Gerenciamento de Solicitações
Criação, edição e acompanhamento de solicitações de extração de dados. Inclui informações sobre solicitante, procedimentos, dispositivos e status.

### 📁 Gerenciamento de Cases
Criação de casos a partir de solicitações, com numeração sequencial automática, atribuição de prioridades e controle de status completo.

### 🔍 Gerenciamento de Extrações
Controle detalhado de extrações de dados, incluindo tipos (lógica, física, sistema de arquivos, nuvem), força bruta, e resultados.

### 📱 Gerenciamento de Dispositivos
Cadastro e rastreamento de dispositivos móveis, incluindo marca, modelo, IMEI, acessórios (cartão de memória, chip SIM) e características.

### 📄 Gerenciamento de Documentos
Armazenamento e organização de documentos relacionados aos casos, incluindo ofícios, procedimentos e arquivos diversos.

### 👥 Gerenciamento de Usuários
Controle de perfis de usuários, permissões, associações com unidades organizacionais e configurações de acesso.

### 🏢 Configurações Organizacionais
Gerenciamento de organizações, agências, unidades operacionais, unidades de extração e cargos.

### 📊 Relatórios e Auditoria
Sistema de auditoria completo para rastreamento de ações, logs de acesso e geração de relatórios.

### 💾 Armazenamento
Controle de locais de armazenamento de extrações, com informações sobre tamanho e localização dos arquivos.

---

## 🔄 Fluxo de Trabalho

### 1. Criação da Solicitação de Extração (Extraction Request)
- **Responsável:** Requester
- **Status Inicial:** Pendente
- **Ações:**
  - Criar solicitação com informações do solicitante
  - Informar unidade solicitante, cargo, email de resposta
  - Definir procedimentos (IP, PJ)
  - Especificar quantidade de dispositivos
  - Selecionar tipo de crime e unidade de extração

### 2. Atribuição da Solicitação
- **Status:** Aguardando Material
- **Ações:**
  - Solicitação é atribuída a uma unidade de extração
  - Aguarda recebimento do material físico

### 3. Recebimento do Material
- **Responsável:** Extractor
- **Status:** Material Recebido
- **Ações:**
  - Extractor registra o recebimento do material
  - Adiciona notas sobre o recebimento
  - Status muda para "Material Recebido"

### 4. Criação do Case
- **Responsável:** Extractor
- **Status Inicial:** Cadastro Incompleto
- **Ações:**
  - Extractor cria um Case a partir da Extraction Request
  - Define prioridade do caso (Baixa, Média, Alta, Urgente)
  - Cadastra dispositivos (marca, modelo, IMEI, acessórios)
  - Adiciona documentos relacionados
  - Completa informações obrigatórias

### 5. Finalização do Cadastro do Case
- **Responsável:** Extractor
- **Status:** Aguardando Extrator
- **Ações:**
  - Sistema valida se todas as informações obrigatórias estão preenchidas
  - Gera número sequencial do caso automaticamente (formato: ANO.NNNNN)
  - Marca data de conclusão do cadastro
  - Opcionalmente, pode atribuir o caso a um extrator

### 6. Criação de Extrações
- **Responsável:** Extractor ou Sistema
- **Status Inicial:** Aguardando Extrator
- **Ações:**
  - Para cada dispositivo do case, uma Extraction é criada
  - Pode ser criada manualmente ou automaticamente via comando
  - Extraction pode ser atribuída a um extrator específico

### 7. Atribuição da Extração
- **Status:** Aguardando Início
- **Ações:**
  - Extraction é atribuída a um extrator
  - Extrator deve estar associado à unidade de extração do case
  - Registra quem atribuiu e quando

### 8. Início da Extração
- **Responsável:** Extractor
- **Status:** Em Andamento
- **Ações:**
  - Extractor inicia o processo de extração
  - Pode adicionar observações iniciais
  - Registra data e hora de início

### 9. Processo de Extração
- **Responsável:** Extractor
- **Status:** Em Andamento ou Pausado
- **Ações:**
  - Extractor pode pausar a extração se necessário
  - Registra tipo de extração realizada:
    - Extração Lógica
    - Extração Física
    - Extração Completa do Sistema de Arquivos
    - Extração em Nuvem
  - Pode realizar força bruta (brute force) se necessário
  - Registra uso de Cellebrite Premium

### 10. Finalização da Extração
- **Responsável:** Extractor
- **Status:** Finalizada
- **Ações:**
  - Extractor finaliza a extração
  - Registra resultado (sucesso/falha)
  - Informa tamanho da extração (GB)
  - Define local de armazenamento
  - Adiciona observações finais
  - Registra data e hora de término

### 11. Finalização do Case
- **Responsável:** Extractor
- **Status:** Finalizada
- **Pré-requisitos:**
  - Todas as extrações do case devem estar finalizadas
- **Ações:**
  - Extractor finaliza o case
  - Gera ofício de resposta (opcional)
  - Registra número e data do ofício
  - Adiciona observações de finalização
  - Status muda para "Aguardando Coleta"

### 12. Coleta do Material
- **Status Final:** Aguardando Coleta
- **Descrição:**
  - Material e resultados aguardam coleta pelo solicitante
  - Processo completo finalizado

---

## 📊 Status e Transições

### Status de Extraction Request
- **Pendente:** Solicitação criada, aguardando processamento
- **Aguardando Material:** Solicitação atribuída, aguardando recebimento
- **Material Recebido:** Material físico recebido pela unidade
- **Aguardando Início:** Case criado, aguardando início das extrações
- **Em Andamento:** Extrações em processo
- **Aguardando Coleta:** Processo finalizado, aguardando coleta

### Status de Case
- **Cadastro Incompleto:** Case criado mas ainda faltam informações
- **Aguardando Extrator:** Cadastro completo, aguardando atribuição
- **Aguardando Início:** Atribuído a um extrator, aguardando início
- **Em Andamento:** Extrações em processo
- **Pausada:** Processo temporariamente pausado
- **Finalizada:** Todas as extrações concluídas
- **Aguardando Coleta:** Processo completo, aguardando coleta

### Status de Extraction
- **Aguardando Extrator:** Extração criada, aguardando atribuição
- **Aguardando Início:** Atribuída a um extrator, aguardando início
- **Em Andamento:** Extração em processo
- **Pausado:** Extração temporariamente pausada
- **Finalizada:** Extração concluída com sucesso ou falha

---

## 📦 Módulos do Sistema

### 📋 Requisitions
Gerenciamento de solicitações de extração de dados

### 📁 Cases
Gerenciamento de casos e processos de extração

### 🔍 Extractors
Interface específica para extractors gerenciarem suas extrações

### 👥 Users
Gerenciamento de usuários e perfis

### ⚙️ Configs
Configurações do sistema, unidades, armazenamento e perfis RBAC

### 📊 Base Tables
Tabelas base: organizações, agências, tipos de crime, dispositivos, etc.

### 🔐 Auditing
Sistema de auditoria e logs de ações

### 🌐 Public
Área pública do sistema

---

## 🛠️ Características Técnicas

### Arquitetura
- **Framework:** Django (Python)
- **Banco de Dados:** MySQL/PostgreSQL
- **Deploy:** Docker e Docker Compose
- **Arquitetura:** Modular com apps Django separados

### Recursos de Segurança
- Sistema de permissões baseado em perfis
- Sistema RBAC (Role-Based Access Control)
- Auditoria completa de ações
- Soft delete para preservação de dados
- Validações de negócio em múltiplas camadas

### Funcionalidades Avançadas
- Numeração sequencial automática de casos
- Geração automática de extrações a partir de casos
- Comandos de gerenciamento para operações em lote
- Sistema de backup automatizado
- Interface responsiva e moderna

---

## 📝 Notas Finais

Este documento apresenta uma visão geral do sistema NEXT. Para informações mais detalhadas sobre implementação técnica, consulte a documentação específica de cada módulo.

---

**NEXT - Sistema de Gerenciamento de Extrações de Dados**  
Versão 1.0 | Documentação gerada automaticamente

