# predefine ANSI Font color/style schematics.
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

# Figure this error later... :/
# class state:
#     bool initialized = False


# code to init device. check availability of the port, and determines whether the fingerprint reader is connected or not.
def initializeDevice():
    result = 1
    return result

# function to adjuct baud rate.
def setBaudrate(brate = 9600):
    result = 1
    return result

# function to open the connection between the controller and the scanner.
def openDevice():
    result = 1
    return result

# function to toggle LED value. Default call turns off the LED in the scanner.
def setLED(sval = False):
    result = 1
    return result

# function to start the enrollment sequence.
def enrollSeq(): #parameters are still undef.
    return True

# function to connect the module to the remote database.
def dbaseConnect():
    return True

# function to send any detected fingerprints scans to the database.
def sendInfo():
    return True

# function that print ok message.
def printOKload(msg):
    print bcolors.ENDC + "[  " + bcolors.OKGREEN + bcolors.BOLD + "OK" + bcolors.ENDC + "  ]  " + msg

# function to print fail message.
def printFLload(msg):
    print bcolors.ENDC + "[ " + bcolors.FAIL + bcolors.BOLD + "FAIL" + bcolors.ENDC + " ]  " + msg



# main GUI.
print bcolors.WARNING + bcolors.BOLD + "CLOUD-BAS: version [alpha] 0.17. SUNY KOREA, LEAD LABORATORIES & BLUE SMOKE LABS, in conjucntions with ITCCP. \n INITIALIZING BIOMETRIC ATTENDANCE SYSTEM... "

# initialize device
result = 0
# init device
result = initializeDevice()
if (result == 1):
    printOKload("Succesfully initialized device.")
else:
    printFLload("ERROR: Failed to initialize device. Check the connection, device power status, or connections.")
# open device
result = openDevice()
if (result == 1):
    printOKload("Succesfully opened port to device.")
else:
    printFLload("ERROR: Failed to open port to device. Check the connection, device power status, or connections.")
