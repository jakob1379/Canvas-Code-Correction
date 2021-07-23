from config import *
from test import test
import glob
import os
import re
import subprocess
import time


def addMissingIncluded(filename, existing):
    cppfiles = [(name.split("."))[0] for name in glob.glob("*.cpp")]
    existingIncludes = filename.split(" ")
    newIncludes = []

    regex = re.compile("\"[^\.][\S]+.h[pp]*\"")
    for cppfile in filename.split(" "):
        try:
            with open(cppfile) as f:
                content = f.readlines()
                for line in content:
                    hits = regex.findall(line)
                    for hit in hits:
                        hit = (hit.split("."))[0]
                        hit = hit.replace("\"", "")
                        hit = hit + ".cpp"
                        if hit not in newIncludes and hit not in existingIncludes and (hit.split(".c"))[0] in cppfiles:
                            newIncludes.append(hit)
        except:
            if not cppfile.strip():
                pass
            else:
                print("Error, but was catched. Tried to find '" +
                      cppfile + "' in file '" + filename + "'")

    #print("\n added: " + " ".join(newIncludes) + "\n")
    return existing + " ".join(newIncludes)


def extractStandardCompile():
    filename = "standard.txt"
    try:
        with open(filename) as f:
            content = f.readlines()
            line = content[0].split("\n")[0]
            if "c++11" in line:
                return (True, " -std=c++11 ")
            if "c++98" in line:
                return (True, " -std=c++98 ")
            return (False, " -std=c++11 ")
    except Exception as e:
        return (False, " -std=c++11 ")


def run(foldername):

    test_files_compiled = [True for i in range(len(test_files))]
    valgrind_logs = [test_files[i] + ".valgrind.txt" for i in range(len(test_files))]

    # check if all files are present
    # not neccersary since if they are not present, then they cant compile, so it's already taken care of.

    # compile files
    for i in range(len(test_files)):
        #print("compiler line before: " + compiler_lines[i])
        line = addMissingIncluded(sub_files[test_files[i]], compiler_lines[i])
        #print("after: " + line)

        # add the std flag
        nvmvalue, standard = extractStandardCompile()
        # print("########################")
        # print(standard)
        # print(line)
        # print("=")
        line = line + standard
        # print("####", line)

        res = subprocess.call(line, shell=True)
        if res != 0:
            test_files_compiled[i] = False
            print("could not compile: " + line)
            print("------------------------------------------")

    # run files with valggrind
    reachedTimeLimit = [False for i in range(len(test_files))]
    for i in range(len(test_files)):
        if test_files_compiled[i]:
            # cmd = "valgrind  --log-file='" + \
            #     valgrind_logs[i] + "' ./" + \
            #     object_files[test_files[i]] + " > deleteme.txt"
            cmd = './' + object_files[test_files[i]] + " > deleteme.txt"
            myproces = subprocess.Popen(cmd, shell=True)
            start = time.time()

            while (time.time()-start < TIME_LIMIT and myproces.poll() == None):
                continue
            if(myproces.poll() == None):
                myproces.kill()
                reachedTimeLimit[i] = True

    # clean()
    # f = open(foldername+ ".txt","w")
    # f.write(".")#+outputFile)
    # f.close()

    # f = open(foldername+ "_points.txt","w")
    # f.write("0.0")#+"".join([str(s)+"\n" for s in points]))
    # f.close()


def clean(clean_txt=False):
    with open(os.devnull, 'w') as FNULL:
        if clean_txt:
            for fil in glob.glob("*.txt"):
                subprocess.call("rm " + fil, shell=True, stdout=FNULL, stderr=FNULL)
        for fil in object_files.values():
            subprocess.call("rm " + fil, shell=True, stdout=FNULL, stderr=FNULL)
        subprocess.call("rm *.dat", shell=True, stdout=FNULL, stderr=FNULL)
        subprocess.call("rm *.pyc", shell=True, stdout=FNULL, stderr=FNULL)
        subprocess.call("rm *.py", shell=True, stdout=FNULL, stderr=FNULL)
        subprocess.call("rm -rf armadillo*", shell=True, stdout=FNULL, stderr=FNULL)
        subprocess.call("rm deleteme.txt", shell=True, stdout=FNULL, stderr=FNULL)


def testPassed(title, result):
    passed = True
    description = ""
    if "Failed" in result:
        passed = False
        newtitle = (title.split(":"))[1]
        description += "-Failed test: " + newtitle.strip()
    return (passed, description)


if __name__ == '__main__':
    path = os.getcwd()
    folders = path.split("/")
    # print(folders)
    run(folders[-1])
    test()
    clean()
