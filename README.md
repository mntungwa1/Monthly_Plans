# DM RMO Monthly Reporting App

A Streamlit app for each RMO sub-stream to capture monthly workplans, progress, hours and portfolio of evidence, and download Word documents based on the supplied DM RMO executive summary template.

## Included features

- Editable reporting and forward planning dates, author and sub-stream.
- Activity register with KRA, dates, deliverables, purpose, strategy/Matrix/APP alignment, status, owner, evidence, dependencies and activity details.
- Separate actual, estimated, scheduled and anticipated hour totals. Actual entries require an evidence reference. Negative hours and reversed dates block Word generation; out-of-window dates and missing KRA/output fields generate review notes.
- Separate progress report and monthly workplan Word downloads, retaining the template's branding, section structure, four-column output table, footer and sign-off block. Original numbering omissions are corrected.
- Document content previews, CSV activity register, JSON draft save/restore and an overview from multiple uploaded sub-stream drafts.
- An editable BBB example drawn from the supplied September–October report. No actual hours are invented. The source's 24-hour strategic-report entry is treated as Estimated pending verification; the example records 48 estimated and 7 scheduled progress hours, with 72 anticipated forward hours. Of those estimated progress hours, 24 fall in October and 24 in September.
- Larger restored CoGTA/NDMC logo artwork. Select **Original template** in the sidebar when official fidelity is required; restoration is display artwork, not an authoritative replacement for the source emblems.
- Required app password and a separate admin password through Streamlit Secrets. Blank passwords block access.
- Admin-only server draft archive and cross-stream overview. Session authentication expires after 30 minutes of inactivity; five unsuccessful attempts trigger a one-minute pause in that browser session.

## Run on your computer

Use Python 3.12. Open a terminal in this folder and run:

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS / Linux:
# source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Deploy to your Streamlit apps

1. Extract the ZIP and create a GitHub repository such as `rmo-monthly-reporting`.
2. Upload the **contents** of this folder into the repository root. Keep `app.py`, `reporting.py`, `requirements.txt`, `templates/`, `assets/` and `examples/` together. Uploading only `app.py` will not work.
3. At https://share.streamlit.io select **Create app**, select the repository and branch `main`, and set **Main file path** to `app.py`. Select Python 3.12 in the advanced settings.
4. Add the following in the app's private Secrets settings. Enter your own passwords privately; do not put real passwords in GitHub. `secrets.example.toml` contains the complete configuration you requested:

```toml
APP_PASSWORD = " "
ADMIN_PASSWORD = " "
# On Cloud omit BASE_DIR or use ./ndmc_data.
# On Windows you may set BASE_DIR = "C:/Monthly_Plan".
EMAIL_MODE = "testing" # Later: "administrator"
EMAIL_ADDRESS = "dingaanm@gmail.com"
EMAIL_PASSWORD = " " # Optional Google App Password
ADMIN_EMAIL = "admin@ncuma.co.za"
```

5. Replace the blank password values and deploy. Missing or whitespace-only `APP_PASSWORD` blocks the app. Missing or blank `ADMIN_PASSWORD` blocks only the admin dashboard. Admin email is corrected to `admin@ncuma.co.za` without spaces. With valid Gmail credentials, the **Submit workplan and progress report by email** button sends both Word documents. In `testing` mode they go to `EMAIL_ADDRESS` (dingaanm@gmail.com); change `EMAIL_MODE` to `administrator` later to send to `ADMIN_EMAIL`.

Official deployment guidance: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy

No OpenAI API key, database, Google credentials, paid API or LibreOffice installation is needed for this version. It sends email only when the user explicitly clicks the submission button; it does not publish automatically.

## Monthly workflow

1. Start blank or load the BBB example and change the sub-stream and reporting cycle.
2. Enter the progress and forward workplan windows. Use contract notes to identify interruptions or excluded dates in a combined report.
3. Enter activities. Choose **Progress** for reported contributions and **Workplan** for forward commitments. Record actual hours only after checking supporting records. An evidence reference is a record supplied by the user, not independent verification by the app.
4. Complete the narrative fields. The app assembles the documents; it does not invent narrative achievements or generate prose through an AI service.
5. Review validation notes and the preview, then download Word reports and the activity register. To submit both Word documents by email, click **Submit workplan and progress report by email**. The displayed recipient confirms testing or administrator mode. Annexures are referenced, not embedded. Check the Word pagination and sign the report outside the app.
6. Click **Save draft JSON** before leaving. For next month's plan, restore the draft, change dates, edit the carried-forward activities and save a new draft.
7. A coordinator unlocks **Admin dashboard** with `ADMIN_PASSWORD`, opens server-saved drafts or uploads colleagues' draft JSON files, and downloads the comparison as CSV. Duplicate author/sub-stream/report-cycle records are skipped to avoid double counting.

## Draft storage and access

Drafts remain in the individual Streamlit session until downloaded or explicitly saved with **Save draft to server archive**. Only the separately authenticated administrator can list, download and open the server archive. Each save creates a new file using a generated filename; it does not overwrite previous submissions.

`BASE_DIR` defaults to `C:/Tmp/Monthly_Plan` on Windows or `./ndmc_data` on Cloud/Linux. A configured Windows drive path such as `C:/Monthly_Plan` on Linux falls back to `./ndmc_data` with a visible notice. Server-local Cloud storage is not durable across restart/redeployment; retain downloaded JSON backups. There is no shared database or individual staff account system.

App and admin authentication use separate session checks and constant-time password comparison. Password changes invalidate existing access on the next interaction; sign-out clears both roles and the draft. The five-attempt pause is per browser session, not a service-wide brute-force defence. Resetting or restoring replaces the current in-session draft. Secrets and real passwords must remain outside the repository. No password is included in JSON or Word exports.

The original uploaded template and report are not modified. Sample Word files in `samples/` show the generated layout. The HTML preview shows the same captured content but is not a rendering of the Word file and does not reproduce its pagination.

## Verification

Run `python -m unittest discover -s tests -v` after installing requirements. Checks cover hour-basis separation, invalid date/hour rejection, JSON round trips, template-based Word structure and branding, and Streamlit blank/example/restored-state flows. The supplied sample Word documents were also rendered and visually inspected before packaging.

## Gmail submission setup

In private Streamlit Secrets, set `EMAIL_ADDRESS = "dingaanm@gmail.com"` and enter a Google App Password as `EMAIL_PASSWORD`. Keep `EMAIL_MODE = "testing"` while testing. For operational use, change only `EMAIL_MODE` to `"administrator"` and verify `ADMIN_EMAIL = "admin@ncuma.co.za"`. Both reports are attached as Word files. No password or secret is embedded in the attachments.

The app uses Gmail SMTP over TLS. The success message confirms Gmail accepted the message, not that the recipient opened it. There is no automatic retry. If a timeout or error occurs, check the mailbox before retrying. Identical report contents cannot be resubmitted in the same session after a successful send; this does not guarantee duplicate prevention across different sessions. No live email was sent during automated testing; SMTP was mocked.
