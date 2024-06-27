import torch
import torch.nn as nn

class ADHDModel(nn.Module):
    def __init__(self, input_size, hidden_size, num_layers):
        super(ADHDModel, self).__init__()
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True)
        self.fc = nn.Linear(hidden_size, 2)  # Binary classification
        self.num_layers = num_layers
        self.hidden_size = hidden_size
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        
    def forward(self, x):
        h0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size).to(x.device)
        c0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size).to(x.device)
        
        out, _ = self.lstm(x, (h0, c0))
        out = out[:, -1, :]  # Take the output from the last time step
        out = self.fc(out)
        return out

def predict(age, handedness, sex, reaction_times):
    rt_mean = 2892.4247596153846
    rt_std = 1944.9682754013772
    age_mean = 26.192307692307693
    age_std = 2.849353530834194

    reaction_time = [i['time'] for i in reaction_times]
    accuracy = [int(i['accurate']) for i in reaction_times]

    handedness = 0 if handedness == 'right' else 1
    sex = 0 if sex=='male' else 1
    
    age = (age - age_mean) / age_std
    reaction_time = [(i*1000 - rt_mean) / rt_std for i in reaction_time]

    tensor = []
    for i in range(len(reaction_time)):
        tensor.append([age, sex, handedness, 0, reaction_time[i], accuracy[i]])
    
    model = ADHDModel(6, 64, 5)
    model.load_state_dict(torch.load('model.pth'))
    model.to(model.device)
    tensor = torch.tensor(tensor).float().to(model.device).unsqueeze(0)

    model.eval()
    with torch.no_grad():
        output = model(tensor)
        _, predicted = torch.max(output, 1)
    return "You probably have ADHD" if predicted.item() == 1 else "You probably don't have ADHD"