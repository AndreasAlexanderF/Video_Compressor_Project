from moviepy.editor import VideoFileClip
from progress_bar_loader import MyBarLogger
from main import download_progress_bar

# Import logger for compress_video
logger = MyBarLogger(progress_bar=download_progress_bar)


def compress_video(input_path, output_path, bitrate, codec):
    video_clip = VideoFileClip(input_path)
    video_clip.write_videofile(output_path, bitrate=bitrate, codec=codec, logger=logger)
    video_clip.close()  # Closes the internal reader

# compress_video("NewFileLocation/nwBY9tp7MjyOX8nE.mp4",
#                      "gmod_webswinging_compressed.mp4", bitrate='400k')
