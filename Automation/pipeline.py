import os
import shutil
import subprocess
import time
import json
import pyautogui
import pygetwindow as gw
import sys

# ==========================================
# [설정] 프로젝트 루트의 config.json 에서 일괄 로드
# ==========================================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
CONFIG_PATH = os.path.join(PROJECT_ROOT, "config.json")

def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

# ==========================================
# [기능 0] C# 애드인 빌드 (dotnet CLI)
# ==========================================
def build_addin(config):
    print(f"[0/4] C# 애드인 빌드 및 Config 갱신 (dotnet)...")
    
    # config.json에서 솔루션 경로 가져오기
    solution_rel_path = config['build']['solutionPath']
    solution_path = os.path.join(PROJECT_ROOT, solution_rel_path)

    # 명령어: dotnet build -c Debug
    # (이 과정에서 .csproj 설정에 의해 config.json이 DLL 폴더로 자동 복사됨)
    command = ["dotnet", "build", solution_path, "-c", "Debug"]

    try:
        # 빌드 실행 (로그가 너무 길면 stdout=subprocess.DEVNULL 추가)
        subprocess.run(command, check=True)
        print("   - ✅ 빌드 성공 (DLL 및 config.json 갱신 완료)")
    except subprocess.CalledProcessError as e:
        print(f"❌ 빌드 실패! (Exit Code: {e.returncode})")
        print("   - 소스코드나 config.json 경로를 확인해주세요.")
        sys.exit(1)
    except FileNotFoundError:
        print("❌ 오류: 'dotnet' 명령어를 찾을 수 없습니다.")
        sys.exit(1)

# ==========================================
# [자동화 로직 시작]
# ==========================================
def run_pipeline():
    print("------------------------------------------------")
    print("🚀 BIM 자동화 파이프라인을 가동합니다.")
    print("------------------------------------------------")

    config = load_config()

    # ★ [Step 0] 여기서 빌드를 먼저 합니다!
    # 그래야 최신 코드가 반영되고, 최신 config.json이 DLL 옆으로 갑니다.
    build_addin(config)

    # 설정 변수 로드
    # (config.json 구조에 따라 exePath가 없으면 installPath + Revit.exe 조합 사용)
    if "exePath" in config["revit"]:
        revit_path = config["revit"]["exePath"]
    else:
        revit_path = os.path.join(config["revit"]["installPath"], "Revit.exe")

    target_rvt_file = config["revit"]["targetRvtFile"]
    out = config["output"]
    
    # 웹 뷰어 경로 설정
    web_server_path = os.path.join(PROJECT_ROOT, "WebViewer", "models")
    CONFIG_FOR_WEB = "config.json"
    files_to_move = [out["gltf"], out["gltfBin"], out["semanticTwinJson"]]

    # [Step 1] 웹뷰어용 Config 복사
    os.makedirs(web_server_path, exist_ok=True)
    shutil.copy(CONFIG_PATH, os.path.join(web_server_path, CONFIG_FOR_WEB))
    print(f"[1/4] 웹 뷰어 설정 파일 복사 완료")

    # [Step 2] 청소 (기존 모델 파일 삭제)
    print(f"   - 기존 데이터 청소 중...")
    for file_name in files_to_move:
        web_file = os.path.join(web_server_path, file_name)
        if os.path.exists(web_file):
            os.remove(web_file)

    # [Step 3] Revit 실행
    print(f"[2/4] Revit 실행 중... (유령 모드 👻)")
    print(f"   - 대상: {target_rvt_file}")

    if not os.path.exists(target_rvt_file):
        print(f"❌ 오류: RVT 파일을 찾을 수 없습니다: {target_rvt_file}")
        return

    process = subprocess.Popen([revit_path, target_rvt_file])

    # --- 보안 경고창 처리 ---
    print("   - 🛡️ 보안 경고창 감시 시작 (최대 60초 대기)...")
    for i in range(30): 
        time.sleep(2)
        target_titles = ["보안 - ", "Security - "]
        windows = gw.getAllTitles()
        found_security_window = False
        
        for title in windows:
            if any(t in title for t in target_titles):
                print(f"   - 🚨 보안 경고창 발견! ({title})")
                try:
                    win = gw.getWindowsWithTitle(title)[0]
                    if not win.isActive: win.activate()
                except: pass
                
                time.sleep(1.0)
                pyautogui.press(['left', 'left', 'left']) 
                time.sleep(0.5)
                pyautogui.press('enter')
                print("   - 👉 '항상 로드' 입력 완료.")
                found_security_window = True
                break
        
        if found_security_window: break
        if process.poll() is not None: break

    # [Step 4] 대기
    print(f"[3/4] 데이터 추출 대기 중... (Revit 종료 대기)")
    process.wait()
    print("   - Revit 종료 감지됨!")

    # [Step 5] 결과 확인
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
    if success_count >= 2:
        print("🎉 자동화 성공! 웹 뷰어를 확인하세요.")
    else:
        print(f"💥 일부 실패! 출력 경로({web_server_path})의 error.txt를 확인하세요.")
    print("------------------------------------------------")

if __name__ == "__main__":
    run_pipeline()
    input("엔터 키를 누르면 종료합니다...")