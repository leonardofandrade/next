# language: pt

Funcionalidade: Models Base do Core
  Como um desenvolvedor do sistema
  Eu quero ter models base abstratos
  Para garantir auditoria e campos comuns em todos os models

  Contexto:
    Dado que existe um usuário "João Silva" com email "joao@example.com"

  Cenário: Criar instância de model com AuditedModel
    Quando eu crio uma nova instância de um model que herda de AuditedModel
    Então o campo "created_at" deve ser preenchido automaticamente
    E o campo "created_by" deve ser preenchido com o usuário atual
    E o campo "version" deve ser 1

  Cenário: Atualizar instância de model com AuditedModel
    Dado que existe uma instância de um model que herda de AuditedModel
    Quando eu atualizo a instância
    Então o campo "updated_at" deve ser atualizado
    E o campo "updated_by" deve ser preenchido com o usuário atual

  Cenário: Soft delete de instância
    Dado que existe uma instância de um model que herda de AuditedModel
    Quando eu realizo um soft delete da instância
    Então o campo "deleted_at" deve ser preenchido
    E o campo "deleted_by" deve ser preenchido com o usuário atual

  Cenário: AbstractCaseModel com campos de solicitação
    Quando eu crio uma instância de um model que herda de AbstractCaseModel
    Então deve ter os campos:
      | campo                        |
      | requester_agency_unit        |
      | requested_at                 |
      | requested_device_amount      |
      | extraction_unit              |
      | requester_reply_email        |
      | requester_authority_name     |
      | requester_authority_position |
      | request_procedures           |
      | crime_category               |
      | additional_info              |

  Cenário: AbstractDeviceModel com informações de dispositivo
    Quando eu crio uma instância de um model que herda de AbstractDeviceModel
    Então deve ter os campos de informação do dispositivo:
      | campo             |
      | device_category   |
      | device_model      |
      | color             |
      | is_imei_unknown   |
      | imei_01           |
      | imei_02           |
      | imei_03           |
      | imei_04           |
      | imei_05           |
      | owner_name        |
      | internal_storage  |

  Cenário: AbstractDeviceModel com informações de status
    Quando eu crio uma instância de um model que herda de AbstractDeviceModel
    Então deve ter os campos de status:
      | campo         |
      | is_turned_on  |
      | is_locked     |

  Cenário: AbstractDeviceModel com informações de senha
    Quando eu crio uma instância de um model que herda de AbstractDeviceModel
    Então deve ter os campos de senha:
      | campo              |
      | is_password_known  |
      | password_type      |
      | password           |

  Cenário: AbstractDeviceModel com informações de condição física
    Quando eu crio uma instância de um model que herda de AbstractDeviceModel
    Então deve ter os campos de condição física:
      | campo              |
      | is_damaged         |
      | damage_description |
      | has_fluids         |
      | fluids_description |

  Cenário: AbstractDeviceModel com informações de acessórios
    Quando eu crio uma instância de um model que herda de AbstractDeviceModel
    Então deve ter os campos de acessórios:
      | campo                   |
      | has_sim_card            |
      | sim_card_info           |
      | has_memory_card         |
      | memory_card_info        |
      | has_other_accessories   |
      | other_accessories_info  |

  Cenário: AbstractDeviceModel com informações de segurança
    Quando eu crio uma instância de um model que herda de AbstractDeviceModel
    Então deve ter os campos de segurança:
      | campo          |
      | is_sealed      |
      | security_seal  |

  Cenário: Obter lista de IMEIs do dispositivo
    Dado que existe um dispositivo com:
      | imei_01 | 123456789012345 |
      | imei_02 | 987654321098765 |
    Quando eu chamo o método "get_device_imei_as_list"
    Então o resultado deve ser "123456789012345, 987654321098765"

  Cenário: Obter lista de IMEIs quando não há IMEI informado
    Dado que existe um dispositivo sem IMEIs informados
    Quando eu chamo o método "get_device_imei_as_list"
    Então o resultado deve ser "IMEI Não Informado"
