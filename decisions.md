# Architecture decisions

## Authoritative source

The tagged `erp_semester5_etl_package/` is the only source used by the local
CSV mode. The legacy `data/` files describe a separate 10-row Semester 6
prototype and are not merged silently.

## CSV development mode

CSV mode is the default because local development does not have a MySQL
server. `data_store.py` loads the package once per process, validates required
columns, references, ranges, and reconciliation rules, and serves all shared
calculations from those frames. This avoids four independent CSV readers in
routes and keeps dashboard/profile values consistent.

## Hosted MySQL path

MySQL configuration remains environment-driven and is selected with
`DATA_MODE=mysql`. The connector is optional at import time so CSV mode starts
without a server. Hosted MySQL remains the warehouse deployment path and must
be tested separately before being called production-ready.

## Missing attributes

The package student file has no `Date_of_Birth` column. The application does
not fabricate one; unavailable attributes remain absent/null. Sections and
semester values are derived from records rather than inferred from enrollment
prefixes.

## Attention threshold

The current dashboard attention count uses student-level mean attendance below
75 percent. It is a transparent operational rule, not a predictive model.

## Student fee profile navigation

Fee records link to `/student/<Enrollment_No>` using the row's own
`Enrollment_No`; the profile service then joins attendance, examination, and
fees only for that same key. Invalid or incomplete profile requests now return
explicit 400/404 responses instead of redirecting to a general page, so a
wrong or missing identifier cannot appear to open another student's profile.
