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
    import math
    import cv2
    import platform
    import time
    import numpy as np
    from rich import print as rich_print
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
def print(text="", log_filename="", end="\n"):
    if log_filename != "":
        with open(os.path.join(maindirectory, "logs", log_filename), "a") as f:
            f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {text}")
    rich_print(text, end=end)

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
    print("Example: `python3 auto.py input=\"FULL_PATH_TO_IMAGE.png\" output=\"FULL_PATH_TO_OUTPUT.gcode\"`")
    quit()

# Override everything with help command
if "help" in arguments:
    print("=== MarbleMachine HELP ===")
    print("This script is used to convert an image, either from a webcam or a file, into a set of line segment g-code, similar to a CNC etch-a-sketch.")
    print("Under optimal conditions, the image should be 1:1 ratio, and be black and white.")
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
    print("[INFO]: No output filename was provided. Using \"output.gcode\".")
    program_output_filename = "output.gcode"

# Get the program_maximum_x
try:
    program_maximum_x = int(arguments["maximum_x"])
except KeyError:
    print("[INFO]: No maximum x was provided. Using 613.")
    program_maximum_x = 613

# Get the program_maximum_y
try:
    program_maximum_y = int(arguments["maximum_y"])
except KeyError:
    print("[INFO]: No maximum y was provided. Using 548.")
    program_maximum_y = 548

# Get the program_initial_speed
try:
    program_initial_speed = int(arguments["initial_speed"])
except KeyError:
    print("[INFO]: No initial speed was provided. Using 50000.")
    program_initial_speed = 50000

# Get the program_border_x
try:
    program_border_x = int(arguments["border_x"])
except KeyError:
    print("[INFO]: No border x was provided. Using 50.")
    program_border_x = 50

# Get the program_border_y
try:
    program_border_y = int(arguments["border_y"])
except KeyError:
    print("[INFO]: No border y was provided. Using 50.")
    program_border_y = 50

# Get the program_debug
try:
    program_debug = bool(arguments["debug"])
except KeyError:
    print("[INFO]: Debug mode was not specified. Assuming production mode.")
    program_debug = False

# Get the program_display
try:
    program_display = bool(arguments["display"])
except KeyError:
    print("[INFO]: Display mode was not specified. Assuming you do NOT want to display the image.")
    program_display = False

# Get the program_dwell_time
try:
    program_dwell_time = int(arguments["dwell_time"])
except KeyError:
    print("[INFO]: No dwell time was provided. Using 10000.")
    program_dwell_time = 10000

# Get the program_acceleration
try:
    program_initial_acceleration = int(arguments["acceleration"])
except KeyError:
    print("[INFO]: No acceleration was provided. Using 1000.")
    program_initial_acceleration = 1000

# Get the camera_number
try:
    camera_number = int(arguments["camera_number"])
except KeyError:
    print("[INFO]: No camera number was provided. Using 0.")
    camera_number = 0

# Get the pi_mode
try:
    pi_mode = bool(arguments["pi_mode"])
except KeyError:
    print("[INFO]: Pi mode was not specified. Assuming you are NOT on Pi.")
    pi_mode = False

# Get the input_pin
try:
    input_pin = int(arguments["input_pin"])
except KeyError:
    if pi_mode:
        print("[INFO]: No input pin was provided. Using 17.")
        input_pin = 17

# Get the print_flag
try:
    print_flag = bool(arguments["execute"])
except KeyError:
    print("[INFO]: Execution was not specified. Will NOT automatically print.")
    print_flag = False

# If print_flag is set, import the printer libraries
if print_flag:
    try:
        print("DEBUG")
        # from printrun.printrun.printcore import printcore
        # from printrun import gcoder
    except ImportError as e:
        print("[ERROR] You are missing one or more libraries. This script cannot continue")
        print(e)
        print("Try running `python3 -m pip install -r requirements.txt`")
        quit()

# Get the program_camera_bounds
try:
    program_camera_bounds = arguments["camera_bounds"]
    print(program_camera_bounds)
    # Convert the format of "(0,0)(0,0)" to [[0,0],[0,0]]
    program_camera_bounds = program_camera_bounds.replace("(", "")
    program_camera_bounds = program_camera_bounds.replace(")", ",")
    program_camera_bounds = program_camera_bounds.split(",")
    program_camera_bounds = [[int(program_camera_bounds[0]), int(program_camera_bounds[1])], [int(program_camera_bounds[2]), int(program_camera_bounds[3])]]
except KeyError:
    print("[INFO]: No camera bounds were provided. Using default.")
    program_camera_bounds = [[0, 0], [0, 0]]

# Newline
print()

# [ MAIN ]

if __name__ == "__main__":
    # Init program

    if pi_mode:
        import RPi.GPIO as GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(input_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    # GPIO protection
    try:
        # Get paths
        if program_input_filename != "":
            program_input_filename = os.path.join(maindirectory, "temp", program_input_filename)
        if program_output_filename != "":
            program_output_filename = os.path.join(maindirectory, "temp", program_output_filename)
        
        # Welcome message
        print("=== Welcome to MarbleMachine ===")
        print(f"Input Filename: \"{program_input_filename}\"")
        print(f"Output Filename: \"{program_output_filename}\"")
        print()

        bool_camera = False
        while True:
            print("[INFO]: Starting a new loop")
            print()
            # If the input filename is empty, then we are capturing from a webcam
            # Open the webcam, then wait for the user to press enter before capturing
            if program_input_filename == "" or bool_camera:
                image_looks_good = False
                while not image_looks_good:
                    bool_camera = True
                    print("[INFO]: Press [yellow]ENTER[/yellow] to capture an image from the webcam.")
                    input()
                    print("[INFO]: Capturing image from webcam...")
                    cap = cv2.VideoCapture(camera_number)
                    ret, frame = cap.read()
                    cv2.imwrite(os.path.join(maindirectory, "temp", "webcam_capture.png"), frame)
                    program_input_filename = os.path.join(maindirectory, "temp", "webcam_capture.png")
                    print("[INFO]: Image captured.")
                    print()
                    print("[INFO]: Displaying image...")
                    cv2.imshow("Original", frame)
                    cv2.waitKey(0)
                    cv2.destroyAllWindows()
                    print("[INFO]: Image displayed.")
                    print()
                    print("[INFO]: Does the image look good? [yellow]Y[/yellow]es/[yellow]N[/yellow]o")
                    image_looks_good = input().lower() == "y"
                    print()
                    if not image_looks_good:
                        print("[INFO]: Retrying...")
                        print()
                    else:
                        print("[INFO]: Image looks good.")
                        print()
            
            # Import the image of the whiteboard with the drawing in black expo marker
            print("[INFO]: Importing image...")
            try:
                image = cv2.imread(program_input_filename)
            except FileNotFoundError:
                print("[ERROR]: The file you provided does not exist.")
                quit()
            print("[INFO]: Image imported.")

            # Rotate the image 180 degrees
            print("[INFO]: Rotating image...")
            image = cv2.rotate(image, cv2.ROTATE_180)
            print("[INFO]: Image rotated.")

            # Display the image with the caption of "Original"
            if program_display:
                print("[INFO]: Displaying image...")
                cv2.imshow("Original", image)
                cv2.waitKey(0)
                cv2.destroyAllWindows()
                print("[INFO]: Image displayed.")

            # Crop the image based on the camera bounds, if they were provided
            if program_camera_bounds != [[0, 0], [0, 0]]:
                print("[INFO]: Cropping image...")
                print("[INFO]: Camera bounds: " + str(program_camera_bounds))
                image = image[program_camera_bounds[0][1]:program_camera_bounds[1][1], program_camera_bounds[0][0]:program_camera_bounds[1][0]]
                print("[INFO]: Image cropped.")

            # Convert the image to grayscale
            print("[INFO]: Converting image to grayscale...")
            image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            print("[INFO]: Image converted to grayscale.")

            # Display the image
            if program_display:
                print("[INFO]: Displaying image...")
                cv2.imshow("Grayscale", image)
                cv2.waitKey(0)
                cv2.destroyAllWindows()
                print("[INFO]: Image displayed.")

            # Invert the image
            print("[INFO]: Inverting image...")
            image = cv2.bitwise_not(image)
            print("[INFO]: Image inverted.")

            # Display the image
            if program_display:
                print("[INFO]: Displaying image...")
                cv2.imshow("Inverted", image)
                cv2.waitKey(0)
                cv2.destroyAllWindows()
                print("[INFO]: Image displayed.")

            # Threshold the image
            print("[INFO]: Thresholding image...")
            ret, image = cv2.threshold(image, 127, 255, cv2.THRESH_BINARY)
            print("[INFO]: Image thresholded.")

            # Display the image
            if program_display:
                print("[INFO]: Displaying image...")
                cv2.imshow("Thresholded", image)
                cv2.waitKey(0)
                cv2.destroyAllWindows()
                print("[INFO]: Image displayed.")

            # Convert the image to a fixed size
            print("[INFO]: Converting image to fixed size...")
            image = cv2.resize(image, (1000, 1000))
            print("[INFO]: Image converted to fixed size.")

            # Display the image
            if program_display:
                print("[INFO]: Displaying image...")
                cv2.imshow("Resized", image)
                cv2.waitKey(0)
                cv2.destroyAllWindows()
                print("[INFO]: Image displayed.")
            
            # Apply Euclidean Distance Transform to get distance map
            print("[INFO]: Applying Euclidean Distance Transform...")
            distance_map = cv2.distanceTransform(image, cv2.DIST_L2, 5)
            print("[INFO]: Euclidean Distance Transform applied.")

            # Normalize the distance map
            print("[INFO]: Normalizing distance map...")
            cv2.normalize(distance_map, distance_map, 0, 1.0, cv2.NORM_MINMAX)
            print("[INFO]: Distance map normalized.")

            # Display the image
            if program_display:
                print("[INFO]: Displaying image...")
                cv2.imshow("Distance Transform", distance_map)
                cv2.waitKey(0)
                cv2.destroyAllWindows()
                print("[INFO]: Image displayed.")

            # Use thinning method to get skeleton of the image
            print("[INFO]: Applying thinning method...")
            skeleton = cv2.ximgproc.thinning(image, cv2.ximgproc.THINNING_ZHANGSUEN)
            print("[INFO]: Thinning method applied.")

            # Convert the skeleton to an image
            print("[INFO]: Converting skeleton to image...")
            skeleton = skeleton.astype(np.uint8)
            skeleton = cv2.cvtColor(skeleton, cv2.COLOR_GRAY2BGR)
            print("[INFO]: Skeleton converted to image.")

            # Display the image
            if program_display:
                print("[INFO]: Displaying image...")
                cv2.imshow("Skeleton", skeleton)
                cv2.waitKey(0)
                cv2.destroyAllWindows()
                print("[INFO]: Image displayed.")

            # Find the coordinates of each white pixel and store in a list
            print("[INFO]: Finding coordinates of white pixels...")
            white_pixels = []
            for y in range(0, 1000):
                for x in range(0, 1000):
                    if skeleton[y][x][0] == 255:
                        white_pixels.append([x, y])
            print("[INFO]: Coordinates of white pixels found.")

            # Create a new list of solved_white_pixels
            solved_white_pixels = []

            # Loop through the list of white_pixels and identify the ordered pair that has the least neighbors
            print("[INFO]: Identifying pixel with least neighbors...")
            least_neighbors = 2
            least_neighbors_index = 0
            # Print progress bar with 50 hashtags
            print("[INFO]: Progress: [                                                 ]", end=f"\r[INFO]: Progress: [")
            for i in range(0, len(white_pixels)):
                neighbors = 0
                for j in range(0, len(white_pixels)):
                    # Print hashtags for progress bar based on len(white_pixels)*len(white_pixels) iterations, limited to 50
                    if len(white_pixels)*len(white_pixels) > 50:
                        if (i*len(white_pixels) + j) % (len(white_pixels)*len(white_pixels) // 50) == 0:
                            print("#", end="")
                    if i != j:
                        if abs(white_pixels[i][0] - white_pixels[j][0]) <= 1:
                            if abs(white_pixels[i][1] - white_pixels[j][1]) <= 1:
                                neighbors += 1
                if neighbors < least_neighbors:
                    least_neighbors = neighbors
                    least_neighbors_index = i
            print("]")
            
            # Add the pixel with the least neighbors to solved_white_pixels
            try:
                solved_white_pixels.append(white_pixels[least_neighbors_index])
                # Pop the pixel with the least neighbors from the white_pixels list
                white_pixels.pop(least_neighbors_index)
            except IndexError:
                print("[ERROR]: No white pixels found in image.")
                quit()

            # Loop through white_pixels, identifying the closest pixel to the current pixel and popping it from the list
            print("[INFO]: Solving white pixels...")
            # Print progress bar with 50 hashtags
            print("[INFO]: Progress: [                                                 ]", end=f"\r[INFO]: Progress: [")
            for i in range(0, len(white_pixels)):
                # Get the current pixel
                current_pixel = solved_white_pixels[-1]
                # Get the distance between the current pixel and the first pixel in white_pixels
                distance = math.sqrt(((white_pixels[0][0] - current_pixel[0]) ** 2) + ((white_pixels[0][1] - current_pixel[1]) ** 2))
                # Get the index of the closest pixel
                closest_pixel_index = 0
                # Loop through white_pixels, finding the closest pixel
                for j in range(0, len(white_pixels)):
                    # Print hashtags for progress bar based on len(white_pixels)*len(white_pixels) iterations, limited to 50
                    if len(white_pixels)*len(white_pixels) > 50:
                        if (i*len(white_pixels) + j) % (len(white_pixels)*len(white_pixels) // 50) == 0:
                            print("#", end="")
                    # Get the distance between the current pixel and the current pixel in white_pixels
                    current_distance = math.sqrt(((white_pixels[j][0] - current_pixel[0]) ** 2) + ((white_pixels[j][1] - current_pixel[1]) ** 2))
                    # If the current distance is less than the distance, then set the distance to the current distance and set the closest pixel index to the current index
                    if current_distance < distance:
                        distance = current_distance
                        closest_pixel_index = j
                # Add the closest pixel to the solved_white_pixels list
                solved_white_pixels.append(white_pixels[closest_pixel_index])
                # Pop the closest pixel from the white_pixels list
                white_pixels.pop(closest_pixel_index)
            print("[INFO]: White pixels solved.")
            
            print(solved_white_pixels)

            # Init gcode
            gcode = []

            # If the initial speed is not 0, then set the initial speed
            if program_initial_speed != 0:
                gcode.append(f"G0 F{program_initial_speed}\n")
            
            # If the initial acceleration is not 0, then set the initial acceleration
            if program_initial_acceleration != 0:
                gcode.append(f"M204 X{program_initial_acceleration} Y{program_initial_acceleration} Z{program_initial_acceleration}\n")

            # Convert the list of pixels to gcode
            print("[INFO]: Converting pixels to gcode...")
            for point in solved_white_pixels:
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

                # Append the point to gcode
                gcode.append(f"G0 X{printer_x} Y{printer_y} Z{printer_z}\n")
            print("[INFO]: Contours converted to gcode.")

            # print(f"Maximum X in solved_white_pixels: {max(solved_white_pixels, key=lambda x: x[0])[0]}")
            # print(f"Maximum Y in solved_white_pixels: {max(solved_white_pixels, key=lambda x: x[1])[1]}")
            # print(f"Maximum X in printer coordinates: {max_printer_x}")
            # print(f"Maximum Y in printer coordinates: {max_printer_y}")
            # print(f"Minimum X in solved_white_pixels: {min(solved_white_pixels, key=lambda x: x[0])[0]}")
            # print(f"Minimum Y in solved_white_pixels: {min(solved_white_pixels, key=lambda x: x[1])[1]}")
            # print(f"Minimum X in printer coordinates: {min_printer_x}")
            # print(f"Minimum Y in printer coordinates: {min_printer_y}")

            # Insert a dwell at line 3
            gcode.insert(2, f"G04 P{program_dwell_time}\n")

            # Convert the gcode list to a string
            gcode = "".join(gcode)

            # Write the gcode to a file
            print("[INFO]: Writing gcode to file...")
            with open(program_output_filename, "w") as f:
                f.write(gcode)
            print(f"[INFO]: Gcode written to {program_output_filename}.")

            print("Done!")

            if print_flag:
                # Print the gcode
                print("[INFO]: Beginning to print/draw gcode...")
                # Run the pronterface -b & command (if on Linux) or pronterface.exe -b & command (if on Windows)
                if platform.system() == "Linux":
                    # Get the filename path of program_output_filename without the other directories
                    temp_program_output_filename = program_output_filename.split("/")[-1]
                    # CD into maindirectory and then run the command "sudo pronterface -a -e \"load temp_program_output_filename print\"
                    os.system(f"cd \"{os.path.join(maindirectory, 'temp')}\" && sudo pronterface -a -e \"load {temp_program_output_filename}\"")
                elif platform.system() == "Windows":
                    # Get the filename path of program_output_filename without the other directories
                    temp_program_output_filename = program_output_filename.split("\\")[-1]
                    # CD into maindirectory and then run the command "pronterface.exe -a -e \"load temp_program_output_filename print\"
                    os.system(f"cd \"{os.path.join(maindirectory, 'temp')}\" && ..\\pronterface.exe -a -e \"load {temp_program_output_filename}\"")
                else:
                    print("[ERROR]: Unsupported operating system.")
                    quit()
                
                print("[INFO]: Gcode printed/drawn.")

            if program_input_filename != "":
                if pi_mode:
                    # Wait for button press from GPIO pin 17
                    print("[INFO]: Press the button to convert another image, or [bright_red]CTRL+C[/bright_red] to exit.")
                    GPIO.wait_for_edge(input_pin, GPIO.FALLING)
                else:
                    # Wait for user input
                    print("[INFO]: Press [bright_yellow]ENTER[/bright_yellow] to convert another image, or [bright_red]CTRL+C[/bright_red] to exit.")
                    input()
                print()
    except KeyboardInterrupt:
        print("[INFO]: Keyboard interrupt detected, exiting...")
        if pi_mode:
            GPIO.cleanup()
        quit()
