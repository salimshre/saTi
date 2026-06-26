


#######################################
cd ~/SaTi

# Create a virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Install the base dependency
pip install platformdirs

# Run the app
python main.py
#######################################


Right‑click on your desktop → New → Shortcut.

In the location field, enter:


#create shortcut files and add this commands.
pythonw.exe "C:\path\to\your\sati\main.py"


#######################################3
# to show on tray #exit from tray, app exited.
🔧 Fix – install the optional dependencies
Open a terminal (Command Prompt or PowerShell) in your project folder and run:

bash
pip install -e .[desktop]
This installs all required packages plus the optional desktop extras defined in pyproject.toml (pystray, pillow, plyer, pyinstaller).
If you prefer to install them manually:

bash
pip install pystray pillow
After installation, restart the app – the tray icon should now work.
#######################################3

