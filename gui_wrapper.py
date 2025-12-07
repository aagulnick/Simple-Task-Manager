import tkinter as tk
from tkinter import scrolledtext, ttk
import subprocess
import threading
import queue
import json
import base64

class TaskManagerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Task Manager GUI")
        self.root.geometry("900x700")
        
        # Queue for thread-safe communication
        self.output_queue = queue.Queue()
        
        # Start the Python subprocess
        self.process = None
        self.reader_thread = None
        
        # Track display requests
        self.pending_display_update = False
        
        # Create GUI elements
        self.create_widgets()
        
        # Start the task_manager.py process
        self.start_process()
        
        # Start checking the queue
        self.check_queue()
        
        # Run display() on startup
        self.root.after(500, self.update_display)
    
    def create_widgets(self):
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Display output area (top)
        display_label = ttk.Label(main_frame, text="Task Manager Display:", font=("Arial", 10, "bold"))
        display_label.grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        
        self.display_text = scrolledtext.ScrolledText(
            main_frame, 
            height=20, 
            width=80, 
            font=("Courier", 10),
            bg="#f0f0f0",
            state=tk.DISABLED
        )
        self.display_text.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # Command input area (bottom)
        command_frame = ttk.Frame(main_frame)
        command_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
        command_frame.columnconfigure(1, weight=1)
        
        command_label = ttk.Label(command_frame, text="Command:")
        command_label.grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        
        self.command_entry = ttk.Entry(command_frame, font=("Courier", 10))
        self.command_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 5))
        self.command_entry.bind("<Return>", self.on_enter_key)
        
        self.execute_button = ttk.Button(command_frame, text="Execute", command=self.execute_command)
        self.execute_button.grid(row=0, column=2)
        
        # Output log area (for other outputs)
        log_label = ttk.Label(main_frame, text="Command Output:", font=("Arial", 10, "bold"))
        log_label.grid(row=3, column=0, sticky=tk.W, pady=(15, 5))
        
        self.log_text = scrolledtext.ScrolledText(
            main_frame, 
            height=10, 
            width=80, 
            font=("Courier", 9),
            state=tk.DISABLED
        )
        self.log_text.grid(row=4, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        main_frame.rowconfigure(4, weight=1)
    
    def start_process(self):
        """Start the task_manager.py in interactive mode"""
        try:
            self.process = subprocess.Popen(
                ["python", "-i", "task_manager.py"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # Start a thread to read output
            self.reader_thread = threading.Thread(target=self.read_output, daemon=True)
            self.reader_thread.start()
            
        except FileNotFoundError:
            self.log_message("Error: task_manager.py not found in current directory!")
        except Exception as e:
            self.log_message(f"Error starting process: {e}")
    
    def read_output(self):
        """Read output from the subprocess in a separate thread"""
        try:
            for line in iter(self.process.stdout.readline, ''):
                if line:
                    self.output_queue.put(line)
        except Exception as e:
            self.output_queue.put(f"Error reading output: {e}\n")
    
    def check_queue(self):
        """Check the output queue and update the GUI"""
        try:
            while True:
                line = self.output_queue.get_nowait()
                line_stripped = line.rstrip()
                
                # Check for our special display marker
                if line_stripped.startswith("__GUI_DISPLAY__:"):
                    try:
                        # Extract the base64 encoded display content
                        encoded = line_stripped.split(":", 1)[1]
                        display_content = base64.b64decode(encoded).decode('utf-8')
                        
                        # Update the display area
                        self.display_text.config(state=tk.NORMAL)
                        self.display_text.delete(1.0, tk.END)
                        self.display_text.insert(tk.END, display_content)
                        self.display_text.config(state=tk.DISABLED)
                    except Exception as e:
                        self.log_message(f"Error decoding display output: {e}")
                else:
                    # Log everything else to command output
                    self.log_message(line_stripped)
                
        except queue.Empty:
            pass
        
        # Schedule the next check
        self.root.after(100, self.check_queue)
    
    def update_display(self):
        """Request display output from the subprocess"""
        if self.process and self.process.poll() is None:
            # Send a command that gets display() return value and encodes it
            cmd = "import base64; __result = display(); print('__GUI_DISPLAY__:' + base64.b64encode(__result.encode()).decode())"
            self.send_command(cmd)
    
    def send_command(self, command):
        """Send a command to the subprocess"""
        if self.process and self.process.poll() is None:
            try:
                self.process.stdin.write(command + "\n")
                self.process.stdin.flush()
            except Exception as e:
                self.log_message(f"Error sending command: {e}")
        else:
            self.log_message("Process is not running!")
    
    def on_enter_key(self, event):
        """Handle Enter key press"""
        self.execute_command()
        return "break"  # Prevent default behavior
    
    def execute_command(self):
        """Execute the command from the entry field"""
        command = self.command_entry.get().strip()
        if command:
            self.send_command(command)
            
            # Clear the entry
            self.command_entry.delete(0, tk.END)
            
            # Update display after a short delay
            self.root.after(300, self.update_display)
    
    def log_message(self, message):
        """Add a message to the log text area"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
    
    def on_closing(self):
        """Clean up when closing the window"""
        if self.process:
            self.process.terminate()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = TaskManagerGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()