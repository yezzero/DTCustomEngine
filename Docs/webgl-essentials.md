# WebGL 알아두면 좋은 것들

> **Scope:** WebGL 1.0/2.0 개발자가 반드시 알아야 할 개념, API, 한계, 모범 사례  
> **Key Finding:** WebGL은 상태 기계 기반의 래스터화 API이며, GLSL 셰이더·버퍼·상태 관리·컨텍스트 손실·성능 주의점을 이해해야 안정적으로 사용할 수 있다.

---

## 1. WebGL이란

**WebGL**은 HTML `<canvas>` 위에서 GPU 가속 2D/3D 그래픽을 그리기 위한 JavaScript API이다. Khronos가 명세를 관리하며, OpenGL ES를 브라우저용으로 포팅한 것이다.

| 버전   | 기반           | 셰이더 언어 |
| ------ | -------------- | ----------- |
| WebGL 1.0 | OpenGL ES 2.0 | GLSL 100 (ESSL 1.0) |
| WebGL 2.0 | OpenGL ES 3.0 | GLSL 300 ES (ESSL 3.0) |

- **플러그인 불필요**, 모든 현대 브라우저에서 지원.
- **상태 기계(state machine)**: 현재 바인딩된 버퍼, 셰이더, 텍스처, 블렌딩 등 전역 상태를 바꾼 뒤 `drawArrays`/`drawElements`를 호출하면, 그 시점의 상태 조합으로 렌더링된다.

---

## 2. 렌더링 파이프라인 (두 단계)

WebGL은 **래스터화 엔진**이다. 정점/선/삼각형을 그리기 위해 두 가지 셰이더만 제공한다.

```
[정점 데이터] → Vertex Shader → [클립 공간 정점]
     → (고정: 프리미티브 조립·래스터화)
     → Fragment Shader → [픽셀 색상] → (고정: Depth/Blend) → Framebuffer
```

- **Vertex Shader**: 정점마다 한 번 실행. `gl_Position`에 클립 공간 좌표(x,y,z,w, 범위 -1~1)를 쓴다.
- **Fragment Shader**: 래스터화된 각 픽셀(프래그먼트)마다 실행. 최종 색상을 출력한다 (WebGL1: `gl_FragColor`, WebGL2: `out` 변수).

클립 공간은 캔버스 크기와 무관하게 -1~+1 범위이다.

---

## 3. 셰이더에 데이터 넣는 네 가지 방법

| 방식        | 설명 |
| ----------- | ---- |
| **Attribute** | 정점마다 다른 값. Vertex Shader에서만 읽기. 버퍼에서 끌어옴. |
| **Uniform**   | 한 드로우 콜 안에서 모든 정점/픽셀에 동일. (시간, 행렬, 색상 등) |
| **Texture**   | 텍스처 유닛에 바인딩된 이미지/데이터. `texture2D`/`texture()` 등으로 샘플링. |
| **Varying**   | Vertex → Fragment로 전달. 래스터화 시 자동 보간됨. (WebGL2: `out` / `in`) |

- Attribute는 `enableVertexAttribArray` + `vertexAttribPointer`로 “어떤 버퍼에서, 몇 컴포넌트, 어떤 타입으로 읽을지” 설정한다.
- **Vertex attrib 0은 반드시 배열로 활성화**해야 한다. 비활성이면 데스크톱 OpenGL(macOS 등)에서 에뮬레이션 비용이 든다. `bindAttribLocation(program, 0, "a_position")` 등으로 위치 0을 쓰고 `enableVertexAttribArray(0)` 호출.

---

## 4. 버퍼(Buffer)와 드로우

- **Buffer**: GPU에 올리는 데이터. `createBuffer` → `bindBuffer(ARRAY_BUFFER/ELEMENT_ARRAY_BUFFER)` → `bufferData`로 채운다.
- **Vertex Array Object (VAO)**: WebGL2에서는 기본 제공. “어떤 버퍼를 어떤 attribute에 어떻게 연결했는지”를 묶어 두어, 드로우 전에 VAO만 바인딩하면 된다. **VAO를 매 프레임 바꾸지 말고, 정적 VAO를 재사용**하는 편이 빠르다.
- **Draw Call**: `drawArrays(primitiveType, offset, count)` 또는 `drawElements(...)`. 호출 시점의 **현재 바인딩된 프로그램, 버퍼, VAO, 텍스처, 상태**가 그대로 사용된다.

---

## 5. WebGL 1.0 vs 2.0 — 꼭 알아둘 차이

| 항목 | WebGL 1 | WebGL 2 |
| ---- | ------- | ------- |
| 컨텍스트 | `getContext("webgl")` | `getContext("webgl2")` |
| 셰이더 | `attribute`, `varying`, `gl_FragColor`, `texture2D` | `in`/`out`, 커스텀 `out`, `texture()`, `#version 300 es` |
| VAO | 확장 `OES_vertex_array_object` | 내장 |
| 텍스처 | 2D, Cube; 비 POT 제한 있음 | 2D, 3D, 배열; 비 POT 풀 지원, `texelFetch`, `textureSize` |
| 인덱스 | 보통 16bit (확장으로 32bit) | 32bit 기본 |
| 인스턴싱 | 확장 `ANGLE_instanced_arrays` | 내장 |
| Uniform | `uniform*` 호출 여러 번 | Uniform Buffer Object로 한 번에 묶어 전달 가능 |
| 루프 | 상수 반복 횟수만 허용 | 변수 허용 (GLSL 300 es) |
| 행렬 | 역행렬 등은 JS에서 계산해 uniform으로 | `inverse()`, `transpose()` 내장 |

WebGL2는 대부분 하위 호환에 가깝지만, **셰이더 문법이 GLSL 300 ES로 바뀌므로** 기존 GLSL 100 코드는 수정이 필요하다.

---

## 6. 반드시 알아야 할 한계와 주의사항

### 6.1 시스템 한계 (최소 보장값)

자기 머신만 기준으로 하지 말고, **클라이언트 최소 사양**을 가정해야 한다. 예:

- `MAX_TEXTURE_SIZE`: 4096
- `MAX_VIEWPORT_DIMS`: [4096, 4096]
- `MAX_VERTEX_ATTRIBS`: 16
- `MAX_COMBINED_TEXTURE_IMAGE_UNITS`: 8 (WebGL1), 16 (WebGL2)
- `MAX_VERTEX_UNIFORM_VECTORS`: 128, `MAX_FRAGMENT_UNIFORM_VECTORS`: 64

필요하면 `getParameter(gl.XXX)`로 런타임에 확인한다.

### 6.2 확장(Extension) 의존성

대부분의 WebGL 확장은 **기기/드라이버에 따라 있을 수도 없을 수도 있다**. 확장 사용 시 “없으면 기능 축소”처럼 **선택적**으로 쓰는 것이 안전하다. WebGL 1에서 사실상 널리 쓰이는 확장: `OES_vertex_array_object`, `OES_element_index_uint`, `ANGLE_instanced_arrays` 등.

### 6.3 컨텍스트 손실 (Context Lost)

GPU는 공유 자원이라 **WebGL 컨텍스트가 브라우저/OS에 의해 회수될 수 있다**.

- 다른 탭의 무거운 GPU 사용, 드라이버 업데이트, 그래픽 카드 전환 등으로 발생.
- **한 페이지에 활성 WebGL 컨텍스트가 너무 많으면**(예: 16개 초과) 가장 오래된 컨텍스트가 강제로 손실된다는 제한이 있다.

**대응:**

1. `webglcontextlost` 이벤트 리스너를 달고 `preventDefault()` 호출.
2. 렌더 루프 중단.
3. `webglcontextrestored`에서 **모든 리소스(버퍼, 텍스처, 셰이더, 프로그램, FBO 등)를 다시 생성**하고 초기화.

에러 처리 시 `gl.getError()`가 `CONTEXT_LOST_WEBGL`을 반환할 수 있으므로, `isContextLost()`를 먼저 확인한 뒤 나머지 에러만 해석하는 것이 좋다.

### 6.4 에러와 프로덕션

- **정상적인 앱은 `OUT_OF_MEMORY`와 `CONTEXT_LOST` 외에는 WebGL 에러를 만들지 않는다.** 그 외 에러가 나면 반드시 원인을 제거해야 한다.
- `getError()`, `getParameter()`, `getProgramParameter()`, `getShaderParameter()` 등은 **동기적으로 GPU와 통신**할 수 있어 지연이 크다. **프로덕션 루프 안에서는 가능한 한 호출하지 않는다.** 초기화·디버깅 시에만 사용.

### 6.5 정밀도(Precision)

- **WebGL 1 Fragment Shader**: `highp float`가 선택 사항인 기기가 있다. 무조건 `highp`를 쓰면 일부 모바일에서 동작하지 않을 수 있다. `#ifdef GL_FRAGMENT_PRECISION_HIGH`로 분기하는 패턴이 안전하다.
- **WebGL 2**: ESSL 300 es 기준으로 정밀도 요구사항이 명확해졌지만, float 텍스처 샘플링 등에서는 플랫폼별로 제한이 있을 수 있다 (예: iOS에서 float 텍스처는 `highp sampler2D` 필요).
- 셰이더 간에 **32비트 정수를 넘기려면** `highp`를 명시해야 이식성이 좋다.

---

## 7. 성능·모범 사례 (요약)

- **Draw call·상태 변경 최소화**
  - 같은 텍스처·같은 셰이더를 쓰는 오브젝트는 **한 번에 그리기**(배칭). 텍스처 아틀라스로 텍스처 전환을 줄인다.
  - FBO attachment를 자주 바꾸지 말고, **자주 쓰는 framebuffer는 미리 구성해 두고 재사용**한다.

- **버퍼·텍스처**
  - 정점/인덱스는 **VBO/IBO에 올려 두고** 매 프레임 CPU→GPU 복사를 피한다.
  - WebGL2에서는 **texStorage + texSubImage**로 텍스처를 만들면 드라이버가 메모리를 미리 잡아 두어 유리하다.
  - 3D/멀리 보이는 텍스처는 **mipmap**을 켜 두면 캐시 효율이 좋다. 2D만 쓰고 줌 아웃이 없으면 레벨 1만 쓰는 식으로 메모리 절약.

- **셰이더**
  - 계산은 **가능하면 vertex shader에서** 하고, 결과만 varying으로 fragment에 넘긴다. fragment는 픽셀 수만큼 실행되므로 비용이 크다.
  - 셰이더 컴파일·링크는 **비동기로** 처리할 수 있으면 한다. `KHR_parallel_shader_compile` 확장이 있으면 `COMPLETION_STATUS_KHR`로 완료 여부만 확인하고, **링크 실패 시에만** getProgramParameter(LINK_STATUS)와 info log를 사용한다.

- **리소스 관리**
  - 더 이상 쓰지 않는 버퍼·텍스처·프로그램·셰이더는 **delete해서** 핸들을 해제한다. 가비지 컬렉터에만 맡기지 않는다.
  - 페이지를 떠날 때가 아니라, **해당 캔버스를 더 이상 쓰지 않을 때** `WEBGL_lose_context`로 컨텍스트를 명시적으로 잃어 주면 리소스 회수에 도움이 된다.

- **VRAM**
  - WebGL은 “최대 비디오 메모리”를 묻는 API가 없다. **퍼픽셀 VRAM 예산** 같은 방식으로 “창 크기 × 단위당 바이트” 상한을 두고, 텍스처·버퍼 캐시 크기를 제한하는 전략이 실전에서 유용하다.

- **블로킹 API**
  - `readPixels`(CPU로 읽기), `getBufferSubData`는 동기·고비용이다. 가능하면 **비동기 readback**이나 GPU 내부에서만 쓰는 방식으로 설계한다.
  - `requestAnimationFrame`을 쓰지 않는 경우, 프레임 끝에 `flush()`를 호출해 명령이 GPU에 넘어가도록 하는 것이 좋다.

---

## 8. 용어·개념 정리

| 용어 | 의미 |
| ---- | ---- |
| Clip space | Vertex Shader가 출력하는 좌표 공간. x,y,z가 [-1,1] 범위이고, w로 원근 나눔. |
| VBO / IBO | Vertex Buffer Object / Index Buffer Object. 정점·인덱스 데이터를 GPU에 두는 객체. |
| VAO | Vertex Array Object. attribute–버퍼 바인딩 집합. |
| FBO | Framebuffer Object. 렌더 타겟(텍스처/렌더버퍼) 묶음. |
| Mipmap | 텍스처의 축소판 체인. 거리별로 적절한 해상도를 샘플링해 캐시 효율·품질 향상. |
| Pipeline flush | 상태/셰이더/타겟 변경 등으로 이전 GPU 작업이 완료될 때까지 기다리는 동기화. DOM에서 texImage2D(비디오 등) 할 때 내부적으로 파이프라인 플러시가 일어날 수 있으므로, **업로드는 그리기 시작 전이나 파이프라인 사이에** 하는 것이 좋다. |

---

## 9. 참고 자료

1. [WebGL Specification (Khronos)](https://registry.khronos.org/webgl/specs/latest/) — WebGL 1.0 / 2.0 명세
2. [WebGL Best Practices (MDN)](https://developer.mozilla.org/en-US/docs/Web/API/WebGL_API/WebGL_best_practices) — 에러, 한계, FBO, 셰이더, 텍스처, 성능
3. [WebGL Fundamentals](https://webglfundamentals.org/webgl/lessons/webgl-how-it-works.html) — 파이프라인, attribute/varying, 버퍼
4. [WebGL2 Fundamentals — What's New](https://webgl2fundamentals.org/webgl/lessons/webgl2-whats-new.html) — WebGL2 기능 요약
5. [Handling Context Lost (Khronos Wiki)](https://www.khronos.org/webgl/wiki/HandlingContextLost) — 컨텍스트 손실 처리
