# MILESTONES_INBOX.md
## Drafted Milestone Sequencing

*Review these items. Move to `MILESTONES.md` to formally sequence the work.*

### Target: Milestone 2 (Core Additions)
- [ ] Add minimal Party model
- [ ] Add `cp_role`, `cm_presence`, `cm_authority_delegated` to Contract model
- [ ] Add `is_public_works` to Job model
- [ ] Add `authorization_gap`, `notice_given_date`, `notice_given_to` to EWO model

### Target: Milestone 3 (Delta & Daily)
- [ ] Build DeltaPlan model
- [ ] Build DailyReport model
- [ ] Add `EWOFlag` field to ExtraWorkOrder (single migration)

### Target: Milestone 4 (Risk & Standby)
- [ ] US.1: SOV Importer (Upload formatted Excel SOV -> populates versioned PayItem table)
- [ ] US.4: LD Alert (CurrentDate > StartDate + ContractDays -> Daily Penalty warning)
- [ ] Build Change Order lifecycle models
- [ ] Build Delay Log model
- [ ] Build EWOScenario model
- [ ] Build StandbyEvent model
- [ ] Build Agency / Inspector layer

### Target: Milestone 5 (AI & Field UI Foundation)
- [ ] US.2: Daily Nut Calculator
- [ ] US.3: Live Tachometer
- [ ] Build WitnessSelector component
- [ ] Build Dynamic Billing UI (based on cp_role)
- [ ] Notice auto-generation from voice (Fedora comms server)
- [ ] AI Research flag overnight Cowork task workflow
- [ ] Scenario library database seeding
- [ ] Standby cost auto-calculation logic
- [ ] Bond Tracker, Stop Notice / Lien, Claims module

### Target: Milestone 6+ (Field Adoption)
- [ ] Field capture UI (Implement 3-tap flow constraint)
- [ ] Field Pilot (Deploy to one foreman)
- [ ] US.5: Evidence Vault (EWO photos sync to Dropbox)
- [ ] iPad-optimized foreman interface
- [ ] RFI and Submittal modules
