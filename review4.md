# powuk review4.md

> Looking across `datagarden`, `ographuk`, `cgraphuk`, UKOpportunity/UKBoring and the older UKGraph work, **POWUK has recovered the capacity side but has dropped several of the best economic primitives.**

The clean formulation should be:

```text
POWUK
=
UK physical capability
× local demand
× entry/crowding
× rules
× time
× observed outcomes
```

Current POWUK is mostly building:

```text
CAPACITY
training
certifications
firms
jobs
procurement
planning
```

The older work shows we're missing some important dimensions.

## 1. Wage/price response is the biggest missing layer

The old `datagarden/resources/ukgraph_resources.md` explicitly had:

```text
ASHE Table 15 — earnings by SOC × region
ASHE Table 14 — occupation × region
ASHE Table 5  — region × industry
ASHE Table 29 — industry × occupation
EARN06        — quarterly occupation earnings
Average Weekly Earnings
```

This matters enormously.

Currently POWUK can eventually know:

```text
electrician demand ↑
electrician supply →
```

but not necessarily:

```text
electrician wage £21/hr → £27/hr
```

The wage is basically an observable **shadow-price proxy for skilled labour**.

So add a first-class series:

```text
capability_price(
    capability,
    geography,
    time
)
```

using wages/salaries.

Then:

```text
demand ↑
capacity →
wages ↑
```

is much stronger evidence of real constraint than job adverts alone.

### P0 additions

```text
ONS ASHE historical releases
ONS EARN06
ONS Average Weekly Earnings
ONS online job-ad salaries
```

Backfill as far as practical.

---

# 2. We need actual workforce stock, not merely companies/providers

The old UKGraph work correctly had both:

```text
Companies House
```

and:

```text
Nomis / ONS labour stock
```

Current POWUK risks conflating:

```text
number of firms
```

with:

```text
number of people capable of doing work
```

Those are very different.

Add:

```text
SOC × geography × time:
employment
employees
self-employed
unemployment
claimants
hours worked
```

The **self-employed** piece is especially important because this is the "Dave/Gary with a van" economy we're specifically trying to model.

The old resource set had Nomis claimant count as one of the most timely local labour signals.

So:

```text
Nomis APS/LFS-derived occupation supply
Nomis claimant count
ONS Workforce Jobs
ONS vacancies by industry
```

should be core POWUK.

Then capability supply becomes:

```text
certified providers
+
estimated workers
+
self-employed workers
+
firms
+
training pipeline
```

instead of just company/register counts.

---

# 3. Bring back Entry / Exit / Crowding / Saturation

This was one of the strongest UK Opportunity ideas and has mostly vanished.

Do not model merely:

```text
demand vs supply
```

Model:

```text
DEMAND
CAPACITY
ENTRY
EXIT
PRICE
CROWDING
FRICTION
```

For every:

```text
Capability × Place × Time
```

calculate eventually:

```text
demand_momentum
entry_velocity
exit_velocity
capacity_growth
wage_momentum
crowding_acceleration
supplier_density
```

The question isn't merely:

> Are electricians scarce?

It is:

> Are electricians scarce **and is everybody already rushing into the shortage?**

Example:

```text
heat pumps

demand             +42%
installer capacity +8%
wages              +14%
apprentice starts  +55%
new businesses     +47%
```

This might mean the shortage is real but **rapidly being competed away**.

Compare:

```text
industrial controls

demand             +31%
capacity           +2%
wages              +18%
training pipeline  flat
business entry     +1%
```

Much more structurally interesting.

This is pure Seesaw.

---

# 4. Supplier population density

`UKOpportunity` explicitly preserved:

```text
SupplierPopulationDensity
```

This should return to POWUK.

Not simply:

```text
500 electricians in Manchester
```

but something normalized against relevant demand:

```text
providers / households
providers / commercial premises
providers / construction activity
providers / job demand
providers / £ procurement
```

Depending on capability.

Examples:

```text
EV installers / EV stock
heat-pump installers / eligible housing stock
electricians / building stock
HVAC firms / commercial floorspace
repairers / installed equipment stock
```

This turns raw counts into meaningful capacity.

---

# 5. Property/building stock should partially return

Not the whole giant UK property graph.

But **physical demand denominators** from UKGraph are extremely relevant.

Older UKGraph had:

```text
EPC
Land Registry
planning
property
```

POWUK probably wants EPC/building stock much more than Land Registry prices.

For example, heat-pump opportunity is not just:

```text
number of heat-pump jobs
```

It's:

```text
eligible homes
× current heating system
× EPC characteristics
× subsidy/regulatory environment
÷ local installation capacity
```

Likewise:

```text
solar
insulation
electrical upgrades
EV charging
retrofit
```

all benefit from building-stock denominators.

So bring in:

```text
EPC open data
building/property counts by geography
dwelling type
energy rating
heating type where available
```

This makes POWUK dramatically more grounded.

---

# 6. Regulation should be a causal object, not a document feed

This is one of the best things from the older system.

The old formulation was essentially:

```text
RULE / CHANGE
    ↓
affected entity
    ↓
prerequisite
    ↓
deadline
    ↓
required physical action
    ↓
supplier capability
    ↓
potential transaction
```

That belongs directly in POWUK.

Don't just collect GOV.UK pages mentioning EV chargers.

Represent:

```text
PolicyEvent
Rule
Requirement
AffectedPopulation
EffectiveDate
Deadline
RequiredCapability
```

Example:

```text
regulation X
↓
commercial landlords affected
↓
electrical modification required
↓
deadline 2028
↓
requires electrical_installation
↓
affected premises by LAD
↓
local qualified supply
```

Then POWUK can quantify **regulation-created demand**.

This is potentially one of the most unique parts of the entire garden.

---

# 7. Grants and subsidies are missing

UKOpportunity explicitly included:

```text
grant_programme_announcements
```

and Route type:

```text
GRANT
```

For POWUK they're even more interesting as **demand accelerants**.

Track programmes such as categories of:

```text
heat pump support
retrofit funding
EV infrastructure
industrial energy efficiency
skills/training subsidies
local authority decarbonisation
business capital grants
```

Canonical object:

```text
FundingProgramme

programme
opens_at
closes_at
budget
eligibility
geography
funded_action
required_capabilities
```

Then measure:

```text
£ subsidy / qualified local provider
```

That's a very powerful pressure measure.

---

# 8. Planning needs semantic downstream-demand mapping

Current POWUK appears to be treating:

```text
planning application count
```

as demand.

Old UKGraph was much better:

```text
PLANNING APPROVED
 ↓
future demand
 ├ electricians
 ├ plumbers
 ├ scaffolding
 ├ waste
 ├ flooring
 ├ broadband
 ├ EV charging
 └ property management
```

This is exactly the transformation worth preserving.

Planning should normalize:

```text
application
development_type
units
floorspace
status
decision_date
expected construction scale
```

and eventually map:

```text
development_type
→ capability demand vector
```

Example:

```text
200-flat development
→ electrical_installation
→ plumbing_heating
→ HVAC
→ telecom_cabling
→ solar
→ EV charging
```

Not with fake precision initially.

Store a versioned semantic mapping and improve it through outcomes.

---

# 9. Procurement needs `time-to-award` and supplier outcome history

The old opportunity garden retained:

```text
appearance/disappearance
time-to-fill
conversion
award patterns
```

POWUK currently risks simply collecting tenders.

Much more valuable to preserve the lifecycle:

```text
notice published
deadline
award
supplier
value
actual duration
amendments
```

Then learn:

```text
CPV X
in geography Y
typical award value
typical supplier size
typical time to award
incumbent/repeat supplier frequency
```

This creates:

```text
public demand
→ who actually wins
→ what capabilities capture it
```

and also lets you measure crowding.

---

# 10. Job listing disappearance / time-to-fill

This was explicitly part of the UKOpportunity moat:

> listing appearance/disappearance through time and time-to-fill per capability × locale.

We absolutely want this.

A vacancy snapshot shouldn't only be:

```text
electrician vacancy exists
```

but:

```text
first_seen
last_seen
salary
employer
location
requirements
filled/disappeared
```

Then:

```text
median listing duration
```

becomes another scarcity signal.

If:

```text
electrician ads
salary ↑
time-to-fill ↑
vacancies ↑
```

that's much stronger than vacancy count.

This is exactly why ephemeral job listings are a garden rather than a static dataset.

---

# 11. Technology/AGI exposure needs to return

This is perhaps the biggest conceptual omission given **why POW exists**.

Older UKGraph had:

```text
AGI capability
→ task
→ skill
→ occupation
→ firm
→ labour effect
```

and the opportunity loop:

```text
capability change
→ task exposure
→ vacancy/wage/business signals
→ displacement/augmentation
→ adjacent physical scarcity
```

Current POWUK tracks the physical economy, but without this layer it won't know **why AGI is shifting it**.

You don't need a giant AGI model in checkpoint 1.

But preserve these joins:

```text
SOC occupation
→ tasks
→ skills/capabilities
→ automation exposure
→ physical complementarity
```

Then later ask:

```text
software/accounting demand ↓
electrician demand ↑
data-centre technician demand ↑
network cabling demand ↑
industrial automation demand ↑
```

Importantly, this should be a **separate explanatory layer**, not allowed to contaminate raw labour truth.

---

# 12. BICS / technology adoption needs to return

Older UKGraph explicitly included ONS **BICS / AI adoption**.

This applies directly.

We want to know:

```text
which sectors are adopting AI?
which firm sizes?
how quickly?
```

Then join:

```text
AI adoption
× SIC
× occupation mix
× hiring
× wages
× business formation
```

That provides an official observation of technology diffusion rather than relying entirely on tech-news narratives.

I'd add the relevant ONS business technology/AI adoption series where available.

---

# 13. Skills England occupational graph should be much more central

Current source matrix had it, but current working POWUK seems centered on APAR/Ofqual.

The old architecture had a valuable semantic chain:

```text
occupation
→ SOC
→ duties
→ knowledge/skills/behaviours
→ training products
```

That is critical because:

```text
"electrician"
```

isn't really the primitive.

The useful primitive is:

```text
Capability
```

Skills England gives us an official-ish bridge between occupations, duties and training.

That lets POWUK reason about **adjacent worker mobility**:

```text
current occupation A
has 80% of capability requirements for B
additional training = X
time = Y
```

Then supply isn't just:

```text
existing B workers
```

but:

```text
existing B
+
plausibly convertible adjacent workers
```

That was already partially represented in `models/skills.py`; the data spine needs to support it.

---

# 14. Training ROI is missing

UKOpportunity treated training itself as a Route.

For POWUK:

```text
TRAINING
```

should be an economic object.

Given:

```text
course
duration
cost
qualification
completion rate
capability gained
regional demand
regional wage
```

derive later:

```text
expected wage uplift
time to qualification
local scarcity after qualification
payback period
```

This is extremely relevant in an AGI transition.

The user-facing question becomes:

> "What physical skill can I acquire fastest that is getting scarcer where I live?"

That's a natural POW product built entirely on this garden.

---

# 15. Claimant / displacement signals

Nomis claimant count was singled out in the old resources as a very timely local signal.

For AGI-related economic transition:

```text
claimants ↑
vacancies ↓
```

in one occupation versus:

```text
vacancies ↑
wages ↑
training ↓
```

in an adjacent physical occupation is important.

So build local transition matrices eventually:

```text
declining occupation
→ adjacent capability
→ viable training route
→ growing occupation
```

Again: that belongs later in modelling, but the underlying time series should be planted now.

---

# 16. Business demography deserves explicit collection

We currently have Companies House, but old UKGraph also used:

```text
ONS UK Business: Activity, Size and Location
ONS Business Demography
```

These are valuable calibration layers because Companies House ≠ active economic business.

Use both.

Companies House gives:

```text
high-frequency firm events
```

ONS gives:

```text
official business stock / births / deaths / size
```

Then we can calibrate our CH-derived capacity estimates.

Very important.

---

# 17. We should bring back a real Place spine

The old UKGraph mantra:

> **Don't own the Nottingham webpage. Own the Nottingham joins.**

Still applies.

POWUK's native key should be:

```text
Capability × Place × Time
```

and `Place` should have proper mappings:

```text
postcode
↓
postcode district
↓
LSOA/MSOA
↓
LAD
↓
region
↓
nation
```

plus:

```text
travel radius / travel time
```

where appropriate.

The source old work also included postcode→jurisdiction resolution.

That matters because:

```text
40 electricians in an LAD
```

doesn't tell you the true labour market if 20 are reachable across the boundary.

Eventually use practical travel catchments.

---

# 18. The old `OpportunityConversionHistory` idea is gold

Don't build it in Checkpoint 1, but design storage so we can eventually capture:

```text
opportunity shown
→ contacted
→ quoted
→ won/lost
→ work performed
→ payment
```

The UKOpportunity contract was very explicit about this.

Why it matters:

A planning application may *look* like an electrician opportunity.

Eventually we can learn:

```text
planning type X
→ electrical work within 6 months
probability = 0.32
```

A tender may look attractive:

```text
small electrical contractor bidding on tender class Y
historical win rate = 2%
```

That feedback turns abstract "signals" into actual economic calibration.

That's the long-term moat.

---

# 19. Bring over OGraphUK's hard data laws

This may actually be more important than additional sources.

`ographuk` already had stronger rules than current POWUK:

```text
Unknown = NULL, never fake zero

Quarantine-first

SUCCESS_EMPTY ≠ FAILED ≠ PARTIAL

No fuzzy joins in canonical truth

Raw evidence retained

No observation without provenance

Idempotent transforms

History never overwritten

Current state = view over full history
```

POWUK should steal these wholesale.

Especially:

```text
FetchResult:
SUCCESS
SUCCESS_EMPTY
PARTIAL
FAILED
BLOCKED
```

That would fix the exact monitoring problem we found in the latest peer review.

---

# 20. What NOT to copy back

There is also a lot of old UKGraph complexity that should **not** return to POWUK yet.

Don't bring back:

```text
generic Muse workflows
council-tax administration
crime data
property sales generally
broad consumer services
massive Provider/Offer/Action ontology
MCP surfaces
Jev opportunity ranking
AgentCom campaigns
generic WantGraph
generic MarketGraph
```

unless they directly improve physical-capacity measurement.

And `cgraphuk`'s 24 vertical templates / 72 pains / 174 tools are mostly semantic/business-automation material. Useful historical research, but not core POWUK garden ingestion.

---

# The actual POWUK data model is sharper now

I think it should ultimately measure these **nine primitives**:

```text
                    POWUK

1. DEMAND
   jobs
   tenders
   planning
   mandatory regulatory work
   subsidies

2. CAPACITY
   workers
   self-employed
   firms
   certified providers

3. PIPELINE
   apprentices
   qualifications
   training providers
   adjacent workers

4. PRICE
   wages
   salaries
   contract values
   eventually service prices

5. ENTRY
   new firms
   new certifications
   new trainees

6. EXIT
   company deaths
   insolvencies
   certification departures
   occupation exits

7. FRICTION
   qualification time
   completion rates
   capital
   certification
   geography/travel
   regulation

8. TECHNOLOGY
   AI adoption
   task automation
   complementary physical demand

9. OUTCOMES
   time-to-fill
   contract awards
   supplier survival
   eventual verified opportunity conversion
```

all indexed primarily by:

```text
Capability × Geography × Time
```

That is much more complete than:

```text
jobs + apprenticeships + registered tradesmen
```

---

## What I would add to Checkpoint 1 immediately

I wouldn't expand randomly. Add the missing historical foundations in this order:

| Add                                                             | Why it matters                                  |
| --------------------------------------------------------------- | ----------------------------------------------- |
| **ASHE full history**                                           | wage/shadow-price layer                         |
| **Nomis occupation + self-employed**                            | actual local labour capacity                    |
| **ONS Business Demography + Business Activity/Size/Location**   | calibrate CH business capacity                  |
| **Skills England Occupational Maps**                            | capability/occupation/training joins            |
| **DfE apprenticeship full historical flows**                    | supply pipeline                                 |
| **UKRLP**                                                       | training-provider geography                     |
| **MCS / OZEV / Competent Person / REFCOM entities / TrustMark** | qualified physical supply                       |
| **EPC stock**                                                   | physical-demand denominator for retrofit/energy |
| **Claimant Count**                                              | local displacement/transition signal            |
| **ONS technology/AI adoption where available**                  | AGI diffusion                                   |
| **grants/subsidy programmes**                                   | funded demand                                   |
| **legislation → effective/deadline/affected/capability schema** | mandatory future demand                         |
| **job listing first_seen/last_seen**                            | time-to-fill/scarcity                           |
| **procurement release→award lifecycle**                         | realised demand/outcomes                        |

Then POWUK becomes much more than a shortage dashboard.

It becomes:

$$
\boxed{
\text{technology/policy shock}
\rightarrow
\text{physical demand}
\rightarrow
\text{local scarcity}
\rightarrow
\text{price response}
\rightarrow
\text{entry/training}
\rightarrow
\text{capacity response}
}
$$

That is basically the best parts of **UKGraph + UKOpportunity + Data Garden + Seesaw**, stripped of all the platform sprawl.
