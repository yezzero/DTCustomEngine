## 1️⃣ Revit API의 필연성

Revit 파일(`.rvt`)은 엑셀이나 JSON처럼 텍스트로 읽을 수 있는 파일이 아님. 복잡한 연산 로직이 포함된 **거대 데이터베이스**이자 **암호화된 블랙박스**임.

### 1.1. .rvt 파일의 구조 (OLE Structured Storage)

Revit은 Autodesk 고유의 바이너리 구조를 따름. 메모장으로 열면 해석 불가능한 기계어만 보임.

* **JSON:** 구조가 보임 (`{ "wall": ... }`).
* **RVT:** 구조가 안 보임 (바이너리 데이터).

Autodesk가 내부 구조(Spec)를 공개하지 않았음(Closed Source). 따라서 외부에서 파이썬 등으로 파일을 직접 읽어 데이터를 꺼내는 건 불가능함.

### 1.2. 파라메트릭(Parametric) 데이터의 특징

바이너리를 해독한다 해도 문제임. Revit은 **'결과값(형상)'**이 아니라 **'공식(로직)'**을 저장함.

* **일반 3D 툴:** 점, 선, 면의 좌표를 저장. (읽으면 바로 형상이 나옴)
* **Revit:** "1층에서 2층까지 벽을 세워라"는 명령어를 저장. (좌표가 파일에 없음)

**결론:** 이 '공식'을 계산해 형상을 만들어줄 **연산 엔진, 즉 Revit.exe**가 반드시 필요

### 1.3. 그래서 Revit API 사용이 필수

`.rvt` 파일을 강제로 뜯을 수 없으니 정식 통로인 **Revit API**를 써야 함.

1.  Revit API는 독립 실행 불가. **Revit이 켜져 있는 상태**에서만 작동함.
2.  Revit이 건물을 메모리에 로딩하고 연산을 끝내야, API를 통해 "벽의 좌표 줘"라고 요청 가능.
3.  그래서 **Add-in(DLL)** 형태로 만들어 Revit에 기생하는 구조가 됨.



## 2️⃣ 왜 콘솔 대신 무거운 Revit.exe를 썼나?

보통 자동화는 가벼운 콘솔(CLI)이 정석임. 하지만 우리는 **Revit.exe(GUI 버전)**를 통째로 실행하는 방식을 택함.

### 2.1. RevitCoreConsole 사용 불가 이유

`RevitCoreConsole.exe`라는 CLI 도구가 존재하긴 하나, 로컬 자동화엔 부적합함.

* **설치본 미포함:** 일반 데스크톱용 Revit 설치 시 포함되지 않음.
* **비공식 사용 위험:** Mock 등으로 우회 사용 시 매우 불안정하며 기능 제약이 많음.
* **호환성 및 법적 문제:** EULA(라이선스) 위반 소지가 있고, Revit 버전 업데이트 시 작동을 보장 못 함.

### 2.2. 해결책: "가짜 헤드리스(Fake Headless)" 전략

따라서 가장 확실한 **Revit.exe**를 쓰되, 사람이 쓰는 것처럼 보이지 않게 **"치고 빠지는"** 전략을 사용함.

1.  **자동 실행:** 배치 파일(.bat)로 Revit 실행.
2.  **납치:** 켜지자마자 우리 코드(`AutoRunner`)가 제어권 획득.
3.  **추출:** 사람의 클릭 과정을 코드로 처리.
4.  **자폭:** 작업 직후 `Environment.Exit(0)`으로 강제 종료.

사용자가 따로 건드릴 필요 없이, Revit 엔진을 완벽하게 구동하여 데이터를 뽑아내는 방식.

## 3️⃣ 애드인 코드 뜯어보기

이 코드는 크게 두 부분으로 나뉨.
1.  **AutoRunner:** Revit을 켜고 끄는 '관리자'.
2.  **MyObjContext:** 3D 형상을 가로채서 번역하는 '통역사'.

### 3.1. AutoRunner 클래스: "자동화의 지휘자"

Revit이 실행될 때(`OnStartup`)와 문서가 열릴 때(`OnDocumentOpened`) 무엇을 할지 정의함. `IExternalDBApplication` 인터페이스의 구조를 그대로 구현하여 백그라운드 앱으로 동작.

#### 주요 메서드 흐름

1.  **OnStartup (출근):**
    * Revit이 켜지자마자 실행됨.
    * `application.DocumentOpened += OnDocumentOpened;`
    * **의미:** "문서가 열리는 사건(Event)이 발생하면 나한테 알려줘."라고 예약.

2.  **OnDocumentOpened (작업 개시):**
    * 실제 파일이 열리면 자동으로 호출되는 함수. 여기가 **메인 로직**.
    * `config.json` 로드: 저장 경로와 파일 설정을 읽음.
    * `FilteredElementCollector`: DB에서 3D 뷰와 벽(Wall) 데이터를 수집.
    * `CustomExporter`: 3D 추출 시작 명령.

3.  **Environment.Exit(0) (퇴근):**
    * **핵심:** 모든 작업(JSON 저장, 3D 변환)이 끝나면 **즉시 프로세스 종료**.
    * 사용자에게 "저장하시겠습니까?" 묻지 않고 강제로 끔. (자동화를 위함함)

### 3.2. MyObjContext 클래스: "3D 통역사"

`IExportContext`를 상속받아, Revit이 화면에 렌더링하려는 정보를 중간에 가로챔(Hooking).

#### 주요 메서드 분석

1.  **OnElementBegin (객체 식별):**
    * Revit이 벽 하나를 그리기 직전에 호출됨.
    * `_writer.WriteLine($"o {elementId}");`
    * **의미:** OBJ 파일에 객체 ID를 기록함. 나중에 웹(Three.js)에서 "이 벽을 클릭했다"고 알기 위함.

2.  **OnPolymesh (형상 변환):**
    * 실제 3D 형상(점, 면) 데이터를 받는 곳.
    * **좌표계 변환 (Coordinate System Conversion):**
        * **Revit:** Z축이 높이 (Right-handed, Z-up).
        * **WebGL/Three.js:** Y축이 높이인 경우가 많음 (Right-handed, Y-up).
        * 여기서 $X, Y, Z$ 좌표를 $X, Z, -Y$ 등으로 치환하여 건물을 **"벌떡 일으켜 세우는"** 수학적 변환을 수행함.

### 3.3. 핵심 API 사용 이유

* **FilteredElementCollector:**
    * SQL의 `SELECT * FROM Walls`와 같음. 수만 개의 객체 중 원하는 것만 빠르게 필터링.
* **CustomExporter:**
    * Revit의 렌더링 파이프라인을 그대로 이용하므로, 복잡한 벽의 결합이나 구멍(Opening)이 뚫린 형상을 우리가 직접 계산할 필요 없이 **"보이는 그대로"** 추출 가능.

## 4️⃣ Revit 실행 시 벌어지는 일 (Add-in 로딩 메커니즘)

Revit 실행 시 플러그인(`HelloRevit.dll`)이 자동 로드되는 과정 요약.

### 4.1. 로딩 프로세스 (The Loading Pipeline)

1.  **탐색 (Scanning):** Revit이 실행되면 `Addins` 폴더 내의 `.addin` 파일들을 스캔함.
2.  **파싱 (Parsing):** `.addin` 내용을 읽어 DLL 위치와 실행할 클래스명을 파악함.
3.  **로드 (Loading):** 해당 경로의 DLL을 메모리에 올림. (이때부터 파일 잠김)
4.  **객체 생성 (Instantiation):** **리플렉션(Reflection)**으로 `AutoRunner` 클래스를 찾아 객체(`new`)를 생성함.
5.  **실행 (Execution):** `IExternalDBApplication` 인터페이스 확인 후 `OnStartup` 함수 호출. -> **이벤트 등록 완료.**

---

### 4.2. HelloRevit.addin 상세 분석 (Line-by-Line)

이 파일은 Revit에게 우리 프로그램의 **신원 정보**를 알려주는 **명세서(Manifest)**.

```xml
<?xml version="1.0" encoding="utf-8"?>
<RevitAddIns>
  <AddIn Type="DBApplication">
    <Name>MyHeadlessEngine</Name>
    <Assembly>C:\Users\...\HelloRevit.dll</Assembly>
    <AddInId>A1B2C3D4-E5F6-7890-ABCD-1234567890AB</AddInId>
    <FullClassName>MyRevitExtractor.AutoRunner</FullClassName>
    <Text>자동화 엔진</Text>
    <VendorId>MyCompany</VendorId>
    <VendorDescription>My Custom Engine</VendorDescription>
  </AddIn>
</RevitAddIns>
```

#### 각 태그별 역할 설명

* **`<RevitAddIns>`**: 루트 태그.
* **`<AddIn Type="DBApplication">`**:
    * **중요:** 플러그인 성격 정의.
    * `DBApplication`: UI 없이 백그라운드/DB 처리 전용. (가장 가볍게 실행 가능)
    * `Command`: 버튼 클릭용 1회성 명령어.
    * `Application`: 리본 메뉴 등 UI 포함 앱.
* **`<Name>`**: Revit 내부 관리용 이름.
* **`<Assembly>`**: **(핵심)** DLL 파일의 **절대 경로**. 틀리면 로딩 실패.
* **`<AddInId>`**: 플러그인 고유 ID (GUID). 전 세계 유일값이어야 함.
* **`<FullClassName>`**: **(핵심)** 실행 진입점(Entry Point) 클래스. `네임스페이스.클래스명` 형식 필수.
* **`<VendorId>`**: 개발사 ID.
* **`<VendorDescription>`**: 개발사 설명.