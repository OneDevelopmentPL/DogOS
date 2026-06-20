import os
import torch
import torch.nn as nn
import torch.optim as optim
import pandas as pd
import numpy as np

from .model import MLP

def load_csv(path):
    df = pd.read_csv(path)
    return df

def train(data_csv, joint_order, model_out='nn/model.pt', epochs=50, lr=1e-3, batch_size=64):
    df = load_csv(data_csv)

    # build input features and targets based on header convention
    cols_state = ['roll','pitch','yaw','angvx','angvy','angvz']
    for j in joint_order:
        cols_state += [f'jp_{j}', f'jv_{j}']
    cols_target = [f'tgt_{j}' for j in joint_order]

    X = df[cols_state].values.astype(np.float32)
    y = df[cols_target].values.astype(np.float32)

    input_size = X.shape[1]
    output_size = y.shape[1]

    model = MLP(input_size, output_size)
    opt = optim.Adam(model.parameters(), lr=lr)
    loss_fn = nn.MSELoss()

    dataset = torch.utils.data.TensorDataset(torch.from_numpy(X), torch.from_numpy(y))
    loader = torch.utils.data.DataLoader(dataset, batch_size=batch_size, shuffle=True)

    model.train()
    for ep in range(epochs):
        total = 0.0
        for xb, yb in loader:
            pred = model(xb)
            loss = loss_fn(pred, yb)
            opt.zero_grad()
            loss.backward()
            opt.step()
            total += loss.item() * xb.size(0)
        print(f"Epoch {ep+1}/{epochs} loss={total/len(dataset):.6f}")

    os.makedirs(os.path.dirname(model_out), exist_ok=True)
    torch.save({'input_size': input_size, 'output_size': output_size, 'state_dict': model.state_dict()}, model_out)
    print('Model saved to', model_out)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('csv')
    parser.add_argument('--joints', nargs='+', type=int, required=True)
    parser.add_argument('--out', default='nn/model.pt')
    parser.add_argument('--epochs', type=int, default=50)
    args = parser.parse_args()
    train(args.csv, args.joints, model_out=args.out, epochs=args.epochs)
