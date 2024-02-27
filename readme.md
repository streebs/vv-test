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
