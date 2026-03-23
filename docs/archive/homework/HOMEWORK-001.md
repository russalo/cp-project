# HOMEWORK-001 (Completed Archive)

This batch is complete. Accepted answers were folded into `DECISIONS.md` on 2026-03-14.

Use this list to drive the next planning pass. These are intentionally early, high-impact questions.

1. **Minimum context required to create an EWO:** should v1 require only `Job`, or require `Job + JobSite` (and optional `WorkLocation`)?
   - Answer: For v1, we only need to track the job no. on the EWO. The Job model will be later.
2. **People model boundary:** do we keep separate models for internal labor (`Employee`) and customer-side contacts (`CustomerContact`) from day one?
   - Answer: People/Employees are really 3 different things in our Project. 1. Users that will using the webapp. 2. The Labor/Laborers that we track for the work. 3. Clients, that work for our Customers.     * for v1 we will only deal with our Users and Labor and not intermingle them. Customer and Job will be added later.
3. **Material evidence policy:** are invoice/receipt PDFs required for all material charges, optional for all, or required only above a threshold?
   - Answer: They are optional.
4. **PDF upload constraints:** what are allowed file types/sizes, and should uploads be PDF-only in v1?
   - Answer: In v1 we don't need PDF upload capability.
5. **Final EWO PDF composition:** should the output merge/append full uploaded PDFs, or include summary pages with references/links?
   - Answer: Ideally the user could select what elements to include in the final PDF. No required for v1
6. **Rate precedence rule:** when rates differ between source tables and manual entry, what wins and who can override?
   - Answer: The latest entry. We should track past rates for Equipment and LaborTrades
7. **Rate snapshot behavior:** once an EWO is submitted/approved, should line-item rates lock permanently even if global rates change?
   - Answer: The rate that is used when the EWO is submitted is the rate for that EWO.
8. **EWO lifecycle detail:** confirm exact statuses and edit-lock rules at each stage (`draft`, `submitted`, `approved/rejected`, `billed`).
   - Answer: For v1 yes. Ultimately the tool will generate a EWO, Cost Analysis or Estimate.
9. **Document storage strategy for v1:** local media on VPS first or object storage abstraction now?
   - Answer: I need to understand the pros and cons or each 1st.
10. **Dropbox integration boundary for v1:** should Dropbox be intake/export only, optional convenience, or explicitly deferred until core workflows stabilize?
    - Answer: For v1 Dropbox integration is not needed. We need to explore what benefit Dropbox integration will give the tool beyond v1 if at all.

## Suggested Working Method

- Answer these in order.
- Record final choices in `DECISIONS.md` before implementation.
- For unresolved items, mark temporary assumptions and expiration dates.
