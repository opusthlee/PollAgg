# PollAgg Lightsail Deployment

## 0. 사전 조건
- Lightsail 인스턴스 생성됨 (Ubuntu 22.04 권장)
- 고정 IP 할당
- DNS A 레코드 2개를 인스턴스 IP로:
  - `api-poll.dailyprizm.com`
  - `poll.dailyprizm.com`
- SSH 키로 접근 가능

## 1. 서버 초기 설정 (한 번만)
```bash
ssh ubuntu@<인스턴스_IP>
git clone <pollagg repo url> ~/pollagg
cd ~/pollagg
bash setup_server.sh
# 그룹 적용 위해 재로그인
exit
ssh ubuntu@<인스턴스_IP>
```

## 2. 환경변수 작성
```bash
cd ~/pollagg
cp .env.example .env
# 강력한 POSTGRES_PASSWORD 생성 (예: openssl rand -base64 24)
nano .env
```

## 3. 첫 빌드 및 기동 (HTTP 단독)
```bash
docker compose up -d --build
docker compose ps   # 4개 컨테이너 Running 확인
docker compose logs backend --tail 50
docker compose logs frontend --tail 50
```

확인:
- `curl http://api-poll.dailyprizm.com/api/data` → JSON 응답
- 브라우저 `http://poll.dailyprizm.com/dashboard` → 대시보드 표시

## 4. DB 스키마 적용 (Alembic)
```bash
docker compose exec backend alembic upgrade head
```

## 5. SSL 인증서 발급 (Let's Encrypt)
```bash
sudo apt-get install -y certbot
sudo certbot certonly --webroot -w ./nginx/webroot \
  -d api-poll.dailyprizm.com -d poll.dailyprizm.com \
  --email <your-email> --agree-tos --no-eff-email

# 생성된 인증서를 nginx 컨테이너가 읽을 수 있게 복사
sudo cp -rL /etc/letsencrypt/live ./nginx/certs/live
sudo cp -rL /etc/letsencrypt/archive ./nginx/certs/archive
sudo chown -R $USER:$USER ./nginx/certs

# nginx/conf.d/pollagg.conf에서 HTTPS server 블록 주석 해제
nano nginx/conf.d/pollagg.conf

docker compose exec nginx nginx -s reload
# 또는
docker compose restart nginx
```

## 6. 자동 갱신 cron
```bash
sudo crontab -e
# 매일 새벽 3시 갱신 시도, 성공 시 nginx 리로드
0 3 * * * certbot renew --quiet --deploy-hook "cd /home/ubuntu/pollagg && cp -rL /etc/letsencrypt/live ./nginx/certs/live && docker compose exec nginx nginx -s reload"
```

## 7. 운영 체크리스트
- [ ] Lightsail 방화벽: 22 (내 IP), 80 (Anywhere), 443 (Anywhere)
- [ ] `.env`는 인스턴스 외부에 백업 (1Password 등)
- [ ] `docker compose logs --tail 100 -f` 로 첫 트래픽 모니터링
- [ ] DB 백업 스케줄 (예: `pg_dump`를 S3/Lightsail snapshot으로)

## 데이터 마이그레이션 (로컬 SQLite → 운영 PG)
로컬 `pollagg.db` 데이터를 운영 PG로 옮기려면:
```bash
# 로컬에서
python scripts/export_sqlite_to_json.py > /tmp/seed.json   # 별도 작성 필요
scp /tmp/seed.json ubuntu@<IP>:~/pollagg/
# 서버에서
docker compose exec backend python scripts/import_json.py /app/seed.json
```
*(현재 export/import 스크립트는 미구현. 필요 시 별도 작업)*
