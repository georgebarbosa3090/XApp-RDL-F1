"""Modelo de energia (docs/17 §4 e §5.2): TR 38.864 e EARTH sobre raw/rdl_cell_state.csv."""
import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
CERT = ROOT / "scripts" / "certification"
if str(CERT) not in sys.path:
    sys.path.insert(0, str(CERT))
import energy_model as em  # noqa: E402

MODELS = em.load_models()
TR1, TR2, EARTH = MODELS["tr1"], MODELS["tr2"], MODELS["earth"]
SLOT_S, N_SYM, RB = 0.001, 14, 106
P_REF_MW = 10 ** (43.0 / 10)


def row(t_end, cell=1, slots=100, data_sym=0, ctrl_sym=0, data_reg=0, ctrl_reg=0, ptx_dbm=43.0, alloc="used",
        sleep_slots=0, sleep_sym=0, sleep_data_reg=0, rb_frac=1.0, dl=0, ul=0, rb=RB):
    """Linha sintética do rdl_cell_state.csv. rb_frac: fração dos RBs ocupada nos símbolos de dados."""
    mw = 10 ** (ptx_dbm / 10)
    data_reg = data_reg or int(round(data_sym * rb * rb_frac))
    ctrl_reg = ctrl_reg or ctrl_sym * rb
    return {
        "t_end_s": f"{t_end:.3f}", "cell_id": str(cell), "gnb": str(cell - 1), "slots": str(slots),
        "slot_s": str(SLOT_S), "sym_per_slot": str(N_SYM), "avail_rb": str(rb), "data_reg": str(data_reg),
        "ctrl_reg": str(ctrl_reg), "data_sym": str(data_sym), "ctrl_sym": str(ctrl_sym), "active_slots": "0",
        "sched_ue_sum": "0", "ptx_dbm_min": str(ptx_dbm), "ptx_dbm_max": str(ptx_dbm),
        "reg_ptx_mw": str((data_reg + ctrl_reg) * mw), "sym_ptx_mw": str((data_sym + ctrl_sym) * mw),
        "sleep_slots": str(sleep_slots), "sleep_data_reg": str(sleep_data_reg), "sleep_sym": str(sleep_sym),
        "dl_tb_bytes": str(dl), "ul_tb_bytes": str(ul), "connected_ues": "0", "power_alloc": alloc,
    }


def test_models_file_matches_pinned_sha256(tmp_path):
    assert MODELS["sha256"] == em.EXPECTED_SHA256
    changed = tmp_path / "energy_models.json"
    data = json.loads(em.DEFAULT_MODELS_PATH.read_text(encoding="utf-8"))
    data["earth"]["types"]["macro"]["p_sleep_w"] = 4.3
    changed.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError):
        em.load_models(changed)
    assert em.load_models(changed, expected_sha256=None)["earth"].p_sleep_w == 4.3


def test_set_by_bandwidth():
    assert TR1.set_for(20e6) == "set2" and TR1.bandwidth_ratio(20e6) == 1.0
    assert TR1.set_for(10e6) == "set2" and TR1.bandwidth_ratio(10e6) == 0.5      # S12
    assert TR1.set_for(100e6) == "set1" and TR1.bandwidth_ratio(100e6) == 1.0


def test_idle_cell_whole_life_is_micro_sleep_floor():
    rows = [row(0.1 * k) for k in range(1, 301)]                                  # 30 s sem transmissão
    e = em.energy_window(rows, TR1, 0.0, 30.0, bandwidth_hz=20e6)
    assert e == pytest.approx(30000 * SLOT_S * 50)                                # N_slot·T_slot·P3 (Cat. 1, Set 2)
    assert em.energy_window(rows, EARTH, 0.0, 30.0) == pytest.approx(30.0 * 130.0)


def test_sleeping_cell_is_deep_sleep_plus_one_transition():
    rows = [row(0.1 * k, sleep_slots=100) for k in range(1, 101)]                 # 10 s em sono
    episodes = [(1, 0.0, 10.0)]
    e1 = em.energy_window(rows, TR1, 0.0, 10.0, episodes, bandwidth_hz=20e6)
    assert e1 == pytest.approx(10.0 * 1 + 1000 / 1000)                            # P1·T + E1 (Cat. 1, deep)
    e2 = em.energy_window(rows, TR2, 0.0, 10.0, episodes, bandwidth_hz=20e6)
    assert e2 == pytest.approx(10.0 * 2.1 + 1088 / 1000)                          # Cat. 2: deep de 10 s não cabe
    assert em.energy_window(rows, EARTH, 0.0, 10.0, episodes) == pytest.approx(10.0 * 75.0)


def test_full_load_slot_matches_docs17_example_in_bw_mode():
    # docs/17 §2.3: modo bw, todos os 14 símbolos, teto de 30 % contra 100 %: 200 -> 137 u.r.; EARTH 224 -> 158 W
    full = row(0.1, data_sym=1400, rb_frac=1.0, alloc="bw")
    capped = row(0.1, data_sym=1400, rb_frac=0.3, alloc="bw")
    assert em.energy_window([full], TR1, 0.0, 0.1, bandwidth_hz=20e6) / 0.1 == pytest.approx(200.0)
    assert em.energy_window([capped], TR1, 0.0, 0.1, bandwidth_hz=20e6) / 0.1 == pytest.approx(137.0, abs=0.05)
    p_out_w = P_REF_MW / 1000                                                    # 43 dBm = 19,95 W (≈ 20 W)
    assert em.energy_window([full], EARTH, 0.0, 0.1) / 0.1 == pytest.approx(130 + 4.7 * p_out_w)       # ≈ 224 W
    assert em.energy_window([capped], EARTH, 0.0, 0.1) / 0.1 == pytest.approx(130 + 4.7 * 0.3 * p_out_w,
                                                                            rel=1e-3)                   # ≈ 158 W


def test_used_mode_cap_does_not_change_energy_when_all_symbols_transmit():
    full = row(0.1, data_sym=1400, rb_frac=1.0, alloc="used")
    capped = row(0.1, data_sym=1400, rb_frac=0.3, alloc="used")
    for model in (TR1, TR2):
        assert em.energy_window([capped], model, 0.0, 0.1, bandwidth_hz=20e6) == pytest.approx(
            em.energy_window([full], model, 0.0, 0.1, bandwidth_hz=20e6))
    assert em.energy_window([capped], EARTH, 0.0, 0.1) == pytest.approx(em.energy_window([full], EARTH, 0.0, 0.1))


def test_window_convention_and_sleep_state_choice():
    rows = [row(1.0), row(1.1), row(1.2)]
    assert em.energy_window(rows, TR1, 1.0, 1.2, bandwidth_hz=20e6) == pytest.approx(2 * 0.1 * 50)  # t0 < t <= t1
    assert TR1.sleep_state(0.03) == "light_sleep" and TR1.sleep_state(0.004) == "micro_sleep"
    assert TR2.sleep_state(10.5) == "deep_sleep" and TR2.sleep_state(10.0) == "light_sleep"


def test_sleep_episodes_from_actuation_and_from_rows():
    act = [
        {"time_s": "15", "cell_id": "1", "parameter": "CELL_STATE", "value": "0", "status": "APPLIED"},
        {"time_s": "16", "cell_id": "1", "parameter": "CELL_STATE", "value": "0", "status": "APPLIED"},  # reaplicado
        {"time_s": "18", "cell_id": "1", "parameter": "CELL_STATE", "value": "1", "status": "APPLIED"},
        {"time_s": "20", "cell_id": "2", "parameter": "CELL_STATE", "value": "0", "status": "APPLIED"},
        {"time_s": "21", "cell_id": "2", "parameter": "TX_POWER", "value": "10", "status": "APPLIED"},
    ]
    assert em.sleep_episodes_from_actuation(act, 30.0) == [(1, 15.0, 18.0), (2, 20.0, 30.0)]
    rows = [row(2.0), row(2.1, sleep_slots=40), row(2.2, sleep_slots=100), row(2.3, sleep_slots=70), row(2.4)]
    (cell, start, end), = em.sleep_episodes_from_rows(rows)
    assert cell == 1 and start == pytest.approx(2.06) and end == pytest.approx(2.27)


def test_metrics_without_cell_state_are_none_and_proxy_is_kept():
    act = [{"time_s": "16", "gnb": "0", "cell_id": "1", "parameter": "PRB_QUOTA", "value": "30", "status": "APPLIED"},
           {"time_s": "18", "gnb": "1", "cell_id": "2", "parameter": "CELL_STATE", "value": "0", "status": "APPLIED"}]
    out = em.energy_metrics(None, [], act, MODELS, 15.0, 20.0, bandwidth_hz=20e6, sim_end_s=30.0, n_gnbs=2)
    assert all(out[k] is None for k in em.ENERGY_METRICS if k != "energy_proxy_commanded")
    assert out["power_alloc"] is None
    # Proxy: 2 células cheias por 1 s, 1,3 por 2 s, 0,3 por 2 s -> média em 5 s
    assert out["energy_proxy_commanded"] == pytest.approx((2 * 1 + 1.3 * 2 + 0.3 * 2) / 5)


def test_metrics_with_cell_state():
    cells = [row(15.0 + 0.1 * k, cell=c, data_sym=600, ctrl_sym=200, dl=1000, ul=10) for k in range(1, 51) for c in (1, 2)]
    kpi = [{"t_end_s": f"{15.0 + 0.1 * k:.3f}", "rx_bytes": "1250"} for k in range(1, 51)]
    out = em.energy_metrics(cells, kpi, [], MODELS, 15.0, 20.0, bandwidth_hz=20e6, sim_end_s=30.0, n_gnbs=2)
    assert out["bits_conflict"] == 8 * 1250 * 50
    assert out["energy_per_bit_j"] == pytest.approx(out["energy_conflict_j"] / out["bits_conflict"])
    assert out["energy_conflict_fullload_s"] == pytest.approx(out["energy_conflict_tr1"] / 200.0)
    assert out["prb_occupancy_conflict"] == pytest.approx(600 / 1400)
    assert out["ul_share"] == pytest.approx(10 / 1010)
    assert out["sleep_time_s"] == 0 and out["sleep_leak_reg"] == 0 and out["power_alloc"] == "used"
    assert out["energy_proxy_commanded"] == pytest.approx(2.0)


def _analyzer():
    spec = importlib.util.spec_from_file_location("analyze_conflict_runs", CERT / "analyze_conflict_runs.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _fake_run(tmp_path, name, with_cell_state):
    run = tmp_path / name
    (run / "raw").mkdir(parents=True)
    (run / "execution_manifest.json").write_text(json.dumps({"run_status": "SUCCESS", "command": "x --seed=1"}),
                                                 encoding="utf-8")
    kpi = ["t_end_s,cell_id,rx_packets,rx_bytes,throughput_mbps,mean_delay_ms"]
    kpi += [f"{0.1 * k:.3f},1,10,12500,1.0,2.0" for k in range(1, 301)]
    (run / "raw" / "rdl_kpi_timeseries.csv").write_text("\n".join(kpi) + "\n", encoding="utf-8")
    if with_cell_state:
        rows = [row(0.1 * k, cell=c, data_sym=600, ctrl_sym=200) for k in range(1, 301) for c in (1, 2)]
        header = list(rows[0])
        lines = [",".join(header)] + [",".join(r[h] for h in header) for r in rows]
        (run / "raw" / "rdl_cell_state.csv").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return run


def test_analyze_run_energy_columns(tmp_path):
    an = _analyzer()
    catalog = json.loads((ROOT / "simulations/ns3/conflicts/catalog.json").read_text(encoding="utf-8"))
    old = an.analyze_run(_fake_run(tmp_path, "nr_G1_B0_seed1", False), catalog, MODELS)
    new = an.analyze_run(_fake_run(tmp_path, "nr_G1_B3_seed1", True), catalog, MODELS)
    assert old["energy_conflict_tr1"] is None and old["power_alloc"] == "used"
    assert new["energy_conflict_tr1"] > 0 and new["energy_conflict_j"] > 0 and new["power_alloc"] == "used"
    assert old["thp_conflict"] == new["thp_conflict"]                              # colunas antigas inalteradas
    rows = [old, new]
    an.add_paired_savings(rows)
    assert new["saving_vs_b0_tr1_pct"] is None                                     # o B0 da semente não tem energia
    agg = an.aggregate(rows)
    md = an.render(agg, rows, [], "2026-11-13T00:00:00Z", MODELS["sha256"])
    assert "Energia na janela de conflito" in md and MODELS["sha256"] in md
