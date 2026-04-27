# Assignment Submission Organization

이 폴더의 표준 정리 도구는 `organize_assignment_submissions.py`이다. LMS에서 내려받은 과제 제출 폴더가 학생별 하위 폴더로 나뉘고, 각 폴더에 `md` 파일 1개와 관련 `pdf` 첨부가 들어 있는 경우에 쓴다.

정리 후 구조는 `asmt-05`, `asmt-06`과 같이 맞춘다.

```text
asmt-XX/
  asmt-XX-012-01-김현주/
    asmt-XX-012-01-김현주.md
  pdf/
    asmt-XX-012-01-01.pdf
    asmt-XX-012-01-02.pdf
```

각 markdown 파일 하단에는 다음 형식의 PDF 링크 섹션을 붙인다.

```markdown
## PDF 링크

- [원래 PDF 파일명.pdf](/2026-1-012/asmt-XX/pdf/asmt-XX-012-01-01.pdf)
```

## 재수행 절차

1. 새 제출물 폴더를 `asmt-XX/` 아래에 그대로 둔다.
2. 먼저 dry run으로 변경 계획을 확인한다.

   ```bash
   python3 scripts/organize_assignment_submissions.py --assignment-dir asmt-XX
   ```

3. 출력에서 학생 수, PDF 수, 이상한 학생명, 충돌 경고를 확인한다.
4. 문제가 없으면 적용한다.

   ```bash
   python3 scripts/organize_assignment_submissions.py --assignment-dir asmt-XX --apply
   ```

5. 검산한다.

   ```bash
   find asmt-XX -type f | awk 'BEGIN{md=0;pdf=0} /\.md$/{md++} /\.pdf$/{pdf++} END{print "md=" md " pdf=" pdf}'
   python3 scripts/verify_assignment_pdf_links.py asmt-XX
   ```

## 조별 문서 상단 정보 보정

`asmt-06-01.md`, `asmt-06-02.md`처럼 조별 요약문을 모으는 문서는 각 조의 주제와 조원 편성이 확정된 뒤 상단 항목만 수동으로 맞춘다. 008반, 006반, 013반 `asmt-06`에서 같은 방식으로 처리했다.

1. 조별 문서의 `title` 또는 `parent`에서 조 번호를 확인한다.
2. 학생별 제출 문서 상단의 `parent: 과제-06 (N조)` 값과 사용자가 제공한 조 편성표를 대조한다.
3. 각 조별 문서에서 아래 세 줄만 수정한다.

   ```markdown
   - 선정된 주제: ...
   - 주제에 대한 설명(1문장): ...
   - 참여 조원: ...
   ```

4. `요약문 List` 아래 내용은 자동 생성 또는 기존 링크 목록이므로 수정하지 않는다.
5. 수정 뒤에는 다음처럼 세 항목만 바뀌었는지 확인한다.

   ```bash
   rg -n "선정된 주제|주제에 대한 설명|참여 조원|요약문 List" asmt-XX-*.md
   git diff -- asmt-XX-*.md
   ```

## 이름 기준

기본 학생명 roster는 이미 정리된 `asmt-05` 학생 폴더명에서 가져온다. 다른 과제를 기준으로 삼아야 할 때는 `--roster-from`을 지정한다.

```bash
python3 scripts/organize_assignment_submissions.py --assignment-dir asmt-XX --roster-from asmt-06
```

roster에 없는 학생은 markdown의 `title`, 파일명, 폴더명에서 한글 이름을 추출한다.

## 주의

- 각 학생 폴더에는 markdown 파일이 정확히 1개 있어야 한다.
- PDF는 원래 파일명을 링크 텍스트로 보존하고, 실제 파일명만 `asmt-XX-012-NN-MM.pdf`로 바꾼다.
- 이미 `pdf/`로 정리된 과제에 다시 실행해도 링크 섹션을 재생성하는 방식으로 동작한다.
- PDF가 없는 제출물은 경고가 뜨지만 폴더명과 markdown 파일명 정리는 수행된다.
- PDF가 아닌 이미지 등 기타 첨부 파일은 학생 폴더 안에 보존한다.
