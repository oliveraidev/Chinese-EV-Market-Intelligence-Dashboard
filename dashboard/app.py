"""Compact, source-transparent competitor screening; run with Streamlit."""
from pathlib import Path
import sys

import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from dashboard.data import load_data, comparable_models, kpis, presence_matrix

st.set_page_config(page_title="Chinese EV | Competitor Screening", layout="wide")
st.title("Chinese EV · Competitor Screening")
st.caption("MARKET INTELLIGENCE  /  Source review: 17 September 2026")
st.write("How do selected Chinese EV models compare on like-for-like vehicle attributes, "
         "and where is international brand presence documented?")
st.caption("For market-intelligence analysts and importers building an initial research shortlist. "
           "Eight selected models, not a market census. Historical specifications are labelled. "
           "No sales performance, market-entry recommendation or causal inference.")

try:
    models, brands, presence = load_data()
except (OSError, ValueError, pd.errors.ParserError) as exc:
    st.error(f"Cannot load the portfolio data: {exc}. Check the CSV files in data/.")
    st.stop()

brand = st.sidebar.selectbox("Brand", ["All"] + sorted(models.brand.unique()))
st.sidebar.caption("All figures and views follow this selection. Missing evidence remains unknown.")
selected = models if brand == "All" else models.loc[models.brand.eq(brand)].copy()
scope = presence.loc[presence.brand.isin(selected.brand.unique())].copy()
metrics = kpis(selected)
columns = st.columns(4)
for column, label, value, help_text in zip(columns,
        ["Models selected", "Brands represented", "Comparable price + range", "Electric range evidence"],
        [metrics['models'], metrics['brands'], f"{metrics['comparable']} / {metrics['models']}",
         f"{metrics['range']} / {metrics['models']}"],
        ["Count of distinct model rows in the selection.", "Count of distinct brands in the selection.",
         "BEV; Dutch listed RRP; currently listed available; EV Database Real Range. No imputation.",
         "Non-missing sourced electric-range values. Standards differ; this is coverage, not an average."]):
    column.metric(label, value, help=help_text)

overview, international = st.tabs(["Model comparison", "International presence"])


def number(value, decimals=0):
    return "Not verified" if pd.isna(value) else f"{value:,.{decimals}f}"


with overview:
    st.subheader("Model comparison")
    st.caption("Source-checked values only. Scroll horizontally for context and source links; "
               "‘Partial’ means some fields are withheld, not that missing values are zero.")
    display = pd.DataFrame({
        "Brand": selected.brand,
        "Model": selected.model,
        "Powertrain": selected.powertrain_type,
        "Price / market": selected.apply(lambda r: "Not verified" if pd.isna(r.price_eur)
                                         else f"€{r.price_eur:,.0f} · {r.price_market}", axis=1),
        "Electric range": selected.apply(lambda r: "Not verified" if pd.isna(r.electric_range_km)
                                         else f"{r.electric_range_km:,.0f} km · {r.range_standard}", axis=1),
        "Battery": selected.apply(lambda r: "Not verified" if pd.isna(r.battery_capacity_kwh)
                                  else f"{r.battery_capacity_kwh:g} kWh · {r.battery_capacity_basis} · {r.battery_chemistry}", axis=1),
        "Status": selected.verification_status.map({'verified_values': 'Source-checked', 'partial': 'Partial'}),
        "Availability": selected.availability_context,
        "Variant / period": selected.variant_context,
        "Price basis": selected.price_basis.fillna("Not verified"),
        "Source": selected.source_url,
        "Reviewed": selected.verification_date,
        "Notes": selected.notes,
    })
    st.dataframe(display, hide_index=True, width="stretch", height=325,
                 column_config={"Source": st.column_config.LinkColumn("Source", display_text="Open source")})

    st.subheader("Comparable Dutch listings")
    comparison = comparable_models(selected)
    st.caption(f"{len(comparison)} of {len(selected)} selected models qualify: BEV, Netherlands listed RRP, "
               "listed available on the source-review date, and EV Database Real Range. "
               "Prices exclude indirect incentives. These are listing comparisons, not transaction prices; "
               "confirm options and battery ownership terms. The historical Seal is excluded.")
    if comparison.empty:
        st.info("No models in this selection meet the comparison rules. See individual sourced values above.")
    else:
        fig, ax = plt.subplots(figsize=(8.5, 3.4), layout="constrained")
        ax.scatter(comparison.price_eur, comparison.electric_range_km, color="#087f8c", s=75)
        for row in comparison.itertuples():
            label = f"{row.brand} {row.model.split()[0]}"
            ax.annotate(label, (row.price_eur, row.electric_range_km), xytext=(7, 7),
                        textcoords="offset points", fontsize=9)
        ax.set(xlabel="Netherlands listed RRP (€)", ylabel="EV Database Real Range (km)")
        ax.margins(x=0.20, y=0.25)
        ax.grid(alpha=0.15)
        ax.spines[['top', 'right']].set_visible(False)
        st.pyplot(fig, width="stretch")
        plt.close(fig)

    with st.expander("Battery context — individual capacities, never a mixed average"):
        st.write("Usable capacity is available to drive the vehicle; nominal capacity is the full rated pack. "
                 "An unspecified basis is not treated as usable. NMC811 is a subtype of NMC. "
                 "EREV describes a powertrain, not battery chemistry.")
        battery = selected[['brand', 'model', 'battery_chemistry', 'battery_capacity_kwh', 'battery_capacity_basis']].copy()
        battery['battery_capacity_kwh'] = battery.battery_capacity_kwh.map(lambda x: number(x, 1))
        st.dataframe(battery.fillna("Not verified"), hide_index=True, width="stretch")

    with st.expander("Business observations — scope and limitations"):
        if {'XPeng', 'Zeekr'}.issubset(set(comparison.brand)):
            x = comparison.loc[comparison.brand.eq('XPeng')].iloc[0]
            z = comparison.loc[comparison.brand.eq('Zeekr')].iloc[0]
            st.markdown(f"**Observation:** The selected Zeekr has {z.electric_range_km-x.electric_range_km:.0f} km "
                        f"more EV Database Real Range and a €{z.price_eur-x.price_eur:,.0f} higher Dutch listed price "
                        "than the selected XPeng. **Business relevance:** A starting point to investigate the "
                        "price/range trade-off. **Limitation:** Different vehicle formats and equipment; no best-buy conclusion.")
        st.markdown(f"**Observation:** {metrics['comparable']} of {metrics['models']} selected models meet "
                    "the common price/range rules. **Business relevance:** The shortlist must separate comparable "
                    "listings from further research. **Limitation:** Exclusion is a data-context decision, not a negative brand assessment.")

with international:
    st.subheader("Documented international presence")
    st.write("A country-specific commercial listing, official sales/test-drive channel or delivery report "
             "can establish presence in that region. One country does not establish region-wide coverage.")
    st.caption("Brand-level evidence may concern a different model or powertrain. Unknown means insufficient "
               "evidence retained in this limited review — never absence. This is an evidence map, not an attractiveness ranking.")
    matrix = presence_matrix(scope)
    known = int(scope.presence_status.ne('unknown').sum())
    st.markdown(f"**Evidence coverage: {known} / {len(scope)} selected brand–region cells resolved.** "
                "Uneven research coverage prevents brand ranking by the number of documented regions.")
    codes = matrix.replace({'unknown': 0, 'present': 1, 'absent': 2}).astype(int)
    fig, ax = plt.subplots(figsize=(9, max(2.4, len(matrix) * .48 + .9)), layout="constrained")
    ax.imshow(codes, cmap=ListedColormap(['#edf1f4', '#087f8c', '#f0c987']), vmin=0, vmax=2, aspect='auto')
    ax.set_xticks(range(len(matrix.columns)), matrix.columns)
    ax.set_yticks(range(len(matrix.index)), matrix.index)
    for y, b in enumerate(matrix.index):
        for x, r in enumerate(matrix.columns):
            status = matrix.loc[b, r]
            ax.text(x, y, status.title(), ha='center', va='center', fontsize=9,
                    color='white' if status == 'present' else '#415164')
    ax.tick_params(length=0, pad=8)
    for spine in ax.spines.values():
        spine.set_visible(False)
    st.pyplot(fig, width="stretch")
    plt.close(fig)
    st.subheader("Evidence behind each cell")
    st.dataframe(scope[['brand', 'region', 'presence_status', 'evidence_country', 'evidence_date',
                        'source_url', 'verification_date', 'evidence_note']], hide_index=True, width="stretch",
                 column_config={'source_url': st.column_config.LinkColumn('Source', display_text='Open evidence')})
    st.caption("Use resolved cells to locate competitor evidence and unknown cells to plan further research. "
               "Presence does not measure demand, registrations, profitability or entry feasibility.")

with st.expander("Methodology, sources and limitations"):
    st.write("The original hand-curated eight-model case is retained; its original sampling rationale was not "
             "documented. Review date means the source was checked, not that all specifications are from 2026. "
             "No prices are imputed or converted from CNY. CLTC, WLTP and EV Database Real Range remain separate. "
             "Electric and total range are different fields; unverified numbers remain missing. "
             "Source-checked means matching a cited publication, not independently tested vehicle performance.")
    st.write("Li Auto retains its EREV identity but no trim-specific numeric claims. Xiaomi retains a historical "
             "800 km CLTC launch claim; battery data and its former EUR conversion are withheld. "
             "Jaecoo capacity is 58.9 kWh with an unspecified nominal/usable basis. "
             "Full field definitions and the source-review log are in data/README.md and data/SOURCES.md.")
    st.dataframe(brands.loc[brands.brand.isin(selected.brand)], hide_index=True, width="stretch",
                 column_config={'source_url': st.column_config.LinkColumn('Company source', display_text='Open source')})
    st.caption("Positioning is an editorial description of this selected case. Company/group links do not constitute "
               "a complete ownership tree. AI assisted the portfolio repair, documentation and tests; the evidence comes from cited external sources.")
