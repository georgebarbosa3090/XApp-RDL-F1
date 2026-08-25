# Troubleshooting e Solução: Falha de Diretório Helm Chart (`no such file or directory`)

**Documento:** Relatório de Diagnóstico e Procedimento de Recuperação  
**Projeto:** xApp RDL (Resource and Decision Layer)  
**Ambiente:** Servidor Near-RT RIC (`SAC-10806`)  
**Data:** 25/08/2026  

---

## 1. Identificação do Problema

Durante a tentativa de empacotamento e deploy da xApp RDL via Helm no cluster, foram registradas as seguintes falhas consecutivas no terminal:

```text
root@SAC-10806:~/XApp-RDL-F1# helm lint deploy/helm/iqos-xapp-rdl
==> Linting deploy/helm/iqos-xapp-rdl
Error unable to check Chart.yaml file in chart: stat deploy/helm/iqos-xapp-rdl/Chart.yaml: no such file or directory
Error: 1 chart(s) linted, 1 chart(s) failed

root@SAC-10806:~/XApp-RDL-F1# helm package deploy/helm/iqos-xapp-rdl
Error: stat deploy/helm/iqos-xapp-rdl: no such file or directory

root@SAC-10806:~/XApp-RDL-F1# helm upgrade --install ricxapp-iqos-xapp-rdl ./iqos-xapp-rdl-1.1.0.tgz \
  --namespace ricxapp \
  --create-namespace
Release "ricxapp-iqos-xapp-rdl" does not exist. Installing it now.
Error: path "./iqos-xapp-rdl-1.1.0.tgz" not found
```

---

## 2. Análise de Causa Raiz

| Falha Registrada | Causa Raiz Identificada | Impacto |
| :--- | :--- | :--- |
| `stat deploy/helm/iqos-xapp-rdl/Chart.yaml: no such file or directory` | A pasta `deploy/helm/iqos-xapp-rdl/` ainda não havia sido baixada no servidor via `git pull origin main` ou criada localmente no filesystem do host. | O comando `helm lint` e `helm package` são interrompidos imediatamente por ausência do descritor `Chart.yaml`. |
| `Error: path "./iqos-xapp-rdl-1.1.0.tgz" not found` | Como o comando anterior `helm package` falhou, o arquivo binário compactado `.tgz` não foi gerado no diretório corrente. | O comando `helm install/upgrade` não encontra o pacote de release para aplicar no Kubernetes. |

---

## 3. Solução Definitiva (Procedimento Autônomo / Offline)

Para resolver a dependência imediatamente sem necessidade de esperar autenticação do Git, executa-se o script autônomo abaixo no terminal do servidor `SAC-10806`.

### 3.1. Gerar a Estrutura Completa do Helm Chart

```bash
# 1. Entrar no diretório do projeto e criar a árvore de diretórios
cd ~/XApp-RDL-F1
mkdir -p deploy/helm/iqos-xapp-rdl/templates

# 2. Criar Chart.yaml
cat << 'EOF' > deploy/helm/iqos-xapp-rdl/Chart.yaml
apiVersion: v2
name: iqos-xapp-rdl
description: Near-RT RIC xApp Resource and Decision Layer (RDL) for O-RAN Conflict Mitigation
type: application
version: 1.1.0
appVersion: "1.1.0"
maintainers:
  - name: OpenRAN Brasil / IQoS Team
    email: contact@openran.org.br
EOF

# 3. Criar values.yaml
cat << 'EOF' > deploy/helm/iqos-xapp-rdl/values.yaml
replicaCount: 1

image:
  repository: iqos-xapp-rdl
  pullPolicy: IfNotPresent
  tag: "1.1.0"

imagePullSecrets: []
nameOverride: ""
fullnameOverride: "ricxapp-iqos-xapp-rdl"

serviceAccount:
  create: false
  name: ""

podAnnotations:
  prometheus.io/scrape: "true"
  prometheus.io/port: "8081"
  prometheus.io/path: "/metrics"

podSecurityContext:
  runAsNonRoot: true
  runAsUser: 1000

securityContext:
  allowPrivilegeEscalation: false
  capabilities:
    drop:
      - ALL

env:
  useFakeSdl: "false"
  rmrSeedRt: "/app/configs/routes.rt"
  configFile: "/app/configs/config-file.json"
  rmrWaitForReady: "true"
  logLevel: "INFO"

service:
  http:
    type: ClusterIP
    port: 8080
    targetPort: 8080
  metrics:
    type: ClusterIP
    port: 8081
    targetPort: 8081
  rmr:
    type: ClusterIP
    dataPort: 4560
    routePort: 4561

resources:
  limits:
    cpu: 2000m
    memory: 4Gi
  requests:
    cpu: 500m
    memory: 512Mi

livenessProbe:
  httpGet:
    path: /health
    port: 8080
  initialDelaySeconds: 5
  periodSeconds: 15

readinessProbe:
  httpGet:
    path: /ready
    port: 8080
  initialDelaySeconds: 10
  periodSeconds: 15

nodeSelector: {}
tolerations: []
affinity: {}
EOF

# 4. Criar templates/_helpers.tpl
cat << 'EOF' > deploy/helm/iqos-xapp-rdl/templates/_helpers.tpl
{{- define "iqos-xapp-rdl.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{- define "iqos-xapp-rdl.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{- define "iqos-xapp-rdl.labels" -}}
helm.sh/chart: {{ include "iqos-xapp-rdl.chart" . }}
{{ include "iqos-xapp-rdl.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{- define "iqos-xapp-rdl.selectorLabels" -}}
app: {{ include "iqos-xapp-rdl.fullname" . }}
app.kubernetes.io/name: {{ include "iqos-xapp-rdl.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{- define "iqos-xapp-rdl.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}
EOF

# 5. Criar templates/deployment.yaml
cat << 'EOF' > deploy/helm/iqos-xapp-rdl/templates/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "iqos-xapp-rdl.fullname" . }}
  labels:
    {{- include "iqos-xapp-rdl.labels" . | nindent 4 }}
spec:
  replicas: {{ .Values.replicaCount }}
  selector:
    matchLabels:
      {{- include "iqos-xapp-rdl.selectorLabels" . | nindent 6 }}
  template:
    metadata:
      {{- with .Values.podAnnotations }}
      annotations:
        {{- toYaml . | nindent 8 }}
      {{- end }}
      labels:
        {{- include "iqos-xapp-rdl.selectorLabels" . | nindent 8 }}
    spec:
      terminationGracePeriodSeconds: 15
      securityContext:
        {{- toYaml .Values.podSecurityContext | nindent 8 }}
      containers:
        - name: {{ .Chart.Name }}
          securityContext:
            {{- toYaml .Values.securityContext | nindent 12 }}
          image: "{{ .Values.image.repository }}:{{ .Values.image.tag | default .Chart.AppVersion }}"
          imagePullPolicy: {{ .Values.image.pullPolicy }}
          env:
            - name: USE_FAKE_SDL
              value: {{ .Values.env.useFakeSdl | quote }}
            - name: RMR_SEED_RT
              value: {{ .Values.env.rmrSeedRt | quote }}
            - name: CONFIG_FILE
              value: {{ .Values.env.configFile | quote }}
            - name: RMR_WAIT_FOR_READY
              value: {{ .Values.env.rmrWaitForReady | quote }}
            - name: LOG_LEVEL
              value: {{ .Values.env.logLevel | quote }}
          ports:
            - name: rmr-data
              containerPort: {{ .Values.service.rmr.dataPort }}
              protocol: TCP
            - name: rmr-route
              containerPort: {{ .Values.service.rmr.routePort }}
              protocol: TCP
            - name: http-health
              containerPort: {{ .Values.service.http.port }}
              protocol: TCP
            - name: http-metrics
              containerPort: {{ .Values.service.metrics.port }}
              protocol: TCP
          livenessProbe:
            {{- toYaml .Values.livenessProbe | nindent 12 }}
          readinessProbe:
            {{- toYaml .Values.readinessProbe | nindent 12 }}
          resources:
            {{- toYaml .Values.resources | nindent 12 }}
      {{- with .Values.nodeSelector }}
      nodeSelector:
        {{- toYaml . | nindent 8 }}
      {{- end }}
      {{- with .Values.affinity }}
      affinity:
        {{- toYaml . | nindent 8 }}
      {{- end }}
      {{- with .Values.tolerations }}
      tolerations:
        {{- toYaml . | nindent 8 }}
      {{- end }}
EOF

# 6. Criar templates/service-http.yaml
cat << 'EOF' > deploy/helm/iqos-xapp-rdl/templates/service-http.yaml
apiVersion: v1
kind: Service
metadata:
  name: {{ include "iqos-xapp-rdl.fullname" . }}-http
  labels:
    {{- include "iqos-xapp-rdl.labels" . | nindent 4 }}
spec:
  type: {{ .Values.service.http.type }}
  ports:
    - port: {{ .Values.service.http.port }}
      targetPort: {{ .Values.service.http.targetPort }}
      protocol: TCP
      name: http-health
    - port: {{ .Values.service.metrics.port }}
      targetPort: {{ .Values.service.metrics.targetPort }}
      protocol: TCP
      name: http-metrics
  selector:
    {{- include "iqos-xapp-rdl.selectorLabels" . | nindent 4 }}
EOF

# 7. Criar templates/service-rmr.yaml
cat << 'EOF' > deploy/helm/iqos-xapp-rdl/templates/service-rmr.yaml
apiVersion: v1
kind: Service
metadata:
  name: {{ include "iqos-xapp-rdl.fullname" . }}-rmr
  labels:
    {{- include "iqos-xapp-rdl.labels" . | nindent 4 }}
spec:
  type: {{ .Values.service.rmr.type }}
  ports:
    - port: {{ .Values.service.rmr.dataPort }}
      targetPort: {{ .Values.service.rmr.dataPort }}
      protocol: TCP
      name: rmr-data
    - port: {{ .Values.service.rmr.routePort }}
      targetPort: {{ .Values.service.rmr.routePort }}
      protocol: TCP
      name: rmr-route
  selector:
    {{- include "iqos-xapp-rdl.selectorLabels" . | nindent 4 }}
EOF
```

---

## 4. Execução do Empacotamento e Deploy

Com os arquivos criados, execute a sequência padrão:

```bash
# 1. Validar a integridade estrutural do chart
helm lint deploy/helm/iqos-xapp-rdl
# Saída esperada: 1 chart(s) linted, 0 chart(s) failed

# 2. Empacotar o chart em .tgz
helm package deploy/helm/iqos-xapp-rdl
# Saída esperada: Successfully packaged chart and saved it to: /root/XApp-RDL-F1/iqos-xapp-rdl-1.1.0.tgz

# 3. Executar o deploy no namespace ricxapp
helm upgrade --install ricxapp-iqos-xapp-rdl ./iqos-xapp-rdl-1.1.0.tgz \
  --namespace ricxapp \
  --create-namespace

# 4. Acompanhar a subida do Pod
kubectl get pods -n ricxapp -l app=ricxapp-iqos-xapp-rdl -w
```
