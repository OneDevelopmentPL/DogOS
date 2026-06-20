import csv
import os
import threading

class DataCollector:
    def __init__(self, path, joint_order):
        self.path = path
        self.joint_order = joint_order
        self.lock = threading.Lock()
        header = [
            't', 'roll', 'pitch', 'yaw', 'angvx', 'angvy', 'angvz'
        ]
        for j in joint_order:
            header += [f'jp_{j}', f'jv_{j}']
        for j in joint_order:
            header += [f'tgt_{j}']

        os.makedirs(os.path.dirname(path), exist_ok=True)
        new_file = not os.path.exists(path)
        self.file = open(path, 'a', newline='')
        self.writer = csv.writer(self.file)
        if new_file:
            self.writer.writerow(header)

    def log(self, t, rpy, angv, joint_positions, joint_vels, targets):
        row = [t, rpy[0], rpy[1], rpy[2], angv[0], angv[1], angv[2]]
        for j in self.joint_order:
            row.append(joint_positions.get(j, 0.0))
            row.append(joint_vels.get(j, 0.0))
        for j in self.joint_order:
            row.append(targets.get(j, 0.0))
        with self.lock:
            self.writer.writerow(row)
            self.file.flush()

    def close(self):
        try:
            self.file.close()
        except Exception:
            pass
