{{/*
Expand the name of the chart.
*/}}
{{- define "clusters-4wm.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "clusters-4wm.fullname" -}}
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

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "clusters-4wm.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "clusters-4wm.labels" -}}
helm.sh/chart: {{ include "clusters-4wm.chart" . }}
{{ include "clusters-4wm.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "clusters-4wm.selectorLabels" -}}
app.kubernetes.io/name: {{ include "clusters-4wm.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "clusters-4wm.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "clusters-4wm.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{- define "clusters-4wm.databaseHost" -}}
{{- if .Values.database.external }}
{{- printf "%s" .Values.database.host }}
{{- else }}
{{- printf "%s-database" (include "clusters-4wm.fullname" . ) }}
{{- end }}
{{- end }}

{{- define "clusters-4wm.databaseName" -}}
{{- if not .Values.database.external -}}
{{- printf "%s-db" (include "clusters-4wm.fullname" . ) }}
{{- end -}}
{{- end -}}

{{- define "clusters-4wm.databaseLabel" -}}
{{- if not .Values.database.external -}}
app.kubernetes.io/name: {{ include "clusters-4wm.databaseName" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}
{{- end -}}
