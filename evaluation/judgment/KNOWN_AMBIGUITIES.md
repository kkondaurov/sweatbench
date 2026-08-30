# Known ambiguities excluded from Judgment scoring

- **Expiry exactly at reporting inception.** Request 6 does not say whether a lot expiring exactly
  on `starts_on` belongs entirely to opening state or should also appear as an inception-day
  movement. R4 deliberately uses one lot expired strictly before inception and one expiring strictly
  after it.
- **Deadline on already-cancelled groups.** Request 2 determines the policy version of existing
  readable groups, but does not make `refundable_until` operationally meaningful after settlement.
  R1 checks the version and preserved settlement, not that field.
