import pybullet as p
import pybullet_data
import time
import math
import tkinter as tk
from tkinter import scrolledtext
import threading

physicsClient = p.connect(p.GUI)
p.setAdditionalSearchPath(pybullet_data.getDataPath())
p.configureDebugVisualizer(p.COV_ENABLE_GUI, 0)

p.setGravity(0, 0, -9.81)
planeId = p.loadURDF("plane.urdf")

urdf_path = "./models/go1_description/urdf/go1.urdf"

robotStartPos = [0, 0, 0.4] 
robotStartOrientation = p.getQuaternionFromEuler([0, 0, 0])

print("Pobieranie i wczytywanie modelu Unitree Go1...")
try:
    go1_id = p.loadURDF(urdf_path, robotStartPos, robotStartOrientation, useFixedBase=False)
    print("Unitree Go1 wczytany pomyślnie!")
    
    num_joints = p.getNumJoints(go1_id)
    print(f"\nDostępne joints ({num_joints}):")
    joint_indices = {}
    joint_limits = {}
    for i in range(num_joints):
        info = p.getJointInfo(go1_id, i)
        joint_name = info[1].decode('utf-8')
        joint_type = info[2]
        lower_limit = info[8]
        upper_limit = info[9]
        joint_indices[joint_name] = i
        joint_limits[i] = (lower_limit, upper_limit)
        print(f"  {i}: {joint_name} | Limity: [{lower_limit:.2f}, {upper_limit:.2f}]")
    
except Exception as e:
    print("Błąd wczytywania z sieci. Możesz też pobrać folder 'go1_description' lokalnie na dysk.", e)
    exit()

p.resetDebugVisualizerCamera(cameraDistance=1.5, cameraPitch=-20, cameraYaw=45, 
                             cameraTargetPosition=[0, 0, 0.3])

print("\nInicjalizacja pozycji robota...")
for joint_name, joint_idx in joint_indices.items():
    lower_limit, upper_limit = joint_limits[joint_idx]
    
    if lower_limit < upper_limit:
        target_pos = (lower_limit + upper_limit) / 2
    else:
        target_pos = 0
    
    if 'hip' in joint_name.lower():
        target_pos = 0
    elif 'thigh' in joint_name.lower() or 'upper_leg' in joint_name.lower():
        target_pos = min(0, (lower_limit + upper_limit) / 2)
    elif 'calf' in joint_name.lower() or 'lower_leg' in joint_name.lower():
        target_pos = min(0, (lower_limit + upper_limit) / 2)
    
    p.setJointMotorControl2(go1_id, joint_idx, p.POSITION_CONTROL, 
                          targetPosition=target_pos, force=1000, maxVelocity=5.0)

for step in range(200):
    p.stepSimulation()
    if step % 50 == 0:
        print(f"  Krok: {step}/200")
    time.sleep(1./240.)

print("Robot gotów!")

walk_speed = 0
turn_speed = 0
gait_phase = 0
last_time = time.time()
simulation_running = True

def simulation_loop():
    global gait_phase, walk_speed, turn_speed, simulation_running
    
    while simulation_running:
        try:
            hip_amplitude = 0.2
            thigh_amplitude = 0.4
            calf_amplitude = 0.4
            
            if walk_speed != 0 or turn_speed != 0:
                gait_phase += 0.02
                if gait_phase > 2 * math.pi:
                    gait_phase = 0
                
                for joint_name, joint_idx in joint_indices.items():
                    lower_limit, upper_limit = joint_limits[joint_idx]
                    
                    if 'hip' in joint_name.lower():
                        target = hip_amplitude * math.sin(gait_phase + walk_speed)
                        if 'l_' in joint_name.lower() or 'fl' in joint_name.lower() or 'rl' in joint_name.lower():
                            target += turn_speed * 0.2
                    elif 'thigh' in joint_name.lower() or 'upper_leg' in joint_name.lower():
                        mid_point = (lower_limit + upper_limit) / 2
                        target = mid_point + thigh_amplitude * math.sin(gait_phase + walk_speed)
                    elif 'calf' in joint_name.lower() or 'lower_leg' in joint_name.lower():
                        mid_point = (lower_limit + upper_limit) / 2
                        target = mid_point + calf_amplitude * math.sin(gait_phase + walk_speed + math.pi)
                    else:
                        continue
                    
                    p.setJointMotorControl2(go1_id, joint_idx, p.POSITION_CONTROL, 
                                          targetPosition=target, force=1000, maxVelocity=5.0)
            else:
                for joint_name, joint_idx in joint_indices.items():
                    lower_limit, upper_limit = joint_limits[joint_idx]
                    
                    if 'hip' in joint_name.lower():
                        target_pos = 0
                    elif 'thigh' in joint_name.lower() or 'upper_leg' in joint_name.lower():
                        target_pos = min(0, (lower_limit + upper_limit) / 2)
                    elif 'calf' in joint_name.lower() or 'lower_leg' in joint_name.lower():
                        target_pos = min(0, (lower_limit + upper_limit) / 2)
                    else:
                        continue
                    
                    p.setJointMotorControl2(go1_id, joint_idx, p.POSITION_CONTROL, 
                                          targetPosition=target_pos, force=1000, maxVelocity=5.0)
            
            p.stepSimulation()
            time.sleep(1./240.)
        except:
            break

sim_thread = threading.Thread(target=simulation_loop, daemon=True)
sim_thread.start()

root = tk.Tk()
root.title("Unitree Go1 - Kontrola Robotem")
root.geometry("900x700")

code_frame = tk.LabelFrame(root, text="Python Code Editor", font=("Arial", 10, "bold"))
code_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

code_text = scrolledtext.ScrolledText(code_frame, height=25, width=100, font=("Courier", 10))
code_text.pack(fill=tk.BOTH, expand=True)

code_text.insert("1.0", """# Available variables:
# - go1_id: Robot ID
# - p: PyBullet module
# - joint_indices: Dict of joint names
# - joint_limits: Joint angle limits

# Examples:
# walk_speed = 1.0  # Move forward
# walk_speed = -0.5  # Move backward
# turn_speed = 0.5  # Turn left
# turn_speed = -0.5  # Turn right

# Control specific joints:
# joint_idx = joint_indices['FR_hip_joint']
# p.setJointMotorControl2(go1_id, joint_idx, p.POSITION_CONTROL, 
#                        targetPosition=0.5, force=500)

""")

# Frame dla przycisków
button_frame = tk.Frame(root)
button_frame.pack(fill=tk.X, padx=10, pady=5)

def execute_code():
    try:
        code = code_text.get("1.0", tk.END)
        
        exec_globals = {
            'go1_id': go1_id,
            'p': p,
            'joint_indices': joint_indices,
            'joint_limits': joint_limits,
            'math': math,
            'time': time,
            '__builtins__': __builtins__
        }
        
        exec_globals['walk_speed'] = walk_speed
        exec_globals['turn_speed'] = turn_speed
        
        exec(code, exec_globals)
        
        globals()['walk_speed'] = exec_globals.get('walk_speed', walk_speed)
        globals()['turn_speed'] = exec_globals.get('turn_speed', turn_speed)
        
        output_text.config(state=tk.NORMAL)
        output_text.delete("1.0", tk.END)
        output_text.insert(tk.END, "✓ Kod wykonany pomyślnie!")
        output_text.config(state=tk.DISABLED)
    except Exception as e:
        output_text.config(state=tk.NORMAL)
        output_text.delete("1.0", tk.END)
        output_text.insert(tk.END, f"✗ Błąd:\n{str(e)}")
        output_text.config(state=tk.DISABLED)

execute_btn = tk.Button(button_frame, text="▶ Execute Code", command=execute_code, 
                       bg="#4CAF50", fg="white", font=("Arial", 11, "bold"), padx=20, pady=8)
execute_btn.pack(side=tk.LEFT, padx=5)

def clear_code():
    code_text.delete("1.0", tk.END)

clear_btn = tk.Button(button_frame, text="Clear", command=clear_code, 
                     bg="#f44336", fg="white", font=("Arial", 11), padx=20, pady=8)
clear_btn.pack(side=tk.LEFT, padx=5)

def stop_simulation():
    global simulation_running
    simulation_running = False
    try:
        p.disconnect()
    except:
        pass
    root.destroy()

stop_btn = tk.Button(button_frame, text="Exit", command=stop_simulation, 
                    bg="#FF9800", fg="white", font=("Arial", 11), padx=20, pady=8)
stop_btn.pack(side=tk.LEFT, padx=5)

output_frame = tk.LabelFrame(root, text="Output", font=("Arial", 10, "bold"))
output_frame.pack(fill=tk.BOTH, expand=False, padx=10, pady=5)

output_text = tk.Text(output_frame, height=3, width=100, font=("Courier", 9))
output_text.pack(fill=tk.BOTH, expand=True)
output_text.config(state=tk.DISABLED)

root.mainloop()