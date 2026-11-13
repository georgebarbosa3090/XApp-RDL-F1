"""
Testes da ponte KPM -> RDL-N1 -> cotas de PRB (src/closed_loop/hrdl_slice_loop.py).

A decisão passa pelo pipeline real da xApp RDL (RDLxApp.process_actions); os KPM aqui são
dicionários no formato que src/e2/v3/codec.py devolve ao decodificar as Indications do NORI.
"""

from src.closed_loop import hrdl_slice_loop as loop

NODE_ID = "gnb_268_341_00000001"
UES = [{"ue_id": 1, "measurements": {"DRB.NetworkSlicing.SST": 1}},
       {"ue_id": 2, "measurements": {"DRB.NetworkSlicing.SST": 2}}]
CONGESTED = {"RRU.PrbUsedDl": 236, "RRU.PrbAvailDl": 139}


def test_state_reads_congestion_and_slices_from_kpm():
    state = loop.slice_state(CONGESTED, UES)
    assert state["congested"] is True
    assert state["ues_by_sst"] == {"1": [1], "2": [2]}
    assert loop.slice_state({"RRU.PrbUsedDl": 100, "RRU.PrbAvailDl": 139}, UES)["congested"] is False
    assert loop.slice_state({}, UES)["congested"] is False


def test_policies_conflict_on_the_same_target():
    proposals = loop.reference_proposals(loop.slice_state(CONGESTED, UES), NODE_ID)
    assert {(p.xapp_id, p.value, p.priority) for p in proposals} == {
        ("xapp-qos-xslice", 25.0, 90), ("xapp-embb-throughput", 80.0, 60)}
    assert {(p.node_id, p.parameter) for p in proposals} == {(NODE_ID, "PRB_QUOTA")}
    only_embb = [UES[0]]
    assert loop.reference_proposals(loop.slice_state(CONGESTED, only_embb), NODE_ID) == []


def test_real_hrdl_pipeline_resolves_the_direct_conflict():
    record = loop.decide_slice_quotas(NODE_ID, CONGESTED, UES)
    assert record["decision_source"] == "H_RDL" and record["engine"] == loop.ENGINE
    assert [r["conflict_type"] for r in record["resolutions"]] == ["DIRECT"]
    assert record["resolutions"][0]["strategy"] == "TVS"
    # Previsão pré-registrada da v2 (docs/preregistros): com 25 contra 80, o TVS escolhe a política de vazão eMBB.
    assert record["selected"]["xapp_id"] == "xapp-embb-throughput"
    assert record["quotas"] == [
        {"sst": 1, "max_prb_ratio": 80, "min_prb_ratio": 0, "dedicated_prb_ratio": 0},
        {"sst": 2, "max_prb_ratio": 20, "min_prb_ratio": 0, "dedicated_prb_ratio": 0}]


def test_decision_is_reproducible_across_fresh_deciders():
    a = loop.decide_slice_quotas(NODE_ID, CONGESTED, UES)
    b = loop.decide_slice_quotas(NODE_ID, CONGESTED, UES)
    assert (a["selected"], a["quotas"]) == (b["selected"], b["quotas"])


def test_no_control_without_congestion():
    record = loop.decide_slice_quotas(NODE_ID, {"RRU.PrbUsedDl": 10, "RRU.PrbAvailDl": 139}, UES)
    assert record["quotas"] == [] and record["selected"] is None and record["proposals"] == []


def test_quota_mapping_is_complementary():
    assert [(q.sst, q.max_prb_ratio) for q in loop.quotas_for(40)] == [(1, 40), (2, 60)]
