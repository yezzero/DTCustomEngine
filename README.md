# 🏗️ Revit to Web BIM Pipeline

Revit 모델(RVT)을 자동으로 추출하여, 웹상에서 가볍게 시각화(Three.js)하는 **자동화 파이프라인(End-to-End)** 프로젝트입니다.

## 🛠️ Tech Stack
- **Revit API (C# .NET 4.8):** 모델 형상(Geometry) 및 속성(Property) 데이터 추출
  - **[Revit2glTF](https://github.com/McCulloughRT/Revit2glTF):** glTF 내보내기 참조 (오픈소스)
  - **Newtonsoft.Json:** JSON 직렬화 (NuGet 패키지)
- **Python:** Revit 자동 실행(Automation) 및 최적화 파이프라인
- **Three.js:** BVH 가속화 및 Post-processing(Outline)이 적용된 고성능 웹 뷰어

## 📂 Project Structure

```
📦 DTCustomEngine
├── 📄 config.json      # ★ 출력 파일명·Revit 경로 등 설정 (이 파일만 수정하면 됨)
├── 📂 RevitAddin       # C# Revit 애드인 소스 코드 (Visual Studio 솔루션)
├── 📂 Automation       # 파이썬 자동화 스크립트 (pipeline.py)
├── 📂 WebViewer        # 웹 뷰어 (index.html)
│   └── 📂 models       # 변환된 glTF, JSON 파일이 저장되는 곳 (gitignore 처리됨)
└── 📂 SampleModels     # 테스트용 Revit 샘플 파일 (.rvt)
```

### ⚙️ 설정 변경 (config.json)
**파일 경로나 출력 파일 이름을 바꾸고 싶으면 프로젝트 루트의 `config.json`만 수정하면 됩니다.**  
Revit 실행 경로, 대상 RVT 경로, glTF/JSON 출력 파일명 등이 한 곳에 정의되어 있으며, 파이프라인·애드인·웹 뷰어가 이 설정을 공유합니다.

## ✅ Prerequisites
이 프로젝트를 실행하기 위해 다음 환경이 필요합니다.
- **Autodesk Revit 2024** (필수)
- **Visual Studio 2022** (.NET Framework 4.8 개발 환경)
- **Python 3.9+**

## ⚙️ Setup & Installation

### 1. 프로젝트 클론 및 필수 라이브러리 설치
```bash
git clone https://github.com/yezzero/DTCustomEngine.git
cd 레포지토리명
pip install -r requirements.txt
```

### 2. 라이브러리 참조 설정 (Check References)
이 프로젝트는 Revit API를 참조합니다. 처음 열었을 때 참조 경로가 깨져있다면 다시 연결해야 합니다.

1. Visual Studio에서 `RevitAddin/HelloRevit.sln`을 엽니다.
2. **참조(References)** 우클릭 > **참조 추가(Add Reference)**
3. Revit 2024 설치 경로(`C:\Program Files\Autodesk\Revit 2024\`)에서 아래 두 파일을 추가합니다.
   - `RevitAPI.dll`
   - `RevitAPIUI.dll`
4. **★중요 설정:** 추가된 두 파일의 속성(Properties) 창에서 **로컬 복사(Copy Local)** 값을 **False**로 변경합니다. (빌드 오류 방지용)

### 3. 애드인 등록 (Register Add-in - 최초 1회)
Revit이 빌드된 DLL을 인식할 수 있도록 `.addin` 매니페스트 파일을 연결합니다. **이 과정은 한 번만 수행하면 됩니다.**

1. 메모장을 열어 아래 코드를 붙여넣습니다. 단, `<Assembly>` 태그 안의 경로를 **현재 내 컴퓨터의 DLL 생성 경로**로 수정합니다.

```xml
<?xml version="1.0" encoding="utf-8"?>
<RevitAddIns>
  <AddIn Type="DBApplication">
    <Name>MyHeadlessEngine</Name>
    
    <Assembly>C:\Users\yeyeo\Desktop\DTCustomEngine\RevitAddin\HelloRevit\HelloRevit\bin\x64\Debug\HelloRevit.dll</Assembly>
    
    <AddInId>A1B2C3D4-E5F6-7890-ABCD-1234567890AB</AddInId>
    
    <FullClassName>MyRevitExtractor.AutoRunner</FullClassName>
    
    <Text>자동화 엔진</Text>
    <VendorId>MyCompany</VendorId>
    <VendorDescription>My Custom Engine</VendorDescription>
  </AddIn>
</RevitAddIns>
```

2. 파일을 `HelloRevit.addin`이라는 이름으로 아래 **Revit 애드인 폴더**에 저장합니다.
   - 경로: `C:\ProgramData\Autodesk\Revit\Addins\2024\`
   - (참고: ProgramData 폴더는 숨겨져 있을 수 있습니다.)

### 4. 빌드 (Build)
1. 상단 메뉴에서 **빌드(Build) > 솔루션 빌드(Build Solution)**를 클릭합니다. (단축키: `Ctrl + Shift + B`)
2. 이제 Revit을 실행하면 자동으로 플러그인이 로드됩니다.

### 5. 모델 추가
- `SampleModels` 디렉터리에 `.rvt` 파일을 두거나, 원하는 위치에 샘플 `.rvt` 파일을 둡니다.
- 그 경로를 `config.json`의 `revit.targetRvtFile` 항목에 작성합니다.

## 🚀 How to Run

### 1. 파이프라인 실행
파이썬 스크립트가 Revit을 '유령 모드'로 실행하여 데이터를 추출합니다.

1. `config.json` 내부의 설정 변수들을 본인 환경에 맞게 수정합니다.
2. 스크립트 실행:
   ```bash
   python Automation/pipeline.py
   ```
   ⚠️ **주의사항 (Caution):** 스크립트가 실행되고 Revit이 로딩되는 동안(약 10~30초) **마우스나 키보드를 건드리지 마세요.**
      - 파이썬이 마우스 제어권을 가져가서 보안 경고창을 클릭합니다.
      - 이 때 마우스를 움직이면 클릭 위치가 어긋나 자동화가 실패할 수 있습니다.

### 2. 웹 뷰어 확인
1. VS Code에서 **Live Server** 확장 프로그램을 사용하여 `WebViewer/index.html`을 엽니다.
2. 브라우저에서 변환된 3D 모델과 속성 정보를 확인합니다.


## ❓ 트러블슈팅 (Troubleshooting)
**1. 빌드 시 "참조를 찾을 수 없습니다" 오류가 뜬다면?**
사용자의 Revit 설치 경로가 기본 경로와 다를 수 있습니다.
1. 솔루션 탐색기에서 **참조(References)** 하위의 `RevitAPI`, `RevitAPIUI`에 노란색 경고등(⚠️)이 있는지 확인합니다.
2. 경고가 있다면 우클릭 후 **제거(Remove)**합니다.
3. **참조 추가(Add Reference)**를 눌러 본인의 Revit 설치 경로(보통 `C:\Program Files\Autodesk\Revit 2024`)에서 `RevitAPI.dll`, `RevitAPIUI.dll`을 다시 추가하세요.
4. 두 파일의 속성에서 **로컬 복사(Copy Local): False** 설정을 잊지 마세요.

**2. 빌드 시 "프로세서 아키텍처 MSIL과 RevitAPI 참조의 AMD64가 일치하지 않습니다" 경고가 뜬다면?**
- **원인:** Revit은 64비트(AMD64) 전용 프로그램인데, 프로젝트가 Any CPU(MSIL)로 설정되어 있어 발생합니다. "Revit은 64비트 전용인데, 프로젝트를 범용(Any CPU)으로 빌드하고 있다"는 의미의 경고입니다. 무시해도 실행되는 경우가 많지만, x64로 맞추는 것이 권장됩니다.
- **해결 방법:** 프로젝트 대상을 **x64**로 설정합니다.
  1. Visual Studio 상단 메뉴에서 **[빌드(Build)]** → **[구성 관리자(Configuration Manager)]**를 클릭합니다. (또는 상단 툴바의 Debug 옆 **Any CPU** 드롭다운 → **[구성 관리자...]** 선택)
  2. **활성 솔루션 플랫폼(Active solution platform)** 드롭다운을 클릭 후 **\<새로 만들기...\>**를 선택합니다.
  3. **새 플랫폼(New platform)**에서 **x64**를 선택하고, '다음에서 설정 복사'는 **Any CPU**로 둔 뒤 **[확인]**을 누릅니다.
  4. 구성 관리자를 닫고, 상단 툴바가 **Debug / x64**로 바뀌었는지 확인한 뒤 **[빌드]** → **[솔루션 다시 빌드(Rebuild Solution)]**를 실행합니다.
