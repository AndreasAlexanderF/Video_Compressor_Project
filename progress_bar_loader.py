from proglog import ProgressBarLogger
import tracemalloc

tracemalloc.start()

class MyBarLogger(ProgressBarLogger):
    def __init__(self, progress_bar, app, status_message):
        super().__init__()
        self.percentage = 0
        self.progress_bar = progress_bar
        self.app = app
        self.status_message = status_message
        self.original_message = None
        self.animation_timer = 0
        self.animation_counter = 0

    def callback(self, **changes):
        # Every time the logger message is updated, this function is called with
        # the `changes` dictionary of the form `parameter: new value`.
        for (parameter, value) in changes.items():
            if "Writing audio" in value:
                self.status_message.configure(text="Writing audio")
                self.original_message = "Writing audio"

            elif "Writing video" in value:
                self.status_message.configure(text="Writing video")
                self.original_message = "Writing video"

            elif "video ready" in value:
                self.status_message.configure(text="Video successfully compressed!")

    def loading_animation(self):
        # Makes a loading animation to the status_message while the file is compressing

        if self.animation_counter > 3:
            self.animation_counter = 0
            self.status_message.configure(text=self.original_message)

        period_timer = 120
        if self.animation_timer >= period_timer:
            self.animation_timer = 0
            self.animation_counter += 1

            periods = "." * self.animation_counter
            self.status_message.configure(text=f"{self.original_message}{periods}")
        else:
            self.animation_timer += 1

    def bars_callback(self, bar, attr, value, old_value=None):
        # Every time the logger progress is updated, this function is called
        bar_progress = (value / self.bars[bar]['total'])
        self.percentage = bar_progress * 100
        self.progress_bar.set(bar_progress)

        # Updates the progress bar from the GUI visually
        self.app.update_idletasks()
        # Concurrently updates the status_message upon updating the idle tasks
        self.app.after_idle(self.loading_animation)
