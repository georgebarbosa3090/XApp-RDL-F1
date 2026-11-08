{{- define "nori-ns3.name" -}}nori-ns3{{- end -}}

{{- define "nori-ns3.labels" -}}
app.kubernetes.io/name: {{ include "nori-ns3.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
helm.sh/chart: {{ .Chart.Name }}-{{ .Chart.Version }}
{{- end -}}

{{- define "nori-ns3.selector" -}}
app.kubernetes.io/name: {{ include "nori-ns3.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}
