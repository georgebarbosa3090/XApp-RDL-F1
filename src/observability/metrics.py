from typing import Any

try:
    from prometheus_client import REGISTRY, CollectorRegistry, Counter, Histogram, Gauge, start_http_server
    HAS_PROMETHEUS = True
except ImportError:
    HAS_PROMETHEUS = False
    REGISTRY = None
    class _DummyMetric:
        def __init__(self, *args, **kwargs): pass
        def inc(self, *args, **kwargs): pass
        def set(self, *args, **kwargs): pass
        def observe(self, *args, **kwargs): pass
        def labels(self, *args, **kwargs): return self
    Counter = Histogram = Gauge = _DummyMetric
    def start_http_server(port, registry=None): pass

def _get_or_create(metric_cls, name: str, documentation: str, labelnames=(), registry=None, **kwargs):
    if not HAS_PROMETHEUS:
        return metric_cls(name, documentation, labelnames=labelnames, **kwargs)
    reg = registry or REGISTRY
    if hasattr(reg, "_names_to_collectors") and name in reg._names_to_collectors:
        return reg._names_to_collectors[name]
    try:
        return metric_cls(name, documentation, labelnames=labelnames, registry=reg, **kwargs)
    except (ValueError, Exception):
        if hasattr(reg, "_names_to_collectors") and name in reg._names_to_collectors:
            return reg._names_to_collectors[name]
        raise

class MetricsServer:
    def __init__(self, port: int = 8081, registry=None):
        self.port = port
        self.registry = registry
        self._init_metrics()

    def _init_metrics(self):
        reg = self.registry
        # RMR
        self.rmr_rx = _get_or_create(Counter, 'rdl_rmr_messages_received_total', 'Total RMR messages received', registry=reg)
        self.rmr_tx = _get_or_create(Counter, 'rdl_rmr_messages_sent_total', 'Total RMR messages sent', registry=reg)
        self.rmr_errors = _get_or_create(Counter, 'rdl_rmr_message_errors_total', 'Total RMR message errors', registry=reg)
        
        # KPM
        self.kpm_ind = _get_or_create(Counter, 'rdl_kpm_indications_total', 'Total KPM indications received', registry=reg)
        self.kpm_decode_err = _get_or_create(Counter, 'rdl_kpm_decode_errors_total', 'Total KPM decode errors', registry=reg)
        
        # Subscriptions
        self.subs_total = _get_or_create(Counter, 'rdl_subscriptions_total', 'Total subscriptions created', registry=reg)
        self.subs_failures = _get_or_create(Counter, 'rdl_subscription_failures_total', 'Total subscription failures', registry=reg)
        
        # RDL Logic
        self.action_proposals = _get_or_create(Counter, 'rdl_action_proposals_total', 'Total action proposals received', registry=reg)
        self.conflicts = _get_or_create(Counter, 'rdl_conflicts_detected_total', 'Total conflicts detected', labelnames=['type'], registry=reg)
        self.decisions = _get_or_create(Counter, 'rdl_decisions_total', 'Total decisions made', labelnames=['strategy'], registry=reg)
        
        # Control
        self.ctrl_req = _get_or_create(Counter, 'rdl_control_requests_total', 'Total control requests sent', registry=reg)
        self.ctrl_ack = _get_or_create(Counter, 'rdl_control_ack_total', 'Total control acks received', registry=reg)
        self.ctrl_fail = _get_or_create(Counter, 'rdl_control_failures_total', 'Total control failures', registry=reg)
        self.ctrl_timeout = _get_or_create(Counter, 'rdl_control_timeouts_total', 'Total control timeouts', registry=reg)
        
        # Latency
        self.decision_latency = _get_or_create(Histogram, 'rdl_decision_latency_seconds', 'Decision latency', registry=reg)
        self.control_latency = _get_or_create(Histogram, 'rdl_control_latency_seconds', 'Control latency', registry=reg)
        self.e2e_latency = _get_or_create(Histogram, 'rdl_e2e_loop_latency_seconds', 'E2E loop latency', registry=reg)
        
        # Gauges
        self.active_e2_nodes = _get_or_create(Gauge, 'rdl_active_e2_nodes', 'Active E2 nodes', registry=reg)
        self.active_xapps = _get_or_create(Gauge, 'rdl_active_xapps', 'Active xApps', registry=reg)
        self.active_subs = _get_or_create(Gauge, 'rdl_active_subscriptions', 'Active subscriptions', registry=reg)
        self.ready_state = _get_or_create(Gauge, 'rdl_ready', 'Is RDL ready (1 or 0)', registry=reg)

    def record_kpm(self):
        self.kpm_ind.inc()

    def update_active_xapps(self, count: int):
        self.active_xapps.set(count)

    def record_conflict(self, conflict: Any):
        ctype = getattr(conflict, "conflict_type", None)
        cname = getattr(ctype, "name", str(ctype)) if ctype else "UNKNOWN"
        self.conflicts.labels(type=cname).inc()

    def record_resolution(self, resolution: Any, latency_s: float):
        strat = getattr(resolution, "strategy_used", None)
        sname = getattr(strat, "name", str(strat)) if strat else "UNKNOWN"
        self.decisions.labels(strategy=sname).inc()
        self.decision_latency.observe(latency_s)

    def start(self):
        if HAS_PROMETHEUS:
            try:
                start_http_server(self.port)
            except Exception:
                pass

