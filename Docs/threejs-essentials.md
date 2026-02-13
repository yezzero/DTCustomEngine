# Three.js 알아두면 좋은 것

> **Scope:** WebGL/WebGPU를 추상화하는 JavaScript 3D 라이브러리인 Three.js를 실무에 쓰기 위해 알아야 할 개념, API, 성능, 한계를 정리한 문서.

---

## 1. 개요

**Three.js**는 브라우저에서 3D 콘텐츠를 쉽게 만들기 위한 JavaScript 라이브러리다. WebGL은 점·선·삼각형만 그리는 저수준 API라서, 셰이더 작성·버퍼 관리·행렬 계산 등을 직접 하려면 코드가 길어진다. Three.js는 Scene, Light, Material, Texture, 3D 수학 등을 처리해 주므로, 개발자는 고수준 객체만 다루면 된다.

- **역할:** WebGL(및 WebGPU)을 내부에서 호출하는 **추상화 레이어**. WebGL/WebGPU를 "대체"하는 것이 아니라 그 위에 올라간다.
- **로딩:** r147부터 ES 모듈(`import * as THREE from 'three'`) 방식만 권장. `<script type="module">` 또는 번들러 사용.

---

## 2. 앱 구조 — Renderer, Scene, Camera

Three.js 앱은 **Renderer**, **Scene**, **Camera** 세 가지를 연결하는 구조다.

| 구성 요소 | 역할 |
| --------- | ----- |
| **Renderer** | `Scene`과 `Camera`를 받아, 카메라 **frustum** 안의 3D 장면을 2D 이미지로 그려 canvas에 출력한다. |
| **Scene** | 모든 3D 객체(Mesh, Light, Group 등)를 담는 **scene graph의 루트**. 배경색·안개 등도 여기서 설정한다. |
| **Camera** | 시점 정의. Scene graph에 넣지 않아도 동작한다. 넣으면 부모 기준으로 이동·회전한다. |

**Frustum:** PerspectiveCamera의 `fov`, `aspect`, `near`, `far`로 정해지는 "잘린 피라미드" 영역. 이 안에 있는 것만 그려진다.

- 카메라 기본: **-Z 방향**을 바라보고, **+Y**가 위.
- 첫 큐브를 보려면 `camera.position.z = 2`처럼 카메라를 원점에서 뒤로 빼면 된다.

---

## 3. Scene Graph (장면 그래프)

**Scene graph**는 노드들이 부모-자식으로 이어진 **계층 구조**다. 각 노드는 **로컬 공간(local space)**을 나타낸다. 자식의 위치·회전·스케일은 **부모 기준**으로 적용된다.

- **Object3D:** Geometry/Material이 없는 "빈" 노드. 그룹·피벗·궤도용으로 쓴다.
- **Mesh:** Geometry + Material을 가진 렌더 가능한 객체. Object3D를 상속한다.
- 자식은 부모를 따라 움직인다. 예: 차체에 바퀴를 자식으로 두면, 차체만 움직여도 바퀴가 함께 이동한다.
- 스케일이 있는 부모 아래 자식을 두면, 자식도 그 스케일을 물려받는다. "태양–지구–달" 예제에서는 스케일을 분리하려고 `Object3D`(solarSystem, earthOrbit, moonOrbit)를 두고, Mesh는 그 자식으로 넣는다.

**유용한 메서드**

- `object.add(child)` — 자식 추가
- `camera.lookAt(x, y, z)` — 카메라가 해당 점을 보도록 방향 설정
- `mesh.getWorldPosition(targetVector3)` — 월드 좌표 계산

---

## 4. Mesh = Geometry + Material

**Mesh**는 다음 세 가지의 조합이다.

1. **Geometry** — 형태 데이터(정점, 법선, UV 등)
2. **Material** — 표면 속성(색, 광택, 텍스처 등)
3. **위치·회전·스케일** — 부모 기준 변환 (Object3D에서 상속)

하나의 Geometry·Material을 여러 Mesh가 공유할 수 있다. 예: 같은 `BoxGeometry`와 같은 `MeshPhongMaterial`로 여러 큐브를 만들 수 있다.

### Geometry

- **내장 프리미티브:** `BoxGeometry`, `SphereGeometry`, `PlaneGeometry`, `CylinderGeometry`, `TorusGeometry` 등.
- **BufferGeometry:** 정점 데이터를 Typed Array로 갖는 형태. 기본 Geometry보다 메모리·성능에 유리. 커스텀 geometry나 로더 결과는 보통 BufferGeometry다.
- 커스텀 geometry 생성, 또는 파일에서 로드(OBJ, glTF 등) 가능.

### Material

- **MeshBasicMaterial:** 조명 무시. 항상 균일한 색/텍스처.
- **MeshPhongMaterial:** 조명 반응. 하이라이트 있음.
- **MeshStandardMaterial:** PBR(물리 기반). metalness, roughness 사용. 실사에 가깝게 쓰는 경우 많음.
- **MeshLambertMaterial:** 조명 반응, 하이라이트 없음.
- Material은 **Texture**를 참조할 수 있다 (색상, 법선, roughness 등).

---

## 5. 조명 (Lights)

- **AmbientLight:** 전역 환경광. 그림자 없음.
- **DirectionalLight:** 방향광(태양처럼). position과 target으로 방향 설정.
- **PointLight:** 한 점에서 사방으로 퍼지는 광원.
- **SpotLight:** 원뿔 형태 조명.

`MeshBasicMaterial`은 조명 영향을 받지 않는다. 조명을 쓰려면 `MeshPhongMaterial`, `MeshStandardMaterial` 등을 사용한다.

---

## 6. 텍스처·그림자

- **Texture:** 이미지 파일, canvas, 또는 다른 씬을 렌더한 결과(RenderTarget)를 쓸 수 있다.
- **그림자:** `renderer.shadowMap.enabled = true`, 광원/물체별 `castShadow`, `receiveShadow` 설정 필요. 성능 비용이 있으므로 필요한 곳만 켠다.

---

## 7. 커스텀 셰이더 — ShaderMaterial

내장 Material로 부족할 때 **ShaderMaterial**로 Vertex/Fragment 셰이더(GLSL)를 직접 작성한다. Scene graph와 행렬(modelViewMatrix, projectionMatrix 등)은 Three.js가 넘겨 준다.

- **uniforms:** JS에서 셰이더로 넘기는 상수. `{ uTime: { value: 0 } }` 형태. 매 프레임 `material.uniforms.uTime.value = time`처럼 갱신.
- **attribute:** 정점마다 다른 값(위치, UV 등). Three.js가 제공하는 `position`, `uv`, `normal` 등을 그대로 쓸 수 있다.
- **varying:** Vertex → Fragment로 전달 후, 래스터화 시 보간되는 값.
- **ShaderMaterial**은 **WebGLRenderer** 전용. WebGPU는 TSL(Three Shader Language) 등 다른 경로 사용.
- 내장 uniform/attribute를 쓰지 않으려면 **RawShaderMaterial** 사용.

---

## 8. 로더 (Loaders)

- **GLTFLoader:** glTF 2.0 (.gltf, .glb). 메시, 머티리얼, 텍스처, 애니메이션, 카메라, (확장 시) 조명까지 로드. addon이므로 `three/addons/loaders/GLTFLoader.js` 등에서 별도 import.
- **DRACO:** `KHR_draco_mesh_compression` 사용 시 DRACODecoder 설정 필요. 용량·로딩 최적화에 유리.
- 기타: OBJLoader, BufferGeometryLoader 등. 필요한 로더만 addon에서 import.

---

## 9. 애니메이션 루프

```javascript
function animate(time) {
  time *= 0.001;
  // rotation, position 등 갱신
  renderer.render(scene, camera);
  requestAnimationFrame(animate);
}
requestAnimationFrame(animate);
```

- `requestAnimationFrame`에 넘기는 콜백의 인자(ms)를 초 단위로 바꿔 쓰면 편하다.
- Three.js 각도는 **라디안**이다 (예: `cube.rotation.y = time`).

---

## 10. 반응형·리사이즈

캔버스 크기가 바뀔 때:

- `renderer.setSize(width, height)`
- `camera.aspect = width / height`
- `camera.updateProjectionMatrix()`

포스트 프로세싱(EffectComposer)을 쓰면 composer와 각 pass에도 `setSize`를 호출해야 한다.

---

## 11. Addons (컨트롤·포스트프로세싱 등)

코어와 별도로 **addon**에서 import한다.

- **설치:** `npm install three`만 하면 되고, addon은 패키지에 포함된다.
- **import 예:**
  - `import { OrbitControls } from 'three/addons/controls/OrbitControls.js';`
  - `import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';`
  - `import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';`
- **OrbitControls:** 카메라를 마우스로 회전·줌. 데모/뷰어에서 자주 사용.
- **EffectComposer:** RenderPass → 여러 효과 패스 → OutputPass 순으로 post-processing. 블룸, FXAA, 필름 그레인 등.

---

## 12. 성능·베스트 프랙티스

| 항목 | 권장 |
|------|------|
| **Draw call** | 프레임당 수를 줄인다. 수백 개 이상이면 병목 가능. |
| **InstancedMesh** | 같은 geometry·material을 여러 개 그릴 때. draw call 1개로 처리. |
| **Geometry 병합** | 정적인 오브젝트는 `BufferGeometry` merge로 하나로 묶을 수 있음. |
| **Material 공유** | 같은 재질이면 Material 인스턴스를 재사용. |
| **LOD** | 거리에 따라 저폴리/빌보드로 전환해 연산량 감소. |
| **리소스 해제** | geometry, material, texture, render target 사용 끝나면 `.dispose()` 호출. |
| **텍스처** | KTX2 등 압축 포맷, 필요 시 해상도/크기 조절. |
| **Frustum culling** | 기본 지원. 카메라 frustum 밖은 그리지 않음. |

---

## 13. WebGPU

- **WebGPURenderer**가 별도로 있다. WebGL과 빌드/import 경로가 다름.
- r167 근처부터 WebGPU 빌드가 도입되었고, WebGL 빌드와 한 번들에 같이 넣기 어려운 구조였음. r171 등에서 addon/빌드 정리 진행.
- WebGPU 사용 시 **TSL(Three Shader Language)** 등 다른 셰이더 경로를 쓸 수 있고, compute shader 등 활용 시 성능 이득이 있을 수 있다.
- 브라우저 지원이 WebGL보다 좁으므로, 필요 시 `WebGPURenderer` 지원 여부를 검사하고 WebGL로 fallback 하는 전략이 필요하다.

---

## 14. 한계·적용 시점

**Three.js에 맞는 경우**

- 웹에서 3D 시각화, 뷰어, 간단한 인터랙티브 3D
- 비교적 빠르게 프로토타입을 만들고, PBR·다양한 포맷(glTF 등)·커뮤니티/문서를 활용하고 싶을 때

**한계·대안을 고려할 부분**

- **Forward rendering만 지원.** Deferred rendering 파이프라인이 없어, 특정 고급 기법은 구현이 제한적일 수 있다.
- **게임 엔진이 아니다.** 물리, 파티클 시스템, 입력, 사운드, 에디터, 스크립팅 등은 직접 붙이거나 다른 라이브러리와 조합해야 한다.
- **저수준 제어:** 고급 렌더링/최적화를 위해 WebGL/WebGPU를 직접 다루는 것보다 제어 범위가 좁다. 매우 특수한 요구는 raw WebGL/WebGPU가 나을 수 있다.

---

## 15. 참고 링크

- [Three.js 공식 문서](https://threejs.org/docs/)
- [Fundamentals (공식 매뉴얼)](https://threejs.org/manual/en/fundamentals.html)
- [Scene Graph (공식 매뉴얼)](https://threejs.org/manual/en/scenegraph.html)
- [Optimize Lots of Objects](https://threejs.org/manual/en/optimize-lots-of-objects.html)
- [WebGPURenderer](https://threejs.org/docs/#api/en/renderers/WebGPURenderer) — WebGPU 사용 시

---

이 문서는 `Docs/web-graphics.md`의 WebGL/WebGPU/Three.js 정리 중 **Three.js**만 골라, 실무에서 알아두면 좋은 개념·API·성능·한계를 정리한 것이다. 셰이더·렌더링 파이프라인·용어(Vertex, Normal, UV, Uniform 등)는 `web-graphics.md`의 해당 섹션을 참고하면 된다.
