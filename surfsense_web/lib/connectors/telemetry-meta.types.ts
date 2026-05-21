export type ConnectorTelemetryGroup = "oauth" | "composio" | "crawler" | "other" | "unknown";

export interface ConnectorTelemetryMeta {
	connector_type: string;
	connector_title: string;
	connector_group: ConnectorTelemetryGroup;
	is_oauth: boolean;
}
