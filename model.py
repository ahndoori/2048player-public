import torch
import torch.nn as nn
import random
from dotenv import load_dotenv

class DQN(nn.Module):
    def __init__(self):
        super(DQN, self).__init__()
        self.network = nn.Sequential( # 4x4보드 16개 처리
            nn.Linear(16, 128),
            nn.ReLU(),
            nn.Linear(128, 128),
            nn.ReLU(),
            nn.Linear(128, 4) # 상하좌우 액션
        )

    def forward(self, x):
        return self.network(x)

    def get_action(self, state, trained=False):
        if not trained:
            return random.randint(0, 3)
        state_tensor = torch.FloatTensor(state).unsqueeze(0) # 배치 차원 추가
        with torch.no_grad():
            q_values = self.forward(state_tensor)
        return torch.argmax(q_values).item()
