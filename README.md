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
├── 📄 config.json      # ★ 출력 경로·Revit 경로·빌드 솔루션 경로 등 (이 파일만 수정하면 됨)
├── 📂 RevitAddin       # C# Revit 애드인 (HelloRevit.slnx — dotnet build / pipeline으로 빌드)
├── 📂 Automation       # 파이썬 자동화 스크립트 (pipeline.py: 빌드 → Revit 실행 → 결과 확인)
├── 📂 WebViewer        # 웹 뷰어 (index.html)
│   └── 📂 models       # 변환된 glTF, JSON 파일이 저장되는 곳 (gitignore 처리됨)
└── 📂 SampleModels     # 테스트용 Revit 샘플 파일 (.rvt)
```

### ⚙️ 설정 변경 (config.json)
**파일 경로나 출력 파일 이름을 바꾸고 싶으면 프로젝트 루트의 `config.json`만 수정하면 됩니다.**  
`revit`(실행 경로·대상 RVT), `output`(출력 폴더·glTF/JSON 파일명), `build.solutionPath`(C# 솔루션 경로, 예: `RevitAddin/HelloRevit/HelloRevit.slnx`) 등이 한 곳에 정의되어 있으며, 파이프라인·애드인·웹 뷰어가 이 설정을 공유합니다.

## ✅ Prerequisites
이 프로젝트를 실행하기 위해 다음 환경이 필요합니다.
- **Autodesk Revit 2024** (필수)
- **.NET SDK** (dotnet CLI — `dotnet build`로 C# 애드인 빌드용, Visual Studio 없이 파이프라인 빌드 가능)
- **Python 3.9+**
- **Visual Studio 2022** (선택) — 참조 경로 수정 등이 필요할 때만 사용

## ⚙️ Setup & Installation

### 1. 프로젝트 클론 및 필수 라이브러리 설치
```bash
git clone https://github.com/yezzero/DTCustomEngine.git
cd 레포지토리명
pip install -r requirements.txt
```

### 2. 라이브러리 참조 설정 (Check References)
이 프로젝트는 Revit API를 참조합니다. `.csproj`에 이미 Revit 2024 기본 경로(`C:\Program Files\Autodesk\Revit 2024\`)가 설정되어 있습니다. Revit을 다른 경로에 설치했다면 `RevitAddin/HelloRevit/HelloRevit/HelloRevit.csproj`의 `HintPath`를 수정하세요. Visual Studio에서 수동으로 바꾸려면 `RevitAddin/HelloRevit/HelloRevit.slnx`를 열고, 참조(References)에서 `RevitAPI.dll`, `RevitAPIUI.dll` 경로를 추가·수정한 뒤 **로컬 복사(Copy Local): False**로 두면 됩니다.

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
**Visual Studio에서 별도로 빌드할 필요 없습니다.** 아래 **How to Run**에서 `python Automation/pipeline.py`를 실행하면, 파이프라인이 먼저 `dotnet build`로 C# 애드인을 빌드한 뒤 Revit을 실행합니다. `.cs` 파일만 수정했다면 파이프라인을 다시 실행하면 자동으로 최신 코드가 빌드·반영됩니다.

### 5. 모델 추가
- `SampleModels` 디렉터리에 `.rvt` 파일을 두거나, 원하는 위치에 샘플 `.rvt` 파일을 둡니다.
- 그 경로를 `config.json`의 `revit.targetRvtFile` 항목에 작성합니다.

## 🚀 How to Run

### 1. 파이프라인 실행
파이썬 스크립트가 **먼저 C# 애드인을 `dotnet build`로 빌드**한 뒤, Revit을 '유령 모드'로 실행하여 데이터를 추출합니다. `.cs` 수정 후 Visual Studio에서 빌드할 필요 없이, 파이프라인만 다시 실행하면 됩니다.

1. `config.json` 내부의 설정 변수들을 본인 환경에 맞게 수정합니다. (솔루션 경로는 `build.solutionPath`: `RevitAddin/HelloRevit/HelloRevit.slnx` 등)
2. 프로젝트 루트 또는 `Automation` 폴더에서 스크립트 실행:
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
Revit 설치 경로가 기본 경로와 다를 수 있습니다. `RevitAddin/HelloRevit/HelloRevit/HelloRevit.csproj`를 열어 `<Reference>`의 `HintPath`를 본인 Revit 경로(예: `C:\Program Files\Autodesk\Revit 2024\`)로 수정하세요. Visual Studio를 쓰는 경우에는 `RevitAddin/HelloRevit/HelloRevit.slnx`를 열고 참조(References)에서 `RevitAPI.dll`, `RevitAPIUI.dll` 경로를 추가·수정한 뒤 **로컬 복사(Copy Local): False**로 두면 됩니다.
