{{/*
Expand the name of the chart.
*/}}
{{- define "clusters-metadata-api.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "clusters-metadata-api.fullname" -}}
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
{{- define "clusters-metadata-api.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "clusters-metadata-api.labels" -}}
helm.sh/chart: {{ include "clusters-metadata-api.chart" . }}
{{ include "clusters-metadata-api.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "clusters-metadata-api.selectorLabels" -}}
app.kubernetes.io/name: {{ include "clusters-metadata-api.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{- define "clusters-metadata-api.databaseHost" -}}
{{- if .Values.database.external }}
{{- printf "%s" .Values.database.host }}
{{- else }}
{{- printf "%s-database" (include "clusters-metadata-api.fullname" . ) }}
{{- end }}
{{- end }}

{{- define "clusters-metadata-api.databaseName" -}}
{{- if not .Values.database.external -}}
{{- printf "%s-db" (include "clusters-metadata-api.fullname" . ) }}
{{- end -}}
{{- end -}}

{{- define "clusters-metadata-api.databaseLabel" -}}
{{- if not .Values.database.external -}}
app.kubernetes.io/name: {{ include "clusters-metadata-api.databaseName" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}
{{- end -}}
