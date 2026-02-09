using System;
using System.IO;
using System.Reflection;
using System.Linq;
using System.Collections.Generic;
using Autodesk.Revit.ApplicationServices;
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Events; // 이벤트 처리를 위해 추가
using Autodesk.Revit.UI;
using Autodesk.Revit.Attributes;
using Newtonsoft.Json.Linq;

namespace MyRevitExtractor
{
    // ★ 변경점 1: IExternalCommand 대신 IExternalDBApplication 사용
    // (이건 버튼용이 아니라, Revit 실행 시 자동 로드되는 앱용입니다)
    [Transaction(TransactionMode.Manual)]
    public class AutoRunner : IExternalDBApplication
    {
        // 1. Revit이 켜질 때 실행되는 함수
        public ExternalDBApplicationResult OnStartup(ControlledApplication application)
        {
            // "문서가 열리면 나를 불러줘"라고 이벤트 등록
            application.DocumentOpened += OnDocumentOpened;
            return ExternalDBApplicationResult.Succeeded;
        }

        // 2. Revit이 꺼질 때 실행되는 함수
        public ExternalDBApplicationResult OnShutdown(ControlledApplication application)
        {
            application.DocumentOpened -= OnDocumentOpened;
            return ExternalDBApplicationResult.Succeeded;
        }

        // 3. 문서가 열렸을 때 자동으로 실행될 함수 (여기가 핵심!)
        private void OnDocumentOpened(object sender, DocumentOpenedEventArgs e)
        {
            Document doc = e.Document;

            // 패밀리 파일이나 템플릿이면 무시
            if (doc.IsFamilyDocument) return;

            try
            {
                // ==========================================
                // 아까 짰던 추출 로직 (복사 붙여넣기)
                // ==========================================

                // 1. config는 DLL과 같은 폴더(빌드 시 config.json 복사됨). 출력 경로·파일명은 config에서 읽음.
                string addinDir = Path.GetDirectoryName(Assembly.GetExecutingAssembly().Location);
                string fallbackDir = Environment.GetFolderPath(Environment.SpecialFolder.Desktop);
                string configPath = Path.Combine(addinDir ?? fallbackDir, "config.json");
                string outputDir = fallbackDir;
                string gltfName = "model.gltf";
                string semanticTwinJsonName = "semantic_twin.json";
                if (File.Exists(configPath))
                {
                    try
                    {
                        var config = JObject.Parse(File.ReadAllText(configPath));
                        var output = config["output"];
                        if (output != null)
                        {
                            string dir = output["dir"]?.ToString();
                            if (!string.IsNullOrEmpty(dir)) outputDir = dir;
                            gltfName = output["gltf"]?.ToString() ?? gltfName;
                            semanticTwinJsonName = output["semanticTwinJson"]?.ToString() ?? semanticTwinJsonName;
                        }
                    }
                    catch { /* 실패 시 기본값 유지 */ }
                }
                string jsonPath = Path.Combine(outputDir, semanticTwinJsonName);

                // 2. 3D 뷰 찾기
                View3D view3D = new FilteredElementCollector(doc)
                    .OfClass(typeof(View3D))
                    .Cast<View3D>()
                    .FirstOrDefault(v => !v.IsTemplate && v.CanBePrinted);

                // JSON 추출 (간단 버전)
                var walls = new FilteredElementCollector(doc)
                    .OfCategory(BuiltInCategory.OST_Walls)
                    .WhereElementIsNotElementType()
                    .ToElements();

                List<string> dataList = new List<string>();
                foreach (Element elem in walls)
                {
                    string id = elem.Id.ToString();
                    string name = elem.Name;
                    // 간단 JSON 생성
                    dataList.Add($"{{\"id\": \"{id}\", \"name\": \"{name}\", \"length\": \"Unknown\"}}");
                }
                File.WriteAllText(jsonPath, "[" + string.Join(",", dataList) + "]");

                if (view3D != null)
                {
                    // [수정] OBJ 대신 glTF로 저장 (경로·파일명은 config 기준)
                    string fileName = gltfName;
                    string directory = outputDir;

                    // ★ McCulloughRT 라이브러리 사용
                    // (이 부분은 가져온 소스코드의 클래스 생성자에 맞춰야 합니다.)
                    // 보통 아래와 같은 식입니다.
                    var context = new glTFExportContext(doc, fileName, directory);

                    CustomExporter exporter = new CustomExporter(doc, context);
                    exporter.IncludeGeometricObjects = true;

                    // 재질까지 포함하려면 보통 true로 설정 (라이브러리마다 다름)
                    exporter.ShouldStopOnError = false;

                    exporter.Export(view3D);
                }

                // ==========================================
                // 작업 끝!
                // ==========================================
            }
            catch (Exception ex)
            {
                // 에러나면 로그 남기기 (출력 폴더 error.txt)
                File.WriteAllText(
                    Path.Combine(outputDir, "error.txt"),
                    ex.ToString()
                );
            }
            finally
            {
                // ★ 중요: 작업이 끝나면 Revit을 강제로 꺼버립니다.
                // (사용자 저장 여부를 묻지 않고 끔)
                Environment.Exit(0);
            }
        }
    }

    // (MyObjContext 클래스는 아까와 똑같이 아래에 붙여넣으세요. 생략함)
    class MyObjContext : IExportContext
    {
        private Document _doc;
        private StreamWriter _writer;
        private string _path;

        // OBJ 파일은 정점 번호가 파일 전체에서 계속 누적됩니다.
        private int _vertexOffset = 1;

        public MyObjContext(Document doc, string path)
        {
            _doc = doc;
            _path = path;
        }

        public bool Start()
        {
            _writer = new StreamWriter(_path);
            _writer.WriteLine("# Revit Extracted Model (Y-Up Fixed)");
            return true;
        }

        public void Finish()
        {
            _writer?.Close();
        }

        // 1. 요소가 시작될 때마다 "그룹 이름(ID)"을 붙여줍니다.
        public RenderNodeAction OnElementBegin(ElementId elementId)
        {
            if (elementId == ElementId.InvalidElementId) return RenderNodeAction.Proceed;

            Element elem = _doc.GetElement(elementId);
            if (elem == null) return RenderNodeAction.Skip;

            // 벽(Walls)만 추출
            if (elem.Category != null &&
                elem.Category.BuiltInCategory == BuiltInCategory.OST_Walls)
            {
                // ★ 핵심: OBJ 파일에 'o 객체ID'를 적어줍니다.
                // 이제 Three.js가 이걸 보고 "아, 여기서부턴 다른 물체구나"라고 인식합니다.
                _writer.WriteLine($"o {elementId}");
                return RenderNodeAction.Proceed;
            }

            return RenderNodeAction.Skip;
        }

        // 2. 실제 형상(메쉬)을 쓸 때 좌표를 돌려서 씁니다.
        public void OnPolymesh(PolymeshTopology node)
        {
            // 미터 변환 비율
            double scale = 0.3048;

            IList<XYZ> points = node.GetPoints();
            foreach (XYZ p in points)
            {
                // ★ 핵심: 좌표계 변환 (Revit Z-Up -> WebGL Y-Up)
                // Revit (X, Y, Z) ===> Web (X, Z, -Y)
                // 이렇게 하면 건물이 벌떡 일어섭니다.
                double newX = p.X * scale;
                double newY = p.Z * scale;      // Revit의 높이(Z)를 웹의 높이(Y)로
                double newZ = -p.Y * scale;     // Revit의 북쪽(Y)을 웹의 깊이(-Z)로

                _writer.WriteLine($"v {newX} {newY} {newZ}");
            }

            int numberOfFacets = node.NumberOfFacets;
            for (int i = 0; i < numberOfFacets; i++)
            {
                PolymeshFacet facet = node.GetFacet(i);
                // 정점 인덱스는 그대로 유지
                _writer.WriteLine($"f {facet.V1 + _vertexOffset} {facet.V2 + _vertexOffset} {facet.V3 + _vertexOffset}");
            }

            _vertexOffset += points.Count;
        }

        // --- 필수 구현 메서드들 (변경 없음) ---
        public bool IsCanceled() => false;
        public void OnRPC(RPCNode node) { }
        public void OnLight(LightNode node) { }
        public RenderNodeAction OnViewBegin(ViewNode node) => RenderNodeAction.Proceed;
        public void OnViewEnd(ElementId elementId) { }
        public RenderNodeAction OnFaceBegin(FaceNode node) => RenderNodeAction.Proceed;
        public void OnFaceEnd(FaceNode node) { }
        public void OnElementEnd(ElementId elementId) { }
        public RenderNodeAction OnInstanceBegin(InstanceNode node) => RenderNodeAction.Proceed;
        public void OnInstanceEnd(InstanceNode node) { }
        public RenderNodeAction OnLinkBegin(LinkNode node) => RenderNodeAction.Proceed;
        public void OnLinkEnd(LinkNode node) { }
        public void OnMaterial(MaterialNode node) { }
    }
}