from config import *
import subprocess
import glob
import os
import time
import re

def addMissingIncluded(filename, existing):
    cppfiles = [ (name.split("."))[0] for name in glob.glob("*.cpp") ]
    existingIncludes = filename.split(" ");
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
                        hit = hit.replace("\"","")
                        hit = hit + ".cpp"
                        if hit not in newIncludes and hit not in existingIncludes and (hit.split(".c"))[0] in cppfiles:
                            newIncludes.append(hit)
        except:
            if not cppfile.strip():
                pass
            else:
                print "Error, but was catched. Tried to find '" + cppfile + "' in file '" + filename +"'"

    #print "\n added: " + " ".join(newIncludes) + "\n"
    return existing + " ".join(newIncludes)

def extractStandardCompile():
    filename = "standard.txt"
    try:
        with open(filename) as f:
            content = f.readlines()
            line = content[0].split("\n")[0]
            if "c++11" in line:
                return (True," -std=c++11 ")
            if "c++98" in line:
                return (True," -std=c++98 ")
            return (False, " -std=c++11 ")
    except Exception as e:
        return (False," -std=c++11 ")

def run(foldername):

    test_files_compiled = [True for i in xrange(len(test_files))]
    valggrind_logs = [test_files[i] + ".valgrind.txt" for i in xrange(len(test_files))]

    ## check if all files are present
    # not neccersary since if they are not present, then they cant compile, so it's already taken care of.

    ## compile files
    for i in xrange(len(test_files)):
        #print "compiler line before: " + compiler_lines[i]
        line = addMissingIncluded(sub_files[test_files[i]], compiler_lines[i])
        #print "after: " + line

        # add the std flag
        nvmvalue,standard = extractStandardCompile();
        #print "########################"
        #print standard
        #print line
        #print "="
        line = line + standard
        #print line

        res = subprocess.call(line, shell=True)
        if res != 0:
            test_files_compiled[i] = False
            print "could not compile: " + line
            print "------------------------------------------"

    ## run files with valggrind
    reachedTimeLimit = [False for i in xrange(len(test_files))]
    for i in xrange(len(test_files)):
        if test_files_compiled[i]:
            #print ("valgrind --log-file='" + valggrind_logs[i] + "' ./" + object_files[test_files[i]])
            cmd = "valgrind  --log-file='" + valggrind_logs[i] + "' ./" + object_files[test_files[i]] + " > deleteme.txt"
            myproces = subprocess.Popen(cmd,shell=True)
            start = time.time()

            while (time.time()-start < TIME_LIMIT and myproces.poll() == None):
                continue
            if(myproces.poll() == None):
                myproces.kill()
                reachedTimeLimit[i] = True

            ##subprocess.call("valgrind  --log-file='" + valggrind_logs[i] +
            ##    "' ./" + object_files[test_files[i]] + " > deleteme.txt", shell=True)

    ## analyze result files from valggrind
    result_files = [test_files[i] + ".valgrind.txt" for i in xrange(len(test_files))]
    test_files_memory_freed = [True for x in xrange(len(test_files))]
    test_files_segfault = [False for x in xrange(len(test_files))]
    count = 0
    for result in result_files:
        if test_files_compiled[count] and not reachedTimeLimit[count]:
            with open(result) as f:
                content = f.readlines()
                (test_files_memory_freed[count],test_files_segfault[count]) = memoryFreed_segfaulted(content)
        count+=1

    ## analyse result files from the tests and generate resulting file
    outputFile = ""
    points = [0 for i in xrange(len(result_files))]
    result_files = [test_files[i] + ".result.txt" for i in xrange(len(test_files))]
    allResultFiles = glob.glob("*.result.txt");

    currentTestNumber = 0
    points_earned = 0
    for result in result_files:
        outputFile+= head_lines[test_files[currentTestNumber]] + "\n"
        if reachedTimeLimit[currentTestNumber]:
            outputFile+= "-Time limit of " + str(TIME_LIMIT) + " seconds was reached - check for very bad code or infite loops.\n"
            points[currentTestNumber] = 0
        else:
            # check if segfault occured
            if test_files_segfault[currentTestNumber]:
                outputFile+= "-Segfault occured.\n"#" You missed " + str(total_points[test_files[currentTestNumber]]) + " points\n"
                points[currentTestNumber] = 0
            # check if file compiled
            elif not test_files_compiled[currentTestNumber]:
                outputFile+= "-Code could not compile in testing framework (errors in code, perhaps it has a main function, or file has the wrong name).\n"#" You missed " + str(total_points[test_files[currentTestNumber]]) + " points\n"
                points[currentTestNumber] = 0
            # check if result file exists (was created)
            elif result not in allResultFiles:
                outputFile+= "-Something forced the code to exit prematurely (e.g. assertions or exit).\n"#" You missed " + str(total_points[test_files[currentTestNumber]]) + " points\n"
                points[currentTestNumber] = 0
            # open result file
            else:
                with open(result) as f:
                    content = f.readlines()
                    #print content

                    current = 0
                    allPassed = True
                    while current < len(content):
                        (passed, description) = testPassed(content[current], content[current+1])
                        #print str(passed) + " : " + description
                        allPassed = allPassed and passed
                        if not passed:
                            outputFile+= description + "\n"
                        current+=2

                    testsRunned = current/2
                    # check if all the tests were run, and not ended early by something in the submission code
                    if testsRunned != numberOfSubtests[test_files[currentTestNumber]]:
                        outputFile+= "-Something forced the code to exit prematurely (e.g. assertions or exit).\n"#" You missed " + str(total_points[test_files[currentTestNumber]]) + " points\n"
                    # check if all tests passed
                    elif allPassed:
                        # check if memory was freed correctly
                        if test_files_memory_freed[currentTestNumber]:
                            outputFile+= "-No errors found.\n"#" You earned " + str(total_points[test_files[currentTestNumber]]) + " points\n"
                            points_earned+= total_points[test_files[currentTestNumber]]
                            points[currentTestNumber] = total_points[test_files[currentTestNumber]]
                        else:
                            outputFile+= "-No errors found, but memory was leaked.\n"#" You earned " + str(total_points[test_files[currentTestNumber]]- minus_point_for_memory_leak) + " points\n"
                            points_earned+= total_points[test_files[currentTestNumber]]*(1.0-minus_point_for_memory_leak)
                            points[currentTestNumber] = total_points[test_files[currentTestNumber]]*(1-minus_point_for_memory_leak)
                    else:
                        if test_files_memory_freed[currentTestNumber]:
                            outputFile+= "-Errors found.\n"#" You missed " + str(total_points[test_files[currentTestNumber]]) + " points\n"
                        else:
                            outputFile+= "-Errors found, and memory was leaked.\n"#" You missed " + str(total_points[test_files[currentTestNumber]]) + " points\n"
                        points[currentTestNumber] = 0

        outputFile+="\n"
        currentTestNumber+=1

    #outputFile += "You got " + str(round(float(sum(points))/sum(total_points.values())*100,2) ) + "% correct.\n"
    #outputFile+="total points: " + str(sum(points)) + "\n"
    #print outputFile
    #print pointFile

    #filefound, stdflag = extractStandardCompile()
    #if filefound:
    #    outputFile = "Compiled with what you supplied in standard.txt:" + stdflag + "\n\n" + outputFile
    #else:
    #    outputFile = "You did not supply a standard to compile with, so per default" + stdflag + " was used\n\n" + outputFile

    clean()
    f = open(foldername+ ".txt","w")
    f.write(outputFile)
    f.close()

    f = open(foldername+ "_points.txt","w")
    f.write("".join([str(s)+"\n" for s in points]))
    f.close()

def clean():
    with open(os.devnull, 'w')  as FNULL:
        for fil in glob.glob("*.txt"):
            subprocess.call("rm " + fil, shell=True, stdout=FNULL, stderr=FNULL);
        for fil in object_files.values():
            subprocess.call("rm " + fil, shell=True, stdout=FNULL, stderr=FNULL);
        subprocess.call("rm *.dat", shell=True, stdout=FNULL, stderr=FNULL);
        subprocess.call("rm *.pyc", shell=True, stdout=FNULL, stderr=FNULL);

def testPassed(title, result):
    passed = True
    description = ""
    if "Failed" in result:
        passed = False
        newtitle = (title.split(":"))[1]
        description+= "-Failed test: " + newtitle.strip()
    return (passed, description)

def memoryFreed_segfaulted(lines):
    memoryFree = False
    segfaulted = False
    checkStrMem = "All heap blocks were freed -- no leaks are possible"
    checkStrSegfault = "Process terminating with default action of signal 11 (SIGSEGV)"
    for line in lines:
        if checkStrMem in line:
            memoryFree = True
        if checkStrSegfault in line:
            segfaulted = True
    return (memoryFree, segfaulted)

if __name__ == '__main__':
    path = os.getcwd()
    folders = path.split("/")
    #print folders
    run(folders[-1]);

