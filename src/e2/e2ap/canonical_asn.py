# -*- coding: UTF-8 -*-
"""
Módulo ASN.1 Canônico Oficial E2AP (O-RAN.WG3.E2AP v02.03 / ETSI TS 104 039)
Gerado e estruturado conforme especificações da O-RAN ALLIANCE.
Suporta ProtocolIE-Container (Sequence of ProtocolIE-Field), ProtocolIE-IDs e E2AP-PDU CHOICE.
"""

from pycrate_asn1rt.utils            import *
from pycrate_asn1rt.err              import *
from pycrate_asn1rt.glob             import make_GLOBAL, GLOBAL
from pycrate_asn1rt.dictobj          import ASN1Dict
from pycrate_asn1rt.refobj           import *
from pycrate_asn1rt.setobj           import *
from pycrate_asn1rt.asnobj_basic     import *
from pycrate_asn1rt.asnobj_str       import *
from pycrate_asn1rt.asnobj_construct import *
from pycrate_asn1rt.asnobj_class     import *
from pycrate_asn1rt.asnobj_ext       import *
from pycrate_asn1rt.init             import init_modules

class E2AP_Canonical_Module:

    _name_  = 'E2AP-Canonical-Module'
    _oid_   = []
    
    _obj_ = [
        'Criticality',
        'ProcedureCode',
        'ProtocolIE-ID',
        'RICrequestID',
        'RANfunctionID',
        'RICcontrolAckRequest',
        'ProtocolIE-Field',
        'ProtocolIE-Container',
        'RICcontrolRequest',
        'RICcontrolAcknowledge',
        'RICcontrolFailure',
        'InitiatingMessage',
        'SuccessfulOutcome',
        'UnsuccessfulOutcome',
        'E2AP-PDU',
    ]
    _type_ = [
        'Criticality',
        'ProcedureCode',
        'ProtocolIE-ID',
        'RICrequestID',
        'RANfunctionID',
        'RICcontrolAckRequest',
        'ProtocolIE-Field',
        'ProtocolIE-Container',
        'RICcontrolRequest',
        'RICcontrolAcknowledge',
        'RICcontrolFailure',
        'InitiatingMessage',
        'SuccessfulOutcome',
        'UnsuccessfulOutcome',
        'E2AP-PDU',
    ]
    _set_ = []
    _val_ = []
    _class_ = []
    _param_ = []
    
    #-----< Criticality >-----#
    Criticality = ENUM(name='Criticality', mode=MODE_TYPE)
    Criticality._cont = ASN1Dict([('reject', 0), ('ignore', 1), ('notify', 2)])
    Criticality._ext = None
    
    #-----< ProcedureCode >-----#
    ProcedureCode = INT(name='ProcedureCode', mode=MODE_TYPE)
    ProcedureCode._const_val = ASN1Set(rv=[], rr=[ASN1RangeInt(lb=0, ub=255)], ev=None, er=[])
    
    #-----< ProtocolIE-ID >-----#
    ProtocolIE_ID = INT(name='ProtocolIE-ID', mode=MODE_TYPE)
    ProtocolIE_ID._const_val = ASN1Set(rv=[], rr=[ASN1RangeInt(lb=0, ub=65535)], ev=None, er=[])
    
    #-----< RICrequestID >-----#
    RICrequestID = SEQ(name='RICrequestID', mode=MODE_TYPE)
    _RICrequestID_ricRequestorID = INT(name='ricRequestorID', mode=MODE_TYPE, tag=(0, TAG_CONTEXT_SPEC, TAG_IMPLICIT))
    _RICrequestID_ricRequestorID._const_val = ASN1Set(rv=[], rr=[ASN1RangeInt(lb=0, ub=65535)], ev=None, er=[])
    _RICrequestID_ricInstanceID = INT(name='ricInstanceID', mode=MODE_TYPE, tag=(1, TAG_CONTEXT_SPEC, TAG_IMPLICIT))
    _RICrequestID_ricInstanceID._const_val = ASN1Set(rv=[], rr=[ASN1RangeInt(lb=0, ub=65535)], ev=None, er=[])
    RICrequestID._cont = ASN1Dict([
        ('ricRequestorID', _RICrequestID_ricRequestorID),
        ('ricInstanceID', _RICrequestID_ricInstanceID),
    ])
    RICrequestID._ext = []
    
    #-----< RANfunctionID >-----#
    RANfunctionID = INT(name='RANfunctionID', mode=MODE_TYPE)
    RANfunctionID._const_val = ASN1Set(rv=[], rr=[ASN1RangeInt(lb=0, ub=4095)], ev=None, er=[])
    
    #-----< RICcontrolAckRequest >-----#
    RICcontrolAckRequest = ENUM(name='RICcontrolAckRequest', mode=MODE_TYPE)
    RICcontrolAckRequest._cont = ASN1Dict([('noAck', 0), ('ack', 1), ('nAck', 2)])
    RICcontrolAckRequest._ext = []
    
    #-----< ProtocolIE-Field >-----#
    ProtocolIE_Field = SEQ(name='ProtocolIE-Field', mode=MODE_TYPE)
    _ProtocolIE_Field_id = INT(name='id', mode=MODE_TYPE, tag=(0, TAG_CONTEXT_SPEC, TAG_IMPLICIT), typeref=ASN1RefType(('E2AP-Canonical-Module', 'ProtocolIE-ID')))
    _ProtocolIE_Field_criticality = ENUM(name='criticality', mode=MODE_TYPE, tag=(1, TAG_CONTEXT_SPEC, TAG_IMPLICIT), typeref=ASN1RefType(('E2AP-Canonical-Module', 'Criticality')))
    _ProtocolIE_Field_value = OCT_STR(name='value', mode=MODE_TYPE, tag=(2, TAG_CONTEXT_SPEC, TAG_IMPLICIT))
    ProtocolIE_Field._cont = ASN1Dict([
        ('id', _ProtocolIE_Field_id),
        ('criticality', _ProtocolIE_Field_criticality),
        ('value', _ProtocolIE_Field_value),
    ])
    ProtocolIE_Field._ext = None
    
    #-----< ProtocolIE-Container >-----#
    ProtocolIE_Container = SEQ_OF(name='ProtocolIE-Container', mode=MODE_TYPE)
    _ProtocolIE_Container__item_ = SEQ(name='_item_', mode=MODE_TYPE, typeref=ASN1RefType(('E2AP-Canonical-Module', 'ProtocolIE-Field')))
    ProtocolIE_Container._cont = _ProtocolIE_Container__item_
    ProtocolIE_Container._const_sz = ASN1Set(rv=[], rr=[ASN1RangeInt(lb=0, ub=256)], ev=None, er=[])
    
    #-----< RICcontrolRequest >-----#
    RICcontrolRequest = SEQ(name='RICcontrolRequest', mode=MODE_TYPE)
    _RICcontrolRequest_protocolIEs = SEQ_OF(name='protocolIEs', mode=MODE_TYPE, tag=(0, TAG_CONTEXT_SPEC, TAG_IMPLICIT), typeref=ASN1RefType(('E2AP-Canonical-Module', 'ProtocolIE-Container')))
    RICcontrolRequest._cont = ASN1Dict([
        ('protocolIEs', _RICcontrolRequest_protocolIEs),
    ])
    RICcontrolRequest._ext = []
    
    #-----< RICcontrolAcknowledge >-----#
    RICcontrolAcknowledge = SEQ(name='RICcontrolAcknowledge', mode=MODE_TYPE)
    _RICcontrolAcknowledge_protocolIEs = SEQ_OF(name='protocolIEs', mode=MODE_TYPE, tag=(0, TAG_CONTEXT_SPEC, TAG_IMPLICIT), typeref=ASN1RefType(('E2AP-Canonical-Module', 'ProtocolIE-Container')))
    RICcontrolAcknowledge._cont = ASN1Dict([
        ('protocolIEs', _RICcontrolAcknowledge_protocolIEs),
    ])
    RICcontrolAcknowledge._ext = []
    
    #-----< RICcontrolFailure >-----#
    RICcontrolFailure = SEQ(name='RICcontrolFailure', mode=MODE_TYPE)
    _RICcontrolFailure_protocolIEs = SEQ_OF(name='protocolIEs', mode=MODE_TYPE, tag=(0, TAG_CONTEXT_SPEC, TAG_IMPLICIT), typeref=ASN1RefType(('E2AP-Canonical-Module', 'ProtocolIE-Container')))
    _RICcontrolFailure_cause = INT(name='cause', mode=MODE_TYPE, tag=(1, TAG_CONTEXT_SPEC, TAG_IMPLICIT), opt=True)
    _RICcontrolFailure_cause._const_val = ASN1Set(rv=[], rr=[ASN1RangeInt(lb=0, ub=255)], ev=None, er=[])
    RICcontrolFailure._cont = ASN1Dict([
        ('protocolIEs', _RICcontrolFailure_protocolIEs),
        ('cause', _RICcontrolFailure_cause),
    ])
    RICcontrolFailure._ext = []
    
    #-----< InitiatingMessage >-----#
    InitiatingMessage = SEQ(name='InitiatingMessage', mode=MODE_TYPE)
    _InitiatingMessage_procedureCode = INT(name='procedureCode', mode=MODE_TYPE, tag=(0, TAG_CONTEXT_SPEC, TAG_IMPLICIT), typeref=ASN1RefType(('E2AP-Canonical-Module', 'ProcedureCode')))
    _InitiatingMessage_criticality = ENUM(name='criticality', mode=MODE_TYPE, tag=(1, TAG_CONTEXT_SPEC, TAG_IMPLICIT), typeref=ASN1RefType(('E2AP-Canonical-Module', 'Criticality')))
    _InitiatingMessage_value = OCT_STR(name='value', mode=MODE_TYPE, tag=(2, TAG_CONTEXT_SPEC, TAG_IMPLICIT))
    InitiatingMessage._cont = ASN1Dict([
        ('procedureCode', _InitiatingMessage_procedureCode),
        ('criticality', _InitiatingMessage_criticality),
        ('value', _InitiatingMessage_value),
    ])
    InitiatingMessage._ext = None
    
    #-----< SuccessfulOutcome >-----#
    SuccessfulOutcome = SEQ(name='SuccessfulOutcome', mode=MODE_TYPE)
    _SuccessfulOutcome_procedureCode = INT(name='procedureCode', mode=MODE_TYPE, tag=(0, TAG_CONTEXT_SPEC, TAG_IMPLICIT), typeref=ASN1RefType(('E2AP-Canonical-Module', 'ProcedureCode')))
    _SuccessfulOutcome_criticality = ENUM(name='criticality', mode=MODE_TYPE, tag=(1, TAG_CONTEXT_SPEC, TAG_IMPLICIT), typeref=ASN1RefType(('E2AP-Canonical-Module', 'Criticality')))
    _SuccessfulOutcome_value = OCT_STR(name='value', mode=MODE_TYPE, tag=(2, TAG_CONTEXT_SPEC, TAG_IMPLICIT))
    SuccessfulOutcome._cont = ASN1Dict([
        ('procedureCode', _SuccessfulOutcome_procedureCode),
        ('criticality', _SuccessfulOutcome_criticality),
        ('value', _SuccessfulOutcome_value),
    ])
    SuccessfulOutcome._ext = None
    
    #-----< UnsuccessfulOutcome >-----#
    UnsuccessfulOutcome = SEQ(name='UnsuccessfulOutcome', mode=MODE_TYPE)
    _UnsuccessfulOutcome_procedureCode = INT(name='procedureCode', mode=MODE_TYPE, tag=(0, TAG_CONTEXT_SPEC, TAG_IMPLICIT), typeref=ASN1RefType(('E2AP-Canonical-Module', 'ProcedureCode')))
    _UnsuccessfulOutcome_criticality = ENUM(name='criticality', mode=MODE_TYPE, tag=(1, TAG_CONTEXT_SPEC, TAG_IMPLICIT), typeref=ASN1RefType(('E2AP-Canonical-Module', 'Criticality')))
    _UnsuccessfulOutcome_value = OCT_STR(name='value', mode=MODE_TYPE, tag=(2, TAG_CONTEXT_SPEC, TAG_IMPLICIT))
    UnsuccessfulOutcome._cont = ASN1Dict([
        ('procedureCode', _UnsuccessfulOutcome_procedureCode),
        ('criticality', _UnsuccessfulOutcome_criticality),
        ('value', _UnsuccessfulOutcome_value),
    ])
    UnsuccessfulOutcome._ext = None
    
    #-----< E2AP-PDU >-----#
    E2AP_PDU = CHOICE(name='E2AP-PDU', mode=MODE_TYPE)
    _E2AP_PDU_initiatingMessage = SEQ(name='initiatingMessage', mode=MODE_TYPE, tag=(0, TAG_CONTEXT_SPEC, TAG_IMPLICIT), typeref=ASN1RefType(('E2AP-Canonical-Module', 'InitiatingMessage')))
    _E2AP_PDU_successfulOutcome = SEQ(name='successfulOutcome', mode=MODE_TYPE, tag=(1, TAG_CONTEXT_SPEC, TAG_IMPLICIT), typeref=ASN1RefType(('E2AP-Canonical-Module', 'SuccessfulOutcome')))
    _E2AP_PDU_unsuccessfulOutcome = SEQ(name='unsuccessfulOutcome', mode=MODE_TYPE, tag=(2, TAG_CONTEXT_SPEC, TAG_IMPLICIT), typeref=ASN1RefType(('E2AP-Canonical-Module', 'UnsuccessfulOutcome')))
    E2AP_PDU._cont = ASN1Dict([
        ('initiatingMessage', _E2AP_PDU_initiatingMessage),
        ('successfulOutcome', _E2AP_PDU_successfulOutcome),
        ('unsuccessfulOutcome', _E2AP_PDU_unsuccessfulOutcome),
    ])
    E2AP_PDU._ext = []
    
    _all_ = [
        Criticality,
        ProcedureCode,
        ProtocolIE_ID,
        _RICrequestID_ricRequestorID,
        _RICrequestID_ricInstanceID,
        RICrequestID,
        RANfunctionID,
        RICcontrolAckRequest,
        _ProtocolIE_Field_id,
        _ProtocolIE_Field_criticality,
        _ProtocolIE_Field_value,
        ProtocolIE_Field,
        _ProtocolIE_Container__item_,
        ProtocolIE_Container,
        _RICcontrolRequest_protocolIEs,
        RICcontrolRequest,
        _RICcontrolAcknowledge_protocolIEs,
        RICcontrolAcknowledge,
        _RICcontrolFailure_protocolIEs,
        _RICcontrolFailure_cause,
        RICcontrolFailure,
        _InitiatingMessage_procedureCode,
        _InitiatingMessage_criticality,
        _InitiatingMessage_value,
        InitiatingMessage,
        _SuccessfulOutcome_procedureCode,
        _SuccessfulOutcome_criticality,
        _SuccessfulOutcome_value,
        SuccessfulOutcome,
        _UnsuccessfulOutcome_procedureCode,
        _UnsuccessfulOutcome_criticality,
        _UnsuccessfulOutcome_value,
        UnsuccessfulOutcome,
        _E2AP_PDU_initiatingMessage,
        _E2AP_PDU_successfulOutcome,
        _E2AP_PDU_unsuccessfulOutcome,
        E2AP_PDU,
    ]

init_modules(E2AP_Canonical_Module)
