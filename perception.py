import win32gui, win32ui, win32con, win32api
import numpy as np
import cv2
import time

class perception:
	def __init__(self, title="2048desktop"):
		self.title = title
		self.color_map = {
			(187, 173, 160): 0,    # 빈칸
			(218, 228, 238): 2,    # 2
			(200, 224, 237): 4,    # 4
			(121, 177, 242): 8,    # 8
			(99, 149, 245): 16,    # 16
			(95, 124, 246): 32,    # 32
			(75, 95, 246): 64,     # 64
			(114, 207, 242): 128,  # 128
			(97, 204, 242): 256,   # 256
			(80, 200, 242): 512,   # 512
			(62, 197, 242): 1024,  # 1024
			(45, 194, 242): 2048   # 2048
		}
		self.last_img = None

	def getBoardImage(self):
		hwnd = win32gui.FindWindow(None, self.title)
		if not hwnd: 
			print("PERCEPTION: WINDOW NOT FOUND")
			return None

		left, top, right, bot = win32gui.GetWindowRect(hwnd)
		w, h = right - left, bot - top
		if w <= 0 or h <= 0: return None

		hwndDC = win32gui.GetWindowDC(hwnd)
		mfcDC = win32ui.CreateDCFromHandle(hwndDC)
		saveDC = mfcDC.CreateCompatibleDC()
		saveBitMap = win32ui.CreateBitmap()
		saveBitMap.CreateCompatibleBitmap(mfcDC, w, h)
		saveDC.SelectObject(saveBitMap)
		
		try:
			saveDC.BitBlt((0, 0), (w, h), mfcDC, (0, 0), win32con.SRCCOPY)
			bmpstr = saveBitMap.GetBitmapBits(True)
			temp_img = np.frombuffer(bmpstr, dtype='uint8').reshape(h, w, 4)
			img = cv2.cvtColor(temp_img, cv2.COLOR_BGRA2BGR)
			self.last_img = img.copy()
			return img
		except Exception as e:
			print(f"CAPTURE ERROR: {e}")
			return None
		finally:
			win32gui.DeleteObject(saveBitMap.GetHandle())
			saveDC.DeleteDC()
			mfcDC.DeleteDC()
			win32gui.ReleaseDC(hwnd, hwndDC)

	def getBoardMatrix(self):
		img = self.getBoardImage()
		if img is None: return None

		h, w, _ = img.shape
		board_m = np.zeros((4, 4), dtype=int)

		start_x_ratio, start_y_ratio = 0.125, 0.420
		board_w_ratio, board_h_ratio = 0.75, 0.47
		
		step_x = (w * board_w_ratio) / 4
		step_y = (h * board_h_ratio) / 4
		origin_x = w * start_x_ratio
		origin_y = h * start_y_ratio
		row_offsets = [15, 10, 5, 2] 

		for r in range(4):
			for c in range(4):
				check_x = int(origin_x + (c * step_x) + (step_x / 3))
				check_y = int(origin_y + (r * step_y) + row_offsets[r])
				
				if 0 <= check_y < h and 0 <= check_x < w:
					pixel_color = tuple(img[check_y, check_x])
					board_m[r, c] = self.match_color(pixel_color)
		
		'''
		debug_draw = img.copy()
		for r in range(4):
			for c in range(4):
				check_x = int(origin_x + (c * step_x) + (step_x / 3))
				check_y = int(origin_y + (r * step_y) + row_offsets[r])
				if 0 <= check_y < h and 0 <= check_x < w:
					pixel_color = tuple(img[check_y, check_x])
					val = self.match_color(pixel_color)
					board_m[r, c] = val
					cv2.circle(debug_draw, (check_x, check_y), 5, (255, 0, 255), -1)
					cv2.putText(debug_draw, str(val), (check_x-5, check_y+15), 
								cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0,0,255), 1)
		cv2.imwrite("./debug/debug_point.png", debug_draw)
		'''
		return board_m

	def match_color(self, color):
		best_val, min_dist = 0, 1000
		for target, val in self.color_map.items():
			dist = np.linalg.norm(np.array(color) - np.array(target))
			if dist < min_dist:
				min_dist, best_val = dist, val
		return best_val if min_dist < 40 else 0

	def check_game_status(self):
		if self.last_img is None: return "RUNNING"
		h, w, _ = self.last_img.shape
		
		target_color = np.array([102, 122, 143]) #8f7a66
		
		def check_point(px, py):
			if 0 <= py < h and 0 <= px < w:
				pixel = self.last_img[py, px]
				return np.linalg.norm(pixel - target_color) < 50 # 색상 차이가 임계값(50) 이내면 버튼으로 인식
			return False

		y_btn = int(h * 0.67)
		has_left = check_point(int(w * 0.32), y_btn)   # Keep going (Win 시 왼쪽)
		has_right = check_point(int(w * 0.68), y_btn)  # Try again (Win 시 오른쪽)
		has_center = check_point(int(w * 0.50), y_btn) # Try again (GameOver 시 중앙)

		if has_left and has_right:
			return "GAMEWIN"
		elif has_center:
			return "GAMEOVER"
		else:
			return "STUCK"

	def send_key_background(self, key_name):
		hwnd = win32gui.FindWindow(None, self.title)
		vk = {'up': 0x26, 'down': 0x28, 'left': 0x25, 'right': 0x27}[key_name]
		win32gui.SendMessage(hwnd, win32con.WM_ACTIVATE, win32con.WA_CLICKACTIVE, 0)
		win32api.PostMessage(hwnd, win32con.WM_KEYDOWN, vk, 0)
		time.sleep(0.05)
		win32api.PostMessage(hwnd, win32con.WM_KEYUP, vk, 0)