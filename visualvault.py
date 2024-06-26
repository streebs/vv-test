import os
import re
import shutil
import subprocess
import rot_logger
import sys
import requests
import smtplib
import string
from email.mime.text import MIMEText
from os import listdir
from os.path import isfile, join, sep

from vvrest.vault import Vault
from vvrest.services.document_service import DocumentService
from vvrest.services.folder_service import FolderService
from vvrest.services.file_service import FileService

from dotenv import load_dotenv
from pathlib import Path

dotenv_path = Path('.env')
load_dotenv(dotenv_path=dotenv_path)


class VV:
    def __init__(self, ppath):
        """Sets up as member of import class"""
        self.errorfiles = []
        self.vvfiles = []
        self.importdir = ppath + sep + "IMPORT"
        self.tempdir = ppath + sep +  "tmp"
        self.postdir = ppath + sep + "IMPORTED"
        self.errordir = ppath + sep + "ERROR"
        self.logfile = ppath + sep + "vv_import.log"
        self.count = 0
        self.errorcount = 0


        # visual vault setup
        # define credentials
        self.url = 'https://na5.visualvault.com'
        self.customer_alias = 'UtahValleyUniversity'
        self.database_alias = 'StudentRecords'
        self.client_id = os.getenv("API_KEY")
        self.client_secret = os.getenv("API_SECRET")

        # get vault object (authenticate)
        self.vault = Vault(self.url, self.customer_alias, self.database_alias, self.client_id, self.client_secret)

        self.folder_Service = FolderService(self.vault)
        self.document_service = DocumentService(self.vault)
        self.file_service = FileService(self.vault)

    #
    def regex(self, regexstring, file):
        """Tests each file in vvfiles to ensure that they are written correctly
        Keyword arguments:
        regexstring -- passes the actual regex value to search for
        """
        regex = re.compile(regexstring)
        mo = regex.search(file)
        if mo is None:
            self.log.warning(file + " Did not match required filename template")
            self.addtoerror(file)
            return False
        return True
    #
    def build_log(self, size, baks, level):
        """Creates the rotation log file.
        Keyword arguments:
        size -- size of the log file in bytes
        baks -- number of backups: current + (baks)
        level -- at what severity to save in the log. level and below
            (debug,info,warning,error,)
        """
        self.log = rot_logger.create_logger(self.logfile, size, baks, level)
    #
    def buildtempdir(self):
        """Builds the tempdir and checks for existence + files
            if found handles the files so that they don't import incorrectly"""
        try:
            os.makedirs(self.tempdir)
            return True
        except FileExistsError:
            if any(isfile(join(self.tempdir, i)) for i in listdir(self.tempdir)):
                self.log.error("Files have been found in tmp!!!")
                return False
            else:
                return True
    #
    def movetotmp(self, file):
        """Moves files to the temp directory
        Keyword arguments:
        file -- full path to file
        """
        if not movefile(self.importdir + sep + file, self.tempdir + sep + file):
            self.log.error("File In Use! " + file)
            self.movetoerror(file)
            return False
        return True
    #
    def addtoerror(self, file):
        """Adds files to the errorfiles list
        Keyword arguments:
        file -- full path to file
        """
        self.errorcount += 1
        self.errorfiles.append(file)
        self.log.info(file + " is being added to errorfiles")
    #
    def movetoerror(self, file):
        """Moves file to error directory while removing the file from import list
        Keyword arguments:
        file -- full path to file
        """
        self.log.debug(file + " is being removed from vvfiles")
        self.vvfiles.remove(file)
        self.log.warning("Moving " + file + "  to errordir")
        if not movefile(self.importdir + sep + file, self.errordir + sep + file):
            self.log.error("Can't move " + file + " to errordir")
    #
    def writetoimp(self, file, metadata):
        """Writes the import file used by visualvaultimport
        Keyword arguments:
        file -- full path to file
        metadata -- the dictionary that contains the index fields for the import file
        """
        impfile = open(self.tempdir + sep + "import.imp", 'a')
        importstring = (self.tempdir + "/ : " + file + " : " + metadata)
        try:
            impfile.write(importstring + "\r\n")
        except:
            self.log.error("Couldn't write " + file + " to import.imp")
            self.log.error("Moving" + file + " back to import dir")
            if not movefile(self.tempdir + sep + file, self.postdir + sep + file):
                message = "Can't move " + file + " back to importdir"
                self.log.critical(message)
                # emailadmin(message + ": " + self.importdir)
                sys.exit(1)

        self.log.debug("impfile " + importstring)
        self.count += 1
        self.log.info(str(self.count) + " " + file)

    def temprecover(self, filetype):
        """Tries to move any file found in tempdir back out of it
        Keyword Arguments:
        filetype -- filetype of file to search for. ex: .pdf
        """
        files = getfiles(self.tempdir, filetype)
        for file in files:
            if not movefile(self.tempdir + sep + file, self.importdir + sep + file):
                message = file + " cannot be moved in tempdir: " + self.tempdir
                self.log.critical(message)
                # emailadmin(message)
                sys.exit(1)
        self.log.error("Files have been moved out of tmpdir to importdir")
        self.log.error("Skipping the rest of the run")
        shutil.rmtree(self.tempdir)
        sys.exit(1)

    def visualvaultimport(self, destination):
        """moves files from source to visual vault. Utilizes the .imp file in the tempdir to get each file and metadata.
        Keyword Arguments:
        destination -- full path to destination directory in visual vault
        """
        badFiles = []
        flag = True

        self.log.info("Calling Visual Vault Import for " + str(len(self.vvfiles)) + " files")
        files = open(self.tempdir + sep + "import.imp", "r")
        files = files.readlines()
        # files = files.split("\r\n")
        for file in files:
            file = file.strip()
            if file:
                file = file.split(" : ")
                if self.upload_document(destination, file[1], file[0]+file[1], file[2]):
                    self.log.info(file[1] + " uploaded to Visual Vault")
                else:
                    self.log.error(file[1] + " failed to upload to Visual Vault")
                    badFiles.append(file[0]+file[1])

        if badFiles:
            for f in badFiles:
                self.log.error("upload_document failed on " + f)
                self.log.error("Moving " + f + " to " + self.importdir)
                if not shutil.move(f, self.importdir):
                    self.log.critical("Cannot move bad file!!! Exiting...")
                    flag = False

        return flag
                    
    
    def upload_document(self, dest_folder_path, uploaded_file_name, uploaded_file_path, file_metadata = {}):
        """Uploads a document to visual vault via the API
        Keyword Arguments:
        dest_folder_path -- full path to destination directory in visual vault
        uploaded_file_name -- name of the file to be uploaded
        uploaded_file_path -- full path to file to be uploaded
        file_metadata -- dictionary of metadata to be uploaded with the file
        """
        folder_id = ""
        doc_id = ""

        # get the folder id of the folder you want to upload the document to
        get_folder_response = self.folder_Service.get_folder_search(f"/{dest_folder_path}")
        if get_folder_response["meta"]["status"] == 200:
            folder_id = get_folder_response["data"]["id"]
        else:
            self.log.error(f"Failed to get the folder id. Reason: {get_folder_response['meta']['statusMsg']}")
            return False
        # create a new empty document in the folder using the folder id from the previous step
        new_doc_response = self.document_service.new_document(folder_id, 1, uploaded_file_name, "", "1", uploaded_file_name)
        if new_doc_response["meta"]["status"] == 200:
            doc_id = new_doc_response["data"]["id"]
        else:
            self.log.error(f"Failed to get document id. Reason: {new_doc_response['meta']['statusMsg']}")
            return False
        # upload the file to the document newly created in step 2 (use the document id from step 2)
        file_upload_response = self.file_service.file_upload(doc_id, uploaded_file_name, "2", "", "0", str(file_metadata), uploaded_file_name, uploaded_file_path)
        if file_upload_response["meta"]["status"] == 200:
            return True
        else:
            self.log.error(f"Failed to upload file. Reason: {file_upload_response['meta']['statusMsg']}")
            return False

    def cleanup(self):
        """Cleans up the environment for next run"""
        try:
            os.remove(self.tempdir + sep + "import.imp")
        except FileNotFoundError:
            self.log.warning("import.imp was already removed prior to cleanup")
        contents = self.vvfiles
        for content in contents:
            if os.path.exists(os.path.join(self.postdir, content)):
                try:
                    os.remove(os.path.join(self.postdir, content))
                except OSError as os_error:
                    self.log.error("Error removing file " + content + " see following for details: " + os_error)
            if not movefile(self.tempdir + sep + content, self.postdir + sep + content):
                self.log.error("Failed to move " + content + " from tmp directory")
                return False
        try:
            os.removedirs(self.tempdir)
        except OSError:
            self.log.error("Failed to remove tmpdir " + self.tempdir)
            return False

    def getname(self, uvid):
        """Call db to return firstname and lastname"""
        self.log.debug("UVID = " + uvid)
        try:
            domain = 'https://qa.dws.uvu.edu/idname-api/idname.php?funct=namerev&uvid=' + uvid
            r = requests.get(domain)
            name = r.text
            if name:
                name = name.split(',')
                return(name[0], name[1])
            else:
                return(False, False)
        except requests.exceptions.RequestException as e:
            self.log.error("bad request" + str(e))
            return False, False


def movefile(source, dest):
    """Moves file from source to destination
    Keyword Arguments:
    source -- full path of file to be moved
    dest -- full path of destination directory
    """
    try:
        os.rename(source, dest)
    except OSError:
        return False
    return True


def getfiles(path, filetype):
    """Returns list of files for a given path and filetype
    Keyword Arguments:
    path -- full path to find source files
    filetype -- type of files to search for ex: .pdf
    """
    contents = os.listdir(path)
    files = []
    for content in contents:
        if content.lower().endswith(filetype):
            files = files + [content]
    return files


def changefiletype(path, ctype, etype):
    """Changes the filetype for all files of a specific type
    Keyword Arguments:
    path -- full path to find source files
    ctype -- current file type of files in path
    etype -- ending filetype after rename
    """
    files = getfiles(path, ctype)
    for file in files:
        string = file[:-4]
        os.rename(os.path.join(path, file), os.path.join(path, string + etype))





def containsAny(str, set):
    return 1 in [c in str for c in set]
