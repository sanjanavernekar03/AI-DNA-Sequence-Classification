
This folder is the friend's existing DNAura DNA project with the standalone

## What was preserved

- Existing user authentication and user-facing DNA/AI modules
- Existing ML models under `app/ml/models/`
- Existing report generation code
- Existing datasets and application templates
- Existing `dna_sequences`, `classification_results`, `disease_predictions`,
  and `reports` data structures

## What was added


duplicate `dna_uploads`, `predictions`, or fake report tables.

## Database

The merged project uses MySQL. Configure `DB_HOST`, `DB_PORT`, `DB_NAME`,
`DB_USER`, and `DB_PASSWORD` in `.env`. The application creates the configured
database and initializes `schema.sql` on first startup.




## Run

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python run.py
```

Then open:

`http://127.0.0.1:5000/`


## Important

module presents the project's stored records and does not claim clinical diagnosis.


## Administrator Control Center

The project now includes an isolated administrator module at:

`http://127.0.0.1:5000/admin`

### Admin capabilities
- Secure administrator login separate from normal user login
- Dashboard with user, DNA, analysis, prediction, risk and report statistics
- User Management: search, inspect, activate/deactivate, role management and delete
- DNA Upload monitoring
- AI classification and disease prediction monitoring
- High-risk case monitoring
- Generated report monitoring
- Administrator activity/audit logs
- Analytics charts
- Admin theme: Dark AI / Light / System
- Animated DNA visual design
- Collapsible sidebar
- MySQL-backed database

### Local admin account
The bundled local demo database is bootstrapped with:

- Username: `admin`
- Password: `Admin@12345`

Change the password immediately from **Admin → Settings**.

### MySQL
All application and administrator data are stored in the configured MySQL database.
The MySQL connection pool is initialized during application startup.
