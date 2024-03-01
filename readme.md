# Testing Upload to Visual Vault

This will upload three txt files to `Student Records/DevTest` on Visual Vault.

### Overview
Dependencies

`vvrest`
`pytz`
`pyhton-dotenv`

Files used for testing:

`test.txt`
`test2.txt`
`test_folder/test3.txt`

This software utilizes the Visual Vault Pyhton API. Documentation for the API can be found here: [Visual Vault API](https://github.com/VisualVault/vvrest)

### How to Run

If you are using a python virtual environment, `requirements.txt` contains the dependencies need.

If not, install the following dependencies with pip: `vvrest`, `pytz`, `python-dotenv`
```sh
pip install vvrest
pip install pytz
pip install python-dotenv
```

Add your Visual Vault credentials to the `.env` file. 
Create a file called `.env` in the root of the project.
Add the following lines to the `.env` file
```
API_KEY="<your key here>"
API_SECRET="<your secret key here>"
```
Find your API keys in Visual Vault and copy them over.

Now, you should be all set! just run test_upload.py and it should upload those files!

# Test Environment & Running onlinetranscripts_vv.py

Since I don't have access to the S drive currently, I have created a test environment that should mimic the file structure on the S drive.
The test environment is located in the folder `test_env`
```
test_env
    |__ERROR
    |__IMPORT
    |__IMPORTED
    vv_import.log
```

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

