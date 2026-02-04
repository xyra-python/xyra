# Sentinel Journal

## 2025-05-20 – Python `urllib.parse.parse_qsl` default unlimited fields
**Vulnerability pattern:** `parse_qsl` without `max_num_fields` allows Hash Collision / CPU Exhaustion DoS
**Learned constraint:** Always set `max_num_fields` when parsing user-supplied query strings or form data
**Prevention:** Enforce limit (e.g. 1000) in all parsing utilities
