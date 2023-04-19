# MIT License

# Copyright (c) 2023 PHYSCORP

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NON INFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# Attempt to import all necessary libraries
try:
    import os
    import sys
    import cv2
    import time
    import numpy as np
    from rich import print
    from rich.traceback import install
    install()
except ImportError as e:
    print("[ERROR] You are missing one or more libraries. This script cannot continue")
    print(e)
    print("Try running `python3 -m pip install -r requirements.txt`")
    quit()

# Determine main program directory
maindirectory = os.path.dirname(os.path.abspath(__file__)) # The absolute path to this file

# Custom low-level functions
# def print(text="", log_filename=""):
#     if log_filename != "":
#         with open(os.path.join(maindirectory, "logs", log_filename), "a") as f:
#             f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {text}")
#     __builtins__.print(text)

# Get arguments from kwargs
try:
    sys_args = sys.argv[1:]
    arguments = {}
    for value in sys_args:
        if value.startswith("--"):
            value = value[2:]
        if "=" not in value:
            arguments[value] = True
        else:
            value = value.split("=")
            arguments[value[0]] = value[1]
except IndexError:
    print("[ERROR]: No arguments were provided. You must provide arguments in the format of `argument=value`")
    print("Example: `python3 main.py input=\"FULL_PATH_TO_IMAGE.png\" output=\"FULL_PATH_TO_OUTPUT.gcode\"`")
    quit()

# Override everything with help command
if "help" in arguments:
    print("=== MarbleMachine HELP ===")
    print("This script is used to convert an image, either from a webcam or a file, into a set of line segment g-code, similar to a CNC etch-a-sketch.")
    print("The image should be a black and white image, with the drawing in black.")
    print("The image should be a 1:1 ratio, and should be 1000x1000 pixels.")
    print("The image should be a PNG file.")
    print("[OPTIONS]")
    print("input: The input filename. If this is not provided, then the script will capture from a webcam.")
    print("output: The output filename. This is required.")
    print("help: Displays this help message.")
    print("=== END MarbleMachine HELP ===")
    quit()

# Newline
print()

# [ MAIN ]

if __name__ == "__main__":
    # [Options]
    program_input_filename = "input.png"
    program_output_filename = "output.gcode"
    program_maximum_x = 613
    program_maximum_y = 548
    program_initial_speed = 5000
    program_border_x = 50
    program_border_y = 50
    program_debug = True
    
    # Raspberry pi related options
    pi_mode = False
    input_pin = 17

    if pi_mode:
        import RPi.GPIO as GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(input_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    # GPIO protection
    try:
        # Get paths
        program_input_filename = os.path.join(maindirectory, "temp", program_input_filename)
        program_output_filename = os.path.join(maindirectory, "temp", program_output_filename)
        
        # Welcome message
        print("=== Welcome to MarbleMachine ===")
        print(f"Input Filename: \"{program_input_filename}\"")
        print(f"Output Filename: \"{program_output_filename}\"")
        print()

        while True:
            print("[INFO]: Starting a new loop")
            print()
            # If the input filename is empty, then we are capturing from a webcam
            # Open the webcam, then wait for the user to press enter before capturing
            if program_input_filename == "":
                print("[INFO]: Press [yellow]ENTER[/yellow] to capture an image from the webcam.")
                input()
                print("[INFO]: Capturing image from webcam...")
                cap = cv2.VideoCapture(0)
                ret, frame = cap.read()
                cv2.imwrite(os.path.join(maindirectory, "temp", "webcam_capture.png"), frame)
                program_input_filename = os.path.join(maindirectory, "temp", "webcam_capture.png")
                print("[INFO]: Image captured.")
                print()
            
            # Import the image of the whiteboard with the drawing in black expo marker
            print("[INFO]: Importing image...")
            try:
                image = cv2.imread(program_input_filename)
            except FileNotFoundError:
                print("[ERROR]: The file you provided does not exist.")
                quit()
            print("[INFO]: Image imported.")

            # Convert the image to grayscale
            print("[INFO]: Converting image to grayscale...")
            image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            print("[INFO]: Image converted to grayscale.")

            # Invert the image
            print("[INFO]: Inverting image...")
            image = cv2.bitwise_not(image)
            print("[INFO]: Image inverted.")

            # Threshold the image
            print("[INFO]: Thresholding image...")
            ret, image = cv2.threshold(image, 127, 255, cv2.THRESH_BINARY)
            print("[INFO]: Image thresholded.")

            # Convert the image to a fixed size
            print("[INFO]: Converting image to fixed size...")
            image = cv2.resize(image, (1000, 1000))
            print("[INFO]: Image converted to fixed size.")

            # Apply the Euclidean Distance Transform
            print("[INFO]: Applying Euclidean Distance Transform...")
            dist_transform = cv2.distanceTransform(image, cv2.DIST_L2, 5)
            print("[INFO]: Euclidean Distance Transform applied.")

            # Normalize the distance transform image
            print("[INFO]: Normalizing the distance transform image...")
            norm_transform = cv2.normalize(dist_transform, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)
            print("[INFO]: Distance transform image normalized.")

            # Threshold the normalized image to remove all pixels that aren't true black
            print("[INFO]: Thresholding the normalized image...")
            _, thresholded_image = cv2.threshold(norm_transform, 254, 255, cv2.THRESH_BINARY)
            print("[INFO]: Normalized image thresholded.")

            # [ Debug ] Display the image
            print("[INFO]: Displaying image, press [yellow]0[/yellow] to continue ...")
            cv2.imshow("Image", thresholded_image)
            cv2.waitKey(0)
            cv2.destroyAllWindows()

            # Find the contours
            # print("[INFO]: Finding contours...")
            # contours, hierarchy = cv2.findContours(image, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            # print("[INFO]: Contours found.")
            # print(f"[INFO]: Number of contours: {len(contours)}")

            # Init gcode
            gcode = ""
            gcode_temp = ""

            # If the initial speed is not 0, then set the initial speed
            if program_initial_speed != 0:
                gcode += f"M203 X{program_initial_speed} Y{program_initial_speed} Z{program_initial_speed}\n"

            # Convert the contours to gcode
            print("[INFO]: Converting contours to gcode...")
            for contour in contours:
                for point in contour:
                    # Convert the point coordinates to printer coordinates
                    printer_x = (((program_maximum_x-(2*program_border_x))/1000) * point[0]) + program_border_x
                    printer_y = (((program_maximum_y-(2*program_border_y))/1000) * point[1]) + program_border_y

                    if program_debug:
                        printer_z = 0
                    else:
                        printer_z = float(printer_y)

                    # Round all values to 3 decimal places
                    printer_x = round(printer_x, 3)
                    printer_y = round(printer_y, 3)
                    printer_z = round(printer_z, 3)

                    # Append the point to gcode_temp
                    gcode_temp += f"G0 X{printer_x} Y{printer_y} Z{printer_z}\n"
                # # Calculate the minimum enclosing circle
                # (center, radius) = cv2.minEnclosingCircle(contour)
                # # print(f"[INFO]: Center: {center}, Radius: {radius}")

                # # Append center to gcode_temp
                # gcode_temp += f"G0 X{center[0]} Y{center[1]}\n"
                
                # # Get the centroid coordinates
                # centroid_x, centroid_y = center
                
                # # Convert the centroid coordinates to printer coordinates
                # printer_x = (((program_maximum_x-(2*program_border_x))/1000) * centroid_x) + program_border_x
                # printer_y = (((program_maximum_y-(2*program_border_y))/1000) * centroid_y) + program_border_y
                
                # if program_debug:
                #     printer_z = 0
                # else:
                #     printer_z = float(printer_y)
                
                # # Round all values to 3 decimal places
                # printer_x = round(printer_x, 3)
                # printer_y = round(printer_y, 3)
                # printer_z = round(printer_z, 3)
                
                # gcode += f"G0 X{printer_x} Y{printer_y} Z{printer_z}\n"
            print("[INFO]: Contours converted to gcode.")

            # Write the gcode to a file
            print("[INFO]: Writing gcode to file...")
            with open(program_output_filename, "w") as f:
                f.write(gcode)
            print(f"[INFO]: Gcode written to {program_output_filename}.")

            print("Done!")

            if program_input_filename != "":
                if pi_mode:
                    # Wait for button press from GPIO pin 17
                    print("[INFO]: Press the button to capture another image from the webcam, or [bright_red]CTRL+C[/bright_red] to exit.")
                    GPIO.wait_for_edge(input_pin, GPIO.FALLING)
                else:
                    # Wait for user input
                    print("[INFO]: Press [bright_yellow]ENTER[/bright_yellow] to capture another image from the webcam, or [bright_red]CTRL+C[/bright_red] to exit.")
                    input()
                print()
    except KeyboardInterrupt:
        print("[INFO]: Keyboard interrupt detected, exiting...")
        if pi_mode:
            GPIO.cleanup()
        quit()