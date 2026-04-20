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
