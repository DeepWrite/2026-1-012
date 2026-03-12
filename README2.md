# 학생과제 파일명 변경

```
for file in *.md; do
    newname=$(echo "$file" | sed -E 's/.*(asmt-[0-9]{2}-[0-9]{3}-[0-9]{2}-[가-힣]+)\-[0-9]+\.md$/\1.md/')
    # 위 패턴은 접미사 -3 등 있는 경우 처리
    if [ "$file" != "$newname" ]; then
        mv "$file" "$newname"
    else
        # 접미사가 없는 경우도 처리
        newname=$(echo "$file" | sed -E 's/.*(asmt-[0-9]{2}-[0-9]{3}-[0-9]{2}-[가-힣]+)\.md$/\1.md/')
        if [ "$file" != "$newname" ]; then
            mv "$file" "$newname"
        fi
    fi
done
```


```
for file in *.md; do
    newname=$(echo "$file" | sed -E 's/.*(revision-asmt-[0-9]{2}-[0-9]{3}-[0-9]{2}-[가-힣]+)\-[0-9]+\.md$/\1.md/')
    # 위 패턴은 접미사 -3 등 있는 경우 처리
    if [ "$file" != "$newname" ]; then
        mv "$file" "$newname"
    else
        # 접미사가 없는 경우도 처리
        newname=$(echo "$file" | sed -E 's/.*(revision-asmt-[0-9]{2}-[0-9]{3}-[0-9]{2}-[가-힣]+)\.md$/\1.md/')
        if [ "$file" != "$newname" ]; then
            mv "$file" "$newname"
        fi
    fi
done
```

for file in *.md; do
    newname=$(echo "$file" | sed -E 's/.*(asmt-[0-9]{2}-[0-9]{3}-[0-9]{2}-[가-힣]+)\-[0-9]+\.md$/\1.md/')
    # 위 패턴은 접미사 -3 등 있는 경우 처리
    if [ "$file" != "$newname" ]; then
        mv "$file" "$newname"
    else
        # 접미사가 없는 경우도 처리
        newname=$(echo "$file" | sed -E 's/.*(asmt-[0-9]{2}-[0-9]{3}-[0-9]{2}-[가-힣]+)\.md$/\1.md/')
        if [ "$file" != "$newname" ]; then
            mv "$file" "$newname"
        fi
    fi
done