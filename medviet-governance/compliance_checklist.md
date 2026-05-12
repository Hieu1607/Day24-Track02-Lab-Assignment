# NĐ13/2023 Compliance Checklist — MedViet AI Platform

## A. Data Localization
- [ ] Tất cả patient data lưu trên servers đặt tại Việt Nam
- [ ] Backup cũng phải ở trong lãnh thổ VN
- [ ] Log việc transfer data ra ngoài nếu có

## B. Explicit Consent
- [ ] Thu thập consent trước khi dùng data cho AI training
- [ ] Có mechanism để user rút consent (Right to Erasure)
- [ ] Lưu consent record với timestamp

## C. Breach Notification (72h)
- [ ] Có incident response plan
- [ ] Alert tự động khi phát hiện breach
- [ ] Quy trình báo cáo đến cơ quan có thẩm quyền trong 72h

## D. DPO Appointment
- [ ] Đã bổ nhiệm Data Protection Officer
- [ ] DPO có thể liên hệ tại: dpo@medviet.vn

## E. Technical Controls (mapping từ requirements)
| NĐ13 Requirement | Technical Control | Status | Owner |
|-----------------|-------------------|--------|-------|
| Data minimization | PII anonymization pipeline (Presidio) | ✅ Done | AI Team |
| Access control | RBAC (Casbin) + ABAC (OPA) | ✅ Done | Platform Team |
| Encryption | AES-256 at rest, TLS 1.3 in transit | 🚧 In Progress | Infra Team |
| Audit logging | CloudTrail + API access logs | ⬜ Todo | Platform Team |
| Breach detection | Anomaly monitoring (Prometheus) | ⬜ Todo | Security Team |

## F. TODO: Điền vào phần còn thiếu
- Audit logging: thêm FastAPI middleware ghi lại `user`, `role`, `endpoint`, `action`, `timestamp`, `status_code`; forward log sang ELK/S3 và áp dụng retention tối thiểu 180 ngày.
- Audit logging: log mọi thao tác đọc raw patient data, export report và request bị RBAC/OPA từ chối để phục vụ forensic review.
- Breach detection: dùng Prometheus scrape metrics từ API, tạo Grafana alert cho spike 4xx/5xx, số lần access bị từ chối và volume download bất thường.
- Breach detection: thêm rule cảnh báo khi một token truy cập quá nhiều patient records trong thời gian ngắn hoặc export dữ liệu restricted ra ngoài VN; gửi alert sang email/Slack/on-call.
