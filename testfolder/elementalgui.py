# imports & other misc stuff.

import struct
from time import sleep
from threading import Timer
from exceptions import *
import fingerpi as fp

# Global variables:
port = '/dev/ttyAMA0'

# repeating timer.
class RepeatingTimer(object):
    def __init__(self, interval, f, *args, **kwargs):
        self.interval = interval
        self._f = f
        self.args = args
        self.kwargs = kwargs

        self.timer = None

    def callback(self):
        self._f(*self.args, **self.kwargs)
        self.start()

    def cancel(self):
        self.timer.cancel()

    def start(self):
        self.timer = Timer(self.interval, self.callback)
        self.timer.start()

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

    def Blink(self, *args, **kwargs):
        if not self.open:
            raise NotOpenError('Please, open the port first!')
        screen = args[0]
        y, x = screen.getmaxyx()
        screen.border(0)
        screen.addstr(0, 1, 'Press any button to stop...'[:x-2], curses.A_STANDOUT)

        t = RepeatingTimer(0.5, self.CmosLed, screen)
        t.start()

        screen.refresh()
        inp = screen.getch()
        if inp:
            t.cancel()
            self.CmosLed(led = False)
            self._led = False

        return ['', None]

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

    def CmosLed(self, *args, **kwargs): # Need screen for popup window
        # Several modes of operation:
        # 1) If no argument is given - toggle LED
        # 2) If named boolean argument `led` is given - set the led to specified value
        # 3) If positional argument is given - don't return the result, show the result on a separate curses.window
        if not self.open:
            raise NotOpenError('Please, open the port first!')
        if self._led is None:
            self._led = True
        else:
            self._led = not self._led

        if kwargs.get('led', None) is not None:
            self._led = kwargs['led']
        response = self._f.CmosLed(self._led)
        # response = [{'ACK': True}]
        if response[0]['ACK']:
            if len(args) > 0:
                # Screen is given, show a message
                args[0].addstr(2, 2, 'LED is set to ' + (' ON' if self._led else 'OFF'))
                args[0].refresh()
                return ['', None]
            else:
                # Screen is not given, return the message
                return ['LED is set to ' + ('ON' if self._led else 'OFF'), None]
        else:
            raise NackError(response[0]['Parameter'])

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

    def CheckEnrolled(self, *args, **kwargs):
        if not self.open:
            raise NotOpenError('Please, open the port first!')
        screen = args[0]
        y, x = screen.getmaxyx()
        # screen.border(0)
        # screen.addstr(0, 1, 'Enter the ID to check, or empty field to exit...'[:x-2], curses.A_STANDOUT)
        curses.echo()
        while True:
            screen.addstr(2, 2, '>>> ')
            screen.clrtoeol()
            screen.border(0)
            screen.addstr(0, 1, 'Enter the ID to check, or empty field to exit...'[:x-2], curses.A_STANDOUT)
            ID = screen.getstr(2, 6)
            if ID.isdigit():
                response = self._f.CheckEnrolled(int(ID))
                if response[0]['ACK']:
                    screen.addstr(3, 2, 'ID in use!')
                    screen.clrtoeol()
                else:
                    screen.addstr(3, 2, response[0]['Parameter'])
                    screen.clrtoeol()
            elif ID.isalnum():
                curses.noecho()
                raise ValueError('Non-numeric value found!')
            else:
                break
        curses.noecho()
        return [None, None]

    def IsPressFinger(self, *args, **kwargs):
        if not self.open:
            raise NotOpenError('Please, open the port first!')
        response = self._f.IsPressFinger()
        if response[0]['ACK']:
            if response[0]['Parameter'] == 0:
                # Finger is pressed
                return [True, None]
            else:
                return [False, None]
        else:
            raise NackError(response[0]['Parameter'])

    def EnrollStart(self, *args, **kwargs):
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
            screen.addstr(0, 1, 'Enter a new ID for enrollment, or empty field to cancel...'[:x-2], curses.A_STANDOUT)
            ID = screen.getstr(2, 6)
            if ID.isdigit():
                response = self._f.EnrollStart(int(ID))
                if response[0]['ACK']:
                    # screen.addstr(3, 2, 'ID in use!')
                    # screen.clrtoeol()
                    ret[0] = 'Enrollment of ID {0:d} started'.format(response[0]['Parameter'])
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

    def Enroll1(self, *args, **kwargs):
        if not self.open:
            raise NotOpenError('Please, open the port first!')
        response = self._f.Enroll1()
        if not response[0]['ACK']:
            if response[0]['ACK'] in errors:
                err = response[0]['ACK']
            else:
                err = 'Duplicate ID: ' + str(response[0]['ACK'])
            raise NackError(err)
        return [None, None]

    def Enroll2(self, *args, **kwargs):
        if not self.open:
            raise NotOpenError('Please, open the port first!')
        response = self._f.Enroll1()
        if not response[0]['ACK']:
            if response[0]['ACK'] in errors:
                err = response[0]['ACK']
            else:
                err = 'Duplicate ID: ' + str(response[0]['ACK'])
            raise NackError(err)
        return [None, None]

    def Enroll3(self, *args, **kwargs):
        if not self.open:
            raise NotOpenError('Please, open the port first!')
        response = self._f.Enroll1()
        if not response[0]['ACK']:
            if response[0]['ACK'] in errors:
                err = response[0]['ACK']
            else:
                err = 'Duplicate ID: ' + str(response[0]['ACK'])
            raise NackError(err)
        if self._f.save:
            return [str(len(response[1]['Data'])) + ' bytes received... And purged!', None]
        return [None, None]

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
        response = self._f.DeleteAll()
        if not response[0]['ACK']:
            raise NackError(response[0]['Parameter'])
        return [None, None]

    def Verify(self, *args, **kwargs):
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
            screen.addstr(0, 1, 'Enter an ID to verify, or empty field to cancel...'[:x-2], curses.A_STANDOUT)
            ID = screen.getstr(2, 6)
            if ID.isdigit():
                response = self._f.Verify(int(ID))
                if response[0]['ACK']:
                    # screen.addstr(3, 2, 'ID in use!')
                    # screen.clrtoeol()
                    ret[0] = 'ID {0:d} verified'.format(ID)
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

    def Identify(self, *args, **kwargs):
        if not self.open:
            raise NotOpenError('Please, open the port first!')
        response = self._f.Identify()
        if not response[0]['ACK']:
            raise NackError(response[0]['Parameter'])
        return [response[0]['Parameter'], None]

    def CaptureFinger(self, *args, **kwargs):
        if not self.open:
            raise NotOpenError('Please, open the port first!')

        best_image = 1
        if len(args) > 0:
            best_image = args[0]
        response = self._f.CaptureFinger(best_image)
        if not response[0]['ACK']:
            raise NackError(response[0]['Parameter'])
        return [None, None]

    def GetImage(self, *args, **kwargs):
        if not self.open:
            raise NotOpenError('Please, open the port first!')
        response = self._f.GetImage()
        if not response[0]['ACK']:
            raise NackError(response[0]['Parameter'])

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
            screen.addstr(0, 1, 'Enter an the path to save the file to, or empty field to cancel...'[:x-2], curses.A_STANDOUT)
            ID = screen.getstr(2, 6)
            if len(ID) > 0:
                data = response[1]['Data']
                # Try saving the file
                # try:
                # fl = open(ID, 'w')
                # fl.write(response[1]['Data'])
                # fl.close()
                # except IOError as e:
                #     curses.noecho()
                #     fl.close()
                #    raise IOError('Could not write file! ' + str(e))
                with open('ID', 'w') as f:
                    pickle.dump(data, f)
                break
            else:
                break
        curses.noecho()
        return ret


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
    if (localFPS.ChangeBaudrate(rate = brate) == [None, None]):
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
    print bcolors.ENDC + "[ " + bcolors.FAIL + bcolors.BOLD + "FAIL" + bcolors.ENDC + " ]  "+ bcolors.FAIL + bcolors.BOLD + msg

def printWorkload(msg):
    print bcolors.WARNING + bcolors.BOLD + msg

# THE GUI code.

# main GUI.
print bcolors.WARNING + bcolors.BOLD + "CLOUD-BAS: version [alpha] 0.17. SUNY KOREA, LEAD LABORATORIES & BLUE SMOKE LABS, in conjunction with ITCCP.\nINITIALIZING BIOMETRIC ATTENDANCE SYSTEM... "

# initialize device
result = 0
initializeDevice()
# open device
openDevice()
# change baud rate
ChangeBaudrate(brate = 115200)

closeDevice()
