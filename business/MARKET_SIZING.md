# Spice — Market Sizing (TAM / SAM / SOM)

> Versioned home for the market-sizing model behind the deck. Figures prepared 2026-06-28.
> The per-client revenue model and GTM revenue ramp built on top of these numbers live in
> [`UNIT_ECONOMICS.md`](UNIT_ECONOMICS.md). Source tags `[Sx]` map to the `## Sources` list below.

## Core thesis

Spice turns fragmented SME commodity risk into institutional-scale hedge, procurement and
market-intelligence flow.

## Unit economics by typical business

| Business type | Annual hedge notional | Procurement volume | Short-term base revenue/client | Long-term base revenue/client |
| --- | ---: | ---: | ---: | ---: |
| Boulangeries / food craft | €83.9k | €251.6k | €795 | €5.4k |
| Road transport / logistics | €352.7k | €1.1M | €2.6k | €18.9k |
| Construction / renovation | €185.3k | €555.0k | €1.5k | €10.6k |
| Plastics / resins | €590.9k | €590.9k | €4.2k | €13.1k |
| Metalwork / fabrication | €277.6k | €555.0k | €2.2k | €11.2k |
| Woodworking / joinery | €370.3k | €370.3k | €2.7k | €8.3k |
| Light manufacturing | €449.2k | €898.0k | €3.3k | €17.4k |

## SMEs by type — observed and inferred

| Vertical | Observed source categories | EU+US observed SMEs | Share used | Formal worldwide estimate | Broad MSME estimate |
| --- | --- | ---: | ---: | ---: | ---: |
| Construction | EU construction + US construction | 10.09M | 10-19% | 10-19M | 40-76M |
| Transport / logistics | EU mobility/transport/auto + US transport/warehousing | 5.87M | 6-11% | 6-11M | 24-44M |
| Food service / bakeries | EU tourism/agri-food + US accommodation/food; overlaps noted | 4.90M | 3-6% | 3-6M | 12-24M |
| Manufacturing / industrial | EU energy-intensive/electronics/textiles + US manufacturing | 1.59M | 2-6% | 2-6M | 8-24M |
| Retail / wholesale | EU retail + US retail/wholesale | 9.50M | 10-17% | 10-17M | 40-68M |

## Revenue TAM / SAM / SOM

| Vertical | Formal TAM clients | EU+US SAM clients | Mature revenue/client | Revenue TAM | Revenue SAM |
| --- | ---: | ---: | ---: | ---: | ---: |
| Construction | 5.08M | 3.53M | €10.6k | €53.7B | €37.4B |
| Transport / logistics | 4.25M | 2.94M | €18.8k | €80.1B | €55.3B |
| Food service / bakeries | 1.12M | 1.23M | €5.4k | €6.1B | €6.7B |
| Manufacturing / industrial | 1.80M | 0.72M | €13.5k | €24.3B | €9.6B |
| Retail / wholesale | 2.02M | 1.43M | €2.5k | €5.1B | €3.6B |
| **Total** | **14.28M** | **9.83M** | Blended | **€169.3B** | **€112.6B** |

Base revenue **TAM: €169.3B/year** across **14.3M** suitable formal SME accounts.
Base revenue **SAM: €112.6B/year** across **9.8M** suitable EU+US accounts.

| SOM scenario | SAM penetration | Clients | Annual revenue |
| --- | ---: | ---: | ---: |
| Conservative SOM | 0.05% | 4,916 | €56.3M |
| Base SOM | 0.15% | 14,748 | €168.9M |
| Upside SOM | 0.50% | 49,160 | €562.9M |

> **Two vertical groupings, one reconciliation.** The "Unit economics by typical business" table
> uses 7 granular craft/industrial verticals; the TAM/SAM table aggregates into 5 verticals (incl.
> retail). They tie out at the blended level: the mature revenue/client column, weighted by TAM
> client counts, blends to **€11,855** = €169.3B ÷ 14.28M. The 7-vertical table drives the per-client
> build-up chart; the 5-vertical table drives market sizing.

## Sources

- [S1] United Nations — MSMEs Day: MSMEs are ~90% of businesses worldwide, 60-70% of employment, ~50% of global GDP. https://www.un.org/en/observances/micro-small-medium-businesses-day
- [S2] World Bank — SME Finance: SMEs ~90% of businesses and >half of global employment; MSME finance gap is a major global issue. https://www.worldbank.org/ext/en/topic/competitiveness/small-and-medium-enterprises-smes-finance
- [S3] IFC / World Bank — MSME Finance Gap, 2017: ~162M formal MSMEs in developing countries; 65M credit-constrained (40% of formal MSMEs in 128 countries). https://documents1.worldbank.org/curated/en/653831510568517947/pdf/121264-WP-PUBLIC-MSMEReportFINAL.pdf
- [S4] OECD — SMEs and entrepreneurship: across the OECD, SMEs ~99% of all firms and 50-60% of value added. https://www.oecd.org/en/topics/policy-issues/smes-and-entrepreneurship.html
- [S5] European Commission — SME Performance Review: 2025/2026 review reports **34M SMEs in the EU**. https://single-market-economy.ec.europa.eu/smes/sme-strategy-and-sme-friendly-business-conditions/sme-performance-review_en
- [S6] European Commission — Annual Report on European SMEs 2024: 2023 counts by ecosystem — construction 6.54M, retail 5.82M, tourism 3.78M, mobility/transport/auto 2.05M, agri-food 0.67M, energy-intensive 0.58M. https://www.ggb.gr/sites/default/files/basic-page-files/Annual%20Report%20on%20European%20SMEs%202024.pdf
- [S7] U.S. SBA Office of Advocacy — 2024 Small Business Profile: **34.8M U.S. small businesses**; construction 3.55M, transportation/warehousing 3.82M, retail 3.01M, accommodation/food 1.13M, manufacturing 0.60M. https://advocacy.sba.gov/wp-content/uploads/2024/11/United_States.pdf
- [S8] Hong Kong Trade and Industry Department — SME statistics: ~357k SMEs as of March 2026, >98% of enterprises. https://www.success.tid.gov.hk/english/aboutus/what_are_sme.html
- [S9] U.S. GAO — Group Purchasing Organizations: largest GPOs reported **average vendor contract administrative fees of 1.22%-2.25%** by purchasing volume (2008); some codes cap admin fees at 3%. https://www.gao.gov/assets/a308834.html
- [S10] GAO/GPO fee analysis (peer-reviewed): five largest healthcare GPOs had $130.7B purchasing volume and $2.3B fees (FY2012); **reported fee ranges ~0.86%-3.62%** by category. https://pmc.ncbi.nlm.nih.gov/articles/PMC4315108/
- [S11] Privilèges-Pro — Groupement d'achat PME: SME buying groups mutualize purchases to obtain large-account prices; remuneration is typically supplier commission or purchase margin. https://www.privileges-pro.com/content/27-quest-ce-quun-groupement-dachat-pme
- [S12] OECD — Competition and purchasing groups: purchasing groups can improve conditions for small buyers; buyer-power and cartel risks require careful competition-law design. https://one.oecd.org/document/DAF/COMP(2022)4/fr/pdf
- [S13] CFTC — Futures Commission Merchants and Introducing Brokers: FCMs and IBs must register unless exempt; capital, customer-funds, disclosure and filing requirements. https://www.cftc.gov/IndustryOversight/Intermediaries/FCMs/fcmib
- [S14] Databento — Introducing Broker overview: IBs solicit/accept futures/options/swaps orders but do not accept customer money; **compensation is often volume-based**. https://databento.com/compliance/introducing-broker-ib
- [S15] FIA — Commodity derivatives under MiFID II: EU commodity derivatives subject to MiFID II/MiFIR — exemptions, position limits, reporting. https://www.fia.org/fia/articles/special-report-commodity-derivatives-under-mifid-ii
- [S16] Grand View Research — Data marketplace platforms: revenue estimated at **USD 1.49B (2024) → USD 5.73B (2030)**; subscription is the largest model. https://www.grandviewresearch.com/industry-analysis/data-marketplace-market-report
- [S17] Global NAPs — SMEs: ~400M SMEs globally, >95% of firms and 60-70% of employment; used here only as a broad upper-bound universe. https://globalnaps.org/issue/small-medium-enterprises-smes/
