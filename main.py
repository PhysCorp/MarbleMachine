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
def print(text="", log_filename=""):
    if log_filename != "":
        with open(os.path.join(maindirectory, "logs", log_filename), "a") as f:
            f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {text}")
    __builtins__.print(text)

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
    print("Example: `python3 main.py input=\"FULL_PATH_TO_IMAGE.png\" output=\"FULL_PATH_TO_OUTPUT.stl\"`")
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

# Get the input filename
try:
    program_input_filename = arguments["input"]
except KeyError:
    print("[INFO]: No filename was provided. Assuming that you are capturing from a webcam.")
    program_input_filename = ""

# Get the output filename
try:
    program_output_filename = arguments["output"]
except KeyError:
    print("[WARN]: No output filename was provided. You must provide an output filename using the syntax `output=FILENAME`")
    quit()

# Get the bed_shake value
try:
    program_bed_shake = arguments["bed_shake"]
    if "true" in program_bed_shake.lower():
        program_bed_shake = True
    elif "false" in program_bed_shake.lower():
        program_bed_shake = False
    else:
        print("[WARN]: Invalid bed_shake value. Assuming False.")
        program_bed_shake = False
except KeyError:
    # print("[INFO]: No bed_shake value was provided. Assuming False.")
    program_bed_shake = False

# Custom functions
# [ Placeholder ]

# Newline
print()

# [ MAIN ]

if __name__ == "__main__":
    # Welcome message
    print("=== Welcome to MarbleMachine ===")
    print(f"Input Filename: \"{program_input_filename}\"")
    print(f"Output Filename: \"{program_output_filename}\"")
    print(f"Bed Shake: {program_bed_shake}")
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

    # Find the contours of the image
    print("[INFO]: Finding contours...")
    contours, hierarchy = cv2.findContours(image, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    print("[INFO]: Contours found.")

    # [ Debug ] Display the image
    print("[INFO]: Displaying image, press [yellow]0[/yellow] to continue ...")
    cv2.imshow("Image", image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    # Init gcode
    gcode = ""

    # If the bed_shake argument is true, then we need to add a shake to the bed
    if program_bed_shake:
        print("[INFO]: Adding bed shake...")
        # Quickly move the bed back and forth a few times by oscillating the Z value
        for i in range(25):
            # Use modulo to oscillate between 0 and 1
            if i % 2 == 0:
                gcode += "G0 Z0\n"
            else:
                gcode += "G0 Z1\n"
        print("[INFO]: Bed shake added.")

    # Convert the contours to gcode
    print("[INFO]: Converting contours to gcode...")
    for contour in contours:
        for point in contour:
            gcode += f"G0 X{point[0][0]} Y{point[0][1]} Z0\n"
    print("[INFO]: Contours converted to gcode.")

    # Write the gcode to a file
    print("[INFO]: Writing gcode to file...")
    with open(program_output_filename, "w") as f:
        f.write(gcode)
    print("[INFO]: Gcode written to file.")

    print("Done!")

    # Exit message
    print("=== Exiting MarbleMachine ===")