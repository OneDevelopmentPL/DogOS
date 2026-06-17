# Unitree Go1 PyBullet Simulator

A Python-based physics simulation of the Unitree Go1 quadruped robot using PyBullet, with an interactive Python code editor for real-time robot control.

## Features

- **Physics Simulation**: Realistic dynamics simulation powered by PyBullet
- **Interactive GUI**: Built-in Python code editor to control the robot in real-time
- **Trotting Gait**: Pre-implemented diagonal trotting pattern for locomotion
- **Joint Control**: Direct access to all 45 robot joints for custom programming
- **Real-time Visualization**: 3D visualization of robot movements in the PyBullet simulator

## Prerequisites

- Python 3.8+
- PyBullet
- Tkinter (usually comes with Python)

## Installation

### 1. Install PyBullet

```bash
pip install pybullet
```

### 2. Download Robot Model

The simulation requires the Unitree Go1 URDF model files. Download and place them in the `models/` directory:

```bash
mkdir -p models
cd models
git clone https://github.com/unitreerobotics/unitree_ros.git
cp -r unitree_ros/robots/go1_description .
rm -rf unitree_ros
cd ..
```

## Usage

### Running the Simulator

```bash
python main.py
```

This will open two windows:
1. **PyBullet Simulator Window**: Shows the 3D robot and physics world
2. **Code Editor Window**: Write and execute Python code to control the robot

### Control Examples

In the code editor, you can write Python code to control the robot:

#### Simple Movement

```python
# Move forward
walk_speed = 1.0

# Move backward
walk_speed = -0.5

# Turn left
turn_speed = 0.5

# Turn right
turn_speed = -0.5

# Stop
walk_speed = 0
turn_speed = 0
```

#### Control Individual Joints

```python
# Get the joint index
joint_idx = joint_indices['FR_hip_joint']

# Set position target
p.setJointMotorControl2(go1_id, joint_idx, p.POSITION_CONTROL, 
                       targetPosition=0.5, force=500, maxVelocity=2.0)
```

#### Query Joint Information

```python
# Get current joint state
state = p.getJointState(go1_id, joint_idx)
position = state[0]  # Joint position
velocity = state[1]  # Joint velocity
force = state[2]     # Joint reaction force
```

## Available Variables in Code Editor

- **`go1_id`**: The robot body ID in PyBullet
- **`p`**: PyBullet module - use all PyBullet functions
- **`joint_indices`**: Dictionary mapping joint names to their indices
  - Example: `joint_indices['FR_hip_joint']` returns the index of the front-right hip joint
- **`joint_limits`**: Dictionary with (min, max) angle limits for each joint
- **`math`**: Python math module
- **`time`**: Python time module
- **`walk_speed`**: Global variable controlling forward/backward movement
- **`turn_speed`**: Global variable controlling rotation

## Robot Anatomy

The Go1 has 4 legs (Front-Left, Front-Right, Rear-Left, Rear-Right) with 3 joints each:

- **Hip Joint**: Lateral movement
- **Thigh Joint**: Forward/backward movement
- **Calf Joint**: Foot position

Joint naming convention: `{POSITION}_{TYPE}_joint`
- Positions: `FL` (Front-Left), `FR` (Front-Right), `RL` (Rear-Left), `RR` (Rear-Right)
- Types: `hip`, `thigh`, `calf`

Example: `FR_hip_joint`, `RL_thigh_joint`, `FL_calf_joint`

## GUI Buttons

- **▶ Execute Code**: Run the Python code you wrote
- **Clear**: Clear the code editor
- **Exit**: Stop simulation and close the application

## Output Panel

Shows execution status:
- ✓ Success message when code runs without errors
- ✗ Error message with details if something goes wrong

## Advanced Examples

### Walking Pattern

```python
# Simple walking pattern
walk_speed = 1.0
turn_speed = 0
```

### Coordinated Movement

```python
import math

# Sine wave movement
for i in range(100):
    walk_speed = math.sin(i * 0.1)
    time.sleep(0.01)
```

### Custom Gait

```python
# Manually control leg positions
FR_hip_idx = joint_indices['FR_hip_joint']
FR_thigh_idx = joint_indices['FR_thigh_joint']
FR_calf_idx = joint_indices['FR_calf_joint']

# Set positions
p.setJointMotorControl2(go1_id, FR_hip_idx, p.POSITION_CONTROL, 
                       targetPosition=0.2, force=500)
p.setJointMotorControl2(go1_id, FR_thigh_idx, p.POSITION_CONTROL, 
                       targetPosition=-0.5, force=500)
p.setJointMotorControl2(go1_id, FR_calf_idx, p.POSITION_CONTROL, 
                       targetPosition=-1.0, force=500)
```

## Troubleshooting

### Model Not Loading

Make sure the `models/go1_description/urdf/go1.urdf` file exists:

```bash
ls models/go1_description/urdf/go1.urdf
```

If not, re-download the model as described in the Installation section.

### Tkinter Not Available

If you get a Tkinter error:

```bash
# On macOS
brew install python-tk@3.11  # or your Python version

# On Ubuntu/Debian
sudo apt-get install python3-tk

# On Fedora
sudo dnf install python3-tkinter
```

### PyBullet Connection Error

Close the PyBullet window and restart the simulator.

## Physics Parameters

Key simulation parameters you can modify:

```python
# Gravity (in world setup)
p.setGravity(0, 0, -9.81)  # Accelertion in m/s²

# Motor control parameters
p.setJointMotorControl2(
    go1_id, 
    joint_idx, 
    p.POSITION_CONTROL,
    targetPosition=0.5,      # Target angle in radians
    force=1000,              # Max motor force
    maxVelocity=5.0          # Max joint velocity
)

# Simulation step
p.stepSimulation()  # Advance simulation by one time step
time.sleep(1./240.)  # ~240 Hz simulation rate
```

## Project Structure

```
unitree-go1-simulation/
├── main.py                          # Main simulator script
├── README.md                        # This file
├── models/
│   └── go1_description/             # URDF robot model
│       ├── urdf/
│       │   └── go1.urdf
│       └── meshes/                  # 3D model files
└── config.json                      # Configuration (optional)
```

## References

- [PyBullet Documentation](https://pybullet.org/)
- [Unitree Go1 Repository](https://github.com/unitreerobotics/unitree_ros)
- [URDF Format](http://wiki.ros.org/urdf)

## License

This project uses the Unitree Go1 URDF model from the Unitree robotics repository.

## Contributing

Feel free to fork and submit pull requests for improvements!

---

**Happy Simulating! 🤖**
