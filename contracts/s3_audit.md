# s3_audit contract

Producer: `s3-audit` (SC-28 evidence). Extends the common core in `_core.md`.

## Status vocabulary (raw in fixtures → staging)

| Raw (fixture) | Normalized (staging) |
|---------------|----------------------|
| PASS          | PASS                 |
| WARN          | WARN                 |
| FAIL          | FAIL                 |

Encryption checks emit only `PASS` \| `FAIL`. Public-access-block checks can emit all three.

## Check catalog

| check_id | Meaning |
|----------|---------|
| `s3-bucket-encryption-enabled` | Bucket default encryption on/off |
| `s3-bucket-public-access-block-all-enabled` | All four PAB settings enabled |

## resource_id semantics

Bucket name (string). Strong identifier — one finding subject per bucket per check.

## Extension fields (mandatory)

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `enc_type` | string, nullable | no | SSE algorithm, passed through from `SSEAlgorithm` — `AES256`, `aws:kms`, `aws:kms:dsse`. **Non-exhaustive** (AWS adds algorithms; DSSE-KMS arrived in 2023) — do not pin a closed `accepted_values` test on it. Present on encryption `PASS`; null otherwise. The SC-28 detail a bare core would drop. |

**Producer limitation:** both checks wrap the AWS call in a broad `ClientError`
handler that maps **any** client error (including `AccessDenied`) to `FAIL`,
printing the same "Not configured" line regardless of cause — false-FAIL risk
on a live retrofit.

Note this is the *only* path to an encryption `FAIL` — there is no
successful-response FAIL branch. **The intended trigger is stale on live AWS:**
since January 5, 2023, S3 applies SSE-S3 to every bucket as base-level
encryption, and `GetBucketEncryption` returns that default configuration for an
unconfigured bucket instead of raising. On a live retrofit the check's `FAIL`
path is reached in practice by other client errors (`AccessDenied` the
plausible one) — an error signal, not an encryption finding. Recorded, not
fixed: modernizing the check (e.g. asserting the algorithm rather than the
configuration's presence) is producer-repo work. The fixture's
`backups-unencrypted` row exercises the producer's `except` branch, which the
contract covers even though live AWS no longer produces its intended trigger.

**Producer limitation:** `s3-bucket-encryption-enabled` checks whether bucket
default encryption is on. It does not report the key source. `enc_type` passes
through `SSEAlgorithm` (`AES256`, `aws:kms`, `aws:kms:dsse`). That value is not
a CMK ARN, and it does not say who manages the key. `aws:kms` can still be the
AWS-managed `aws/s3` key. Per the `s3-audit` README, the CJIS column for SC-28
reads "Agency-managed CMK required", and agencies must provision their own KMS
CMKs and use SSE-KMS with those CMKs. That README is not the CJIS policy text.
A `PASS` with `enc_type` `AES256` is indeterminate under CJIS v6.1 SC-28.
SSE-S3 never uses an agency CMK, but the agency-CMK requirement comes from that
README and is not verified against the CJIS policy text. A
`PASS` with `enc_type` `aws:kms` or `aws:kms:dsse` is indeterminate under CJIS
v6.1 SC-28. The key may be the AWS-managed `aws/s3` key or an agency CMK. Both
`PASS` results remain valid
FedRAMP High SC-28 evidence. A fixture `FAIL` that records no encryption is
CJIS evidence of a gap. A live `FAIL` is an error signal, per the `ClientError`
limitation above. This is the only CJIS-mapped check in `dim_controls` that
emits `PASS`. The fixture row `app-data-encrypted` is the `AES256` `PASS`.
The seed row for CJIS v6.1 SC-28 stays.
`dim_controls` maps relevance. Dropping the row would discard the
`backups-unencrypted` `FAIL`.

The `s3-audit` README lists "Report encryption key source (CMK ARN)" under
Future Enhancements. That item is unbuilt. If it ships, this limitation
retires. Recorded, not fixed. The check is producer-repo work.

Producer controls (SC-28) travel via `dim_controls` on `check_id` — not restated as this repo's controls.
