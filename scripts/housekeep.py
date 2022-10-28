from pprint import pprint
from httplib2 import Http
import logging
from googleapiclient import discovery
from oauth2client.client import GoogleCredentials
from googleapiclient.errors import HttpError

credentials = GoogleCredentials.get_application_default()

service = discovery.build('sqladmin', 'v1beta4', credentials=credentials)

# Project ID of the project that contains the instance.
project = 'PROJECT_ID'
instance = 'INSTANCE_NAME'

keep_qty = 7
delete_backups = []

request = service.backupRuns()
list_response = request.list(project=project, instance=instance).execute()


if 'items' in list_response:
    for backup in list_response['items']:
        if backup['status'] == "SUCCESSFUL" and backup['type'] == "ON_DEMAND":
            delete_backups.append(int(backup['id']))
    delete_backups = sorted(delete_backups)
    backup_qty = len(delete_backups)
    delete_backup_qty = backup_qty - keep_qty

    if delete_backup_qty <= 0: 
        logging.info("No backups need to Delete.")
        print("No backups need to Delete.")
    else:
        for backup_id in range(0, delete_backup_qty):
            try:
                delete_response = request.delete(project=project, 
                                                 instance=instance, 
                                                 id=delete_backups[backup_id]).execute()
            except HttpError as err:
                logging.error("Could NOT run delete. Reason: {}".format(err))
                print(f"Error: {err}")
            else:
                logging.info(f"Delete backup status: {delete_response}")
                pprint(f"Delete backup status: {delete_response}")
else:
    logging.info(f"No backups exisit Status: {list_response}")
    print(f"No backups exisit Status: {list_response}")
