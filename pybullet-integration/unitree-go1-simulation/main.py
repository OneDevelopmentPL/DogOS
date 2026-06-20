import time

try:
    import pybullet as p
except Exception as e:
    print("Error: could not import pybullet. Make sure the correct Python environment is active and install pybullet.")
    print("Install with: pip install pybullet")
    raise

try:
    import pybullet_data
except Exception:
    print("Warning: could not import pybullet_data; continuing but visuals or search paths may be limited.")

try:
    from robot_control import compute_nominal_positions, apply_stabilization
except Exception as e:
    print(f"Error importing robot_control: {e}")
    raise

physicsClient = p.connect(p.GUI)
p.setAdditionalSearchPath(pybullet_data.getDataPath())

p.setGravity(0, 0, -9.81)
planeId = p.loadURDF("plane.urdf")

urdf_path = "./models/go1_description/urdf/go1.urdf"
robotStartPos = [0, 0, 0.4] 
robotStartOrientation = p.getQuaternionFromEuler([0, 0, 0])

print("Loading Unitree Go1...")
try:
    go1_id = p.loadURDF(urdf_path, robotStartPos, robotStartOrientation, useFixedBase=False)
    print("✓ Go1 loaded!")
    
    num_joints = p.getNumJoints(go1_id)
    print(f"\nJoints: {num_joints}")
    
    joint_indices = {}
    joint_limits = {}
    for i in range(num_joints):
        info = p.getJointInfo(go1_id, i)
        joint_type = info[2]
        # only include revolute/prismatic joints (skip fixed)
        if joint_type == p.JOINT_FIXED:
            continue
        joint_name = info[1].decode('utf-8')
        lower_limit = info[8]
        upper_limit = info[9]
        joint_indices[joint_name] = i
        joint_limits[i] = (lower_limit, upper_limit)
    nominal_positions = compute_nominal_positions(go1_id, joint_indices, joint_limits)
    # deterministic joint order for NN and logging
    joint_order = [joint_indices[n] for n in sorted(joint_indices.keys())]
    # optional NN controller
    try:
        from nn.infer import NNController
        nn_controller = NNController(joint_order)
        use_nn = nn_controller.model is not None
    except Exception:
        nn_controller = None
        use_nn = False
    # optional data collector
    try:
        from nn.collector import DataCollector
        collector = DataCollector('nn/data.csv', joint_order)
        collect_data = True
    except Exception:
        collector = None
        collect_data = False
    
except Exception as e:
    print(f"✗ Error: {e}")
    exit()

p.resetDebugVisualizerCamera(cameraDistance=1.5, cameraPitch=-20, cameraYaw=45, 
                             cameraTargetPosition=[0, 0, 0.3])

print("\n" + "="*50)
print("PyBullet Unitree Go1 Simulator")
print("="*50)
print("\nEdit main.py to control the robot")
print("Available:")
print("  - go1_id: Robot ID")
print("  - joint_indices: Joint name -> index")
print("  - joint_limits: Joint angle limits")
print("  - p: PyBullet module")
print("\nExample:")
print("  idx = joint_indices['FR_hip_joint']")
print("  p.setJointMotorControl2(go1_id, idx, p.POSITION_CONTROL,")
print("                         targetPosition=0.5, force=500)")
print("\nPress Q to quit")
print("="*50 + "\n")

while True:
    try:
        keys = p.getKeyboardEvents()
        if ord('q') in keys:
            break
    except:
        break
    # run stabilization and simulation on main thread
    apply_stabilization(go1_id, joint_indices, joint_limits, nominal_positions)
    # NN inference (adds small offsets)
    if use_nn and nn_controller is not None:
        # build obs vector
        pos, orn = p.getBasePositionAndOrientation(go1_id)
        lin_v, ang_v = p.getBaseVelocity(go1_id)
        rpy = p.getEulerFromQuaternion(orn)
        joint_states = {i: p.getJointState(go1_id, i)[0] for i in joint_order}
        joint_vels = {i: p.getJointState(go1_id, i)[1] for i in joint_order}
        obs = [rpy[0], rpy[1], rpy[2], ang_v[0], ang_v[1], ang_v[2]]
        for j in joint_order:
            obs.append(joint_states.get(j, 0.0))
            obs.append(joint_vels.get(j, 0.0))
        offsets = nn_controller.predict_offsets(obs)
        for j, off in offsets.items():
            # apply small offset to current target
            cur_target = nominal_positions.get(j, 0.0)
            tgt = cur_target + off
            p.setJointMotorControl2(go1_id, j, p.POSITION_CONTROL, targetPosition=tgt, force=80)
    # data collection
    if collect_data and collector is not None:
        pos, orn = p.getBasePositionAndOrientation(go1_id)
        lin_v, ang_v = p.getBaseVelocity(go1_id)
        rpy = p.getEulerFromQuaternion(orn)
        joint_states = {i: p.getJointState(go1_id, i)[0] for i in joint_order}
        joint_vels = {i: p.getJointState(go1_id, i)[1] for i in joint_order}
        # use nominal_positions as targets for logging
        collector.log(time.time(), rpy, ang_v, joint_states, joint_vels, nominal_positions)
    p.stepSimulation()
    time.sleep(1./240.)

p.disconnect()
print("Done.")
