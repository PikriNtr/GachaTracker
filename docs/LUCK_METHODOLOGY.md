# Luck Percentile Methodology

> How `/simulate` computes your luck percentile — and what it does NOT tell you.

---

## What the command does

1. Your **featured character banner** history (pool `1` for WuWa, `301`/`400` for
   Genshin, `1` for HSR) is analyzed: the pity value of every 5-star you pulled
   and your 50/50 record.
2. Your **average pity per 5-star** is compared against **10,000 simulated
   players** whose histories are generated with the game's probability model
   (below), stopping each simulation at the same number of "featured" 5-stars
   you have (50/50 wins + guaranteed pulls).
3. Your **luck percentile** = the percentage of simulated players whose average
   pity is *worse* (higher) than yours.

Interpretation: percentile 90 means 90% of simulated players needed more pulls
per 5-star than you did.

---

## The probability model

Per game, the simulation uses a base rate, a soft-pity ramp, and a hard cap:

| Game | Base 5★ rate | Soft pity starts | Rate increase | Hard pity |
|---|---|---|---|---|
| Wuthering Waves | 0.8% | pull 61 | +5%/pull | 80 |
| Genshin Impact | 0.6% | pull 74 | +6%/pull | 90 |
| Honkai: Star Rail | 0.6% | pull 74 | +6%/pull | 90 |

Notes:

- The **50/50 mechanic** is simulated: each 5-star has a `rateup_chance`
  (0.5 for character events) of being the featured unit; losing flips the
  next 5-star to guaranteed. Config lives in `analytics/pity.py`
  (`rateup_chance`), models in `analytics/simulation.py`.
- The weapon/light-cone event banners use different rate-ups (75/25 for HSR)
  and are **not** simulated individually.
- These parameters match community-measured models, not official formulas.

---

## What this analysis is NOT

- **Not a prediction.** Gacha pulls are independent random events. Your past
  luck does not change future odds — being "unlucky" does not mean a win is
  "due". Each pull's probability is identical regardless of your history
  (pity excepted, which is already deterministic).
- **Not a measure of skill or value.** A low percentile does not mean you
  played wrong; a high percentile is not an achievement. It is descriptive
  statistics, nothing more.
- **Not exact.** Sample sizes matter: with only 2–3 five-stars on record, your
  average pity is extremely noisy and the percentile swings wildly. The
  percentile becomes meaningful only with roughly 10+ five-stars of history.
- **Not independent of banner choice.** The simulation compares you against
  the featured *character* banner only. Pulls on standard/weapon banners are
  not part of the comparison.

---

## Implementation references

- Model + simulation loop: `gacha_tracker/analytics/simulation.py`
- Banner configs (caps, 50/50 pools, rate-up chance): `gacha_tracker/analytics/pity.py`
- Tests: `gacha_tracker/tests/test_analytics_ui.py`
