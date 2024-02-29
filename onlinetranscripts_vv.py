from visualvault import VV, getfiles
from string import Template


def main():
    # Setup BMI Variables
    # source directory
    ppath = "\\\\fs1.ad.uvu.edu\\groups\\admissions_bmi_upload\\ImportTranscripts"
    envfile = "\\\\bmi-db\\ra\\records\\records.ENV"
    regexstring = None
    filetype = ".pdf"
    stringconcat = Template("$last,$first~~$UVID~$doc")
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
    i = VV(ppath)
    i.build_log(20000000, 1, "info")
    i.bmifiles = getfiles(i.importdir, filetype)
    if i.bmifiles:
        i.log.info("There are " + str(len(i.bmifiles)) + " files to import")
        i.log.debug("bmifiles: " + str(i.bmifiles))
        if not i.buildtempdir():
            i.temprecover(filetype)
        for file in i.bmifiles:
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
                    newstring = stringconcat.substitute(last=lname,
                                                        first=fname,
                                                        UVID=string[0],
                                                        doc=doctype[string[1]])
                    if i.movetotmp(file):
                        i.writetoimp(file, newstring)
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
    if i.bmifiles:
        i.log.debug("BMI imp file has been created")
        if not i.bmiimport(envfile):
            i.temprecover(filetype)
        i.cleanup()


if __name__ == "__main__":
    main()
