import os
import glob
import pickle
import shutil
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
from dotenv import load_dotenv
from model import DQN

load_dotenv()
PATH_FILE_MODEL = os.getenv("PATH_FILE_MODEL")
PATH_DIR_DATA = os.getenv("PATH_DIR_DATA")
ARCHIVE_PATH = "./model/archive/"
MODEL_SAVE_PATH = "./model/dqn_model.pth"
BATCH_SIZE = 64
EPOCHS = 10
LEARNING_RATE = 0.001

def load_all_data(trainingLog=None):
	all_states = []
	all_actions = []

	files = glob.glob(os.path.join(PATH_DIR_DATA, "*.pkl"))
	if not files:
		if trainingLog: trainingLog('NO DATA FILES TO TRAINING')
		return None, None, []

	for file in files:
		with open(file, 'rb') as f:
			experiences = pickle.load(f)
			for exp in experiences:
				state = exp['state'].flatten().astype(np.float32)
				all_states.append(state)
				all_actions.append(exp['action'])
	
	return np.array(all_states), np.array(all_actions), files

def train_model(trainingLog=None):
	states, actions, files = load_all_data(trainingLog)
	if states is None: return

	states_t = torch.FloatTensor(states)
	actions_t = torch.LongTensor(actions)
	device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
	model = DQN().to(device)

	if os.path.exists(MODEL_SAVE_PATH):
		try:
			model.load_state_dict(torch.load(MODEL_SAVE_PATH))
			trainingLog("START TRAINING WITH PREVIOUS MODEL")
		except Exception as e:
			trainingLog(f"NEW MODEL CREATED: {e}")

	optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE)
	criterion = nn.CrossEntropyLoss() # 다중분류 접근

	trainingLog(f"START TRAINING, DATA COUNT: {len(states)}, DEVICE: {device}")

	dataset_size = len(states)d
	for epoch in range(EPOCHS):
		indices = np.arange(dataset_size)
		np.random.shuffle(indices)
		
		epoch_loss = 0
		for i in range(0, dataset_size, BATCH_SIZE):
			batch_idx = indices[i:i+BATCH_SIZE]
			batch_s = states_t[batch_idx].to(device)
			batch_a = actions_t[batch_idx].to(device)

			outputs = model(batch_s)
			loss = criterion(outputs, batch_a)

			optimizer.zero_grad()
			loss.backward()
			optimizer.step()

			epoch_loss += loss.item()

		trainingLog(f"EPOCH {epoch+1}/{EPOCHS}, LOSS: {epoch_loss / (dataset_size/BATCH_SIZE):.4f}")

	torch.save(model.state_dict(), MODEL_SAVE_PATH)
	trainingLog(f"COMPLETE TRAINING, SAVED MODEL: {MODEL_SAVE_PATH}")

	os.makedirs(ARCHIVE_PATH, exist_ok=True)
	for f in files:
		shutil.move(f, os.path.join(ARCHIVE_PATH, os.path.basename(f)))
	trainingLog(f"COMPLETE TRAINING, ARCHIVED DATA: {len(files)} FILES MOVED TO ({ARCHIVE_PATH})")

if __name__ == "__main__":
	train_model()