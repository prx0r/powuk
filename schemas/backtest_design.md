# Causal-latency backtests

## Principle

Pre-register event timestamp rules before computing returns.

For each hypothesis/event family define:

```yaml
root_event:
  source:
  metric:
  threshold:
  persistence:
  timestamp_field:

exposure:
  relationship_types:
  minimum_confidence:

market_response:
  metric:
  threshold:
  baseline_window:
  horizon:

controls:
  sector:
  market:
  macro:
```

## Never leak future information

Examples of leakage:
- using a later confirmed component mapping to reclassify historical record without storing when mapping became available
- using revised data as if known at original release
- choosing event threshold after seeing price response
- using company disclosure to define a physical event that supposedly preceded the disclosure

## Key outputs

- distribution of physical→market lags
- lag by signal type
- lag by market cap/liquidity
- lag by analyst coverage if sourced later
- false positive rate
- signal decay
- cross-sectional exposure response
- supply-response lag after price/capital response

## The target question

Not:
“Does the stock go up?”

But:
“Which physical signals are consistently assimilated slowly enough to be economically informative?”
