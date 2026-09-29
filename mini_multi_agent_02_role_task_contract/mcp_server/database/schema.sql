CREATE SCHEMA IF NOT EXISTS mini_multi_agent_02;
CREATE TABLE IF NOT EXISTS mini_multi_agent_02.places (place_id SERIAL PRIMARY KEY, city TEXT NOT NULL, name TEXT NOT NULL, category TEXT NOT NULL, transit_note TEXT NOT NULL, source_url TEXT NOT NULL, verified_at DATE NOT NULL, UNIQUE(city, name));
CREATE TABLE IF NOT EXISTS mini_multi_agent_02.budget_reference (city TEXT PRIMARY KEY, transport INTEGER NOT NULL, lodging_per_night INTEGER NOT NULL, food_per_day INTEGER NOT NULL, source_note TEXT NOT NULL, source_url TEXT NOT NULL, verified_at DATE NOT NULL);
ALTER TABLE mini_multi_agent_02.places ADD COLUMN IF NOT EXISTS indoor BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE mini_multi_agent_02.places ADD COLUMN IF NOT EXISTS source_url TEXT NOT NULL DEFAULT 'https://www.visitbusan.net/';
ALTER TABLE mini_multi_agent_02.places ADD COLUMN IF NOT EXISTS verified_at DATE NOT NULL DEFAULT CURRENT_DATE;
ALTER TABLE mini_multi_agent_02.budget_reference ADD COLUMN IF NOT EXISTS source_note TEXT NOT NULL DEFAULT '교육용 보수적 예산 기준; 실행 전 실제 가격 확인 필요';
ALTER TABLE mini_multi_agent_02.budget_reference ADD COLUMN IF NOT EXISTS source_url TEXT NOT NULL DEFAULT 'https://www.visitbusan.net/';
ALTER TABLE mini_multi_agent_02.budget_reference ADD COLUMN IF NOT EXISTS verified_at DATE NOT NULL DEFAULT CURRENT_DATE;
DELETE FROM mini_multi_agent_02.places WHERE city = '부산' AND name = '해운대 해변';
INSERT INTO mini_multi_agent_02.places (city, name, category, transit_note, source_url, verified_at, indoor) VALUES ('부산','부산박물관','문화','도시철도 대연역 이용','https://museum.busan.go.kr/busan/index','2026-09-22',TRUE), ('부산','영화의전당','문화','도시철도 센텀시티역 이용','https://www.dureraum.org/','2026-09-22',TRUE), ('부산','해운대해수욕장','자연','도시철도 해운대역 이용','https://www.visitbusan.net/','2026-09-22',FALSE) ON CONFLICT (city, name) DO UPDATE SET category=EXCLUDED.category, transit_note=EXCLUDED.transit_note, source_url=EXCLUDED.source_url, verified_at=EXCLUDED.verified_at, indoor=EXCLUDED.indoor;
INSERT INTO mini_multi_agent_02.budget_reference (city, transport, lodging_per_night, food_per_day, source_note, source_url, verified_at) VALUES ('부산',60000,110000,50000,'교육용 보수적 예산 기준; 실행 전 실제 가격 확인 필요','https://www.visitbusan.net/','2026-09-22') ON CONFLICT (city) DO UPDATE SET transport=EXCLUDED.transport, lodging_per_night=EXCLUDED.lodging_per_night, food_per_day=EXCLUDED.food_per_day, source_note=EXCLUDED.source_note, source_url=EXCLUDED.source_url, verified_at=EXCLUDED.verified_at;

CREATE TABLE IF NOT EXISTS mini_multi_agent_02.allergy_guidance (guidance_id SERIAL PRIMARY KEY, city TEXT NOT NULL, guidance TEXT NOT NULL, emergency BOOLEAN NOT NULL DEFAULT FALSE, source_url TEXT NOT NULL, verified_at DATE NOT NULL, UNIQUE(city, guidance));
CREATE TABLE IF NOT EXISTS mini_multi_agent_02.quality_requirements (requirement_id SERIAL PRIMARY KEY, scenario TEXT NOT NULL, requirement_key TEXT NOT NULL, description TEXT NOT NULL, required_term TEXT NOT NULL, UNIQUE(scenario, requirement_key));
CREATE TABLE IF NOT EXISTS mini_multi_agent_02.allergy_sources (source_id SERIAL PRIMARY KEY, source_key TEXT NOT NULL UNIQUE, title TEXT NOT NULL, publisher TEXT NOT NULL, url TEXT NOT NULL, evidence_note TEXT NOT NULL, checked_at DATE NOT NULL);
ALTER TABLE mini_multi_agent_02.allergy_guidance ADD COLUMN IF NOT EXISTS guidance_key TEXT;
ALTER TABLE mini_multi_agent_02.allergy_guidance ADD COLUMN IF NOT EXISTS situation TEXT;
ALTER TABLE mini_multi_agent_02.allergy_guidance ADD COLUMN IF NOT EXISTS action TEXT;
ALTER TABLE mini_multi_agent_02.allergy_guidance ADD COLUMN IF NOT EXISTS source_id INTEGER REFERENCES mini_multi_agent_02.allergy_sources(source_id);
ALTER TABLE mini_multi_agent_02.quality_requirements ADD COLUMN IF NOT EXISTS check_type TEXT NOT NULL DEFAULT 'literal';
CREATE UNIQUE INDEX IF NOT EXISTS allergy_guidance_city_key ON mini_multi_agent_02.allergy_guidance(city, guidance_key);

INSERT INTO mini_multi_agent_02.allergy_sources (source_key, title, publisher, url, evidence_note, checked_at) VALUES
('mfds_ingredients','알레르기 유발 식품 표시에 대해 알아보아요','식품의약품안전처·식품안전나라','https://www.foodsafetykorea.go.kr/portal/board/boardDetail.do?bbs_no=bbs001&menu_grp=MENU_NEW01&menu_no=3120&ntctxt_no=1091412','음식 주문 시 알레르기 원인 식품이 들어가는지 확인하도록 안내한다.','2026-09-28'),
('fare_cross_contact','Avoiding Cross-Contact','Food Allergy Research & Education','https://www.foodallergy.org/resources/avoiding-cross-contact','식당 직원에게 조리 과정의 교차접촉 가능성을 확인하도록 안내한다.','2026-09-28'),
('kdca_anaphylaxis','아나필락시스','질병관리청 국가건강정보포털','https://health.kdca.go.kr/healthinfo/biz/health/gnrlzHealthInfo/gnrlzHealthInfo/gnrlzHealthInfoView.do?cntnts_sn=6684','아나필락시스가 의심될 때 119에 신속히 연락하도록 안내한다.','2026-09-28')
ON CONFLICT (source_key) DO UPDATE SET title=EXCLUDED.title, publisher=EXCLUDED.publisher, url=EXCLUDED.url, evidence_note=EXCLUDED.evidence_note, checked_at=EXCLUDED.checked_at;

-- 기존 Seed 문장을 같은 행에서 구조화해 반복 실행해도 중복되지 않게 한다.
UPDATE mini_multi_agent_02.allergy_guidance SET guidance_key='cross_contact' WHERE city='부산' AND guidance='방문 전에 식재료와 교차접촉 가능성을 매장에 직접 확인한다.' AND guidance_key IS NULL;
UPDATE mini_multi_agent_02.allergy_guidance SET guidance_key='emergency' WHERE city='부산' AND guidance='중증 알레르기 증상이 의심되면 즉시 119에 신고한다.' AND guidance_key IS NULL;
INSERT INTO mini_multi_agent_02.allergy_guidance (city, guidance, guidance_key, situation, action, emergency, source_id, source_url, verified_at) VALUES
('부산','방문 전에 식재료와 교차접촉 가능성을 매장에 직접 확인한다.','cross_contact','음식점 방문 전','식재료와 교차접촉 가능성을 매장에 직접 확인한다.',FALSE,(SELECT source_id FROM mini_multi_agent_02.allergy_sources WHERE source_key='fare_cross_contact'),'https://www.foodallergy.org/resources/avoiding-cross-contact','2026-09-28'),
('부산','음식 주문 전에 알레르기 원인 식품이 들어가는지 확인한다.','ingredients','음식 주문 전','알레르기 원인 식품이 들어가는지 확인한다.',FALSE,(SELECT source_id FROM mini_multi_agent_02.allergy_sources WHERE source_key='mfds_ingredients'),'https://www.foodsafetykorea.go.kr/portal/board/boardDetail.do?bbs_no=bbs001&menu_grp=MENU_NEW01&menu_no=3120&ntctxt_no=1091412','2026-09-28'),
('부산','중증 알레르기 증상이 의심되면 즉시 119에 신고한다.','emergency','중증 알레르기 증상 의심','즉시 119에 신고한다.',TRUE,(SELECT source_id FROM mini_multi_agent_02.allergy_sources WHERE source_key='kdca_anaphylaxis'),'https://health.kdca.go.kr/healthinfo/biz/health/gnrlzHealthInfo/gnrlzHealthInfo/gnrlzHealthInfoView.do?cntnts_sn=6684','2026-09-28')
ON CONFLICT (city, guidance_key) DO UPDATE SET guidance=EXCLUDED.guidance, situation=EXCLUDED.situation, action=EXCLUDED.action, emergency=EXCLUDED.emergency, source_id=EXCLUDED.source_id, source_url=EXCLUDED.source_url, verified_at=EXCLUDED.verified_at;

INSERT INTO mini_multi_agent_02.quality_requirements (scenario, requirement_key, description, required_term) VALUES
('allergy_safety','source','장소와 안전 지침의 출처를 표시한다.','출처'),
('allergy_safety','cross_contact','식재료와 교차접촉 가능성을 직접 확인하도록 안내한다.','교차접촉'),
('allergy_safety','emergency','중증 증상이 의심되면 119 신고를 안내한다.','119'),
('allergy_safety','approval','게시 또는 사용 전에 사용자 승인을 요청한다.','승인')
ON CONFLICT (scenario, requirement_key) DO UPDATE SET description=EXCLUDED.description, required_term=EXCLUDED.required_term;
UPDATE mini_multi_agent_02.quality_requirements SET check_type='emergency_report' WHERE scenario='allergy_safety' AND requirement_key='emergency';
