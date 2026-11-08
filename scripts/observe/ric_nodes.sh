#!/usr/bin/env bash
# Aba Estado do RIC: nós E2 no E2Mgr (conexão, RAN functions), subscrições no SubMgr e xApps no AppMgr,
# atualizados a cada 3 s (consulta feita de dentro do pod da xApp, que alcança os serviços do RIC).
export KUBECONFIG="${KUBECONFIG:-/etc/rancher/k3s/k3s.yaml}"
exec watch -t -n 3 "kubectl -n ricxapp exec deploy/kpm-probe -- python3 -c '
import json, urllib.request
def get(u):
    try: return json.loads(urllib.request.urlopen(u, timeout=2).read() or b\"null\")
    except Exception as e: return str(e)
print(\"== E2Mgr: nós E2\")
for n in get(\"http://service-ricplt-e2mgr-http.ricplt:3800/v1/nodeb/states\") or []:
    print(\"  \", n.get(\"inventoryName\"), n.get(\"connectionStatus\"), n.get(\"globalNbId\"))
print(\"== SubMgr: subscrições REST\")
for s in get(\"http://service-ricplt-submgr-http.ricplt:8088/ric/v1/subscriptions\") or []:
    print(\"  \", s.get(\"SubscriptionId\"), s.get(\"Meid\"), s.get(\"ClientEndpoint\"), s.get(\"E2EventInstanceId\"))
print(\"== AppMgr: xApps registradas\")
for x in get(\"http://service-ricplt-appmgr-http.ricplt:8080/ric/v1/xapps\") or []:
    print(\"  \", x.get(\"name\"), x.get(\"status\"), [i.get(\"rxMessages\") for i in x.get(\"instances\") or []][:1])
' 2>&1 | cut -c1-200"
