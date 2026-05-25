# Google Search Console Setup

The GSC connector uses the Search Console Search Analytics API through `google-auth` and the REST endpoint.

Future env vars:

```bash
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
GSC_SITE_URL=https://nachhilfe-mentor.de/
```

Server path currently expected:

```bash
GOOGLE_APPLICATION_CREDENTIALS=/etc/nachhilfe-mentor/goal-agent-gsc-service-account.json
GSC_SITE_URL=https://nachhilfe-mentor.de/
```

Allowed data:

- query;
- page;
- clicks;
- impressions;
- CTR;
- average position;
- date;
- device/country aggregates.

No user identifiers or personal data should be stored.

If Search Console rejects the service account email, add it again after Google has recognized the service account:

```text
goal-agent-gsc@all-in-one-lernapp.iam.gserviceaccount.com
```
