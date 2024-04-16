from matplotlib.figure import Figure
import numpy as np

# This method now initializes the plot without plotting data
def create_figure():
    fig = Figure(figsize=(5, 4), dpi=100)
    ax = fig.add_subplot(1, 1, 1)
    ax.set_ylim(-1, 1)
    ax.set_title('EEG Brain Wave Signal')
    ax.set_xlabel('Time')
    ax.set_ylabel('MicroVolts')
    ax.legend(['Wave 1', 'Wave 2', 'Wave 3', 'Wave 4'], loc='upper left')

    # Initialize lines for each wave
    lines = ax.plot([], [], 'r-', [], [], 'y-', [], [], 'g-', [], [], 'b-')

    return fig, lines
