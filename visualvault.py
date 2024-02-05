from vvrest.vault import Vault
from vvrest.services.document_service import DocumentService
from vvrest.services.folder_service import FolderService
from vvrest.services.file_service import FileService

from dotenv import load_dotenv
from pathlib import Path
import os

dotenv_path = Path('.env')
load_dotenv(dotenv_path=dotenv_path)
# Load environment variables
client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")

# steps to upload a document to visual vault
# Step 1: get the folder id of the folder you want to upload the document to
# Step 2: create a new empty document in the folder using the document id from the previous step
# Step 3: upload the file to the document newly created in step 2 (use the document id from step 2)

class VV:
    def __init__(self):
        # define credentials
        self.url = 'https://na5.visualvault.com'
        self.customer_alias = 'UtahValleyUniversity'
        self.database_alias = 'StudentRecords'
        self.client_id = client_id
        self.client_secret = client_secret

        # get vault object (authenticate)
        self.vault = Vault(self.url, self.customer_alias, self.database_alias, self.client_id, self.client_secret)

        self.folder_Service = FolderService(self.vault)
        self.document_service = DocumentService(self.vault)
        self.file_service = FileService(self.vault)

    # vv_folder_path = the path that you want to upload the document to on Visual Vault
    # uploaded_file_name = the name of the file you want to upload
    # uploaded_file_path = the path of the file you want to upload local to your machine

    def upload_document(self, vv_folder_path, uploaded_file_name, uploaded_file_path):
        folder_id = ""
        doc_id = ""

        # get the folder id of the folder you want to upload the document to
        get_folder_response = self.folder_Service.get_folder_search(f"/{vv_folder_path}")
        if get_folder_response["meta"]["status"] == 200:
            folder_id = get_folder_response["data"]["id"]
        else:
            print(get_folder_response["meta"]["statusMsg"])
            return
        # create a new empty document in the folder using the document id from the previous step
        new_doc_response = self.document_service.new_document(folder_id, 1, uploaded_file_name, "", "1", uploaded_file_name)
        if new_doc_response["meta"]["status"] == 200:
            doc_id = new_doc_response["data"]["id"]
        else:
            print(new_doc_response["meta"]["statusMsg"])
            return
        # upload the file to the document newly created in step 2 (use the document id from step 2)
        file_upload_response = self.file_service.file_upload(doc_id, uploaded_file_name, "2", "", "1", "{}", uploaded_file_name, uploaded_file_path)
        if file_upload_response["meta"]["status"] == 200:
            print(f"file {uploaded_file_name} uploaded successfully")
        else:
            print(file_upload_response["meta"]["statusMsg"])