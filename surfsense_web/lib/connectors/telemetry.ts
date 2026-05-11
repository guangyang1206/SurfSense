/**
 * Connector telemetry metadata — single source of truth for analytics.
 *
 * Moved out of `components/` so that `lib/posthog/events.ts` (and any other
 * lib-level module) can import telemetry data without creating an illegal
 * upward-import edge (lib → components).
 */

import type {
  OAUTH_CONNECTORS,
  COMPOSIO_CONNECTORS,
  CRAWLERS,
  OTHER_CONNECTORS,
} from "@/components/assistant-ui/connector-popup/constants/connector-constants";

export type ConnectorTelemetryGroup = "oauth" | "composio" | "crawler" | "other" | "unknown";

export interface ConnectorTelemetryMeta {
  connector_type: string;
  connector_title: string;
  connector_group: ConnectorTelemetryGroup;
  is_oauth: boolean;
}

const CONNECTOR_TELEMETRY_REGISTRY: ReadonlyMap<string, ConnectorTelemetryMeta> = (() => {
  const map = new Map<string, ConnectorTelemetryMeta>();

  for (const c of OAUTH_CONNECTORS) {
    map.set(c.connectorType, {
      connector_type: c.connectorType,
      connector_title: c.title,
      connector_group: "oauth",
      is_oauth: true,
    });
  }
  for (const c of COMPOSIO_CONNECTORS) {
    map.set(c.connectorType, {
      connector_type: c.connectorType,
      connector_title: c.title,
      connector_group: "composio",
      is_oauth: true,
    });
  }
  for (const c of CRAWLERS) {
    map.set(c.connectorType, {
      connector_type: c.connectorType,
      connector_title: c.title,
      connector_group: "crawler",
      is_oauth: false,
    });
  }
  for (const c of OTHER_CONNECTORS) {
    map.set(c.connectorType, {
      connector_type: c.connectorType,
      connector_title: c.title,
      connector_group: "other",
      is_oauth: false,
    });
  }

  return map;
})();

/**
 * Returns telemetry metadata for a connector_type, or a minimal "unknown"
 * record so tracking never no-ops for connectors that exist in the backend
 * but were forgotten in the UI registry.
 */
export function getConnectorTelemetryMeta(connectorType: string): ConnectorTelemetryMeta {
  const hit = CONNECTOR_TELEMETRY_REGISTRY.get(connectorType);
  if (hit) return hit;

  return {
    connector_type: connectorType,
    connector_title: connectorType,
    connector_group: "unknown",
    is_oauth: false,
  };
}
