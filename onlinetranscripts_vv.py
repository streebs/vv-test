from visualvault import VV, getfiles
from string import Template


def main():
    # Setup visual vault Variables
    source = "test_env"
    destination = "" 
    regexstring = None
    filetype = ""
    delimiter = "_"
    doctype = {
        "RES": "General",
        "H": "HS Transcript",
        "INT": "General",
        "G": "Paper App"
    }

    #  setup as member of class
    i = VV(source)
    i.build_log(20000000, 1, "info")
    i.vvfiles = getfiles(i.importdir, filetype)
    if i.vvfiles:
        i.log.info("There are " + str(len(i.vvfiles)) + " files to import")
        i.log.debug("vvfiles: " + str(i.vvfiles))
        if not i.buildtempdir():
            i.temprecover(filetype)
        for file in i.vvfiles:
            if regexstring:
                if not i.regex(regexstring, file):
                    continue
            i.log.debug(file)
            string = file[:-4]
            string = string.split(delimiter)

            # add G to the end of the list if there is no doctype
            if len(string) == 1:
                string.append("G")
            # check for doctype and set destination
            if string[1] == "RES":
                destination = "Student Records/DevTest"
            elif string[1] == "H":
                destination = "Student Records/DevTest"
            elif string[1] == "INT":
                destination = "Student Records/DevTest"
            else:
                destination = "Student Records/DevTest"

            try:
                lname, fname = i.getname(string[0])
            except IndexError:
                i.addtoerror(file)
                continue
            if lname:
                try:
                    indexes = {"SR First Name": fname, "SR Last Name": lname, "SR Full Name": lname+", "+fname, "UVID": string[0], "Document Type": doctype[string[1]]}
                    if i.movetotmp(file):
                        i.writetoimp(file, str(indexes))
                except (KeyError,IndexError):
                    i.log.warning("Incorrect Doctype Found")
                    i.addtoerror(file)
                except IndexError:
                    i.log.error("Index out of range")
                    i.addtoerror(file)
            else:
                i.log.error("API did not return name using UVID from " + file)
                i.addtoerror(file)
    if i.errorfiles:
        i.log.info("There were " + str(i.errorcount) + " errors")
        for file in i.errorfiles:
            i.movetoerror(file)
    if i.vvfiles:
        i.log.debug("visual vault imp file has been created")
        if not i.visualvaultimport(destination):
            i.temprecover(filetype)
        i.cleanup()


if __name__ == "__main__":
    main()
