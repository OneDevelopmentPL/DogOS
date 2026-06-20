import math
import pybullet as p

def compute_nominal_positions(go1_id, joint_indices, joint_limits):
    # Set nominal positions to current joint positions to avoid jumps on start
    nominal = {}
    for name, idx in joint_indices.items():
        try:
            state = p.getJointState(go1_id, idx)
            nominal[idx] = state[0]
        except Exception:
            nominal[idx] = 0.0
    return nominal

def apply_stabilization(go1_id, joint_indices, joint_limits, nominal_positions, kp=0.5, kd=0.05, max_offset=0.2):
    # Read base orientation and angular velocity
    pos, orn = p.getBasePositionAndOrientation(go1_id)
    lin_vel, ang_vel = p.getBaseVelocity(go1_id)
    roll, pitch, yaw = p.getEulerFromQuaternion(orn)

    # PD for roll (correct with hip joints)
    roll_offset = -kp * roll - kd * ang_vel[0]
    roll_offset = max(-max_offset, min(max_offset, roll_offset))

    # PD for pitch (correct with thigh joints)
    # Temporarily disable aggressive pitch correction to avoid rearing
    pitch_offset = 0.0

    # Apply offsets to appropriate joints using deterministic mapping
    for name, idx in joint_indices.items():
        target = nominal_positions.get(idx, 0.0)
        lname = name.lower()

        # side and position detection
        prefix = None
        if lname.startswith('fl'):
            prefix = 'FL'
        elif lname.startswith('fr'):
            prefix = 'FR'
        elif lname.startswith('rl'):
            prefix = 'RL'
        elif lname.startswith('rr'):
            prefix = 'RR'

        # roll correction via hip joints: left legs +, right legs -
        if 'hip' in lname and prefix is not None:
            if prefix in ('FL', 'RL'):
                target += roll_offset
            else:
                target -= roll_offset

        # pitch correction via thigh joints: front legs subtract, rear legs add
        if ('thigh' in lname or 'upper_leg' in lname) and prefix is not None:
            if prefix in ('FR', 'FL'):
                target -= pitch_offset
            else:
                target += pitch_offset

        # apply safe position control
        p.setJointMotorControl2(go1_id, idx, p.POSITION_CONTROL,
                    targetPosition=target, force=80, maxVelocity=1.5)