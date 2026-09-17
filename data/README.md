# Data dictionary and methodology

## Scope

This is the original hand-curated portfolio selection: **8 model rows from 7 brands** (BYD has two). Geely's unused standalone row was retired; Zeekr retains its group relationship. The original sampling rationale was not recorded. The repair keeps that selection rather than claiming a representative census or a complete current product catalogue.

**Source-review date: 2026-09-17.** This is a review snapshot, not a common model year, price-validity date or reporting period. Variant context is explicit: historical Seal MY23-25, Dolphin MY25, Zeekr MY24, XPeng MY25, the cited NIO variant, historical Xiaomi launch specifications, Jaecoo MY2026, and an unresolved Li L9 trim. Sources can subsequently change. The manual review and source locators are recorded in [SOURCES.md](SOURCES.md); reproducing the calculations does not reproduce the external websites at a past date.

Model specification contexts: Europe, China (inherited original selection), and Australia. Retained EUR prices are Dutch listings only. Regional evidence retains the original four areas: Europe (including the UK), Southeast Asia, Middle East and Latin America. China and Australia are specification contexts, not additional presence-matrix regions.

## Files and keys

- `model_specs.csv`: one selected model/variant per row; key `(brand, model)`.
- `brands.csv`: one brand per row; key `brand`; editorial descriptions are not measurements.
- `expansion_markets.csv`: legacy filename retained; now one brand–region evidence record per row, key `(brand, region)`. No score.

All CSVs use UTF-8, a semicolon separator, decimal points, and empty cells for missing values. Each model joins to one brand (`many_to_one`). Presence is kept separate so that the four regions do not multiply model rows or KPI denominators.

## Model fields

| Field | Meaning / unit |
|---|---|
| `brand`, `model` | Selected brand and model/variant identity; not a complete brand range |
| `variant_context` | Model year, source edition or historical disclosure context; unresolved where not established |
| `specification_market` | Market context of the specification; not a sales-presence indicator |
| `powertrain_type` | BEV = battery electric; EREV = extended-range electric. EREV is not chemistry |
| `battery_chemistry` | Source-specific LFP, NMC or NMC811; NMC811 is within the NMC family. Blank when not established |
| `battery_capacity_kwh` | Sourced capacity in kWh; interpret only with basis |
| `battery_capacity_basis` | `usable`, `nominal`, or `unspecified`; never assume the latter means usable |
| `electric_range_km` | Sourced electric driving range in km, not fuel-plus-electric total range |
| `range_standard` | `EV Database Real Range`, `WLTP`, or `CLTC`; not interchangeable |
| `total_range_km`, `total_range_standard` | Reserved separate fields for sourced comprehensive range; currently all blank because the original L9 figure was not verified for a specific trim |
| `price_eur` | Directly published EUR listing; no currency conversion, imputation, subscription estimate or transaction inference |
| `price_market` | `Netherlands` for every retained price |
| `price_basis` | Listed recommended retail price excluding indirect incentives; confirm options, battery ownership and availability before commercial use |
| `availability_context` | `listed_available`: source listed order availability when reviewed; `historical`: historical/discontinued specification; `not_established`: unresolved |
| `source`, `source_url` | Publication and direct locator supporting retained values (page number in source name where applicable) |
| `verification_date` | ISO date of review, including an unsuccessful attempt where noted; not a new model-release date |
| `verification_status` | `verified_values`: retained values matched the source; `partial`: some original attributes could not be substantiated and are withheld. Neither means independent road testing or a complete row |
| `notes` | Missing-value rationale and limitations specific to the row |

EV Database Real Range is the publisher's standardized estimate. WLTP and CLTC are different test-cycle claims. Xiaomi's 800 km is an **up-to historical CLTC claim**. No cross-standard mean, conversion factor, composite ranking or causal technology comparison is calculated.

Five capacities have a usable basis. Jaecoo's 58.9 kWh is explicitly unspecified because the Australian sheet does not distinguish nominal and usable. Li Auto and Xiaomi capacities remain blank. No chemistry-versus-range chart or mixed capacity average is produced. Acceleration was removed because it is not used in this case and retaining it would add verification burden without decision value.

## Price/range comparison and KPIs

The comparison subset must satisfy every condition:

1. BEV powertrain;
2. non-missing Dutch EUR RRP with the documented price basis;
3. source lists the variant as available on the review date;
4. non-missing EV Database Real Range.

Four rows qualify: Dolphin, Zeekr 001, XPeng G6, NIO ET5 Touring. The Seal's historical price remains in the table but not in this comparison. A common publisher and price market improve comparability; equipment, segment, model year and purchase terms still differ. The scatter is not a best-value recommendation. No average price is reported.

| KPI | Formula and scope |
|---|---|
| Models selected | Count of model rows after brand filtering; unique model keys are validated |
| Brands represented | Distinct brands in those model rows |
| Comparable price + range | Count meeting all four rules / selected model count |
| Electric range evidence | Non-missing sourced electric range / selected model count; evidence coverage only |
| Presence evidence coverage (presence tab) | Resolved `present` or `absent` cells / all selected brand–region cells; four cells per selected brand |

Default values are **8; 7; 4/8; 7/8**, and presence evidence coverage is **7/28**. There are five retained EUR prices, but only four current-listing comparison rows. The count of range values does not imply that their magnitudes are comparable.

## Brand fields

`group_or_company` and `relationship` distinguish a `group_brand`, `group_business`, or `operating_company`; `not_established` leaves the mapping blank. These are documented relationships, not a complete ownership tree or an assertion of independence. `source_url` and `verification_date` support the mapping. BYD's corporate mapping is intentionally not asserted in this compact review. `positioning_editorial` describes the selected case, not externally verified market positioning. Group-level evidence is never attributed automatically to every brand in the group.

## International presence

**Operational definition:** at least one named country within a region has a source-supported commercial passenger-car listing, official sales/test-drive channel, or reported customer deliveries for the brand. Sources and evidence dates are retained per resolved cell. A dated delivery event establishes documented activity on that date, not uninterrupted operations thereafter. Availability listings are secondary evidence from EV Database; official BYD and JAECOO sources support other cells. Mere expansion plans and a parent group's operations do not qualify.

- `present`: qualifying country-level evidence exists, described in `evidence_note`.
- `absent`: would require explicit evidence covering the defined region and relevant time; **no cell currently meets that burden**.
- `unknown`: insufficient qualifying evidence retained in this bounded review. Not equivalent to zero, absent, planned or withdrawn.

Additional fields: `evidence_country` identifies the witness country; `evidence_date` is the publication/event date or review date for a current listing; `source`, `source_url`, `verification_date`, and `evidence_note` make the decision inspectable.

The matrix contains **7 present, 21 unknown, 0 absent** cells. Europe has evidence for BYD, Zeekr, XPeng, NIO and Jaecoo; BYD also has Thailand and Brazil evidence. Research depth is uneven. Do not rank brands by number of documented regions, treat unknown as absence, or infer market attractiveness. JAECOO UK evidence concerns a PHEV; it does not prove UK availability of the selected Australian J5 EV. Brand presence is not selected-model presence or BEV-only presence.

## Missing values and transformations

Blank means unavailable, unverified, not retained or not applicable as explained in notes. It is never filled with another vehicle's mean. The app displays “Not verified” for unavailable specifications and supplies a clear empty comparison state. Li Auto has no verified numeric attributes for the selected trim. Xiaomi's former EUR price and battery values were withheld; its historical range is independently linked to a company disclosure.

The workflow validates columns, keys, date syntax, categories and metric context, joins brand metadata, selects comparable rows, and counts evidence. CSVs are manually reviewed inputs; the notebook validates and analyzes them without rewriting them. Editing data requires a new source review, metadata update, notebook execution, tests and refreshed screenshots where needed.

## Provenance and reuse

The original repository described manual curation. The 2026-09-17 repair used AI assistance for source checking, code, documentation and regression tests. External publishers provide the factual evidence; AI output is not a data source. No independent vehicle testing or owner validation is claimed.

No open-data redistribution permission was established for all underlying sources. This repository makes no claim that third-party data, marks or source content are openly licensed. Only a compact attributed factual selection is retained; no complete source pages or reports are bundled. Source terms still apply. No blanket code/data licence is added.
