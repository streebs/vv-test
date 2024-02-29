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
from os.path import isfile, join

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
        self.bmifiles = []
        self.importdir = ppath + "/IMPORT"
        self.tempdir = ppath + "/tmp"
        self.postdir = ppath + "/IMPORTED"
        self.errordir = ppath + "/ERROR"
        self.logfile = ppath + "/vv_import.log"
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
        """Tests each file in bmifiles to ensure that they are written correctly
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
        if not movefile(self.importdir + "\\" + file, self.tempdir + "\\" + file):
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
        self.log.debug(file + " is being removed from bmifiles")
        self.bmifiles.remove(file)
        self.log.warning("Moving " + file + "  to errordir")
        if not movefile(self.importdir + "\\" + file, self.errordir + "\\" + file):
            self.log.error("Can't move " + file + " to errordir")
    #
    def writetoimp(self, file, newstring):
        """Writes the import file used by bmiimport3.exe
        Keyword arguments:
        file -- full path to file
        newstring -- the constructed string for the import file
        """
        impfile = open(self.tempdir + "\\" + "import.imp", 'a')
        importstring = ("~\"" + self.tempdir + "\\" + file + "\";~" + newstring)
        try:
            impfile.write(importstring + "\r\n")
        except:
            self.log.error("Couldn't write " + file + " to import.imp")
            self.log.error("Moving" + file + " back to import dir")
            if not movefile(self.tempdir + "\\" + file, self.postdir + "\\" + file):
                message = "Can't move " + file + " back to importdir"
                self.log.critical(message)
                emailadmin(message + ": " + self.importdir)
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
            if not movefile(self.tempdir + "\\" + file, self.importdir + "\\" + file):
                message = file + " cannot be moved in tempdir: " + self.tempdir
                self.log.critical(message)
                emailadmin(message)
                sys.exit(1)
                return False
        self.log.error("Files have been moved out of tmpdir to importdir")
        self.log.error("Skipping the rest of the run")
        shutil.rmtree(self.tempdir)
        sys.exit(1)

    def upload_document(self, dest_folder_path, uploaded_file_name, uploaded_file_path, file_metadata = {}):
        folder_id = ""
        doc_id = ""

        # get the folder id of the folder you want to upload the document to
        get_folder_response = self.folder_Service.get_folder_search(f"/{dest_folder_path}")
        if get_folder_response["meta"]["status"] == 200:
            folder_id = get_folder_response["data"]["id"]
        else:
            print("Error: failed to get the folder id. Reason:")
            print(get_folder_response["meta"]["statusMsg"])
            return
        # create a new empty document in the folder using the folder id from the previous step
        new_doc_response = self.document_service.new_document(folder_id, 1, uploaded_file_name, "", "1", uploaded_file_name)
        if new_doc_response["meta"]["status"] == 200:
            doc_id = new_doc_response["data"]["id"]
        else:
            print("Error: failed to get the document id. Reason:")
            print(new_doc_response["meta"]["statusMsg"])
            return
        # upload the file to the document newly created in step 2 (use the document id from step 2)
        file_upload_response = self.file_service.file_upload(doc_id, uploaded_file_name, "2", "", "0", str(file_metadata), uploaded_file_name, uploaded_file_path)
        if file_upload_response["meta"]["status"] == 200:
            print(f"file {uploaded_file_name} uploaded successfully")
        else:
            print(file_upload_response["meta"]["statusMsg"])

    def bmiimport(self, envfile):
        """Actual subprocess call to BMIImport3.exe
        Keyword Arguments:
        envfile -- path to bmi envfile for import
        """
        # the upload document function needs the follwoing arguments:
        # vv_folder_path - the path to the folder in visualvault
        # uploaded_file_name - the name of the file to be uploaded
        # uploaded_file_path - the full path to the file to be uploaded (as found on the local machine)
        self.log.info("Calling BMI Import for " + str(len(self.bmifiles)) + " files")

        importarg = "-e" + envfile + " -t" + self.tempdir + "\\import.imp" + " -lappend" + " -h" # update
        self.log.debug("BMIImport3.exe " + importarg + " -lappend" + " -h") # update
        process = subprocess.Popen("BMIImport3 " + importarg, shell=True) # should be able to replace this with the upload_document function/code
        process.wait()
        
        if process:
            self.log.info("Import Complete")
            bmilog = self.tempdir + "\\BMIImport.Log"
            try:
                file = open(bmilog, "r")
                self.log.debug("Contents of BMIImport.Log:")
                regex = re.compile("Cannot|Unable")
                regex_filename = re.compile("(\\\\.+\..{3})")
                badfile = []
                flag = True
                for line in file:
                    self.log.info(line)
                    if regex.search(line):
                        string = regex_filename.search(line)
                        string = string.group(1) if string else None
                        self.log.debug("bad file " + string)
                        badfile = badfile + [string]
                for f in badfile:
                    self.log.error("BMIImport failed on " + f)
                    self.log.error("Moving " + f + " to " + self.importdir)
                    if not shutil.move(f, self.importdir):
                        self.log.critical("Cannot move bad file!!! Exiting...")
                        flag = False
            except FileNotFoundError:
                self.log.warning("BMIImport.Log was not found. Potential Data Loss!")
        else:
            self.log.error("BMIImport Crashed!!!!")
            flag = False
        return flag

    def cleanup(self):
        """Cleans up the environment for next run"""
        try:
            os.remove(self.tempdir + "\\" + "import.imp")
        except FileNotFoundError:
            self.log.warning("import.imp was already removed prior to cleanup")
        try:
            os.remove(self.tempdir + "\\" + "BMIImport.Log")
        except FileNotFoundError:
            self.log.warning("BMIImport.log was already removed prior to cleanup")
        contents = self.bmifiles
        for content in contents:
            if os.path.exists(os.path.join(self.postdir, content)):
                try:
                    os.remove(os.path.join(self.postdir, content))
                except OSError as os_error:
                    self.log.error("Error removing file " + content + " see following for details: " + os_error)
            if not movefile(self.tempdir + "\\" + content, self.postdir + "\\" + content):
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
            domain = 'https://ais-linux6.uvu.edu/idm/imaging/getEmployeeName.php?uvid=' + uvid
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


def emailadmin(message):
    msg = MIMEText(message)
    msg['Subject'] = "Critical Error Encountered"
    msg['From'] = "root@bmi-adm"
    msg['To'] = 'natew@uvu.edu'
    s = smtplib.SMTP('smtpmail.ad.uvu.edu')
    s.sendmail('root@bmi-adm', 'natew@uvu.edu', msg.as_string())
    s.quit()


def containsAny(str, set):
    return 1 in [c in str for c in set]
