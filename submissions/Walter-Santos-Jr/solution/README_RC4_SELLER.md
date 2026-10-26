# RC4 DEV — Seller Execution Workspace

Scope: Seller only. Head and Manager workspaces are retained unchanged.

- On cover, select Vendedores, then select region → manager → seller in Main.
- Once a seller identity is selected, Navbar presents Pipeline, Rework and Histórico controls.
- Aside retains the existing persisted deal/job queues. Main retains Opportunity 360 and its Analysis/Qualification/Execution/History views.
- Pipeline count comes from `/api/dashboard` for the selected seller; Rework count counts non-resolved jobs returned by `/api/jobs` (the endpoint currently limits the result to 500, so treat the displayed number as returned jobs, not an authoritative unlimited global count).
- No new scoring rules, data models or workflow transitions were introduced.

## UAT
1. Choose Seller, Central, a manager and a seller. Confirm Navbar identity.
2. Select Pipeline, select a deal in Aside, inspect Opportunity 360 in Main.
3. Select Rework, inspect pending jobs and History; execute a valid correction and verify persistence.
4. Select Histórico; confirm the deal history loads.
5. Switch to Head and Manager; confirm both previously approved workspaces are unchanged.

Demo access is not production authentication. Execute mutable UAT on a disposable copy of the database.
