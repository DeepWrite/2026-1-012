# 학생과제 파일명 변경

반복되는 셸 명령 대신, 프로젝트 전체를 재귀적으로 순회하며 파일명을 정리하는 파이썬 스크립트를 사용한다.

## 지원하는 형식

- `...asmt-04-006-19-최유진-1.md` -> `asmt-04-006-19-최유진.md`
- `...revision-asmt-01-006-16-김혜원-3.md` -> `revision-asmt-01-006-16-김혜원.md`
- 접미사 `-1`, `-3`, `-1-1` 같은 숫자 꼬리는 제거한다.
- 앞에 붙은 업로드 번호나 기타 문자열도 제거한다.

## 사용법

먼저 변경 예정만 확인:

```bash
python3 scripts/rename_student_filenames.py --dry-run .
```

실제로 변경:

```bash
python3 scripts/rename_student_filenames.py .
```

특정 디렉터리만 대상으로 실행할 수도 있다:

```bash
python3 scripts/rename_student_filenames.py --dry-run asmt-04/original asmt-04/revision
```

충돌이 있으면 해당 파일은 건너뛰고 `CONFLICT`로 표시한다.

## asmt-05 PDF 링크 정리

- 학생별 제출 폴더 안에 흩어져 있는 PDF를 `asmt-05/pdf/`로 모은다.
- 파일명은 `asmt-05-반번호-학생번호-순번.pdf` 형식으로 통일한다.
- 각 학생 markdown 끝에 `## PDF 링크` 섹션을 추가하고 절대 경로 링크를 넣는다.
- `png`, `jpg`, `txt` 같은 비PDF 파일은 그대로 둔다.

먼저 변경 예정만 확인:

```bash
python3 scripts/organize_asmt05_pdf_links.py --dry-run
```

실제로 정리:

```bash
python3 scripts/organize_asmt05_pdf_links.py
```

PDF가 없는 제출 폴더나 대상 markdown가 모호한 폴더는 경고로 출력한다.

## asmt-05 제출 폴더명 정리

- 학생 제출 폴더명은 내부 markdown 파일명과 동일하게 맞춘다.
- 예: `..._amst-05`, `..._asmt-05-1`, `asmt-05 2` -> `asmt-05-012-11-이서연`
- `pdf` 폴더는 그대로 둔다.

먼저 변경 예정만 확인:

```bash
python3 scripts/rename_asmt05_submission_dirs.py --dry-run
```

실제로 변경:

```bash
python3 scripts/rename_asmt05_submission_dirs.py
```

## asmt-05 주제 선정 보강 문서

- 메인 토의 페이지는 `asmt-05.md`다.
- `012` 반의 분류별 promising 판단 참고, 대체 후보, 서지 정리 메모는 `asmt-05-commentary.md`에 정리했다.
- 코멘트 문서의 파일명은 `asmt-05-commentary.md`, 문서 제목은 `과제-05 검토 메모`로 통일한다.
- 토의에서 어떤 분류를 남기고 버릴지 가르는 공통 기준은 `asmt-05-topic-selection-guide.md`에 정리했다.
- `asmt-05` 하위에 새 검토 문서를 추가할 때는 학생 문서의 `nav_order`를 다시 손대지 않고, 검토 문서에 `nav_order: 0`을 주는 것을 기본 원칙으로 삼는다.
- 패키지 응집도가 느슨한 분류는 통째로 약하다고 쓰지 말고, 코멘트 문서에서 개별 학생 주제별 생존 가능성을 따로 평가한다.
- 이후 다른 에이전트가 같은 작업을 이어받을 때도, 먼저 이 가이드를 읽고 각 분류의 promising 여부, 경고 신호, 대표 문헌 검증 여부를 보강하면 된다.
