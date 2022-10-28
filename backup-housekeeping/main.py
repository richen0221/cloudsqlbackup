import base64
import logging
import json
from datetime import datetime
from httplib2 import Http
from googleapiclient import discovery
from googleapiclient.errors import HttpError
from oauth2client.client import GoogleCredentials

def main(event, context):
    pubsub_message = json.loads(base64.b64decode(event['data']).decode('utf-8'))
    credentials = GoogleCredentials.get_application_default()
    service = discovery.build('sqladmin', 'v1beta4', http=credentials.authorize(Http()), cache_discovery=False)
    request = service.backupRuns()

    # create new backup
    try:
      insert_response = request.insert(project=pubsub_message['project'],
                                       instance=pubsub_message['instance']).execute()
    except HttpError as err:
        logging.error("Could NOT run backup. Reason: {}".format(err))
    else:
      logging.info("Backup task status: {}".format(insert_response))
    
    # housekeeping
    keep_qty = pubsub_message['keep_qty']
    delete_backups = []

    list_response = request.list(project=pubsub_message['project'], 
                                 instance=pubsub_message['instance']).execute()
    if 'items' in list_response:
        for backup in list_response['items']:
            if backup['status'] == "SUCCESSFUL" and backup['type'] == "ON_DEMAND":
                delete_backups.append(int(backup['id']))
        delete_backups = sorted(delete_backups)
        backup_qty = len(delete_backups)
        delete_backup_qty = backup_qty - keep_qty

        if delete_backup_qty <= 0: 
            logging.info("No backups need to Delete.")
        else:
            for backup_id in range(0, delete_backup_qty):
                try:
                    delete_response = request.delete(project=pubsub_message['project'], 
                                                     instance=pubsub_message['instance'], 
                                                     id=delete_backups[backup_id]).execute()
                except HttpError as err:
                    logging.error("Could NOT run delete. Reason: {}".format(err))
                else:
                    logging.info(f"Delete backup status: {delete_response}")
    else:
        logging.info(f"No backups exisit Status: {list_response}")
