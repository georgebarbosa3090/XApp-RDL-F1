{{- define "kpm-probe.name" -}}kpm-probe{{- end -}}

{{- define "kpm-probe.labels" -}}
app.kubernetes.io/name: {{ include "kpm-probe.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
helm.sh/chart: {{ .Chart.Name }}-{{ .Chart.Version }}
{{- end -}}

{{- define "kpm-probe.selector" -}}
app.kubernetes.io/name: {{ include "kpm-probe.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}
