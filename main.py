import customtkinter
from moviepy import VideoFileClip
from progress_bar_loader import MyBarLogger
import pyglet
from customtkinter import filedialog, CTkFont
import os

# Creating the CTk variable
app = customtkinter.CTk()
app.title("Video Compressor")
app.geometry("1000x800")
app.resizable(False, False)

# Import all custom fonts
pyglet.options['win32_gdi_font'] = True
pyglet.font.add_file('fonts/SplineSans-VariableFont_wght.ttf')

# Global variables
file_selected = False

# Import logger for compress_video
def create_logger(progress_bar):
    logger = MyBarLogger(progress_bar=progress_bar, app=app, status_message=progress_bar_status_message)
    return logger

# Import function for compressing the video
def compress_video(input_path, output_path, bitrate, codec):
    place_progress_bar()  # Calls function to make Progress bar message appear

    video_clip = VideoFileClip(input_path)
    video_clip.write_videofile(output_path, bitrate=bitrate, codec=codec, logger=create_logger(download_progress_bar))
    video_clip.close()  # Closes the internal reader


# Logic
def get_color(widget):
    # Function for retrieving the foreground colour of a widget
    return widget.cget("fg_color")


def get_text(widget):
    # Function for retrieving text from a widget
    return widget.cget("text")


def move_compression_frame(state, widget_offset=None):
    # Responsible for making room for more widgets in the compression frame upon command
    if state == "EXTEND":
        compression_frame.configure(height=(280 + widget_offset))
    elif state == "SHORTEN":
        compression_frame.configure(height=280)

def reset_UI():
    # Check if a file had already been selected to remove compression widgets
    global bitrate_entry

    progress_bar_status_message.place_forget()
    download_progress_bar.set(0)
    download_progress_bar.place_forget()

    # Clears variable in entry
    bitrate_entry.delete(0, 'end')
    name_entry.delete(0, 'end')

    # Restore widgets to default values
    requested_bitrate.configure(text='Requested Bitrate: ' + vacant_value)
    requested_file_size.configure(text='Requested File size: ' + vacant_value)
    requested_file_name.configure(text='Requested File name: ' + vacant_value)

    compress_button.configure(fg_color='gray', hover_color='dark gray',
                              text="First select a Video to Compress", command=None)

    move_compression_frame(state='SHORTEN')

def convert_bytes_to_megabytes(size):
    # Convert file size to the appropriate byte format
    for x in ['bytes', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return "%3.1f %s" % (size, x)
        size /= 1024.0


def calculate_bitrate(file_size, duration):
    # Calculating bitrate of original file
    file_size_mb = file_size / 1e6  # File size in bytes to megabytes (Divide by 1 million)

    # Calculating bitrate
    bitrate_mbps = (file_size_mb * 8) / duration
    bitrate_kbps = "{:.0f}".format(bitrate_mbps * 1000)
    return bitrate_kbps


# Button scripts
def change_button_interactivity(button, command):
    # Turn buttons from gray to a green interactive button
    button.configure(fg_color='green', hover_color='dark green', command=command)


def calculate_new_file_size(bitrate, duration):
    # Formula for calculating new file size
    if bitrate is str:
        bitrate_error_message.configure("You must input a number, not a string")
    else:
        total_bitrate = bitrate * 1000  # Turn bitrate from kbps to bps (bits per second)
        file_size_mb = (total_bitrate * duration) / 8  # Getting file size in megabytes

        requested_bitrate.configure(text='Requested Bitrate: ' + str(bitrate))
        converted_file_size = convert_bytes_to_megabytes(file_size_mb)
        requested_file_size.configure(text='Requested file size: ' + converted_file_size)


def move_widgets(widgets, state='START', error_message=None):  # If no error, error_message defaults to None
    # Moves widgets in compression_frame accordingly based on whether an error message is shown or not
    # State starts at 'START' to let program know to not look for errors
    widget_offset = 25

    if state == 'ERROR':
        for widget in widgets:
            widget.place(y=(widget.y + widget_offset))

        # Make message appear
        error_message.place(relx=error_message.x, y=error_message.y, anchor='center')
        move_compression_frame(state="EXTEND", widget_offset=widget_offset)
    elif state == 'APPROVED':
        for widget in widgets:
            widget.place(y=widget.y)
        error_message.place_forget()
        move_compression_frame(state="SHORTEN")


def verify_bitrate_input(bitrate_entry, file_bitrate, input_path, output_path):
    # Verifying user input for bitrate from bitrate_entry widget
    is_integer = False  # Is the value an integer?
    bitrate_lower = False  # Is the value lower than the file's original bitrate?

    if bitrate_entry.isdigit():
        is_integer = True
    if is_integer and int(bitrate_entry) < int(file_bitrate):
        bitrate_lower = True

    if not is_integer:
        # The only widgets that are moved are the widgets that are lower than the bitrate_entry
        move_widgets(widgets=[name_entry,
                              bitrate_button,
                              name_button,
                              requested_bitrate,
                              requested_file_size,
                              requested_file_name,
                              name_label,
                              compress_button], state='ERROR', error_message=bitrate_error_message)
        bitrate_error_message.configure(text="Error: Not a valid input")
    elif not bitrate_lower:
        bitrate_error_message.configure(text="Error: Input must be lower than bitrate")
        move_widgets(widgets=[name_entry,
                              bitrate_button,
                              name_button,
                              requested_bitrate,
                              requested_file_size,
                              requested_file_name,
                              name_label,
                              compress_button], state='ERROR', error_message=bitrate_error_message)

    elif (bitrate_lower and is_integer) and get_text(bitrate_error_message) != '':
        move_widgets(widgets=[name_entry,
                              bitrate_button,
                              name_button,
                              requested_bitrate,
                              requested_file_size,
                              requested_file_name,
                              name_label,
                              compress_button], state='APPROVED', error_message=bitrate_error_message)
        verify_both_inputs(input_path=input_path, output_path=output_path)

    elif (bitrate_lower and is_integer) and get_text(bitrate_error_message) == '':
        bitrate_error_message.configure(text="")
        move_widgets(widgets=[name_entry,
                              bitrate_button,
                              name_button,
                              requested_bitrate,
                              requested_file_size,
                              requested_file_name,
                              name_label,
                              compress_button], state='START')


def verify_name_input(name, input_path, output_path):
    # Process for verifying the name input
    file_name = name
    input_format = ""
    for video_format in ['.mp4', '.webm', '.ogv']:
        if file_name.endswith(video_format):
            input_format = video_format
            break

    if input_format == "":
        name_error_message.configure(text='Error: Name must end with a video format', text_color='red')
        move_widgets(widgets=[bitrate_button,
                              name_button,
                              requested_bitrate,
                              requested_file_size,
                              requested_file_name,
                              name_label,
                              compress_button], state='ERROR', error_message=name_error_message)
    elif input_format != "" and get_text(name_error_message) != "":
        # If name has format and the error message is present
        move_widgets(widgets=[bitrate_button,
                              name_button,
                              requested_bitrate,
                              requested_file_size,
                              requested_file_name,
                              name_label,
                              compress_button], state='APPROVED', error_message=name_error_message)
        verify_both_inputs(input_path=input_path, output_path=output_path)
    elif input_format != "" and get_text(name_error_message) == "":
        verify_both_inputs(input_path=input_path, output_path=output_path)


def set_name(name):
    # Sets the name for the name you've input to the name_entry widget
    requested_file_name.configure(text='Requested file name: ' + name)


def place_progress_bar():
    # Creates a message upon successfully compressing the video
    # download_progress_bar relx = 0.5 and y = 290
    move_compression_frame(state='EXTEND', widget_offset=50)
    download_progress_bar.place(relx=download_progress_bar.x, y=download_progress_bar.y, anchor='center')
    progress_bar_status_message.place(relx=progress_bar_status_message.x,
                                      y=progress_bar_status_message.y,
                                      anchor='center')


def accepted_file_types():
    # Tuples of only the accepted file types for the software to detect in the File Explorer
    file_types = [('Video Files', '.mp4 .webm .ogv')]
    return file_types


def file_type_codecs(selected_file_type):
    codecs = {'mp4': 'libx264',
              'ogv': 'libtheora',
              'webm': 'libvpx'}
    return codecs[selected_file_type]


def verify_both_inputs(input_path, output_path):
    # Used to verify whether the requested name and requested bitrate were inputted
    if get_text(requested_bitrate) != bitrate_empty_value and get_text(requested_file_name) != file_size_empty_value:
        get_name = get_text(requested_file_name).split(': ')[1]
        full_output_path = f'{output_path}/{get_name}'

        get_file_format = get_name.split('.')[1]  # Gets the file format from splitting the label from the value

        change_button_interactivity(button=compress_button,
                                    command=lambda: compress_video(input_path=input_path, output_path=full_output_path,
                                                               bitrate=f'{bitrate_entry.get()}k',
                                                               codec=file_type_codecs(get_file_format)))
        compress_button.configure(text='Compress Video')


def import_file():
    global file_selected

    # Loading file and getting its byte size
    file = filedialog.askopenfile(initialdir='/', title='Select A File', filetypes=accepted_file_types())
    file_path = file.name
    file_bytes = os.path.getsize(file_path)  # File size in bytes
    file_size = convert_bytes_to_megabytes(file_bytes)  # Convert to proper byte format

    file_text = file_path.split('/')[-1]  # Splitting absolute path to get the name of the file

    output_directory = os.path.abspath('NewFileLocation')  # Getting the absolute path for the folder to store
    # your new file

    # Reset compress button
    if file_selected:
        reset_UI()
    file_selected = True

    # Turning file info into variables
    video_file = VideoFileClip(file_path)
    duration = video_file.duration

    # Getting the bitrate of the file
    file_bitrate = calculate_bitrate(file_size=file_bytes, duration=duration)

    # Creating display text for the button after a file has been selected
    display_names = []
    for widget in [file_text, file_bitrate, file_size]:
        if not isinstance(widget, str):  # If it's not a string, make it a string
            widget = str(widget)
        widget = [widget[i: i + 15] + '\n' for i in range(0, len(widget), 15)]  # Max line length of 15 characters
        display_names.append(widget)

    # Button configures
    import_button.configure(text=(f"File: {''.join(display_names[0])}"
                                  f"Bitrate: {''.join(display_names[1])}"
                                  f"File size: {''.join(display_names[2])}"))

    change_button_interactivity(button=bitrate_button,
                                command=(lambda: (verify_bitrate_input(bitrate_entry=bitrate_entry.get(),
                                                                   file_bitrate=file_bitrate,
                                                                   input_path=file_path,
                                                                   output_path=output_directory),
                                              calculate_new_file_size(duration=duration,
                                                                      bitrate=(int(bitrate_entry.get()))))))

    change_button_interactivity(button=name_button,
                                command=lambda: (set_name(name_entry.get()),
                                             verify_name_input(name=name_entry.get(), input_path=file_path,
                                                               output_path=output_directory)))


# Frames
frame_fg_color = "#2B2B2B"
main_frame = customtkinter.CTkFrame(app, width=900, height=700, fg_color=frame_fg_color)
main_frame.place(x=50, y=50)

title_frame = customtkinter.CTkFrame(main_frame, width=700, height=80, fg_color=frame_fg_color,
                                     border_color="#70c160", border_width=4)
title_frame.x = (main_frame.current_width - title_frame.current_width) / 2
title_frame.y = 30
title_frame.place(x=title_frame.x, y=title_frame.y)

subtitle_frame = customtkinter.CTkFrame(main_frame, width=400, height=50, fg_color=frame_fg_color,
                                        border_color="#70c160", border_width=3)
subtitle_frame.offset = 10
subtitle_frame.x = (main_frame.current_width - subtitle_frame.current_width) / 2
subtitle_frame.y = title_frame.current_height + title_frame.y + subtitle_frame.offset
subtitle_frame.place(x=subtitle_frame.x, y=subtitle_frame.y)

# Frame for the import button title
import_title_frame = customtkinter.CTkFrame(main_frame, width=200, height=50, fg_color=frame_fg_color,
                                            border_color="#70c160", border_width=2)
import_title_frame.x = 100
import_title_frame.y = 250
import_title_frame.place(x=import_title_frame.x, y=import_title_frame.y)

# Frame for the compression frame title
compress_title_frame = customtkinter.CTkFrame(main_frame, width=250, height=40, fg_color=frame_fg_color,
                                              border_color="#70c160", border_width=2)
compress_title_frame.x = 600
compress_title_frame.y = import_title_frame.y  # Same Y position as the import title frame
compress_title_frame.place(x=compress_title_frame.x, y=compress_title_frame.y)

# Frame for all the widgets used for the compression process
compression_frame = customtkinter.CTkFrame(main_frame, width=250, height=280, fg_color=frame_fg_color,
                                           border_color="#70c160", border_width=2)
compression_frame.x = compress_title_frame.x  # Same X position as the compression title frame
compression_frame.y = import_title_frame.y  # Same X position as the import title frame
compression_frame.place(x=compression_frame.x, y=compression_frame.y)

# Fonts
label_font = ('Spline Sans', 13)
notes_font = CTkFont(size=12, family='Spline Sans', slant='italic')
software_description_font = CTkFont(size=13, family='Spline Sans', slant='italic')

# Widgets
# Information Labels
text_fg_color = "#DCE4EE"
software_description_label = customtkinter.CTkLabel(main_frame,
                                                    text='Welcome to my file compressing project! This software allows you to take '
                                                         'any video and compress it. :D \n'
                                                         'To get started, click the "Import Here" button, which will '
                                                         'open your File Explorer, letting you choose a file to import.\n'
                                                         'From there you can adjust the bitrate, filename and format '
                                                         'of your choosing, then compress it. Enjoy!',
                                                    font=software_description_font, text_color=text_fg_color)
software_description_label.place(relx=0.5, y=210, anchor='center')

# Frame Labels
title_label = customtkinter.CTkLabel(title_frame, text="Video Compressor Project",
                                     text_color=text_fg_color,
                                     font=('Spline Sans Bold', 35))
title_label.place(relx=0.5, rely=0.5, anchor='center')

subtitle_label = customtkinter.CTkLabel(subtitle_frame, text="By: Andreas Forootan",
                                        text_color=text_fg_color,
                                        font=('Spline Sans Medium', 23))
subtitle_label.place(relx=0.5, rely=0.5, anchor='center')

# ---------------------------------- Import File frame widgets ----------------------------------

import_label = customtkinter.CTkLabel(import_title_frame, text="Import your Files",
                                      text_color=text_fg_color,
                                      font=('Spline Sans Medium', 20))
import_label.place(relx=0.5, rely=0.5, anchor='center')

compress_label = customtkinter.CTkLabel(compress_title_frame, text="Compress your Files",
                                        text_color=text_fg_color,
                                        font=('Spline Sans Medium', 18))
compress_label.place(relx=0.5, rely=0.5, anchor='center')

vacant_value = 'x'
import_button = customtkinter.CTkButton(main_frame, text='Import Here\n'
                                                         f'Bitrate: {vacant_value}\n'
                                                         f'File Size: {vacant_value}\n', font=('Spline Sans', 14),
                                        text_color=text_fg_color,
                                        width=200,
                                        height=150, border_color="#70c160",
                                        border_width=1, fg_color=frame_fg_color, hover_color='#292929', command=import_file)
import_button.x = import_title_frame.x
import_button.y = 300
import_button.place(x=import_button.x, y=import_button.y)

# ---------------------------------- Compression Frame widgets ----------------------------------
compression_frame_positions = {
    # A dictionary of all the XY coordinates for every widget inside the compression_frame
    "bitrate_entry": {"x": 10,
                      "y": 15},

    "bitrate_error_message": {"relx": 0.5,
                              "y": 54},

    "name_entry": {"x": 10,
                   "y": 45},

    "bitrate_button": {"relx": 0.25,
                       "y": 75},

    "name_button": {"relx": 0.75,
                    "y": 75},

    "requested_bitrate": {"relx": 0.5,
                          "y": 120},

    "requested_file_size": {"relx": 0.5,
                            "y": 145},

    "requested_file_name": {"relx": 0.5,
                            "y": 170},

    "name_label": {"relx": 0.5,
                   "y": 205},

    "name_error_message": {"relx": 0.5,
                           "y": 85},

    "compress_button": {"relx": 0.5,
                        "y": 250},

    "progress_bar_status_message": {"relx": 0.5,
                                    "y": 285},

    "download_progress_bar": {"relx": 0.5,
                              "y": 300}
}

# The font and font size being used for the requested compression widgets
compression_info_font = ('Spline Sans', 14)

bitrate_entry = customtkinter.CTkEntry(compression_frame, height=5, width=230,
                                       placeholder_text="Your requested bitrate here! (in kbps)",
                                       fg_color="#343638",
                                       border_color="#70C160",
                                       border_width=1.25,
                                       justify='center')
bitrate_entry.x = compression_frame_positions['bitrate_entry']['x']  # 10
bitrate_entry.y = compression_frame_positions['bitrate_entry']['y']  # 15
bitrate_entry.place(x=bitrate_entry.x, y=bitrate_entry.y)

name_entry = customtkinter.CTkEntry(compression_frame, height=5, width=230,
                                    placeholder_text='Your file name here!',
                                    fg_color="#343638",
                                    border_color="#70C160",
                                    border_width=1.25,
                                    justify='center')
name_entry.x = compression_frame_positions['name_entry']['x']  # 10
name_entry.y = compression_frame_positions['name_entry']['y']  # 45
name_entry.place(x=name_entry.x, y=name_entry.y)

bitrate_button = customtkinter.CTkButton(compression_frame, width=20, text="Set as Bitrate", fg_color='gray',
                                         hover_color='dark gray')
bitrate_button.x = compression_frame_positions['bitrate_button']['relx']  # relx 0.25
bitrate_button.y = compression_frame_positions['bitrate_button']['y']  # 75
bitrate_button.place(relx=bitrate_button.x, y=bitrate_button.y, anchor='n')

name_button = customtkinter.CTkButton(compression_frame, width=20, text="Set as Name", fg_color='gray',
                                      hover_color='dark gray')
name_button.x = compression_frame_positions['name_button']['relx']  # relx 0.75
name_button.y = compression_frame_positions['name_button']['y']  # 75
name_button.place(relx=name_button.x, y=name_button.y, anchor='n')

bitrate_empty_value = 'Requested Bitrate: ' + vacant_value
requested_bitrate = customtkinter.CTkLabel(compression_frame, text=bitrate_empty_value,
                                           text_color="#DCE4EE",
                                           font=compression_info_font)
requested_bitrate.x = compression_frame_positions['requested_bitrate']['relx']  # relx 0.75
requested_bitrate.y = compression_frame_positions['requested_bitrate']['y']  # 120
requested_bitrate.place(relx=requested_bitrate.x, y=requested_bitrate.y, anchor='center')

file_size_empty_value = 'Requested File size: ' + vacant_value
requested_file_size = customtkinter.CTkLabel(compression_frame, text=file_size_empty_value,
                                             text_color="#DCE4EE",
                                             font=compression_info_font)
requested_file_size.x = compression_frame_positions['requested_file_size']['relx']  # relx 0.5
requested_file_size.y = compression_frame_positions['requested_file_size']['y']  # 145
requested_file_size.place(relx=requested_file_size.x, y=requested_file_size.y, anchor='center')

requested_file_name = customtkinter.CTkLabel(compression_frame, text=('Requested File name: ' + vacant_value),
                                             text_color="#DCE4EE",
                                             font=compression_info_font)
requested_file_name.x = compression_frame_positions['requested_file_name']['relx']  # relx 0.5
requested_file_name.y = compression_frame_positions['requested_file_name']['y']  # 145
requested_file_name.place(relx=requested_file_name.x, y=requested_file_name.y, anchor='center')

name_label = customtkinter.CTkLabel(compression_frame, text='Be sure your name ends with the \n'
                                                            'file format of your choosing '
                                                            '\n(Supported formats: .mp4, .webm, .ogv) ',
                                    font=notes_font, text_color='light gray')
name_label.x = compression_frame_positions['name_label']['relx']  # relx 0.5
name_label.y = compression_frame_positions['name_label']['y']
name_label.place(relx=name_label.x, y=name_label.y, anchor='center')

compress_button = customtkinter.CTkButton(compression_frame, text="First select a Video to Compress",
                                          fg_color='gray', hover_color='dark gray')
compress_button.x = compression_frame_positions['compress_button']['relx']  # relx 0.5
compress_button.y = compression_frame_positions['compress_button']['y']  # 250
compress_button.place(relx=compress_button.x, y=compress_button.y, anchor='center')

# ---------------------------------- Main Frame widgets ----------------------------------

note_label = customtkinter.CTkLabel(main_frame, text="Note: File sizes are not going "
                                                     "to be 100% accurate \ndue to various variables out of the software's control"
                                                     ", \nhowever it is accurate enough to get \na clear idea of the size of"
                                                     " your compression!",
                                    text_color="#DCE4EE",
                                    font=notes_font)
note_label.x = import_title_frame.x + (import_title_frame.current_width / 2)
note_label.place(x=note_label.x, y=490, anchor='center')

# Text messages
# Text is set to an empty value on default
bitrate_error_message = customtkinter.CTkLabel(compression_frame, text='', text_color='red')
bitrate_error_message.x = compression_frame_positions['bitrate_error_message']['relx']  # relx 0.5
bitrate_error_message.y = compression_frame_positions['bitrate_error_message']['y']  # 45
bitrate_error_message.place_forget()

name_error_message = customtkinter.CTkLabel(compression_frame, text='', text_color='red')
name_error_message.x = compression_frame_positions['name_error_message']['relx']  # relx 0.5
name_error_message.y = compression_frame_positions['name_error_message']['y']  # 85
name_error_message.place_forget()

progress_bar_status_message = customtkinter.CTkLabel(compression_frame, text='', text_color='green')
progress_bar_status_message.x = compression_frame_positions['progress_bar_status_message']['relx']
progress_bar_status_message.y = compression_frame_positions['progress_bar_status_message']['y']
progress_bar_status_message.place_forget()

download_progress_bar = customtkinter.CTkProgressBar(compression_frame, progress_color='green')
download_progress_bar.set(0)
download_progress_bar.x = compression_frame_positions['download_progress_bar']['relx']
download_progress_bar.y = compression_frame_positions['download_progress_bar']['y']
download_progress_bar.place_forget()

app.mainloop()
