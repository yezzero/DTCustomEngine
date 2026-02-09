import os
import shutil
import subprocess
import time
import json
import pyautogui
import pygetwindow as gw

# ==========================================
# [설정] 프로젝트 루트의 config.json 에서 일괄 로드
# ==========================================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
CONFIG_PATH = os.path.join(PROJECT_ROOT, "config.json")

def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

web_server_path = os.path.join(PROJECT_ROOT, "WebViewer", "models")
CONFIG_FOR_WEB = "config.json"   # WebViewer/models 에 복사할 이름

# ==========================================
# [자동화 로직 시작]
# ==========================================

def run_pipeline():
    print("------------------------------------------------")
    print("🚀 BIM 자동화 파이프라인을 가동합니다.")
    print("------------------------------------------------")

    config = load_config()
    revit_path = config["revit"]["exePath"]
    target_rvt_file = config["revit"]["targetRvtFile"]
    out = config["output"]
    files_to_move = [out["gltf"], out["gltfBin"], out["semanticTwinJson"]]

    # 웹뷰어가 config를 읽을 수 있도록 복사 (Revit 애드인은 DLL 옆 config.json 사용)
    os.makedirs(web_server_path, exist_ok=True)
    shutil.copy(CONFIG_PATH, os.path.join(web_server_path, CONFIG_FOR_WEB))

    # 1. 청소 단계 (Clean) — WebViewer/models 기존 출력 파일만 삭제
    print(f"[1/4] 기존 데이터 청소 중...")
    for file_name in files_to_move:
        web_file = os.path.join(web_server_path, file_name)
        if os.path.exists(web_file):
            os.remove(web_file)

    # 2. Revit 실행 (Execution)
    print(f"[2/4] Revit 실행 중... (유령 모드 👻)")
    print(f"   - 대상: {target_rvt_file}")

    if not os.path.exists(target_rvt_file):
        print(f"❌ 오류: RVT 파일을 찾을 수 없습니다: {target_rvt_file}")
        return

    # subprocess를 이용해 Revit을 켭니다.
    # Revit은 켜지자마자 우리가 만든 DLL(AutoRunner)에 의해 작업 후 자동 종료됩니다.
    process = subprocess.Popen([revit_path, target_rvt_file])

    # ========================================================
    # ★ 보안 경고창 자동 처리 (Auto-Clicker)
    # ========================================================
    print("   - 🛡️ 보안 경고창 감시 시작 (최대 60초 대기)...")
    
    # 60초 동안 반복하면서 창이 뜨는지 확인
    for i in range(30): 
        time.sleep(2)  # 2초 간격으로 확인
        
        # Revit 2024의 보안 창 제목 (한글/영문 모두 대응)
        # 보통 "보안 - 서명되지 않은 애드인" 또는 "Security - Unsigned Add-in"
        target_titles = ["보안 - ", "Security - "]
        
        # 현재 열린 모든 창 가져오기
        windows = gw.getAllTitles()
        found_security_window = False
        
        for title in windows:
            # 창 제목에 '보안'이나 'Security'가 포함되어 있다면
            if any(t in title for t in target_titles):
                print(f"   - 🚨 보안 경고창 발견! ({title})")
                
                # 해당 창을 맨 앞으로 가져오기
                try:
                    win = gw.getWindowsWithTitle(title)[0]
                    if not win.isActive:
                        win.activate()
                except:
                    pass
                
                time.sleep(1.0) # 창이 뜨고 나서 확실하게 입력을 받을 때까지 1초 대기

                # 왼쪽으로 3번 이동 (제일 왼쪽 버튼이 '항상 로드'임)
                pyautogui.press(['left', 'left', 'left']) 
                time.sleep(0.5)
                pyautogui.press('enter')
                
                print("   - 👉 '항상 로드' (방향키+엔터) 입력 완료.")
                found_security_window = True
                break
        
        if found_security_window:
            break
            
        # (옵션) 만약 Revit이 이미 로딩이 끝나서 꺼졌다면 루프 종료
        if process.poll() is not None:
            break

    # 3. 대기 (Wait)
    print(f"[3/4] 데이터 추출 대기 중... (Revit이 꺼질 때까지 기다립니다)")
    process.wait()  # Revit이 꺼질 때까지 파이썬은 여기서 멈춰있습니다.
    print("   - Revit 종료 감지됨!")

    # 4. 확인 (Revit이 config.output.dir = WebViewer/models 에 직접 저장했으므로 이동 없음)
    print(f"[4/4] 결과물 확인 중... ({web_server_path})")
    success_count = 0
    for file_name in files_to_move:
        path = os.path.join(web_server_path, file_name)
        if os.path.exists(path):
            print(f"   - ✅ 확인: {file_name}")
            success_count += 1
        else:
            print(f"   - ⚠️ 파일이 없습니다: {file_name}")

    print("------------------------------------------------")
    if success_count >= 2:  # gltf + bin + json 중 최소 2개 이상이면 성공
        print("🎉 자동화 성공! 웹 뷰어를 확인하세요.")
    else:
        print(f"💥 일부 실패! 출력 경로({web_server_path})에 error.txt가 있는지 확인하세요.")
    print("------------------------------------------------")

if __name__ == "__main__":
    run_pipeline()
    # 창이 바로 꺼지는 걸 방지하기 위해 입력 대기
    input("엔터 키를 누르면 종료합니다...")
