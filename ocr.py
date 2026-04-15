import cv2
import pytesseract
import os
import numpy as np

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def processOcr(roi, name):
	if roi is None or roi.size == 0: return "N/A"
	
	gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
	_, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
	thresh = cv2.bitwise_not(thresh)
	
	coords = cv2.findNonZero(cv2.bitwise_not(thresh))
	if coords is not None:
		x_b, y_b, w_b, h_b = cv2.boundingRect(coords)
		thresh = thresh[y_b:y_b+h_b, x_b:x_b+w_b]
	
	thresh = cv2.copyMakeBorder(thresh, 15, 15, 15, 15, cv2.BORDER_CONSTANT, value=255)
	thresh = cv2.resize(thresh, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
	
	cv2.imwrite(f"./debug/debug_ocr_{name}.png", thresh)
	config = '--psm 7 -c tessedit_char_whitelist=0123456789'
	text = pytesseract.image_to_string(thresh, config=config).strip()
	
	result = "".join(filter(str.isdigit, text))
	return result if result else "0"
	
def get_scores(img_path):
    if not os.path.exists(img_path):
        return None, f"FILE NOT FOUND: {img_path}"
    img = cv2.imread(img_path)
    if img is None: 
        return None, "IMAGE LOAD FAILED"

    debug_img = img.copy()
    h, w, _ = img.shape
    y1, y2 = int(h * 0.125), int(h * 0.17)
    s_x1, s_x2 = int(w * 0.29), int(w * 0.54)
    b_x1, b_x2 = int(w * 0.57), int(w * 0.83)

    cv2.rectangle(debug_img, (s_x1, y1), (s_x2, y2), (255, 0, 255), 2)
    cv2.rectangle(debug_img, (b_x1, y1), (b_x2, y2), (255, 0, 255), 2)
    cv2.imwrite("./debug/debug_ocr_area.png",debug_img)

    score_roi = img[y1:y2, s_x1:s_x2]
    best_roi = img[y1:y2, b_x1:b_x2]

    results = {
        'score': processOcr(score_roi.copy(), "score"),
        'best': processOcr(best_roi.copy(), "best")
    }
    print(f"Score: {results['score']} / Best: {results['best']}")
    return results, None

'''
if __name__ == "__main__":
    score_data, err = get_scores("./debug/debug_board.png")
    if not err:
        print("COMPLETE OCR")
'''