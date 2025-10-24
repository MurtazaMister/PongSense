# PongSense

A multimodal Pong game controlled by hand gestures and voice commands.

## Features

- **Home Screen**: Clean interface with Start Game and How to Play buttons
- **Tutorial System**: Interactive slideshow with video demonstrations
- **Hand Gesture Control**: Track fist movements to control paddle position
- **Voice Commands**: "faster" and "slower" commands to control ball speed
- **Single-Player Mode**: Play against AI opponent
- **Two-Player Mode**: Two players using hands in the same camera view
- **Real-time Processing**: Low-latency gesture and voice recognition
- **Integrated Camera View**: Camera view at top of screen for hand tracking visualization

## Requirements

- Python 3.10+
- Webcam
- Microphone
- Windows 10/11, macOS, or Linux

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd PongSense
```

2. Create a virtual environment:
```bash
python -m venv pongsense_env
pongsense_env\Scripts\activate  # Windows
# or
source pongsense_env/bin/activate  # Linux/macOS
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Run the application:
```bash
python run_pongsense.py
```

Or alternatively:
```bash
cd src
python main.py
```

2. **Home Screen**: You'll see a welcome screen with two options:
   - **Start Game**: Begin playing immediately
   - **How to Play**: View interactive tutorial with video demonstrations

3. **How to Play Tutorial**: 
   - **Slide 1**: Video demonstration of hand control (close fist and move arm up/down)
   - **Slide 2**: Voice commands explanation ("faster" and "slower")
   - Use navigation buttons or arrow keys to move between slides
   - Click "Play" to start video demonstrations

4. Calibration will happen automatically for 3 seconds when the game starts.

5. Game controls:
   - **Hand gestures**: Move your fist up/down to control paddle position
   - **Voice commands**: Say "faster" or "slower" to control ball speed
   - **Keyboard**: 
     - `SPACE`: Toggle between single-player and two-player modes
     - `ESC`: Exit the game

4. **Integrated Camera View**: You'll see a camera view at the top of the screen showing:
   - Your hand with MediaPipe landmarks
   - **Red circle**: Fist detected (controls paddle)
   - **Green circle**: Open hand detected (controls paddle)
   - **Yellow circle**: Other gestures (ignored)
   - Both FIST and OPEN hand gestures control the paddle

## Game Modes

- **Single Player**: Control Player 1 with FIST or OPEN hand, Player 2 is AI
- **Two Player**: Both players control paddles with FIST or OPEN hands (leftmost hand = Player 1)

## Configuration

Edit `config.yaml` to adjust:
- Camera settings
- Hand tracking sensitivity
- Voice recognition parameters
- Game difficulty
- Performance settings
- Camera overlay (enable/disable, size)

## Troubleshooting

### Camera Issues
- Ensure camera is not being used by other applications
- Check camera permissions
- Try different camera device IDs in config.yaml

### Microphone Issues
- Check microphone permissions
- Ensure microphone is working in other applications
- Adjust energy threshold in config.yaml

### Performance Issues
- Reduce camera resolution in config.yaml
- Lower detection confidence thresholds
- Enable multithreading optimizations

## Architecture

The application follows a modular design:

- `vision/`: Hand tracking and gesture recognition
- `audio/`: Voice recognition and command processing
- `game/`: Game engine and AI opponent
- `multimodal/`: Input fusion and coordination
- `utils/`: Configuration and logging utilities

## Development

To run tests:
```bash
python -m pytest tests/
```

To check code quality:
```bash
black src/
flake8 src/
mypy src/
```
