from visualvault import VV, getfiles


def main():
    # Setup visual vault Variables
    # source directory
    source = "test_env"
    destination = "Student Records/DevTest"
    regexstring = None # this is an optional regex string
    filetype = ".pdf"
    delimiter = "_"
    doctype = {"G": "GRAD APP",
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
               "SAT": "SAT"}

    #  setup as member of class
    i = VV(source)
    i.build_log(20000000, 1, "info")
    i.vvfiles = getfiles(i.importdir, filetype)
    if i.vvfiles:
        i.log.info("There are " + str(len(i.vvfiles)) + " files to import")
        i.log.debug("vvfiles: " + str(i.vvfiles))
        if not i.buildtempdir():
            i.temprecover(filetype) # this will exit the program
        for file in i.vvfiles:
            if regexstring:
                if not i.regex(regexstring, file):
                    continue
            i.log.debug(file)
            string = file[:-4]
            string = string.split(delimiter)
            try:
                lname, fname = i.getname(string[0])
            except IndexError:
                i.addtoerror(file)
                continue
            if lname:
                try:
                    newstring = {"Last Name": lname, "First Name": fname, "UVID": string[0], "Document Type": doctype[string[1]]}
                    if i.movetotmp(file):
                        i.writetoimp(file, str(newstring))
                except (KeyError,IndexError):
                    i.log.warning("Incorrect Doctype Found or Index out of range")
                    i.addtoerror(file)
            else:
                i.log.error("API did not return name using UVID from " + file)
                i.addtoerror(file)
    if i.errorfiles:
        i.log.info("There were " + str(i.errorcount) + " errors")
        for file in i.errorfiles:
            i.movetoerror(file)
    if i.vvfiles:
        i.log.debug("Visual Vault imp file has been created")
        if not i.visualvaultimport(destination):
            i.temprecover(filetype)
        i.cleanup()


if __name__ == "__main__":
    main()
