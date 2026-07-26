# MongoDB Schema Validation

Thu muc nay chua JSON Schema validator cho 16 collections cua he thong.

## Su dung

```bash
# Chay tu thu muc backend/ voi venv active:
cd backend
python db/schemas/apply_schemas.py
```

## Collections duoc quan ly

| Collection | Mo ta |
|-----------|-------|
| students | Ho so sinh vien, risk, enrollments |
| courses | Khoa hoc va cau hinh |
| classrooms | Lop hoc nho theo GV |
| timetable_blocks | Lich hoc co dinh cua SV |
| study_plans | Ke hoach tu hoc do AI de xuat |
| assignments | Bai tap / kiem tra |
| submissions | Bai nop cua sinh vien |
| assignment_milestones | Cac moc nho cua bai tap lon |
| notifications | Thong bao 1 chieu |
| channels | Kenh chat theo khoa hoc |
| messages | Tin nhan real-time |
| knowledge_states | Trang thai kien thuc SV |
| risk_history | Lich su bien dong risk score |
| agent_logs | Nhat ky hoat dong AI Agent |
| resources | Tai nguyen hoc tap |
| audit_logs | Lich su hanh dong trong he thong |

## Ghi chu

- `validationLevel: moderate` — chi validate doc moi/cap nhat, khong anh huong doc cu
- `validationAction: warn` — ghi log vi pham, KHONG tu choi doc
- An toan rollback: chay `collMod` voi `validator: {}` de xoa validation
