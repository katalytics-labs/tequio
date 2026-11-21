# API, messaging and integration reference

Use when the project exchanges contracts or messages across services, or needs correlated observability. Skip for single-process work without external interfaces. Shared source, execution and qualification rules: [coverage guide](coverage-guide.md).

## Three distinct concerns — do not collapse them

- Contracts and compatibility: request/response shapes, versioning, error semantics and backward compatibility. [Google AIP](https://google.aip.dev/general) (index accessed 2026-11-17, includes compatibility/versioning guidance; no page version stated) and OpenAPI are optional design aids, not a middleware architecture or required dependency. License terms differ for content versus code; inspect before reuse.
- Delivery semantics: duplicates, ordering, retries, dead-lettering and backpressure are properties of the actual broker/protocol and consumer design, not of a description format. The [AsyncAPI document](https://www.asyncapi.com/docs/concepts/asyncapi-document) (accessed 2026-11-17; example shows spec version 3.0.0, protocol bindings vary) describes a communication contract; it guarantees nothing about delivery by itself.
- Trace propagation and privacy: [OpenTelemetry context propagation](https://opentelemetry.io/docs/concepts/context-propagation/) (accessed 2026-11-17; default propagator uses W3C TraceContext headers; no page version stated) explains correlation across boundaries. Baggage and trace attributes can carry private data across services — scrutinize what is propagated and to whom. Observability is a distinct tool choice, not a complete integration design.

## Sources

The selected broker, protocol and SDK's exact-version primary docs supply actual delivery/retention/ordering behavior. The candidates above are scoped starting points; none is mandatory, and none guarantees current behavior for your stack.

## Exercise considerations

Realistic exercises include a duplicate event, an out-of-order event, a consumer timeout with bounded retry, and a check that private fields never enter trace baggage or exported spans. Cover expected and denied/failure behavior with actual project evidence.
