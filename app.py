import os
import cv2
import time
import pickle
import threading
import random
import numpy as np
from dotenv import load_dotenv
from datetime import datetime
from flask import Flask, render_template
from flask_socketio import SocketIO, emit
from perception import perception
from algorithm import algorithm
import training as train
import ocr
from model import DQN

load_dotenv()
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")
perception = perception(os.getenv("NAME_WINDOW"))
algorithm = algorithm() # 알고리즘 Expectimax
algorithm_running = False # 알고리즘 실행 상태 Expectimax
dqn_model = DQN()
model_running = False # 모델 실행 상태 DQN
session_start_time = ""

PATH_FILE_MODEL = os.getenv("PATH_FILE_MODEL")
PATH_DIR_DATA = os.getenv("PATH_DIR_DATA")

def save_collected_data(data_list):
	global session_start_time
	if not data_list:
		return
	timestamp = datetime.now().strftime("%H%M%S")
	file_name = f"data_{timestamp}.pkl"
	file_name = f"data_{session_start_time}_{timestamp}.pkl"
	file_full_path = os.path.join(PATH_DIR_DATA, file_name)

	with open(file_full_path, 'wb') as f:
		pickle.dump(data_list, f)
	print(f"[SYSTEM] Data Saved: {file_full_path} (Size: {len(data_list)})")

MOVE_MAP = {0: 'up', 1: 'down', 2: 'left', 3: 'right'}
MOVE_TO_IDX = {'up': 0, 'down': 1, 'left': 2, 'right': 3}

def algorithm_core_loop():
	global algorithm_running
	global session_start_time
	session_start_time = datetime.now().strftime("%Y%m%d_%H%M%S")
	has_saved_this_session = False
	boardPrev = None
	stuck_count = 0
	
	collected_experiences = []

	while algorithm_running:
		board = perception.getBoardMatrix()
		if board is None:
			time.sleep(0.5)
			continue

		is_changed = not np.array_equal(boardPrev, board) if boardPrev is not None else True
		if is_changed:

			stuck_count = 0
			best_move_str = algorithm.get_best_move(board)
			
			if best_move_str is None:
				valid_moves = [MOVE_MAP[m] for m in range(4) if algorithm.simulate_move(board, m)[1]]
				if valid_moves:
					best_move_str = random.choice(valid_moves)

			if best_move_str:
				collected_experiences.append({
				'state': board.copy(),
				'action': MOVE_TO_IDX[best_move_str]
			})

			perception.send_key_background(best_move_str)
			socketio.emit('log',{
				'status':'MOVE',
				'type':'ALGORITHM',
				'move': best_move_str.upper(),
				'max': int(board.max())
			});
			socketio.emit('update', {
				'type':'ALGORITHM',
				'move': best_move_str.upper(),
				'max': int(board.max()),
				'board': board.tolist(),
				'running': algorithm_running
			});
			
			boardPrev = board.copy()
			time.sleep(0.3)
			
			if len(collected_experiences) >= 500:
				save_collected_data(collected_experiences)
				collected_experiences = [] # 리스트 비우기

		else:
			time.sleep(0.2)
			stuck_count += 1
			
			if stuck_count >= 5:
				status = perception.check_game_status()
				socketio.emit('log',{
					'type':'ALGORITHM',
					'status': status
				});
				socketio.emit('update', {
					'type':'ALGORITHM',
					'board': board.tolist(),
					'running': False,
					'status': status
				})

				print(f"[SYSTEM] ALGORITHM STOPPED, STATUS: {status}")
				algorithm_running = False

				if collected_experiences and not has_saved_this_session:
					save_collected_data(collected_experiences)
					has_saved_this_session = True
					collected_experiences = []

				stuck_count = 0
				time.sleep(1.0)

	if collected_experiences:
		save_collected_data(collected_experiences)

	cv2.imwrite(f"./debug/debug_board.png", perception.getBoardImage())
	with open("./debug/debug_board.txt", "w", encoding="utf-8") as f:
		f.write(f"Timestamp: {int(time.time())}\nBoard:\n{board}\n")
	

def dqn_play_loop():
	global model_running
	boardPrev = None
	stuck_count = 0

	while model_running:
		board = perception.getBoardMatrix()
		if board is None:
			time.sleep(0.5)
			continue

		is_changed = not np.array_equal(boardPrev, board) if boardPrev is not None else True

		if is_changed:
			stuck_count = 0
			action_idx = dqn_model.get_action(board.flatten(), trained=os.path.exists(PATH_FILE_MODEL))
			
			_, can_move = algorithm.simulate_move(board, action_idx)
			
			if not can_move:
				valid_moves = [m for m in range(4) if algorithm.simulate_move(board, m)[1]]
				if valid_moves:
					action_idx = random.choice(valid_moves)
					can_move = True

			if can_move:
				best_move_str = MOVE_MAP[action_idx]
				perception.send_key_background(best_move_str)
				socketio.emit('log',{
					'type':'MODEL',
					'status':'MOVE',
					'move': best_move_str.upper(),
					'max': int(board.max())
				});
				socketio.emit('update', {
					'type':'MODEL',
					'move': best_move_str.upper(),
					'max': int(board.max()),
					'board': board.tolist(),
					'running': model_running
				})
			
			boardPrev = board.copy()
			time.sleep(0.3)
		else:
			time.sleep(0.2)
			stuck_count += 1
			if stuck_count >= 5:
				status = perception.check_game_status()
				socketio.emit('log',{
					'type':'MODEL',
					'status': status
				});
				socketio.emit('update', {
					'board': board.tolist(),
					'running': False,
					'status': status
				});
				
				print(f"[SYSTEM] Model Stopped. Result: {status}")
				model_running = False # 루프 종료
				stuck_count = 0
				time.sleep(1.0)

@app.route('/ui')
def ui(): return render_template('ui.html')

@app.route('/')
def index(): return render_template('index.html')

@socketio.on('toggle_algorithm')
def handle_algorithm(data):
	global algorithm_running
	algorithm_running = data['status']
	if algorithm_running:
		print("[SYSTEM] Algorithm Engagement Started. Data collection active.")
		threading.Thread(target=algorithm_core_loop, daemon=True).start()
	else:
		print("[SYSTEM] Algorithm Mission Aborted. Data collection suspended.")

@socketio.on('toggle_model')
def handle_model(data):
	global model_running
	model_running = data['status']
	if model_running:
		print("[SYSTEM] DQN Model Started. Playing game.")
		threading.Thread(target=dqn_play_loop, daemon=True).start()
	else:
		print("[SYSTEM] DQN Model Stopped.")

@socketio.on('get_status')
def handle_get_status(data):
	try:
		result, error = ocr.get_scores("./debug/debug_board.png")
		if error or not result:
			print(f'OCR ERROR: {error}')
			result = {'score': '0', 'best': '0'}

		model_info = "N/A"
		if os.path.exists(PATH_FILE_MODEL):
			m_stat = os.stat(PATH_FILE_MODEL)
			m_time = datetime.fromtimestamp(m_stat.st_mtime).strftime("%Y-%m-%d %H:%M")
			model_info = f"dqn_model.pth {m_time} {format_size(m_stat.st_size)}"

		files = [f for f in os.listdir(PATH_DIR_DATA) if f.endswith('.pkl')]
		data_size = format_size(sum(os.path.getsize(os.path.join(PATH_DIR_DATA, f)) for f in files) )
		file_details = [f"{f} {format_size(os.path.getsize(os.path.join(PATH_DIR_DATA, f)))}" for f in files]

		'''
		socketio.emit('log', {
			'status': 'SCORE',
			'score': result['score'],
			'best': result['best']
		})
		'''

		return {
			'score': result['score'],
			'best': result['best'],
			'model_info': model_info,
			'data_count': len(files),
			'data_size': data_size,
			'file_list': file_details,
			'game_window': perception.getBoardImage() is not None
		}

	except Exception as e:
		print(f"[OCR Error] {str(e)}")


@socketio.on('toggle_training')
def handle_training():
	def trainingLog(message):
		print(f"[TRAINING] {message}")
		socketio.emit('log', {'type':'TRAINING','status': 'TRAINING', 'message': message})
	trainingLog("START MODEL TRAINING")
	threading.Thread(target=train.train_model, args=(trainingLog,), daemon=True).start()


def format_size(size_bytes):
    if size_bytes == 0: return "0B"
    units = ("B", "KB", "MB", "GB", "TB")
    import math
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s}{units[i]}"

if __name__ == '__main__':
	socketio.run(app, port=2048, debug=True, use_reloader=False)