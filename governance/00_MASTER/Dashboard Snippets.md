# Dashboard Snippets

Copy/paste these snippets into your dashboard or other notes.
## 1. Open Tasks Across Vault
```dataview
TASK
WHERE !completed
LIMIT 20
```

## 2. Goals by Status
```dataview
TABLE phase, updated
FROM "03_GOALS_EPICS"
WHERE type = "goal"
SORT status ASC
```

## 3. Goals by Phase
```dataview
TABLE status, id
FROM "03_GOALS_EPICS"
WHERE type = "goal"
SORT phase ASC
```

## 4. Daily work feed (Last 14 days)
```dataview
TABLE without id file.link as "Date", goals as "Focus", list(goals).phase as "Phase"
FROM "01_DAILY"
SORT file.name DESC
LIMIT 14
```

## 5. Decisions Feed
```dataview
TABLE without id file.link as "Decision", date, decision
FROM "04_DECISIONS"
SORT date DESC
LIMIT 10
```

## 6. Audits Feed
```dataview
TABLE without id file.link as "Audit", date, risk
FROM "05_AUDITS"
SORT date DESC
LIMIT 10
```
