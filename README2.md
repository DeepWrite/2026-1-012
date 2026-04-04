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
