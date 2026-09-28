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

INSERT INTO mini_multi_agent_02.allergy_guidance (city, guidance, emergency, source_url, verified_at) VALUES
('부산','방문 전에 식재료와 교차접촉 가능성을 매장에 직접 확인한다.',FALSE,'https://www.foodsafetykorea.go.kr/','2026-09-28'),
('부산','중증 알레르기 증상이 의심되면 즉시 119에 신고한다.',TRUE,'https://www.119.go.kr/','2026-09-28')
ON CONFLICT (city, guidance) DO UPDATE SET emergency=EXCLUDED.emergency, source_url=EXCLUDED.source_url, verified_at=EXCLUDED.verified_at;

INSERT INTO mini_multi_agent_02.quality_requirements (scenario, requirement_key, description, required_term) VALUES
('allergy_safety','source','장소와 안전 지침의 출처를 표시한다.','출처'),
('allergy_safety','cross_contact','식재료와 교차접촉 가능성을 직접 확인하도록 안내한다.','교차접촉'),
('allergy_safety','emergency','중증 증상이 의심되면 119 신고를 안내한다.','119'),
('allergy_safety','approval','게시 또는 사용 전에 사용자 승인을 요청한다.','승인')
ON CONFLICT (scenario, requirement_key) DO UPDATE SET description=EXCLUDED.description, required_term=EXCLUDED.required_term;
