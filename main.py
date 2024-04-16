import tkinter as tk
import numpy as np
import time
import boto3
import requests

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
# Import the create_figure function from the plotting module
from plotting_module import create_figure
from botocore.exceptions import NoCredentialsError
from tkinter import filedialog


class EEGApp:
    def __init__(self, master):
        self.master = master
        self.master.title("EEG Signal Viewer")
        self.start_time = time.time()

        # Add padding with colored background
        self.header_frame = tk.Frame(self.master, background="SteelBlue4")
        self.header_frame.pack(fill=tk.X)

        self.header = tk.Label(self.header_frame, text="New Wave Brain Analysis", font=("Arial", 25), background="SteelBlue4", foreground="white", anchor='w')
        self.header.pack(pady=10, anchor='w', fill=tk.X, padx=10)

        # Create a figure from the plotting module this is in the plotting_module.py file
        self.fig, self.lines = create_figure()
        self.canvas = FigureCanvasTkAgg(self.fig, master)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.setup_ui()

        self.measuring = False

    def setup_ui(self):
        self.ui_frame = tk.Frame(self.master)
        self.ui_frame.pack(side=tk.RIGHT, fill=tk.Y)

        # Title above the text inputs and upload button


        self.start_button = tk.Button(self.ui_frame, text="Start Measurement", font=("Arial", 20), command=self.toggle_measurement, highlightthickness=30, background="SpringGreen3")
        self.start_button.pack(pady=(0), fill=tk.X)

        #Header for Uploading Data
        self.upload_data_label = tk.Label(self.ui_frame, text="Upload Data", font=("Arial", 20))
        self.upload_data_label.pack(pady=(5, 0), fill=tk.X)

        # Adding placeholder text for email
        self.email_input = tk.Entry(self.ui_frame,font=("Arial", 15),highlightthickness=10)
        self.email_input.insert(0, "Email")
        self.email_input.bind("<FocusIn>", lambda args: self.clear_placeholder(self.email_input, "Email"))
        self.email_input.bind("<FocusOut>", lambda args: self.add_placeholder(self.email_input, "Email"))
        self.email_input.pack(pady=5, fill=tk.X)

        # Adding placeholder text for password
        self.password_input = tk.Entry(self.ui_frame, font=("Arial", 15),highlightthickness=10)
        self.password_input.insert(0, "Password")
        self.password_input.bind("<FocusIn>", lambda args: self.clear_placeholder(self.password_input, "Password", True))
        self.password_input.bind("<FocusOut>", lambda args: self.add_placeholder(self.password_input, "Password"))
        self.password_input.pack(pady=5, fill=tk.X)

        # Adding placeholder text for note name
        self.note_name_input = tk.Entry(self.ui_frame, font=("Arial", 15), highlightthickness=10)
        self.note_name_input.insert(0, "Record Name")
        self.note_name_input.bind("<FocusIn>", lambda args: self.clear_placeholder(self.note_name_input, "Record Name"))
        self.note_name_input.bind("<FocusOut>", lambda args: self.add_placeholder(self.note_name_input, "Record Name"))
        self.note_name_input.pack(pady=5, fill=tk.X)

        # Adding placeholder text for note description
        self.note_description_input = tk.Entry(self.ui_frame, font=("Arial", 15), highlightthickness=10)
        self.note_description_input.insert(0, "Record Description")
        self.note_description_input.bind("<FocusIn>", lambda args: self.clear_placeholder(self.note_description_input, "Record Description"))
        self.note_description_input.bind("<FocusOut>", lambda args: self.add_placeholder(self.note_description_input, "Record Description"))
        self.note_description_input.pack(pady=5, fill=tk.X)


        self.upload_button = tk.Button(self.ui_frame, text="Upload Data", command=self.upload_data, state=tk.DISABLED, font=("Arial", 15),highlightthickness=10)
        self.upload_button.pack(pady=10, fill=tk.X)

    def clear_placeholder(self, entry, placeholder, is_password=False):
        """Clear the placeholder text if it's there."""
        if entry.get() == placeholder:
            entry.delete(0, tk.END)
            if is_password:
                entry.config(show="*")
    
    def add_placeholder(self, entry, placeholder):
        """Add the placeholder text if the field is empty."""
        if not entry.get():
            if placeholder == "Password":
                entry.config(show='')
            entry.insert(0, placeholder)

    def toggle_measurement(self):
        self.measuring = not self.measuring
        
        if self.measuring:
            self.start_button.config(text="Stop Measurement",background="FireBrick3")
            self.upload_button.config(state=tk.DISABLED)
            self.start_real_time_plot()
        else:
            self.start_button.config(text="Start Measurement",background="SpringGreen3")
            self.upload_button.config(state=tk.NORMAL)


    #AWS UPLOAD DATA FUNCTION
    def upload_data(self):
        filepath = filedialog.askopenfilename(initialdir=r"C:\Users\dakil\Desktop\SeniorDesign\devicegui_tkinter\csv_data", title="Select file",
                                              filetypes=(("csv files", "*.csv"), ("all files", "*.*")))
        if filepath:
            try:
                s3_key = self.upload_file_to_s3(filepath)
                # Get note name and description from the text inputs
                note_name = self.note_name_input.get()
                note_description = self.note_description_input.get()

                 # Use placeholders if inputs are empty or unchanged
                if note_name in ["", "Note Name"]:
                    note_name = filepath.split('/')[-1]  # Default to file name if no input
                if note_description in ["", "Note Description"]:
                    note_description = "Uploaded from Tkinter App"  # Default description

                #Upload the file to S3 and register it with the GraphQL API
                self.register_file_with_graphql(s3_key, note_name, note_description)
                print("File uploaded successfully")
            except NoCredentialsError:
                print("Credentials not available")
            except Exception as e:
                print(f"Failed to upload file: {e}")

    # Method to upload a file to S3
    def upload_file_to_s3(self, filepath, bucket_name="amplifydemographql751eba538c184c1a974af408f2073234021-staging", object_name=None):
        if object_name is None:
            object_name = filepath.split('/')[-1]

        s3_key = f"public/{object_name}"

        s3_client = boto3.client('s3')
        s3_client.upload_file(filepath, bucket_name, s3_key)
        return object_name
    

    #Access GraphQL API to register the file
    def register_file_with_graphql(self, s3_key, note_name, note_description=""):
        graphql_url = 'https://yd3lsq3roza77eplpnyntuhxn4.appsync-api.us-east-2.amazonaws.com/graphql'
        api_key = 'da2-pyv7yvpsmrbgletapyo722n6vi'
        
        mutation = """
            mutation CreateNote($input: CreateNoteInput!) {
                createNote(input: $input) {
                    id
                    name
                    description
                    csvFile
                }
            }
        """
        
        headers = {'x-api-key': api_key, 'Content-Type': 'application/json'}
        payload = {
            "query": mutation,
            "variables": {
                "input": {
                    "name": note_name,
                    "description": note_description,
                    "csvFile": s3_key
                }
            }
        }
        
        response = requests.post(graphql_url, json=payload, headers=headers)
        
        if response.status_code == 200:
            print("Note successfully created in GraphQL")
            return response.json()
        else:
            print("Failed to create note in GraphQL")
            print(response.text)
            return None


    def start_real_time_plot(self):
        # This is just a placeholder for how you might simulate new data
        # In a real application, you would fetch or receive actual data
        self.update_plot()

    def update_plot(self):
        if not self.measuring:
            return  # Exit the update loop if not measuring

        current_time = time.time() - self.start_time
         # Simulate a window of data that moves with time
        window_width = 10  # seconds
        t = np.linspace(current_time - window_width, current_time, 100)
        
        # Generating new y-data based on the moving window of x-data
        y_data = [
            np.sin(t * 2 * np.pi * 0.1),  # Adjusted frequency for better visualization
            np.sin(t * 2 * np.pi * 0.1 - 0.1),
            np.sin(t * 2 * np.pi * 0.1 - 0.2),
            np.sin(t * 2 * np.pi * 0.1 - 0.3)
        ]

        # Update each line with the new data
        for line, y in zip(self.lines, y_data):
            line.set_xdata(t)
            line.set_ydata(y)

        # Adjust xlim to move the window
        self.fig.axes[0].set_xlim(min(t), max(t))
        self.fig.axes[0].set_ylim(-1, 1)  # Adjust as needed

        # Redraw the canvas
        self.canvas.draw()

        # Schedule the next update
        self.master.after(100, self.update_plot)  # Update every 100 milliseconds for smoother animation

if __name__ == "__main__":
    root = tk.Tk()
    app = EEGApp(root)
    # Set the window size to 1280x800
    root.geometry("1280x800")
    # Prevents resizing of the window
    root.resizable(False, False)  
    root.mainloop()
