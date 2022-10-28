# Goal

This backup script modified the official script [1] but not only backup the CloudSQL but do housekeeping.

It will create the GCP resources as below:
- IAM Role with `cloudsql.backupRuns.create`, `cloudsql.backupRuns.list` and `cloudsql.backupRuns.delete` permission.
- Service account (binding the IAM role).
- PubSub
- Cloud Function
- Scheduler

## Implementation

Please use the Cloudshell to execute.

- Setup the env variable to create resources.
```bash
export PUBSUB_TOPIC="sql-backup-topic"
export SCHEDULER_JOB="sql-backup-job"
export PROJECT_ID="${GOOGLE_CLOUD_PROJECT}"
export SQL_ROLE="sqlBackupCreator"
export GCF_NAME="sql-backup"
export REGION="asia-east1"
export SQL_INSTANCE="YOUR_INSTANCE_NAME"
```

- Setup IAM Role and PubSub
```bash
gcloud iam roles create ${SQL_ROLE} --project ${PROJECT_ID} \
    --title "SQL Backup role" \
    --description "Grant permissions to backup data from a Cloud SQL instance" \
    --permissions "cloudsql.backupRuns.create,cloudsql.backupRuns.list,cloudsql.backupRuns.delete"
gcloud iam service-accounts create ${GCF_NAME} \
    --display-name "Service Account for GCF and SQL Admin API"
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:${GCF_NAME}@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="projects/${PROJECT_ID}/roles/${SQL_ROLE}"
gcloud pubsub topics create ${PUBSUB_TOPIC}
```

- Setup cloud function and scheduler
```bash
cd backup-housekeeping
gcloud functions deploy ${GCF_NAME} \
    --trigger-topic ${PUBSUB_TOPIC} \
    --runtime python37 \
    --entry-point main \
    --service-account ${GCF_NAME}@${PROJECT_ID}.iam.gserviceaccount.com

gcloud app create --region=${REGION}
gcloud scheduler jobs create pubsub ${SCHEDULER_JOB} \
--schedule "0 * * * *" \
--topic ${PUBSUB_TOPIC} \
--message-body '{"instance":'\"${SQL_INSTANCE}\"',"project":'\"${PROJECT_ID}\"',"keep_qty":10}' \
--time-zone 'Asia/Taipei'
```

## Usage
- Please create or modify the scheduler's message body like below to the PubSub.
- Set the `keep_qty` for how many bakups you want to keep.

```json
{"instance":"YOUR_INSTANCE_NAME","project":"YOUR_PROJECT_ID","keep_qty":10}
```

## Know issues
- The housekeep will leave more than one backup not delete becasue housekeep won't count the creating backup.
- if you hope to keep 10 backups, it will left 11 backups.

# Misc
The scripts folder contain `backup-pubsub` and `housekeep` script for test.
- `backup-pubsub` is [1] original script.
- `housekeep` can be executed on the Cloudshell directly.


[1] https://cloud.google.com/sql/docs/mysql/backup-recovery/scheduling-backups