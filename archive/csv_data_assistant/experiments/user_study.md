# User study protocol (planned, not yet conducted)

Recruit 10–15 consenting adult participants with varied data experience. Explain the study, the data sent to Anthropic, and their right to stop. Use only the supplied synthetic sales data. Record participant IDs, not names; obtain any course-required ethical approval before recruitment.

Give each participant the same task sheet. Counterbalance task order where possible and record previous spreadsheet/programming experience. Do not teach specific prompt wording before the first attempt.

1. Upload the sample CSV and report its row count.
2. Identify columns containing missing values.
3. Find and remove duplicates; explain which row is kept.
4. Fill missing units with the median and explain the estimate.
5. Generate a chart of revenue by region.
6. Ask which region has the highest revenue and inspect the supporting SQL.
7. Undo the last data modification and export the result.

For each task record completion (yes/no), elapsed seconds, retries, assistance needed and observed errors. Start timing when the task is read; stop when the participant declares completion. Verify outcomes against the tool results rather than self-report. Record failed tasks separately, rather than omitting their times.

Afterwards rate clarity, trust and perceived control from 1 (low) to 5 (high). Ask: “What did you verify?”, “When were you unsure?” and “What would you change?” Avoid treating trust alone as accuracy. Report sample size, median completion times, completion rates, rating distributions and anonymised themes. A small convenience sample does not establish population-wide usability.

Suggested CSV columns:

```text
participant_id,experience,task_id,completed,seconds,retries,assistance,clarity_1_5,trust_1_5,control_1_5,notes
```

Store consent records separately. Set and communicate a retention period before collecting data. No participant study has been run by the implementation scripts.
