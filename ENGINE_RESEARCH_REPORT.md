# 🏗️ 자체 제작 Web BIM Viewer 개발 가능성 검토 및 구현 리포트

## 1. 개요 (Background)
**목표:** 상용 솔루션 없이 Revit 모델(RVT)을 웹상에서 시각화할 수 있는 **자체 엔진(In-house Engine)** 구현 가능성 조사 및 프로토타입 개발.
**핵심 과제:**
1. Revit 데이터를 외부 포맷(glTF, JSON)으로 자동 추출하는 파이프라인 구축.
2. 대용량 BIM 데이터를 웹에서 끊김 없이(60fps) 렌더링하기 위한 최적화 기술 검증.

---

## 2. 현재 구현 현황 (Phase 1: MVP) (**[리서치 과정 gist](https://gist.github.com/yezzero/17bbe46a4b9af0cd953e37cae8f04928)**)
현재 **End-to-End 자동화 파이프라인**의 프로토타입 구축을 완료했습니다. Revit이 설치된 로컬 환경에서 스크립트 실행 한 번으로 웹 뷰어까지 데이터가 연결됩니다.

### 2.1. 아키텍처 (Architecture)
* **Extraction:** Revit API (C#)를 활용하여 형상 정보(Geometry)와 속성 정보(Property)를 분리 추출.
* **Automation:** Python 스크립트가 Revit을 **Headless(UI 미사용)** 모드처럼 제어하여 변환 과정 자동화.
* **Visualization:** Three.js 기반의 웹 뷰어를 통해 3D 형상 및 메타데이터 시각화.

### 2.2. 기술 스택 (Tech Stack)
| 구분 | 기술 | 설명 |
| :--- | :--- | :--- |
| **Revit Plugin** | **C# .NET 4.8** | `IExternalDBApplication`을 이용하여 Revit 실행 시 DB 레벨에서 데이터 추출 |
| **Automation** | **Python 3.9+** | `subprocess` 및 `pyautogui`를 활용한 Revit 자동 실행 및 보안 팝업 우회 |
| **Web Viewer** | **Three.js** | WebGL 기반 3D 렌더링, `Revit2glTF` 오픈소스 기반 변환 로직 적용 |

### 2.3. 디렉토리 구조
```
📦 DTCustomEngine
├── 📄 config.json      # 통합 설정 파일 (경로, 파일명 등)
├── 📂 RevitAddin       # C# 데이터 추출 플러그인
├── 📂 Automation       # Python 자동화 파이프라인 (pipeline.py)
└── 📂 WebViewer        # Three.js 시각화 뷰어
    └── 📂 models       # 변환된 glTF, JSON 자동 저장소
```


### 2.4. 작동 흐름 (Workflow)
전체 파이프라인은 **'실행 → 추출 → 저장 → 시각화'**의 단계로 자동 수행됩니다.

1.  **Pipeline Initiate:** 개발자가 터미널에서 파이썬 자동화 스크립트(`python pipeline.py`)를 실행합니다.
2.  **Revit Execution:** 스크립트가 `Revit.exe`를 실행하고, 로딩 중 발생하는 보안 팝업 등을 자동으로 처리하여(Auto-click) 애드인 로드 환경을 조성합니다.
3.  **Data Extraction:** Revit 구동 직후 자체 개발한 애드인(`AutoRunner`)이 트리거되어, 3D 형상 정보는 **glTF**로, 속성 정보는 **JSON**으로 분리 추출합니다.
4.  **Artifact Storage:** 추출된 결과물은 `config.json`에 정의된 경로인 `WebViewer/models` 디렉터리에 자동으로 저장됩니다.
5.  **Visualization:** 웹 뷰어(Three.js)가 생성된 최신 모델 파일을 로드하여 브라우저상에 즉시 시각화합니다.

---

## 3. 최적화 및 고도화 계획 (Phase 2: Master Plan)
현재 MVP 모델은 소규모 파일 처리에 적합하나, **초대형 BIM 데이터(Enterprise Level)**를 처리하기 위해 다음과 같은 최적화 로드맵을 수립했습니다.

### 3.1. 형상 데이터 경량화 (Geometry Optimization)
**문제점:** 원본 glTF 파일은 텍스트 기반이므로 용량이 크고 로딩이 느림.
**해결방안:** **Draco 압축 알고리즘** 적용.
* **Action:** `gltf-pipeline`을 도입하여 메쉬 데이터를 바이너리(`.glb`)로 병합하고 압축.
* **예상 효과:** 파일 용량 **90~95% 감소** (100MB → 5MB 수준).

```
bash
# 파이프라인에 추가될 명령어 예시
gltf-pipeline -i model.gltf -o model.glb --draco.compressionLevel 10 --binary
```

### 3.2. 렌더링 성능 가속 (Rendering Acceleration)
**문제점:** 객체 수가 수천 개 이상일 때 마우스 오버(Raycasting) 및 화면 회전 시 프레임 저하.
**해결방안:**
1.  **Three-Mesh-BVH:** 공간 분할 트리(BVH)를 적용하여 마우스 충돌 감지 속도를 물리적으로 가속.
2.  **Post-processing Shader:** CPU 연산(EdgesGeometry) 대신 GPU 셰이더를 사용하여 외곽선(Outline) 렌더링 부하 제거.

### 3.3. 속성 데이터 조회 속도 개선 (Data Query Performance)
**문제점:** 수십만 개의 객체 정보를 담은 JSON 파싱 시 브라우저 멈춤 현상 발생.
**해결방안:** **Parquet + DuckDB** 아키텍처 도입.
* **Action:** JSON을 컬럼 기반 압축 포맷인 `Parquet`로 변환하고, 브라우저 내장 SQL 엔진인 `DuckDB-Wasm`으로 쿼리 수행.
* **예상 효과:** 대용량 데이터 검색 시 0.1초 이내 응답.

```
python
# Python 파이프라인 추가 예정 로직
import pandas as pd
df = pd.read_json("walls.json")
df.to_parquet("walls.parquet", compression='brotli')
```

---

## 4. 결론 및 기대 효과
본 리서치를 통해 자체 엔진 개발이 기술적으로 충분히 가능함을 확인했습니다. Phase 2 최적화 기술(Draco, BVH, DuckDB)을 적용할 경우, 상용 뷰어에 준하는 성능을 웹 환경에서 구현할 수 있을 것으로 기대됩니다.

* **용량:** 원본 대비 95% 절감
* **속도:** 60FPS 안정적 유지 (BVH 가속)
* **데이터:** 실시간 SQL 질의 가능 (DuckDB)

---

