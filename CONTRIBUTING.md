# Contributing

## Add a company

Add one object to `config/sources.json`:

```json
{"company": "Company", "provider": "greenhouse", "slug": "company-slug"}
```

Supported providers are `greenhouse`, `lever`, `ashby`, and `workday`. The slug is the identifier in
the company's hosted ATS URL, not necessarily its display name. Only official
employer job boards should be added.

## Run locally

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
PYTHONPATH=src python3 -m canada_jobs.update
```

Please do not add scraped LinkedIn, Indeed, or other aggregator pages. Respect
site terms, keep requests minimal, and link applicants to the official posting.
