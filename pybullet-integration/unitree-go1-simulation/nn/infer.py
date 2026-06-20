import os
import torch
import numpy as np

from .model import MLP

class NNController:
    def __init__(self, joint_order, model_path='nn/model.pt', device=None):
        self.joint_order = joint_order
        self.model_path = model_path
        self.device = device or ('cuda' if torch.cuda.is_available() else 'cpu')
        self.model = None
        if os.path.exists(model_path):
            try:
                # load metadata
                data = torch.load(model_path, map_location=self.device)
                input_size = data.get('input_size')
                output_size = data.get('output_size')
                model_state = data.get('state_dict')
                self.model = MLP(input_size, output_size).to(self.device)
                self.model.load_state_dict(model_state)
                self.model.eval()
            except Exception:
                self.model = None

    def predict_offsets(self, obs):
        """
        obs: iterable of floats shaped (input_size,)
        returns: dict joint_idx->offset
        """
        if self.model is None:
            return {j: 0.0 for j in self.joint_order}
        x = torch.tensor(obs, dtype=torch.float32, device=self.device).unsqueeze(0)
        with torch.no_grad():
            out = self.model(x).cpu().numpy().ravel()
        # clamp small
        out = np.clip(out, -0.1, 0.1)
        return {j: float(out[i]) for i, j in enumerate(self.joint_order)}
