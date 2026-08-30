# R1: policy history upgrade

**Concept.** Effective-dated policy survives an upgrade for active and already-settled groups.

**Entitlement.** Request 2 says existing groups remain readable and receive the policy implied by
their original booking date; policy is fixed at opening; rescheduling recomputes the deadline; and
the upgrade must not rewrite cash already refunded or retained.

**Scenario.** Seed milestone 1 with active old/new-policy groups plus a post-cutover group already
refunded under the then-current behavior. Upgrade to milestone 2. Check policy versions for every
group, the active rescheduled group's deadline and cancellation behavior, and unchanged historical
settlement. Do not assert `refundable_until` for an already-cancelled group.

**Canary.** Assign every pre-upgrade group `flex-14` regardless of booking date.
