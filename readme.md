# Initial Setup

### Set Up Python Virtual Environment

run the following in the terminal
```sh
python -m venv .venv
```

Activate the virtual environment

MacOs/Linux
```sh
source .venv/bin/activate
```

Windows
```bash
.venv/Scripts/activate.bat //In CMD
.venv/Scripts/Activate.ps1 //In Powershell
```

### Install Dependencies
install dependencies from requirements.txt
```sh
pip install -r requirements.txt
```

If you are not using a Python virtual environment, install the following dependencies with pip: `vvrest`, `pytz`, `python-dotenv`
```sh
pip install vvrest
pip install pytz
pip install python-dotenv
```
### Setup Test Environment

create a directory called `.env` in the root of the project

Add your Visual Vault credentials to the `.env` file. 
```
API_KEY="<your key here>"
API_SECRET="<your secret key here>"
```
Find your API keys in Visual Vault and copy them over.

### Create Test Environment Directory Structure

Since I don't have access to the S drive currently, I have created a test environment that should mimic the file structure on the S drive.
The test environment is located in the folder `test_env`
```
test_env
    |__ERROR
    |__IMPORT
    |__IMPORTED
    vv_import.log
```
# Test an Upload
To test `onlinetranscripts_vv.py`, place any number of files in this directory: `test_env/IMPORT`
The files in this directory should have the format: `<uvid>_<doctype>.pdf`, where `doctype` is one of the following:
```
doctype = {
	"G": "GRAD APP",
	"N": "NON GRAD APP",
	"C": "CHALLENGE EXP",
	"E": "TRANS CRED EVAL",
	"S": "GRAD COURSE SUB",
	"R": "REISSUED DIPLOM",
	"T": "TRANSCRIPT",
	"M": "MAJOR CHANGES",
	"RES": "RESIDENCY",
	"H": "HS TRANSCRIPT",
	"INT": "INTERNATIONAL",
	"GMAT": "GMAT",
	"GRE": "GRE",
	"ACT": "ACT",
	"SAT": "SAT"
}
```
**Warning! The `getname()` function does not work in the local environment will only return info for me, Sheldon Strebe**

Once you have placed files in the IMPORT directory you can run `onlinetranscripts.py`. The script will upload the files to Visual Vault into the `Student Records/Dev Test` directory.
When the script is complete the files in the IMPORT directory will be moved to either the IMPORTED or ERROR directories. 

