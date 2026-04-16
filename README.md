<img src="./2048player-demo.gif" width="100%"/>

# 🎮 2048-Player: Hybrid AI Automation Project

DQN(Deep Q-Network) 강화학습과 Expectimax 알고리즘을 결합하여 2048 게임을 자동 플레이하고, 실시간 모니터링 및 학습 기능을 제공하는 풀스택 AI 자동화 프로젝트입니다.

---

## 🚀 Key Features
* **Hybrid AI Strategy**: 고전적인 탐색 알고리즘(Expectimax)을 통한 데이터 수집과 최신 강화학습(DQN) 모델의 병행 사용.
* **Computer Vision Integration**: Win32 API를 활용한 실시간 화면 캡처 및 Tesseract OCR 기반의 스코어 추출.
* **Real-time Dashboard**: Flask-SocketIO를 활용하여 AI의 현재 상태, 보드 상황, 학습 로그를 실시간으로 웹 UI에 동기화.
* **Automated Pipeline**: [데이터 수집 (Expectimax)] → [모델 학습 (PyTorch)] → [자동 플레이 (DQN)]로 이어지는 엔드 투 엔드 파이프라인.

---

## 🛠 Tech Stack
### **Languages & Frameworks**
* **Language**: Python 3.x
* **AI/ML**: PyTorch (Deep Learning), NumPy
* **Backend**: Flask, Flask-SocketIO (WebSocket)
* **Frontend**: HTML5, CSS3 (Modern Flat UI), JavaScript
* **CV/OCR**: OpenCV, Tesseract OCR

### **Infrastructure & Tools**
* **OS Interface**: Win32 API (GUI 컨트롤), ADB (Android Debug Bridge)
* **Environment**: Dotenv (.env configuration)

---

## ⚙️ Logic Workflow
### **1. 데이터 수집 (Collect)**
* **Expectimax 알고리즘**: 탐색 알고리즘을 사용하여 현재 상태에서 최적의 수를 계산합니다.
* **Dataset 구축**: 탐색 과정에서 발생한 상태와 그에 따른 행동 데이터를 추출하여 학습용 데이터셋을 생성합니다.

### **2. 학습 (Training)**
* **DQN 모델 학습**: 수집된 데이터셋을 PyTorch의 DQN 모델에 로드하여 학습을 진행합니다.
* **모델 아카이빙**: 최신 가중치가 적용된 모델 파일이 갱신됩니다.

### **3. 실행 (Play)**
* **실시간 추론**: 학습된 DQN 모델이 현재 게임보드 상태를 분석합니다.
* **자동 제어**: 예측된 Q-value 중 가장 확률이 높은 방향으로 게임 컨트롤 명령을 전달하여 자동 플레이를 수행합니다.

--- 

## 🏗 System Architecture
1. **Perception Layer (`perception.py`, `ocr.py`)**
    * 게임 윈도우 핸들을 캡처하여 ROI(Region of Interest)를 추출합니다.
    * 보드의 숫자 상태를 행렬(4x4) 데이터로 변환하고 OCR을 통해 점수를 인식합니다.
2. **Logic Layer (`algorithm.py`, `model.py`)**
    * **Expectimax**: 높은 점수를 얻기 위한 최적의 경로를 탐색하여 학습용 데이터를 생성합니다.
    * **DQN Model**: PyTorch 기반 신경망 모델이 현재 보드 상태를 입력받아 4가지 액션(Up, Down, Left, Right) 중 최적의 Q-value를 예측합니다.
3. **Training Layer (`training.py`)**
    * 수집된 데이터를 바탕으로 Batch 단위 학습을 수행하고 모델을 강화하고 아카이빙합니다.
4. **Application Layer (`app.py`, `index.html`)**
    * 멀티스레딩을 통해 제어 로직과 웹 서버를 분리 운영하며, WebSocket으로 실시간 데이터 스트리밍을 구현합니다.

---

## 📂 Project Structure
```text
2048 Player
 ├── debug/              # OCR 및 보드 캡처 디버깅용 이미지/로그
 ├── model/              # PyTorch 모델(.pth) 및 학습 데이터 아카이브
 ├── static/             # Frontend 라이브러리 (socket.io.min.js)
 ├── templates/          # Web Dashboard UI (index.html)
 ├── algorithm.py        # Expectimax 알고리즘 구현
 ├── app.py              # Main Flask-SocketIO 서버 (Control Center)
 ├── model.py            # DQN Neural Network 구조 정의 (PyTorch)
 ├── ocr.py              # Tesseract 기반 텍스트 인식 로직
 ├── perception.py       # 화면 캡처 및 이미지 전처리 로직
 ├── training.py         # 모델 학습 및 검증 파이프라인
 └── requirements.txt    # 의존성 패키지 리스트  
  
  
