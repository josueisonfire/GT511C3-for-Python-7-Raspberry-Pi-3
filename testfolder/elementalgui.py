# imports & other misc stuff.
import sys
import struct
import time
from threading import Timer
from exceptions import *
import fingerpi as fp

# Global variables:
port = '/dev/ttyAMA0'

# commands class:
class Commands():
    ## Every method has to return `status` array of size 2
    def __init__(self):
        self._f = None
        self.status = 'Uninitialized...'
        self._led = None

        self.open = False
        self._status_template = r'%s; Baudrate: %s; Firmware ver.: %s; Serial #: %s'
        self._baudrate = 'N/A'
        self._firmware = 'N/A'
        self._serial_no = 'N/A'

# print status.
    def _update_status(self):
        if self.open:
            __status = 'Open'
        else:
            __status = 'Closed'
        self.status = self._status_template % (
            __status,
            str(self._baudrate),
            str(self._firmware),
            str(self._serial_no)
        )
        printWorkload("FPS Status: Port:" + str(__status) + " baudrate: " + str(self._baudrate) + " firmware: " + str(self._firmware) + " serial no.:" + str(self._serial_no))
# ERROR CODES:
# [0,0] = device is already initialized.
# [0,1] = device's port is not reachable.
    def Initialize(self, *args, **kwargs):
        if self._f is not None:
            raise AlreadyInitializedError('This device is already initialized')
            result = [0,0]
        else:
            try:
                self._f = fp.FingerPi(port = port)
                result = [None, None]
            except IOError as e:
                raise PortError(str(e))
                result = [0,1]

        # self._status = 'Initialized' # Change that to `closed`
        self._update_status()
        return result
# ERROR Codes:
# [0,0] = device already open.
# [0,1] = device uninitialized.
# [0,2] = device open request provided invalid parameters.
    def Open(self, *args, **kwargs):
        if self.open:
            result = [0,0]
            raise AlreadyOpenError('This device is already open')

        if self._f is None:
            result = [0,1]
            raise NotInitializedError('Please, initialize first!')


        # self._f.serial.reset_input_buffer()

        response = self._f.Open(extra_info = True, check_baudrate = True)
        if response[0]['ACK']:
            data = struct.unpack('II16B', response[1]['Data'])
            # serial_number = bytearray(data[2:])

            self._baudrate = response[0]['Parameter']
            self._firmware = data[0]
            self._serial_no = str(bytearray(data[2:])).encode('hex')
            result = [None, None]
            self.open = True # Show the default status iff NOT initialized!
            self._update_status()
        else:
            raise NackError(response[0]['Parameter'])
            result = [0,2]
        return result
    ####################################################################
    ## All (other) commands:
    # ERROR Codes:
    # [0,0] = port is not open. cannot close.
    # [0,2] = device close request provided invalid parameters.

    def Close(self, *args, **kwargs):
        if not self.open:
            result = [0,0]
            raise NotOpenError('Please, open the port first!')
        response = self._f.Close()
        if not response[0]['ACK']:
            result = [0,2]
            raise NackError(response[0]['Parameter'])
        else:
            result = [None, None]
        self.open = False
        self._update_status()
        return result

    def UsbInternalCheck(self, *args, **kwargs):
        if not self.open:
            raise NotOpenError('Please, open the port first!')
        response = self._f.UsbInternalCheck()
        if reponse[0]['ACK']:
            return ['USB Internal Check returned: ' + str(response[0]['Parameter']), None]
        else:
            raise NackError(response[0]['Parameter'])
# ERROR Codes:
# [0,0] = port has not been opened.
# [0,2] = invalid parameters.

    def CmosLed(self, *args, **kwargs): # Need screen for popup window
        # Several modes of operation:
        # 1) If no argument is given - toggle LED
        # 2) If named boolean argument `led` is given - set the led to specified value
        if not self.open:
            result = [0.0]
            raise NotOpenError('Please, open the port first!')
        # toggle function. if called for the first time, set to true.
        if self._led is None:
            self._led = True
        else:
            self._led = not self._led #toggles LED if no arg is given.
        # end of toggle function.
        if kwargs.get('led', None) is not None:
            self._led = kwargs['led']
            response = self._f.CmosLed(self._led)
            result = [None, None]
            # print "response from LED request: " + str(response)
        else:
            raise NackError(response[0]['Parameter'])
            result = [0,2]
        return result

    def ChangeBaudrate(self, *args, **kwargs):
        if not self.open:
            raise NotOpenError('Please, open the port first!')
        rate = int(kwargs['baudrate'])
        if not (9600 <= rate <= 115200):
            raise ValueError('Incorrect baudrate: ' + str(args[0]))
        response = self._f.ChangeBaudrate(rate)
        if response[0]['ACK']:
            self._baudrate = str(rate)
            self._update_status()
            return [None, None]
        else:
            self.open = False
            self._baudrate = 'Unknown'
            self._update_status()
            raise NackError("Couldn't change baudrate: " + str(response[0]['Parameter']))

    def GetEnrollCount(self, *args, **kwargs):
        if not self.open:
            raise NotOpenError('Please, open the port first!')
        response = self._f.GetEnrollCount()
        if response[0]['ACK']:
            return ['Number of enrolled fingerprints: ' + str(response[0]['Parameter']), None]
        else:
            raise NackError(response[0]['Parameter'])
# ERROR Code:
# [0,0] = port has not been opened yet.
# [0,2] = invalid parameters.
# [0,3] = invalid slot parameter.
    def CheckEnrolled(self, ID):
        if not self.open:
            return [0,0]
        if (ID < 200 and ID >= 0):
            response = self._f.CheckEnrolled(int(ID))
            # tester.
            # print "RESPONSE FROM ENROLLCHECK REQUEST:  " + str(response)
            if response[0]['ACK']:
                #ID is in use.
                return [None, None]
            # if the fp slot is populated:
            elif (response[0]['ACK'] == False):
                # print "response[0]['Parameter'] has value of: " + str(response[0]['Parameter'])
                if (response[0]['Parameter'] == 4100):
                    #the specified field is not used.
                    return [None, 0]
                else:
                    printFLload("Invalid paramter in checkEnroll Method.")
                    return [0, 2]
            else:
                #ERROR
                return [0,2]
                #screen.addstr(3, 2, response[0]['Parameter'])
        else:
            return [0,3]

    def IsPressFinger(self, *args, **kwargs):
    # ret values:
    # [None, None] = finger is pressed.
    # [0,0] = port has not yet opened.
    # [0,2] = invalid params
        if not self.open:
            raise NotOpenError('Please, open the port first!')
        response = self._f.IsPressFinger()
        if response[0]['ACK']:
            if response[0]['Parameter'] == 0:
                # Finger is pressed
                return [None, None]
            else:
                return [1, 0]
        else:
            raise NackError(response[0]['Parameter'])

    def EnrollStart(self, ID):
        if not self.open:
            raise NotOpenError('Please, open the port first!')
            return [0,0]
        # ret = [False, None]
        while True:
            # <INPUT digit param here.>
            response = self._f.EnrollStart(ID)
            if response[0]['ACK']:
                return [None, None]
                break
            elif response[0]['ACK'] == False:
                if response[0]['Parameter'] == 4105:
                    printFLload("Enrollment Init Failed. DB is fUll.")
                    return [4105, 0]
                elif response[0]['Parameter'] == 4099:
                    printFLload("Enrollment Init failed. Invalid position given.")
                    return [4099, 0]
                elif response[0]['Parameter'] == 4101:
                    printFLload("Enrollment Init failed. Specified ID is already in use.")
                    return [4101, 0]
            break
        return ret

    def Enroll1(self, ID, *args, **kwargs):
        # ERROR CODES: 
        # [0,0] = port not open
        # [0,2] = invalid params.
        # [4109,0] = Fingerprint has already been registered.
        # [4108,0] = Faulty Fingerprint.
        if not self.open:
            raise NotOpenError('Please, open the port first!')
            return [0,0]
        response = self._f.Enroll1()
        if response[0]['ACK'] == True:
            # no issues.
            return [None, None]
        elif response[0]['ACK'] == False:
            # if ack param was false, that is, there was an error:
            if response[0]['Parameter'] == 4109:
                # enroll failed.
                printFLload("ERR: Fingerprint at slot " + str(ID) + " has already been registered. If you want to try again, press <x>")
                return [4109, 0]
            elif response[0]['Parameter'] == 4108:
                # bad finger.
                printFLload("ERR: Bad fingerprint. Please try again.")
                return [4108, 0]
            else:
                # unexpected error.
                return [0,2]

    def Enroll2(self, ID, *args, **kwargs):
        # ERROR CODES: 
        # [0,0] = port not open
        # [0,2] = invalid params.
        # [4109,0] = Fingerprint has already been registered.
        # [4108,0] = Faulty Fingerprint.
        if not self.open:
            raise NotOpenError('Please, open the port first!')
            return [0,0]
        response = self._f.Enroll2()
        if response[0]['ACK'] == True:
            # no issues.
            return [None, None]
        elif response[0]['ACK'] == False:
            # if ack param was false, that is, there was an error:
            if response[0]['Parameter'] == 4109:
                # enroll failed.
                # printFLload("ERR: Fingerprint at slot " + str(ID) + " has already been registered. If you want to try again, press <x>")
                return [4109, 0]
            elif response[0]['Parameter'] == 4108:
                # bad finger.
                # printFLload("ERR: Bad fingerprint. Please try again.")
                return [4108, 0]
            else:
                # unexpected error.
                return [0,2]

    def Enroll3(self, ID, *args, **kwargs):
        # ERROR CODES:
        # [0,0] = port not open
        # [0,2] = invalid params.
        # [4109,0] = Fingerprint has already been registered.
        # [4108,0] = Faulty Fingerprint.
        if not self.open:
            raise NotOpenError('Please, open the port first!')
            return [0, 0]
        response = self._f.Enroll3()
        if response[0]['ACK'] == True:
            # no issues.
            return [None, None]
        elif response[0]['ACK'] == False:
            # if ack param was false, that is, there was an error:
            if response[0]['Parameter'] == 4109:
                # enroll failed.
                # printFLload("ERR: Fingerprint at slot " + str(ID) + " has already been registered. If you want to try again, press <x>")
                return [4109, 0]
            elif response[0]['Parameter'] == 4108:
                # bad finger.
                # printFLload("ERR: Bad fingerprint. Please try again.")
                return [4108, 0]
            else:
                # unexpected error.
                print "ERR:  Duplicate ID found at slot: " + str(response[0]['Parameter'])
                return [0,2]

    def DeleteID(self, *args, **kwargs):
        if not self.open:
            raise NotOpenError('Please, open the port first!')
        screen = args[0]
        y, x = screen.getmaxyx()
        # screen.border(0)
        # screen.addstr(0, 1, 'Enter the ID to check, or empty field to exit...'[:x-2], curses.A_STANDOUT)
        curses.echo()
        ret = [False, None]
        while True:
            screen.addstr(2, 2, '>>> ')
            screen.clrtoeol()
            screen.border(0)
            screen.addstr(0, 1, 'Enter an ID to delete, or empty field to cancel...'[:x-2], curses.A_STANDOUT)
            ID = screen.getstr(2, 6)
            if ID.isdigit():
                response = self._f.DeleteID(int(ID))
                if response[0]['ACK']:
                    # screen.addstr(3, 2, 'ID in use!')
                    # screen.clrtoeol()
                    ret[0] = 'ID {0:d} deleted'.format(ID)
                    break
                else:
                    screen.addstr(3, 2, response[0]['Parameter'])
                    screen.clrtoeol()
            elif ID.isalnum():
                curses.noecho()
                raise ValueError('Non-numeric value found!')
            else:
                break
        curses.noecho()
        return ret

    def DeleteAll(self, *args, **kwargs):
        if not self.open:
            raise NotOpenError('Please, open the port first!')
            return [0,0]
        response = self._f.DeleteAll()
        if not response[0]['ACK']:
            printFLload("ERR: Deletion failed. Error code: " + str(response[0]['Parameter']))
        else:
            return [None, None]
        
    # ret vals:
    # [0,0] = port not open
    # [0,1] = No fp template matched.
    # [0,3] = Communication error.
    # [param, 0] = scanner found the following match
    def Identify(self, *args, **kwargs):
        if not self.open:
            return [0,0]
            raise NotOpenError('Please, open the port first!')
        response = self._f.Identify()
        if response[0]['ACK'] == True:
            printOKload("Identified Fp at slot: " + str(response[0]['Parameter']))
            if response[0]['Parameter'] == None:
                printFLload("We have a problem: the scanner won't return a valid ID value.")
                return -1
            else:
                return int(response[0]['Parameter'])
        else:
            # ACK was false:
            if response[0]['Parameter'] ==  4105:
                printFLload("ERR: Scanner does not have any templates.")
                return [0,3]
            elif response[0]['Parameter'] == 4104:
                # normal. Means the scanner found no such FP.
                return [0,1]

# Messy code. FIX LATER.
    def CaptureFinger(self, *args, **kwargs):
        if not self.open:
            return [0,0]
            raise NotOpenError('Please, open the port first!')
        # parameter to tell the scanner to capture the best img possible.
        best_image = 1
        if len(args) > 0:
            best_image = args[0]
        response = self._f.CaptureFinger(best_image)
        if not response[0]['ACK']:
            if response[0]['Parameter'] == 4114:
                printFLload("ERR: Finger is not pressed for finger capture.")
            else:
                printFLload("ERR: Unexpected error.")
        else:
            # ACK == true
            return [None, None]
        

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

# instantiate commands class. aka instantiating device object device
localFPS = Commands()

# code to init device. check availability of the port, and determines whether the fingerprint reader is connected or not.
def initializeDevice():
    if (localFPS.Initialize() == [None, None]):
        printOKload("Succesfully initialized device.")
        result = 1
    else:
        printFLload("ERROR: Failed to initialize device. Check the connection, device power status, or connections.")
        result = 0
    return result

# function to adjuct baud rate.
def setBaudrate(brate = 9600):
    printWorkload("Setting baud rate to device...")
    if (localFPS.ChangeBaudrate(baudrate = brate) == [None, None]):
        printOKload("Succesfully set baud rate of the device.")
        result = 1
    else:
        printFLload("ERROR: Failed to set baud rate. check device connetions and baud rate value parameter values.")
        result = 0
    return result

# function to open the connection between the controller and the scanner.
def openDevice():
    printWorkload("Opening port to GT511C3 Fingerprint Scanner Module...")
    if (localFPS.Open() == [None, None]):
        printOKload("Succesfully opened port to device.")
        result = 1
    else:
        printFLload("ERROR: Failed to open port to device. Check the connection, device power status, or connections.")
        result = 0
    return result

# function to close connection between the controller and FPS.
def closeDevice():
    printWorkload("Closing port to GT511C3 Fingerprint Scanner Module...")
    if (localFPS.Close() == [None, None]):
        printOKload("Succesfully closed port to device.")
        result = 1
    else:
        printFLload("ERROR: Failed to close connection between Fingerprint Scanner Module. was the device already closed? Was it initialized int he first place?")
        result = 0
    return result
# function to toggle LED value. Default call turns off the LED in the scanner.
def setLED(sval = False):
    # print "Setting LED value to " + str(sval)
    result = localFPS.CmosLed(led = sval)
    # print "SET LED Function ret Value: " + str(result)
    return result

# helper funcition to find an unoccupied slot in the scanner.
def checkSlot():
    printWorkload("Checking for open ID fields in scanner")
    n = 0
    while True:
        ret = localFPS.CheckEnrolled(ID = n)
        if n == 199:
            "No empty index found"
            return -1
            break
        if (ret == [None, 0]):
        # not occupied
            printOKload("Found empty index at slot " + str(n))
            return n
            break
        elif(ret == [None, None]):
            printWorkload("index " + str(n) + " is occupied.")
        else:
            printFLload("ERROR Ocurred while finding slot in scanner. Error code: " + str(ret))
        n = n + 1
    return None

# function to make user reapply fingerprint to the scanner, without continuously looping.
# once a fingerprint has been taken out, it will light up the light after 0.2 secs and available to take the next fp.
def reCatch():
    while True:
        if localFPS.IsPressFinger() == [1,0]:
            setLED(sval = False)
            time.sleep(0.2)
            setLED(sval = True)
            # TODO : implement light led to do something, like a red light.
            ledagain = 1 # gibberish
            break

# function to start the enrollment sequence.
def enrollSeq(): #parameters are still undef.
# return values:
# -1 error
# -2 unexpected error
# 0 normal execution.
    # Turn on LED light:
    setLED(sval = True)

    # check ID slots until they are unoccupied. If all are occupied, send FULL error. and delete the first in the list.
    slot = checkSlot()
    # start enrollment @ specified ID.
    if (localFPS.EnrollStart(ID = slot) == [None, None]):
        printOKload("Scanner is now ready to accept the fingerprint.")
    elif (localFPS.EnrollStart(ID = slot) == [4105, 0]):
        printFLload("Scanner has failed to initialize enrollment sequence.")
        # erase (delete) 1st item in the scanner, and store it there.
        # TODO : implement automated deletion.
    else: 
        return -1 #error!
    # if perm = [None, None], we're good to go.
    # do first enrollment. figure out how to 1) send the enroll 
    threshhold = 3
    while True:
        # [None, None] = no issues.
        # [4109,0] = Fingerprint has already been registered.
        # [4108,0] = Faulty Fingerprint.
        if (localFPS.IsPressFinger() == [None, None]):
            # 
            if localFPS.CaptureFinger() == [None, None]:
                # then do enrollment
                res = localFPS.Enroll1(ID = slot)
                if (res == [None, None]):
                    # no problems found. continue.
                    printOKload("First Enrollment Successfull!")
                    reCatch()
                    break
                elif (res == [4108,0]):
                    printFLload("Faulty Fingerprint. Please try again!")
                    reCatch()
                elif (res == [4109,0]):
                    if threshhold > 0:
                        printFLload("ERR: Fingerprint has already been registered. To be sure, try again.")
                        threshhold = threshhold - 1
                        reCatch()
                    else:
                        printFLload("ERR: fingerprint has already been registered. Aborting...")
                        return -1
                else:
                    printFLload("ERR: Unparsed Error. Aborting...")
                    return -2
           
    threshhold = 3
    while True:
        # [None, None] = no issues.
        # [4109,0] = Fingerprint has already been registered.
        # [4108,0] = Faulty Fingerprint.
        if (localFPS.IsPressFinger() == [None, None]):
            
            if localFPS.CaptureFinger() == [None, None]:
                # then do enrollment
                res = localFPS.Enroll2(ID = slot)
                if (res == [None, None]):
                    # no problems found. continue.
                    printOKload("Second Enrollment Successfull!")
                    reCatch()
                    break
                elif (res == [4108,0]):
                    printFLload("Faulty Fingerprint. Please try again!")
                    reCatch()
                elif (res == [4109,0]):
                    if threshhold > 0:
                        printFLload("ERR: Fingerprint has already been registered. To be sure, try again.")
                        threshhold = threshhold - 1
                        reCatch()
                    else:
                        printFLload("ERR: fingerprint has already been registered. Aborting...")
                        return -1
                else:
                    printFLload("ERR: Unparsed Error. Aborting...")
                    return -2
       
    # third enrollment
    threshhold = 3
    while True:
        # [None, None] = no issues.
        # [4109,0] = Fingerprint has already been registered.
        # [4108,0] = Faulty Fingerprint.
        if (localFPS.IsPressFinger() == [None, None]):
            if localFPS.CaptureFinger() == [None, None]:
                # then do enrollment
                res = localFPS.Enroll3(ID = slot)
                if (res == [None, None]):
                    # no problems found. continue.
                    printOKload("Third Enrollment Successfull!")
                    reCatch()
                    break
                elif (res == [4108,0]):
                    printFLload("Faulty Fingerprint. Please try again!")
                    reCatch()
                elif (res == [4109,0]):
                    if threshhold > 0:
                        printFLload("ERR: Fingerprint has already been registered. To be sure, try again.")
                        threshhold = threshhold - 1
                        reCatch()
                    else:
                        printFLload("ERR: fingerprint has already been registered. Aborting...")
                        return -1
                else:
                    printFLload("ERR: Duplicate fingerprint already exists in local database. " + str(res) + " Aborting...")
                    return -2
    # turn off LED
    setLED(sval = False)

    return True

# Function to identify fingerprint:
def indentifyFingerprint():
    #Turn on the LED:
    setLED(sval = True)
    printWorkload("Now scanning for fingerprints:")
    res = None
    while True:
        # [None, None] = no issues.
        # [4109,0] = Fingerprint has already been registered.
        # [4108,0] = Faulty Fingerprint.
        if (localFPS.IsPressFinger() == [None, None]):
            # 
            if localFPS.CaptureFinger() == [None, None]:
                # then do enrollment
                res = localFPS.Identify()
                if res == [0,0]:
                    printFLload("Port is not opened")
                    return -1
                elif res == [0,1]:
                # no matching FP template
                    printFLload("Scanner has not found a matching fingerprint.")
                    return -1
                elif res == [0,3]:
                # COMMS error
                    printFLload("Communication ERROR!")
                    return -1
                else:
                    printOKload("SCANNER HAS IDENTIFIED FINGERPRINT WITH ID: " + str(res))
                    break
    reCatch()
    return res


# function to connect the module to the remote database.
def dbaseConnect():
    return True

# function to send any detected fingerprints scans to the database.
def sendInfo():
    return True

# function that print ok message.
def printOKload(msg):
    print bcolors.ENDC + "[  " + bcolors.OKGREEN + bcolors.BOLD + "OK" + bcolors.ENDC + "  ]  " + msg + bcolors.ENDC

# function to print fail message.
def printFLload(msg):
    print bcolors.ENDC + "[ " + bcolors.FAIL + bcolors.BOLD + "FAIL" + bcolors.ENDC + " ]  "+ bcolors.FAIL + bcolors.BOLD + msg + bcolors.ENDC

def printWorkload(msg):
    print bcolors.WARNING + msg + bcolors.ENDC


# THE GUI code.

# main GUI.
print bcolors.WARNING + bcolors.BOLD + "CLOUD-BAS: version [alpha] 0.17. SUNY KOREA, LEAD LABORATORIES & BLUE SMOKE LABS, in conjunction with ITCCP.\nINITIALIZING BIOMETRIC ATTENDANCE SYSTEM... "

# initialize device
result = 0
initializeDevice()
time.sleep(0.1)
# open device
openDevice()
# change baud rate
setBaudrate(brate = 115200)

setLED(sval = True)
time.sleep(0.2)
setLED()

localFPS._update_status()

# Main GUI loop
while True:
    printWorkload("Select a desired operation:\n (S)how information, (E)nroll , (I)dentify, (C)hange baud rate, (D)elete template/s, E(x)it.")
    inp = raw_input("Enter Command: ")
    if inp == "E" or inp == "e":
        # start enrollment sequence.
        enrollSeq()
    elif inp == "i" or inp == "I":
        # Start Indentification sequence.
        indentifyFingerprint()
    elif inp == "C" or inp == "c":
        # start change baud rate sequence.
        cbrt = input("input the desired baud rate. 9600, 14400, 19200, 28800, 38400, 57600, 115200.")
        if cbrt.isdigit():
            if int(cbrt) == 9600 or int(cbrt) == 14400 or int(cbrt) == 19200 or int(cbrt) == 28800 or int(cbrt) == 38400 or int(cbrt) == 57600 or int(cbrt) == 115200:
                setBaudrate(brate = cbrt)
        else:
            printWorkload("ERROR: Invalid Baud rate value input. Please check you input and try again.")
    elif inp == "S" or inp == "s":
        localFPS._update_status()
        # start show info sequence
    elif inp == "d" or inp == "D":
        ret = localFPS.DeleteAll()
        if ret == [None, None]:
            printOKload("Deleted all Fingerprint templates:")
        else:
            printFLload("Failed to delete all fp templates. Either because there was a connection eorro or there are no templates to delete.")
        # Start deletion sequence
    elif inp == "exit" or inp == "Exit" or inp == "Quit" or inp == "quit" or inp == "X" or inp == "x":
        setLED(sval = False)
        closeDevice()
        sys.exit()
        # start exit sequence.

