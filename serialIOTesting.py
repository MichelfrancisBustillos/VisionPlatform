import serial

# Global Vars
ser = serial.Serial("COM7", 115200, timeout=None)  # Create Serial connection on port COM7 w/ baudrate 115200


def main():
    ser.close()  # Close serial port, in case it was left open
    ser.open()  # Reopen serial port for communication

    # Wait for ESP32 Setup() to complete
    setup_complete = False
    while setup_complete == False:
        message_received = ser.readline().decode()
        if message_received != "":  # Do not print blank messages
            print(message_received)
        if ("SETUP COMPLETE!" in message_received):  # If message contains "SETUP COMPLETE!" print alert and exit loop
            print("Setup complete received.")
            setup_complete = True

    while True:
        command = input("Enter command: ")
        serialIO(command)
    ser.close()


def serialIO(command):
    ser.write(command.encode())  # Encode and send command
    message_received = ser.readline().decode()  # Read serial response
    while (not "~" in message_received):  # Read serial response until end of message character received
        print(message_received)
        message_received = ser.readline().decode()


if __name__ == "__main__":
    main()
