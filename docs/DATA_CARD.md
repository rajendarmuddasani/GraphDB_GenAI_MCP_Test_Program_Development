# Synthetic Data Card

## Assets

| Asset | Count | Provenance | License |
|---|---:|---|---|
| Framework graph | 8 symbols, 12 methods | Independently generated | CC0-1.0 |
| Intent benchmark | 96 requests | Independently generated | CC0-1.0 |
| Java compile stubs | 7 classes | Independently generated | CC0-1.0 |

No employer, customer, product, tester, silicon, test-program, log, or source-code data is included.

## Benchmark Split

Each split has 24 supported and 8 adversarial/unsupported requests:

| Split | Cases | Role |
|---|---:|---|
| Development | 32 | Implementation feedback |
| Validation | 32 | Candidate selection and safety gates |
| Confirmation | 32 | Opened once for the selected policy |

Supported scenario families are disjoint across splits. Adversarial strings and case IDs are unique. The generator script fails if counts, uniqueness, or group isolation change.

## Covered Variations

- Three supported natural-language forms
- Distinct synthetic module/class/config names
- Path traversal
- Unsupported version
- Instruction injection
- Control character
- Invalid class and package names
- Invalid config extension
- Oversized intent

## Known Gaps

- Free-form paraphrases and multilingual requests
- Ambiguous or incomplete requirements
- Real Java framework type systems
- Large graphs, graph drift, and missing/contradictory metadata
- Concurrent clients and distributed services
- Human review quality and productivity impact

The benchmark is appropriate for regression and safety contracts inside this bounded implementation. It is not representative evidence for production language understanding.