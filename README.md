# 🎮 PongSense

> **Play Pong like never before** — Control your paddle with hand gestures and voice commands!

PongSense is a revolutionary take on the classic Pong game, combining cutting-edge computer vision and speech recognition to create an immersive, hands-free gaming experience. Wave your fist to control your paddle, speak commands to adjust game speed, and enjoy smooth gameplay powered by MediaPipe and Vosk.

![PongSense Banner](https://via.placeholder.com/800x200/4A90E2/FFFFFF?text=PongSense+-+Multimodal+Pong+Game)

---

## ✨ Features

### 🎯 **Dual Input Control**
- **Hand Gesture Control**: Close your fist and move your arm up/down to control the paddle position in real-time
- **Voice Commands**: Say "faster" or "slower" to dynamically adjust ball speed during gameplay
- **Smooth Tracking**: Powered by Google's MediaPipe for lightning-fast, accurate hand detection

### 🎮 **Game Modes**
- **Single Player Mode**: Challenge yourself against an AI opponent with adjustable difficulty levels
- **Two-Player Mode**: Split the camera view and compete with a friend using parallel hand tracking for smooth performance

### 🎨 **Modern UI**
- **Beautiful Home Screen**: Clean, intuitive interface with easy navigation
- **Interactive Tutorial**: Step-by-step guide with video demonstrations
- **Table Tennis Theme**: Immersive green court background with colored paddles
- **Fullscreen Support**: Toggle fullscreen mode with F11 for the ultimate gaming experience

### 🚀 **Performance**
- **Low Latency**: Real-time processing optimized for smooth gameplay
- **Parallel Processing**: Dual-threaded hand tracking in 2-player mode for maximum performance
- **Integrated Camera View**: See yourself and your hand tracking in real-time at the top of the screen

---

## 🛠️ System Requirements

- **Python**: 3.10 or higher
- **Operating System**: Windows 10/11, macOS 10.14+, or Linux (Ubuntu 20.04+)
- **Hardware**:
  - Webcam (for hand tracking)
  - Microphone (for voice commands)
  - Decent CPU (for real-time processing)

---

## 📥 Installation Guide

### Step 1: Download the Code

First, you'll need to get the PongSense source code on your computer. Choose one of these methods:

**Option A: Using Git (Recommended)**
```bash
# Clone the repository
git clone https://github.com/MurtazaMister/PongSense.git

# Navigate into the project directory
cd PongSense
```

**Option B: Download as ZIP**
1. Click the green "Code" button on GitHub
2. Select "Download ZIP"
3. Extract the ZIP file to a location of your choice
4. Open a terminal/command prompt in the extracted folder

---

### Step 2: Verify Python Installation

Before proceeding, make sure Python is installed on your system:

```bash
# Check Python version (should be 3.10 or higher)
python --version

# Or try this if the above doesn't work
python3 --version
```

**If Python is not installed:**
- **Windows**: Download from [python.org](https://www.python.org/downloads/) - make sure to check "Add Python to PATH" during installation
- **macOS**: `brew install python3` or download from [python.org](https://www.python.org/downloads/)
- **Linux**: `sudo apt-get install python3 python3-pip` (Ubuntu/Debian)

---

### Step 3: Create a Virtual Environment

A virtual environment isolates your project's dependencies from other Python projects. This is a best practice and prevents conflicts.

**On Windows:**
```bash
# Create a virtual environment named 'venv'
python -m venv venv

# Activate the virtual environment
venv\Scripts\activate
```

**On macOS/Linux:**
```bash
# Create a virtual environment named 'venv'
python3 -m venv venv

# Activate the virtual environment
source venv/bin/activate
```

**What just happened?**
- You created a new folder called `venv` that contains a fresh Python installation
- By activating it, you're now using this isolated Python environment
- You should see `(venv)` at the beginning of your command prompt, confirming it's active

**Troubleshooting:**
- If you get "python: command not found", try `python3` instead
- If activation doesn't work on Windows, try: `.\venv\Scripts\activate.bat`
- On PowerShell, you might need: `venv\Scripts\Activate.ps1` (and possibly run `Set-ExecutionPolicy RemoteSigned`)

---

### Step 4: Install Dependencies

Now you'll install all the required packages that PongSense needs to run:

```bash
# Make sure your virtual environment is activated (you should see 'venv' in your prompt)
# Upgrade pip to the latest version first
python -m pip install --upgrade pip

# Install all required packages
pip install -r requirements.txt
```

**This will install:**
- `opencv-python` - Computer vision and image processing
- `mediapipe` - Hand tracking and gesture recognition
- `pygame` - Game engine and graphics
- `SpeechRecognition` - Voice command processing
- `pyaudio` - Audio input handling
- `numpy` - Numerical computations
- `pyyaml` - Configuration file parsing
- `vosk` - Offline speech recognition

**Installation time:** This typically takes 2-5 minutes depending on your internet connection.

**Common Issues:**
- **pyaudio installation fails on Windows**: Install [Microsoft Visual C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/) or use: `pip install pipwin && pipwin install pyaudio`
- **pyaudio installation fails on Linux**: `sudo apt-get install portaudio19-dev` then retry pip install
- **pyaudio installation fails on macOS**: `brew install portaudio` then retry pip install

---

### Step 5: Verify Installation

Let's make sure everything installed correctly:

```bash
# Check that key packages are installed
python -c "import cv2, mediapipe, pygame, vosk; print('✅ All packages installed successfully!')"
```

If you see the success message, you're good to go! If you get import errors, review the troubleshooting section below.

---

## 🎮 Running the Game

Now comes the fun part! Starting PongSense is simple:

**On Windows:**
```bash
# Make sure your virtual environment is activated
venv\Scripts\activate

# Run the game
python .\run_pongsense.py
```

**On macOS/Linux:**
```bash
# Make sure your virtual environment is activated
source venv/bin/activate

# Run the game
python run_pongsense.py
```

**What to expect:**
1. The game window will open (starts in fullscreen by default)
2. You'll see the home screen with three options:
   - **Start Game** - Begin playing immediately
   - **How to Play** - View the interactive tutorial
   - **Quit Game** - Exit the application
3. Click "Start Game" to see mode selection:
   - **Play with AI** - Single player mode
   - **2-Player Mode** - Two players, split camera view

---

## 🎯 How to Play

### Basic Controls

**Hand Gestures:**
- **Fist**: Close your hand into a fist and move your arm up and down to control the paddle
- **Open Hand**: You can also use an open hand gesture to control the paddle
- Keep your hand within the camera view for best tracking

**Voice Commands:**
- Say **"faster"** to increase ball speed (up to 4x)
- Say **"slower"** to decrease ball speed
- The game recognizes commands even in noisy environments

**Keyboard Controls:**
- `ESC` - Return to home screen / Exit game
- `F11` - Toggle fullscreen mode
- `P` - Pause/Resume game

### Two-Player Mode Tips

- The camera is split vertically - left side controls Player 1 (left paddle), right side controls Player 2 (right paddle)
- If your hand is in the middle, it defaults to Player 1
- Both players should position themselves so their hands are clearly on their respective sides

---

## 🐛 Troubleshooting

### Game Won't Start

**"Module not found" errors:**
- Make sure your virtual environment is activated
- Reinstall dependencies: `pip install -r requirements.txt --force-reinstall`

**Import errors:**
- Verify Python version: `python --version` (should be 3.10+)
- Try: `python -m pip install --upgrade pip` then reinstall packages

### Camera Issues

**"Camera not found" or black screen:**
- Ensure no other applications are using the camera
- Check camera permissions in system settings
- Try changing `camera.device_id` in `config.yaml` (try 0, 1, or 2)
- On Linux, you might need: `sudo apt-get install v4l-utils`

**Poor tracking performance:**
- Ensure good lighting
- Keep hand clearly visible and in frame
- Lower camera resolution in config if performance is poor

### Microphone Issues

**Voice commands not working:**
- Check microphone permissions
- Test microphone in other applications first
- Adjust `voice_recognition.energy_threshold` in config.yaml (try 200-500)
- Speak clearly and close to the microphone

**PyAudio installation fails:**
- **Windows**: Install [Microsoft Visual C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)
- **Linux**: `sudo apt-get install portaudio19-dev python3-pyaudio`
- **macOS**: `brew install portaudio`

### Performance Issues

**Low FPS or laggy gameplay:**
- Lower camera resolution in `config.yaml` (try 320x240)
- Reduce `game.fps` target
- Close other resource-intensive applications
- Ensure you have sufficient CPU resources

**Game crashes:**
- Check `logs/pongsense.log` for error messages
- Try running with console enabled to see errors
- Report issues on GitHub with log files

---

## 📁 Project Structure

```
PongSense/
├── src/                    # Source code
│   ├── audio/              # Voice recognition module
│   ├── vision/             # Hand tracking and gestures
│   ├── game/               # Game engine and AI
│   ├── multimodal/         # Input fusion system
│   ├── ui/                 # User interface components
│   └── utils/              # Configuration and logging
├── assets/                 # Game assets (fonts, images, videos)
├── models/                 # Vosk speech recognition model
├── config.yaml            # Configuration file
├── run_pongsense.py       # Main entry point
└── requirements.txt       # Python dependencies
```

---

## 🤝 Contributing

We welcome contributions! Here's how you can help:

1. **Report Bugs**: Found an issue? Open a GitHub issue with details
2. **Suggest Features**: Have ideas? We'd love to hear them
3. **Code Contributions**: Fork, make changes, and submit a pull request
4. **Improve Documentation**: Help make this README even better!

---

## 🙏 Acknowledgments

- **MediaPipe** by Google for excellent hand tracking
- **Vosk** for offline speech recognition
- **Pygame** community for the game framework

---

## 📞 Support

Having trouble? Here's where to get help:

- **GitHub Issues**: Open an issue for bugs or feature requests

---

## 🎉 Enjoy PongSense!

Now that everything is set up, have fun playing! Remember:
- Keep your hand visible to the camera
- Speak clearly for voice commands
- Most importantly, enjoy the game! 🏓

---

**Made with ❤️ by the PongSense team**

*Last updated: 2025*
