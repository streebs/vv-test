from visualvault import VV, getfiles
from string import Template
import datetime


def main():
    # Setup BMI Variables
    source = ""
    destination = ""
    regexstring = "^(\d{8})(_.+)?"
    filetype = ""
    stringconcat = Template("$UVID~$last $first~UPLOADS~$date")
    delimiter = "_"

    #  setup as member of class
    i = VV(source)
    i.build_log(20000000, 1, "info")
    # normalizefiles(i.importdir, filetype)
    i.vvfiles = getfiles(i.importdir, filetype)

    # before doing anyting, check if the ppath has any files.
    if i.vvfiles:

        # enter logs and begin to generate metadata
        i.log.info("There are " + str(len(i.vvfiles)) + " files to import")
        i.log.debug("vvfiles: " + str(i.vvfiles))
        now = datetime.datetime.now()
        today = "{}/{}/{}".format(now.year, now.month, now.day)

        # create a temorary directory. if it fails then it moves any files in the temp directory to the import directory
        if not i.buildtempdir():
            i.temprecover(filetype)

        # loop though each file     
        for file in i.vvfiles:

            # if the file name does not match the format, then skip
            if regexstring:
                if not i.regex(regexstring, file):
                    continue

            # log the file that matches the correct format
            i.log.debug(file)
            string = file[:-4]
            string = string.split(delimiter)
            i.log.debug(string[0])

            # attempt to get name by uvid skip the file if name can not be found
            try:
                lname, fname = i.getname(string[0])
            except IndexError:
                i.addtoerror(file)
                continue

            # if there is a last name then generate metadata and put it into `newstring`
            # once the metadata is compiled move the file to the tmp directory
            # if the move is successful write the file name and the corresponding metadata to the .imp file
            if lname:
                try:
                    newstring = stringconcat.substitute(last=lname,
                                                        first=fname,
                                                        UVID=string[0],
                                                        date=today)
                    newstring = {"Last Name": lname, "First Name": fname, "UVID": string[0], "date": today}
                    if i.movetotmp(file):
                        # create a dictionary here for the metadata to be passed to visual vault via the api. 
                        i.writetoimp(file, newstring) # I dont think this will be necessary for visual vault. will write metadata another way
                except KeyError:
                    i.log.warning("Incorrect Doctype Found")
                    i.addtoerror(file)
                except IndexError:
                    i.log.error("Index out of range")
                    i.addtoerror(file)
            else:
                i.log.error("API did not return name using UVID from " + file)
                i.addtoerror(file)

    # if there is an error, log it and move the file to the error directory            
    if i.errorfiles:
        i.log.info("There were " + str(i.errorcount) + " errors")
        for file in i.errorfiles:
            i.movetoerror(file)

    # yet another check for existing files
    # run visualvaultimport. if unsuccessful, move temp file back to the import dir
    # clean up -> 
    #   remove import.imp from temp directory, 
    #   remove BMIImport.log form temp directory,
    #   remove each file in the import directory,
    #   move each file in the tmp directory into the import directory
    if i.vvfiles:
        i.log.debug("Visual Vault imp file has been created")
        if not i.visualvaultimport(destination):
            i.temprecover(filetype)
        i.cleanup()


if __name__ == "__main__":
    main()
