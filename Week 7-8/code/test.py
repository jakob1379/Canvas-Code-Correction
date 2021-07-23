import numpy as np
import os


def eval_NN(threshold=3):
    # Load student and solution
    NN_ta = np.loadtxt('NN_ta.dat')
    try:
        NN_student = np.loadtxt('NN.dat')
        if len(NN_student) != len(NN_ta):
            print("ERROR: NN.dat has length " + str(len(NN_student)))
            total_diff = len(NN_ta)
        else:
            # Count errors
            total_diff = (NN_ta != NN_student).sum()
        # Return pass/fail
        res = int(total_diff <= threshold)
    except Exception as e:
        print(e)
        res = 0
    return res


def eval_logreg(threshold=3):
    # Load student and solution
    logreg_ta = np.loadtxt('LogReg_ta.dat')
    try:
        logreg_student = np.loadtxt('LogReg.dat')
        if len(logreg_student) != len(logreg_ta):
            print("ERROR: LogReg.dat has length " + str(len(logreg_student)))
            total_diff = len(logreg_ta)
        else:
            # Count errors
            total_diff = (logreg_ta != logreg_student).sum()
        # Return pass/fail
        res = int(total_diff <= threshold)
    except Exception as e:
        print(e)
        res = 0
    return res

def test():
    path = os.getcwd()
    folders = path.split("/")

    content = [str(i) for i in [eval_NN(), eval_logreg()]]

    with open(folders[-1]+'_points.txt', 'w') as f:
        f.write('\n'.join(content))

    with open(folders[-1]+'.txt', 'w') as f:
        # Write comments for knn exercise
        knn_out = "Exercise KNN\n"
        if content[0] == '1':
            knn_out += '-No errors found.'
        else:
            knn_out += '-Errors found: Points not classified correctly or .dat file has wrong format.'
        f.write(knn_out)

        # Write comments for LogReg exercise
        logref_out = "\n\nExercise LogReg\n"
        if content[1] == '1':
            logref_out += '-No errors found.'
        else:
            logref_out += '-Errors found: Points not classified correctly or .dat file has wrong format.\n'
        f.write(logref_out)
