# Google Search Console Setup

The GSC connector uses the Search Console Search Analytics API through `google-auth` and the REST endpoint.

It supports two auth modes:

- `service_account`: uses `GOOGLE_APPLICATION_CREDENTIALS`;
- `oauth`: uses a pre-authorized user credentials JSON for an owner account such as `support@nachhilfe-mentor.de`;
- `auto`: prefers OAuth credentials when `GSC_OAUTH_CREDENTIALS` is set, otherwise falls back to service account credentials.

Future env vars:

```bash
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
GSC_OAUTH_CREDENTIALS=/path/to/authorized-user-credentials.json
GSC_AUTH_MODE=auto
GSC_SITE_URL=https://nachhilfe-mentor.de/
```

Server path currently expected:

```bash
GOOGLE_APPLICATION_CREDENTIALS=/etc/nachhilfe-mentor/goal-agent-gsc-service-account.json
GSC_OAUTH_CREDENTIALS=/etc/nachhilfe-mentor/goal-agent-gsc-oauth-user.json
GSC_AUTH_MODE=auto
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

If the Search Console property is owned by `support@nachhilfe-mentor.de` instead, create an OAuth authorized-user credentials JSON for that Google account and place it on the server with `0600` permissions. Do not commit it. Then set:

```bash
GSC_AUTH_MODE=oauth
GSC_OAUTH_CREDENTIALS=/etc/nachhilfe-mentor/goal-agent-gsc-oauth-user.json
GSC_SITE_URL=https://nachhilfe-mentor.de/
```

The expected JSON shape is the standard `authorized_user` Google credentials file containing a refresh token, client id, and client secret for the Search Console readonly scope. The Goal Agent never prints these values.
