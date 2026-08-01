# Same method, applied evenly: 3F's claim vs. UK & US nationals on EU passports
*Data: Statistics Denmark (VAN1AAR/VAN2AAR), 2007-2025, nationwide*

3F reported (via Information) that Denmark has seen a rise in dual-nationality arrivals using EU
passports: **~1,200 Nepal-origin Portuguese-passport holders**
(+79% in two years) and
**~3,200 Argentina-origin Italian-passport holders**
(+74% in two years).

Those are *stock* figures — total people currently resident — almost certainly from a bespoke Statistics
Denmark register extract that isn't available through the public Statbank API. The public API only exposes
*flow*: immigration/emigration events tagged with country of last residence and citizenship. We built a
**net cumulative stock proxy** (immigration minus emigration, summed since 2007) as the closest public-data
approximation, and checked it against 3F's real numbers:

| Route | Our proxy (2025) | 3F's real figure | Undercount |
|---|---|---|---|
| Argentina -> Italy | ~1,415 | ~3,200 | ~2.3x |
| Nepal -> Portugal | ~17 | ~1,200 | ~70x |

The Nepal/Portugal undercount is severe because Portugal's (until 2026) relatively easy citizenship route
required **10 years of legal residency in Portugal** — so someone born in Nepal who did Nepal -> Portugal ->
Denmark shows up in Danish migration data as arriving *from Portugal*, indistinguishable from a native
Portuguese citizen. Italian citizenship, by contrast, is ancestry-based with no residency requirement, so
Argentina -> Italy direct moves are a much better (if still imperfect) match for the proxy.

**We cannot confirm or refute 3F's exact figures.** What we *can* do is apply the same imperfect method,
with the same known bias, to UK and US nationals — and see whether the "backdoor citizenship" framing holds
up once it's applied evenly.

## UK and USA, by the same method

**UK-origin, top EU citizenships held (net stock proxy):**
  1. Ireland: 501 (was 309, +62%)
  2. Italy: 315 (was 250, +26%)
  3. Poland: 309 (was 219, +41%)
  4. France: 266 (was 202, +32%)
  5. Germany: 194 (was 167, +16%)
  **Total, any EU citizenship: 2,402** (was 1,689, +42%)

**USA-origin, top EU citizenships held (net stock proxy):**
  1. France: 128 (was 98, +31%)
  2. Germany: 104 (was 51, +104%)
  3. Ireland: 98 (was 61, +61%)
  4. Spain: 45 (was 25, +80%)
  5. Italy: 26 (was 3, +767%)
  **Total, any EU citizenship: 347** (was 122, +184%)

## The comparison, side by side

| Route | 2025 proxy | 2023 proxy | 2-year growth |
|---|---|---|---|
| Argentina -> Italy (3F's claim) | 1,415 | 1,213 | +17% |
| Nepal -> Portugal (3F's claim) | 17 | 11 | +55% |
| UK -> any EU citizenship | 2,402 | 1,689 | +42% |
| USA -> any EU citizenship | 347 | 122 | +184% |

**UK's total EU-passport stock proxy (2,402) is already bigger than Argentina->Italy's proxy
(1,415) using the identical method** — and USA's is growing far faster
in percentage terms (+184% vs Argentina's +17% over the same two years, by this method). Ireland is UK
nationals' closest analogue to the Argentina/Italy mechanism (pure ancestry citizenship, no residency
requirement), so it should carry a similar undercount factor to Argentina->Italy's ~2.3x — which would put
UK->Ireland's *true* stock in the same range as 3F's reported Nepal->Portugal figure (~1,200), not the
501 shown by the raw proxy.

## Why this matters for the framing

- **Ancestry- and residency-based EU citizenship is a normal, structural feature of several EU states'
  nationality law** (Italy, Ireland, Portugal, Poland, and others). It shows up wherever there was a
  historic emigration wave — Italians to Argentina/Brazil, Irish to the US/UK, Portuguese to former
  colonies, Bulgarians to Turkey, Romanians to Moldova.
- **Applying 3F's own logic evenly would flag British and American migration to Denmark as an equally
  large, equally fast-growing "loophole"** — which nobody is proposing, because the concern was never
  really about scale. The Nepal/Argentina framing reads as alarming because of who's arriving on these
  passports, not the underlying mechanism or the numbers.
- The one part of 3F's framing we can't wave away: Jens Arnholtz (KU) is right that this was never the
  intended purpose of free movement, and Portugal itself has now tightened its rules from 2026 — so
  something about the *specific* Portugal route was real enough to prompt a policy change, independent of
  whether 3F's precise numbers hold up.

## Caveats to carry into the piece

- Net cumulative flow (since 2007) is a floor, not a stock count — it ignores deaths, citizenship changes
  after arrival, people born in Denmark to these parents, and multi-country routes (Nepal -> Portugal ->
  Denmark). All of these push the true numbers up, not down.
- "Any EU citizenship" for UK/USA sums current EU-27 membership; the club's composition changed over the
  2007-2025 window (Bulgaria/Romania 2007, Croatia 2013), so the earliest years slightly understate what
  would have counted as "EU" at the time.
- Country of last residence != birthplace != ethnicity in all of this. Treat every number here as
  suggestive, not definitive — including 3F's.
