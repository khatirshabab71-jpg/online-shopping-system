# ShopNow: Vercel setup

This repair keeps your HTML/CSS/JavaScript, Python handler, and MySQL.
It does not migrate to Supabase PostgreSQL. No live deployment has been changed.

## 1. Copy the package
Back up your project. Copy these files into your Git repository root, alongside
frontend/ and backend/. Keep your existing .git folder. Do not put this package inside frontend/.
The uploaded email_outbox.log is excluded because it can contain account verification links.

## 2. Prepare cloud MySQL
Create an online MySQL database. Obtain its hostname, port, database name, username,
password, and CA certificate from the provider. Pricing depends on your provider.
Vercel cannot use your laptop's localhost database.

For a NEW EMPTY database: select the provider database in your MySQL client and run
`database/cloud_schema.sql`. It creates 13 tables, without demo accounts or DROP statements.
For an existing database, back up and review the existing migrations first.
Do not run the original online_shopping.sql against existing data: it drops tables
and includes publicly known demo accounts. Do not use those accounts online.

Create a private admin by running `python backend/create_admin.py` locally with the cloud
DB environment variables set. It prompts privately for a password. Then populate your catalog.
The new schema has no sample products. Use a separate privileged account for schema setup,
and a restricted application account for normal queries. Schema creation does not run on requests.

## 3. Vercel environment variables
Open Project > Settings > Environment Variables. Set these for Production.
Use a separate database if enabling Preview deployments.

| Variable | Value |
| --- | --- |
| DB_HOST | Cloud MySQL hostname |
| DB_PORT | Provider's MySQL port |
| DB_NAME | Provider's database name |
| DB_USER | Application database username |
| DB_PASSWORD | Database password |
| DB_SSL_CA_PEM | Provider's complete CA certificate with BEGIN/END lines and line breaks |
| APP_URL | https://online-shopping-system-sooty.vercel.app |
| SMTP_HOST | Email provider's SMTP hostname |
| SMTP_PORT | 587 for a STARTTLS provider |
| SMTP_USER | Email provider's SMTP username |
| SMTP_PASSWORD | SMTP password or app password |
| SMTP_USE_TLS | true |
| SMTP_FROM_EMAIL | Sender approved by your email provider |
| SMTP_FROM_NAME | ShopNow |

Vercel sets VERCEL=1 automatically. Do not enable USE_HTTPS; Vercel handles public HTTPS.
MySQL certificate and hostname verification are enabled on Vercel. Supply the provider's CA
when required. Do not disable verification to bypass errors.
Keep credentials out of frontend code and Git. This project does not automatically load .env files;
local scripts need shell environment variables. APP_URL controls email link destinations.

## 4. Vercel build settings
Project > Settings > Build and Deployment:
- Root Directory: empty, meaning the repository root.
- Framework Preset: Other.
- Build Command: empty, as configured in vercel.json.
- Output Directory: frontend, as configured in vercel.json.
- Install Command: default, with no npm install override.

Root Directory includes backend source. Output Directory publishes frontend files only.
The api/index.py Python function receives /api/* requests through the configured rewrite.
Keep API_BASE_URL='/api'. No background HTTP server starts inside the function.
Vercel supports this existing BaseHTTPRequestHandler pattern; a framework rewrite is not required.

## 5. Push and redeploy
Review changes and exclude secrets, logs, and backups before committing:

    git add .
    git diff --cached --name-only
    git commit -m "Add Vercel API deployment and cloud database setup"
    git push origin main

Redeploy after changing settings or environment variables. Confirm the deployment uses the new commit.

## 6. Test in this order
1. Open / and /register.html. Check CSS and JavaScript load.
2. Open /api/health. Expect HTTP 200 with success=true. This checks routing, not MySQL.
3. Open /api/ready. Expect Database ready. A 503 means DB connection or schema setup remains.
   This only checks table access, not all columns, write permissions, or transactions.
4. An empty JSON POST to /api/register should return JSON validation error 400, not Vercel NOT_FOUND.
5. Register a test customer. Confirm a database row and a real verification email.
6. Verify the link, log in, save a wishlist item, and place a test order against a test catalog.
7. Check ordinary customers cannot use admin actions or access other customers' orders.

If health is 404: check root, commit, function build, and rewrite configuration.
If function import fails: inspect build logs and requirements installation.
If health works but ready fails: check DB credentials, network rules, CA certificate, and schema.
If email is missing: check SMTP, approved sender, spam, and function logs. Email failures in the
existing application do not roll back accounts or retry durably. Use resend after fixing SMTP.
A durable email queue remains a future improvement.

## Changes and limits
Added api/index.py, vercel.json, requirements.txt, Python version, health/readiness checks,
cloud TLS settings, and a new empty schema/admin creation helper.
Cloud email sends finish their SMTP attempt before response instead of using detached threads.
Cloud email bodies/tokens are not written to logs. Temporary storage replaces application-folder logs.
Database query errors no longer log SQL parameters. POST parsing rejects malformed/non-object JSON
and oversized bodies. README's original local-demo instructions are not Vercel setup instructions.

Validation: 9 local adapter tests and 8 existing unit tests passed. The database was unavailable
locally; unit checks are not proof of database integration. Adapter database and email checks use mocks.
Real Vercel build, remote MySQL writes, and SMTP delivery still need the live tests above.
This deployment repair is not a full security audit. Existing token/checkout concurrency and other
application security concerns need review before real customer use.

References:
https://vercel.com/docs/functions/runtimes/python/api-directory
https://vercel.com/docs/project-configuration
https://dev.mysql.com/doc/connector-python/en/connector-python-connectargs.html
