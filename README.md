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
- Optional app password through Streamlit Secrets.

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
4. To password-protect the app, add the following in the app's private Secrets settings. Replace the sample value with your own password; do not put the real password in GitHub:

```toml
APP_PASSWORD = "replace-with-your-own-password"
```

5. Deploy. Without `APP_PASSWORD`, there is no application password gate.

Official deployment guidance: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy

No OpenAI API key, database, Google credentials, paid API or LibreOffice installation is needed for this version. It does not send email or publish automatically.

## Monthly workflow

1. Start blank or load the BBB example and change the sub-stream and reporting cycle.
2. Enter the progress and forward workplan windows. Use contract notes to identify interruptions or excluded dates in a combined report.
3. Enter activities. Choose **Progress** for reported contributions and **Workplan** for forward commitments. Record actual hours only after checking supporting records. An evidence reference is a record supplied by the user, not independent verification by the app.
4. Complete the narrative fields. The app assembles the documents; it does not invent narrative achievements or generate prose through an AI service.
5. Review validation notes and the preview, then download Word reports and the activity register. Annexures are referenced, not embedded. Check the Word pagination and sign the report outside the app.
6. Click **Save draft JSON** before leaving. For next month's plan, restore the draft, change dates, edit the carried-forward activities and save a new draft.
7. A coordinator can upload colleagues' draft JSON files in **Stream overview** and download the comparison as CSV. Duplicate author/sub-stream/report-cycle records are skipped to avoid double counting.

## Draft storage and access

Drafts remain in the individual Streamlit session until downloaded. This version has no automatic persistence, shared database, account-based authorisation or central report repository. Users maintain downloaded drafts and share them through their existing document process. The optional password is a shared app password, not separate staff accounts. Sign-out clears the session. Resetting or restoring a draft replaces the current in-session content.

The original uploaded template and report are not modified. Sample Word files in `samples/` show the generated layout. The HTML preview shows the same captured content but is not a rendering of the Word file and does not reproduce its pagination.

## Verification

Run `python -m unittest discover -s tests -v` after installing requirements. Checks cover hour-basis separation, invalid date/hour rejection, JSON round trips, template-based Word structure and branding, and Streamlit blank/example/restored-state flows. The supplied sample Word documents were also rendered and visually inspected before packaging.
