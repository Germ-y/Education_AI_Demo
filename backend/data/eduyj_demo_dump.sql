PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE organizations (
	id VARCHAR NOT NULL,
	external_key VARCHAR,
	name VARCHAR NOT NULL,
	type VARCHAR NOT NULL,
	region_code VARCHAR,
	PRIMARY KEY (id),
	UNIQUE (external_key)
);
INSERT INTO organizations VALUES('org_yeongju_center','demo_org_yeongju_center','영주 기초학력거점지원센터','learning_support_center','47210');
CREATE TABLE school_profiles (
	id VARCHAR NOT NULL,
	office_code VARCHAR NOT NULL,
	school_code VARCHAR NOT NULL,
	school_name VARCHAR NOT NULL,
	school_kind VARCHAR NOT NULL,
	region_name VARCHAR NOT NULL,
	road_address VARCHAR NOT NULL,
	source_code VARCHAR NOT NULL,
	PRIMARY KEY (id),
	UNIQUE (school_code)
);
INSERT INTO school_profiles VALUES('school_yeongju_jungang_elementary','R10','8811046','영주중앙초등학교','초등학교','경상북도 영주시','경상북도 영주시 중앙로 126','neis_open_api');
INSERT INTO school_profiles VALUES('school_yeongju_middle','R10','8811058','영주중학교','중학교','경상북도 영주시','경상북도 영주시 남간로 29','neis_open_api');
INSERT INTO school_profiles VALUES('school_yeongju_gaheung_elementary','R10','8811067','영주가흥초등학교','초등학교','경상북도 영주시','경상북도 영주시 대동로70번길 8-9','neis_open_api');
CREATE TABLE school_calendar_events (
	id VARCHAR NOT NULL,
	school_code VARCHAR NOT NULL,
	office_code VARCHAR NOT NULL,
	academic_year VARCHAR NOT NULL,
	event_date VARCHAR NOT NULL,
	event_name VARCHAR NOT NULL,
	event_content TEXT,
	schedule_type VARCHAR,
	applies_to_grades JSON NOT NULL,
	source_code VARCHAR NOT NULL,
	retrieved_at VARCHAR NOT NULL,
	PRIMARY KEY (id)
);
INSERT INTO school_calendar_events VALUES('calendar_yeongju_jungang_20260501','8811046','R10','2026','2026-05-01','재량휴업일','','휴업일','["1", "2", "3", "4", "5", "6"]','neis_school_schedule','2026-05-02T00:00:00.000Z');
INSERT INTO school_calendar_events VALUES('calendar_yeongju_jungang_20260502','8811046','R10','2026','2026-05-02','토요휴업일','','휴업일','["1", "2", "3", "4", "5", "6"]','neis_school_schedule','2026-05-02T00:00:00.000Z');
INSERT INTO school_calendar_events VALUES('calendar_yeongju_middle_20260501','8811058','R10','2026','2026-05-01','노동절','','공휴일','["1", "2", "3"]','neis_school_schedule','2026-05-02T00:00:00.000Z');
INSERT INTO school_calendar_events VALUES('calendar_yeongju_middle_20260502','8811058','R10','2026','2026-05-02','토요휴업일','','휴업일','["1", "2", "3"]','neis_school_schedule','2026-05-02T00:00:00.000Z');
INSERT INTO school_calendar_events VALUES('calendar_yeongju_middle_20260504','8811058','R10','2026','2026-05-04','재량휴업일','','휴업일','["1", "2", "3"]','neis_school_schedule','2026-05-02T00:00:00.000Z');
INSERT INTO school_calendar_events VALUES('calendar_yeongju_gaheung_20260501','8811067','R10','2026','2026-05-01','노동절','','공휴일','["1", "2", "3", "4", "5", "6"]','neis_school_schedule','2026-05-02T00:00:00.000Z');
INSERT INTO school_calendar_events VALUES('calendar_yeongju_gaheung_20260502','8811067','R10','2026','2026-05-02','토요휴업일','','휴업일','["1", "2", "3", "4", "5", "6"]','neis_school_schedule','2026-05-02T00:00:00.000Z');
CREATE TABLE school_timetable_slots (
	id VARCHAR NOT NULL,
	school_code VARCHAR NOT NULL,
	office_code VARCHAR NOT NULL,
	academic_year VARCHAR NOT NULL,
	semester VARCHAR NOT NULL,
	timetable_date VARCHAR NOT NULL,
	grade VARCHAR NOT NULL,
	class_name VARCHAR NOT NULL,
	period INTEGER NOT NULL,
	subject_name VARCHAR,
	source_code VARCHAR NOT NULL,
	retrieved_at VARCHAR NOT NULL,
	PRIMARY KEY (id)
);
INSERT INTO school_timetable_slots VALUES('timetable_yeongju_jungang_20260501_3_1_1','8811046','R10','2026','1','2026-05-01','3','1',1,'국어','neis_els_timetable','2026-05-02T00:00:00.000Z');
INSERT INTO school_timetable_slots VALUES('timetable_yeongju_jungang_20260501_3_1_2','8811046','R10','2026','1','2026-05-01','3','1',2,'수학','neis_els_timetable','2026-05-02T00:00:00.000Z');
INSERT INTO school_timetable_slots VALUES('timetable_yeongju_jungang_20260501_3_1_3','8811046','R10','2026','1','2026-05-01','3','1',3,'사회','neis_els_timetable','2026-05-02T00:00:00.000Z');
INSERT INTO school_timetable_slots VALUES('timetable_yeongju_jungang_20260501_3_1_4','8811046','R10','2026','1','2026-05-01','3','1',4,'과학','neis_els_timetable','2026-05-02T00:00:00.000Z');
INSERT INTO school_timetable_slots VALUES('timetable_yeongju_jungang_20260501_3_1_5','8811046','R10','2026','1','2026-05-01','3','1',5,'창의적체험활동','neis_els_timetable','2026-05-02T00:00:00.000Z');
INSERT INTO school_timetable_slots VALUES('timetable_yeongju_middle_20260501_2_1_1','8811058','R10','2026','1','2026-05-01','2','1',1,'역사','neis_mis_timetable','2026-05-02T00:00:00.000Z');
INSERT INTO school_timetable_slots VALUES('timetable_yeongju_middle_20260501_2_1_2','8811058','R10','2026','1','2026-05-01','2','1',2,'동아리활동','neis_mis_timetable','2026-05-02T00:00:00.000Z');
INSERT INTO school_timetable_slots VALUES('timetable_yeongju_middle_20260501_2_1_3','8811058','R10','2026','1','2026-05-01','2','1',3,'진로와 직업','neis_mis_timetable','2026-05-02T00:00:00.000Z');
INSERT INTO school_timetable_slots VALUES('timetable_yeongju_middle_20260501_2_1_4','8811058','R10','2026','1','2026-05-01','2','1',4,'국어','neis_mis_timetable','2026-05-02T00:00:00.000Z');
INSERT INTO school_timetable_slots VALUES('timetable_yeongju_middle_20260501_2_1_5','8811058','R10','2026','1','2026-05-01','2','1',5,'과학','neis_mis_timetable','2026-05-02T00:00:00.000Z');
INSERT INTO school_timetable_slots VALUES('timetable_yeongju_middle_20260501_2_1_6','8811058','R10','2026','1','2026-05-01','2','1',6,'도덕','neis_mis_timetable','2026-05-02T00:00:00.000Z');
INSERT INTO school_timetable_slots VALUES('timetable_yeongju_gaheung_20260501_6_1_1','8811067','R10','2026','1','2026-05-01','6','1',1,'국어','neis_els_timetable','2026-05-02T00:00:00.000Z');
INSERT INTO school_timetable_slots VALUES('timetable_yeongju_gaheung_20260501_6_1_2','8811067','R10','2026','1','2026-05-01','6','1',2,'수학','neis_els_timetable','2026-05-02T00:00:00.000Z');
INSERT INTO school_timetable_slots VALUES('timetable_yeongju_gaheung_20260501_6_1_3','8811067','R10','2026','1','2026-05-01','6','1',3,'사회','neis_els_timetable','2026-05-02T00:00:00.000Z');
INSERT INTO school_timetable_slots VALUES('timetable_yeongju_gaheung_20260501_6_1_4','8811067','R10','2026','1','2026-05-01','6','1',4,'실과','neis_els_timetable','2026-05-02T00:00:00.000Z');
INSERT INTO school_timetable_slots VALUES('timetable_yeongju_gaheung_20260501_6_1_5','8811067','R10','2026','1','2026-05-01','6','1',5,'미술','neis_els_timetable','2026-05-02T00:00:00.000Z');
CREATE TABLE public_data_sources (
	id VARCHAR NOT NULL,
	source_code VARCHAR NOT NULL,
	name VARCHAR NOT NULL,
	base_url VARCHAR,
	auth_type VARCHAR NOT NULL,
	enabled BOOLEAN NOT NULL,
	PRIMARY KEY (id),
	UNIQUE (source_code)
);
INSERT INTO public_data_sources VALUES('source_neis','neis_open_api','나이스 교육정보 개방 포털','https://open.neis.go.kr/','api_key',1);
INSERT INTO public_data_sources VALUES('source_curriculum_seed','curriculum_seed','교육과정 성취기준 seed',NULL,'manual_seed',1);
CREATE TABLE agent_runs (
	id VARCHAR NOT NULL,
	agent_type VARCHAR NOT NULL,
	prompt_version VARCHAR NOT NULL,
	output_schema_name VARCHAR NOT NULL,
	input_snapshot_json JSON NOT NULL,
	output_json JSON,
	model VARCHAR NOT NULL,
	status VARCHAR NOT NULL,
	token_usage_json JSON,
	error_code VARCHAR,
	error_message TEXT,
	review_required BOOLEAN NOT NULL,
	created_at VARCHAR NOT NULL,
	completed_at VARCHAR,
	PRIMARY KEY (id)
);
CREATE TABLE audit_logs (
	id VARCHAR NOT NULL,
	actor_user_id VARCHAR,
	student_id VARCHAR,
	action VARCHAR NOT NULL,
	resource_type VARCHAR NOT NULL,
	resource_id VARCHAR,
	payload_json JSON,
	created_at VARCHAR NOT NULL,
	PRIMARY KEY (id)
);
INSERT INTO audit_logs VALUES('audit_fraction_content_approved','user_teacher_demo','student_learning_fraction','approve_content','mission_content','content_fraction_001','{"reviewSummary": "\uc804\uccb4 \ub2e8\uacc4\uc640 \uc0dd\uc131 \uc790\ub8cc\ub97c \ud559\uc0dd \uc0ac\uc6a9 \uac00\ub2a5 \uc0c1\ud0dc\ub85c \uc2b9\uc778\ud588\uc2b5\ub2c8\ub2e4."}','2026-05-02T09:00:00.000Z');
INSERT INTO audit_logs VALUES('audit_fraction_history_viewed','user_teacher_demo','student_learning_fraction','view_student_history','student','student_learning_fraction','{"reason": "\ucd5c\uadfc \ubd84\uc218 \ubbf8\uc158 \ub9ac\ud3ec\ud2b8 \ud655\uc778"}','2026-05-02T09:28:00.000Z');
INSERT INTO audit_logs VALUES('audit_bus_content_approved','user_teacher_demo','student_life_bus','approve_content','mission_content','content_bus_001','{"reviewSummary": "\uc0dd\ud65c\uc9c0\uc6d0 \uc774\ub3d9 \uacbd\ub85c \uc5f0\uc2b5 \ucf58\ud150\uce20\ub97c \ud559\uc0dd \uc0ac\uc6a9 \uac00\ub2a5 \uc0c1\ud0dc\ub85c \uc2b9\uc778\ud588\uc2b5\ub2c8\ub2e4."}','2026-05-02T09:50:00.000Z');
INSERT INTO audit_logs VALUES('audit_bus_history_viewed','user_teacher_demo','student_life_bus','view_student_history','student','student_life_bus','{"reason": "\ucd5c\uadfc \ubc84\uc2a4 \uc774\ub3d9 \uc5f0\uc2b5 \ub9ac\ud3ec\ud2b8 \ud655\uc778"}','2026-05-02T10:22:00.000Z');
CREATE TABLE users (
	id VARCHAR NOT NULL,
	organization_id VARCHAR NOT NULL,
	email VARCHAR,
	display_name VARCHAR NOT NULL,
	role VARCHAR NOT NULL,
	password_hash VARCHAR,
	status VARCHAR NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(organization_id) REFERENCES organizations (id),
	UNIQUE (email)
);
INSERT INTO users VALUES('user_teacher_demo','org_yeongju_center','teacher.demo@eduyj.local','데모 선생님','teacher',NULL,'active');
CREATE TABLE students (
	id VARCHAR NOT NULL,
	organization_id VARCHAR NOT NULL,
	external_key VARCHAR,
	display_name VARCHAR NOT NULL,
	grade VARCHAR NOT NULL,
	school_code VARCHAR,
	student_type VARCHAR NOT NULL,
	primary_need VARCHAR NOT NULL,
	profile_json JSON NOT NULL,
	status VARCHAR NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(organization_id) REFERENCES organizations (id),
	UNIQUE (external_key)
);
INSERT INTO students VALUES('student_learning_clock','org_yeongju_center','demo_student_learning_clock','김지우','elementary_3','8811046','learning_focus','시간 읽기 기초를 짧은 시각 단서와 2개 선택지로 익히는 수업이 좋겠어요.','{"ageBand": "younger", "gradeNumber": "3", "className": "1", "readingLoad": "very_low", "choiceCountLimit": 2, "dashboard": {"attendanceRate": null, "gradeLabel": "\ucd083", "studentTypeLabel": "\ud559\uc2b5\uc9c0\uc6d0\ud615", "trackLabel": "\uc800\uc5f0\ub839 \ud559\uc2b5\uc9c0\uc6d0\ud615", "statusLabel": "\uc790\ub8cc \uc0dd\uc131", "attendanceLabel": "\uae30\ub85d \uc804", "summaryLine": "\uc9e7\uc740 \uc2dc\uac01 \ub2e8\uc11c\uc640 2\uac1c \uc120\ud0dd\uc9c0\ub85c \uc2dc\uac04 \uc77d\uae30 \uae30\ucd08\ub97c \uc775\ud788\ub294 \uc218\uc5c5\uc774 \uc798 \ub9de\uc544 \ubcf4\uc5ec\uc694.", "primaryNeedTitle": "\uc2dc\uac04 \uc77d\uae30 \uae30\ucd08 \ubcf4\uc644 \uc218\uc5c5", "primaryNeedDetail": "\uae34 \uc124\uba85\ubcf4\ub2e4 \uc9e7\uc740 \uc2dc\uac01 \ub2e8\uc11c\ub85c \uc2dc\uce68\uacfc \ubd84\uce68\uc744 \uad6c\ubd84\ud558\uace0 \uc77d\ub294 \uc21c\uc11c\ub97c \uc775\ud788\ub294 \uc218\uc5c5\uc774 \uc88b\uaca0\uc5b4\uc694.", "supportStrategyTitle": "\uc2dc\uac01 \ub2e8\uc11c \uae30\ubc18 2\uc9c0\uc120\ub2e4 \uc218\uc5c5", "supportStrategyDetail": "\ud55c \ubb38\uc7a5 \uc9c0\uc2dc, \ud070 \uadf8\ub9bc \ub2e8\uc11c, 2\uac1c \uc120\ud0dd\uc9c0\ub97c \uc0ac\uc6a9\ud574 \uc2dc\uac04 \uc77d\uae30 \uc21c\uc11c\ub97c \uc548\uc815\ud654\ud558\ub294 \ucf58\ud150\uce20\uac00 \uc88b\uaca0\uc5b4\uc694.", "strengths": ["\uadf8\ub9bc\uc5d0\uc11c \uc911\uc694\ud55c \ub2e8\uc11c\ub97c \uba3c\uc800 \ucc3e\uc73c\uba74 \ubc14\ub85c \ubc18\uc751\ud574\uc694.", "\uc120\ud0dd\uc9c0\uac00 2\uac1c\uc77c \ub54c \ubd80\ub2f4\uc774 \uc904\uace0 \uc548\uc815\uc801\uc73c\ub85c \uace0\ub97c \uc218 \uc788\uc5b4\uc694.", "\ub9c8\uc2a4\ucf54\ud2b8\uac00 \uc9e7\uac8c \uc548\ub0b4\ud558\uba74 \uc2dc\uc120\uc744 \uc798 \ubaa8\uc544\uc694."], "weaknesses": ["\ubb38\uc7a5\uc774 \uae38\uc5b4\uc9c0\uba74 \ubb34\uc5c7\ubd80\ud130 \ud574\uc57c \ud560\uc9c0 \uba48\uce6b\ud560 \uc218 \uc788\uc5b4\uc694.", "\uc2dc\uacc4\ub97c \uc77d\uc744 \ub54c \uc9e7\uc740 \ubc14\ub298\ubd80\ud130 \ubd10\uc57c \ud558\ub294 \uc21c\uc11c\uac00 \ud754\ub4e4\ub824\uc694.", "\ud2c0\ub9b0 \ub4a4\uc5d0\ub294 \ub2e4\uc2dc \uc2dc\ub3c4\ud558\uae30\uae4c\uc9c0 \uc2dc\uac04\uc774 \uc870\uae08 \ud544\uc694\ud574\uc694."], "emotionalNote": "\ucc98\uc74c \ubb38\ud56d\uc5d0\uc11c \uc131\uacf5 \uacbd\ud5d8\uc744 \uc5bb\uc73c\uba74 \uc774\ud6c4 \ucc38\uc5ec\uac00 \uc548\uc815\ub429\ub2c8\ub2e4.", "responsePattern": "\uadf8\ub9bc\uc744 \uba3c\uc800 \ubcf4\uace0, \ud55c \ubb38\uc7a5 \uc9c0\uc2dc\uc640 2\uac1c \uc120\ud0dd\uc9c0\ub97c \ubc1b\uc744 \ub54c \ubc18\uc751\uc774 \uac00\uc7a5 \uc88b\uc2b5\ub2c8\ub2e4.", "guardianCooperation": "\ubcf4\ud638\uc790\ub294 \uac00\uc815\uc5d0\uc11c \uc9e7\uc740 \uc2dc\uacc4 \uc77d\uae30 \uc5f0\uc2b5\uc744 \ub3c4\uc6b8 \uc218 \uc788\uc73c\ub098, \uae34 \ud559\uc2b5\uc9c0\ub294 \ubd80\ub2f4\uc774 \ud07d\ub2c8\ub2e4.", "schoolContextNote": "NEIS \ud559\uad50 \uae30\ubcf8\uc815\ubcf4\uc640 \uc2dc\uac04\ud45c\ub97c \uc5f0\uacb0\ud574 \ud559\uad50 \uc218\uc5c5 \ud750\ub984\uacfc \ud68c\uae30 \ubaa9\ud45c\ub97c \ud568\uaed8 \ud655\uc778\ud569\ub2c8\ub2e4.", "nextSessionFocus": ["\uc2dc\uac04 \uc77d\uae30 \uc21c\uc11c \uc775\ud788\uae30", "2\uac1c \uc120\ud0dd\uc9c0\ub85c \uc815\uac01 \uc2dc\uac04 \ud655\uc778\ud558\uae30", "\uccab \ubb38\ud56d\uc740 \uc26c\uc6b4 \uc131\uacf5 \uacbd\ud5d8\uc73c\ub85c \uc2dc\uc791"], "aiContextSummary": "\ucd083 \uc800\uc5f0\ub839 \ud559\uc2b5\uc9c0\uc6d0\ud615 \ud559\uc0dd. \uc2dc\uac04 \uc77d\uae30 \uae30\ucd08 \ubcf4\uc644 \uc218\uc5c5\uc774 \uc798 \ub9de\uc544 \ubcf4\uc5ec\uc694. \uae34 \ubb38\uc7a5 \uc124\uba85\ubcf4\ub2e4 \uc9e7\uc740 \uc2dc\uac01 \ub2e8\uc11c\uc640 2\uac1c \uc120\ud0dd\uc9c0\ub97c \uc911\uc2ec\uc73c\ub85c \ud55c \uc131\uacf5 \uacbd\ud5d8\ud615 \ucf58\ud150\uce20\ub85c \uc2dc\uc791\ud558\uba74 \uc88b\uaca0\uc5b4\uc694."}}','active');
INSERT INTO students VALUES('student_learning_fraction','org_yeongju_center','demo_student_learning_fraction','이민준','middle_2','8811058','learning_focus','분수의 전체-부분 관계를 단계적으로 익히는 개념 보완 수업이 좋겠어요.','{"ageBand": "older", "gradeNumber": "2", "className": "1", "interests": ["\uc694\ub9ac", "\ud0d0\ud5d8"], "readingLoad": "low", "choiceCountLimit": 3, "dashboard": {"attendanceRate": 95, "gradeLabel": "\uc9112", "studentTypeLabel": "\ud559\uc2b5\uc9c0\uc6d0\ud615", "trackLabel": "\uace0\uc5f0\ub839 \ud559\uc2b5\uc9c0\uc6d0\ud615", "statusLabel": "\uc790\ub8cc \uac80\ud1a0", "attendanceLabel": "95%", "summaryLine": "\ubd84\uc218\uc758 \uc804\uccb4-\ubd80\ubd84 \uad00\uacc4\ub97c \uc808\ucc28\uc801\uc73c\ub85c \uc775\ud788\ub294 \uac1c\ub150 \ubcf4\uc644 \uc218\uc5c5\uc774 \uc798 \ub9de\uc544 \ubcf4\uc5ec\uc694.", "primaryNeedTitle": "\ubd84\uc218 \uac1c\ub150 \ubcf4\uc644 \uc218\uc5c5", "primaryNeedDetail": "\uc804\uccb4\uc640 \ubd80\ubd84\uc744 \uad6c\ubd84\ud558\uace0 \ubd84\ubaa8\u00b7\ubd84\uc790\uc758 \uc758\ubbf8\ub97c \uc21c\uc11c\ub300\ub85c \uc5f0\uacb0\ud558\ub294 \uc218\uc5c5\uc774 \uc88b\uaca0\uc5b4\uc694.", "supportStrategyTitle": "\uc2dc\uac01 \uc790\ub8cc + \ub2e8\uacc4 \uce74\ub4dc + \ub9d0\ub85c \uc815\ub9ac\ud558\uae30", "supportStrategyDetail": "\uc2dc\uac01 \uc790\ub8cc, \ub2e8\uacc4 \uce74\ub4dc, \ube48\uce78 \ud655\uc778, \ub9d0\ub85c \uc815\ub9ac\ud558\uae30\ub97c \uc0ac\uc6a9\ud574 \uc804\uccb4-\ubd80\ubd84 \uad00\uacc4\ub97c \ubc18\ubcf5 \uc5f0\uacb0\ud558\ub294 \ucf58\ud150\uce20\uac00 \uc88b\uaca0\uc5b4\uc694.", "strengths": ["\uadf8\ub9bc\uc774\ub098 \uc870\uac01 \ubaa8\ub378\uc744 \ubcf4\uba74 \uc804\uccb4\uc640 \ubd80\ubd84\uc744 \ub354 \uc27d\uac8c \uc774\ud574\ud574\uc694.", "\uacfc\uc815\uc744 \uc791\uc740 \ub2e8\uacc4\ub85c \ub098\ub204\uba74 \ub05d\uae4c\uc9c0 \ub530\ub77c\uc62c \uc218 \uc788\uc5b4\uc694.", "\uc694\ub9ac\ub098 \ud0d0\ud5d8\ucc98\ub7fc \uad6c\uccb4\uc801\uc778 \uc18c\uc7ac\uac00 \uc788\uc73c\uba74 \ucc38\uc5ec\uac00 \uc88b\uc544\uc838\uc694."], "weaknesses": ["\ubd84\ubaa8\uc640 \ubd84\uc790\uac00 \uac01\uac01 \ubb34\uc5c7\uc744 \ub73b\ud558\ub294\uc9c0 \uc790\uc8fc \ubc14\uafd4 \uc0dd\uac01\ud574\uc694.", "\ubb38\uc81c \uc124\uba85\uc774 \uae38\uba74 \uc911\uc694\ud55c \uc870\uac74\uc744 \ub193\uce60 \uc218 \uc788\uc5b4\uc694.", "\uc751\uc6a9 \ubb38\uc81c\uc5d0\uc11c\ub294 \uc804\uccb4\ub97c \uba3c\uc800 \ud655\uc778\ud558\ub294 \uc21c\uc11c\uac00 \ud754\ub4e4\ub824\uc694."], "emotionalNote": "\uccab \uc624\ub2f5 \ub4a4\uc5d0\ub3c4 \uc774\uc720\ub97c \uc9e7\uac8c \uc124\uba85\ud558\uba74 \ub2e4\uc2dc \uc2dc\ub3c4\ud569\ub2c8\ub2e4.", "responsePattern": "\uc808\ucc28\ub97c \uce74\ub4dc\ucc98\ub7fc \ub098\ub204\uc5b4 \ubcf4\uc5ec\uc8fc\uba74 \ub530\ub77c\uc624\uace0, \ub9c8\uc9c0\ub9c9\uc5d0 \uc790\uae30 \ub9d0\ub85c \uc124\uba85\ud558\ub294 \ub2e8\uacc4\uac00 \ud6a8\uacfc\uc801\uc785\ub2c8\ub2e4.", "guardianCooperation": "\ubcf4\ud638\uc790 \ud611\uc870\ub294 \ubcf4\ud1b5 \uc218\uc900\uc774\uba70, \uac00\uc815 \ubcf5\uc2b5\uc740 \uc9e7\uc740 \uc608\uc2dc 1\uac1c \uc815\ub3c4\uac00 \uc801\ud569\ud569\ub2c8\ub2e4.", "schoolContextNote": "NEIS \uc2dc\uac04\ud45c\uc5d0\uc11c \ucd5c\uadfc \uc218\ud559 \uc218\uc5c5 \ud750\ub984\uc744 \ud655\uc778\ud574 \ubd84\uc218 \ubcf5\uc2b5 \ucf58\ud150\uce20\uc640 \uc5f0\uacb0\ud569\ub2c8\ub2e4.", "nextSessionFocus": ["\uc804\uccb4\uc640 \ubd80\ubd84 \uad6c\ubd84\ud558\uae30", "\ubd84\ubaa8\u00b7\ubd84\uc790 \uc758\ubbf8 \uc5f0\uacb0\ud558\uae30", "\ub9d0\ub85c \uc9e7\uac8c \uc815\ub9ac\ud558\uae30"], "aiContextSummary": "\uc9112 \uace0\uc5f0\ub839 \ud559\uc2b5\uc9c0\uc6d0\ud615 \ud559\uc0dd. \ubd84\uc218\uc758 \uc804\uccb4-\ubd80\ubd84 \uad00\uacc4\ub97c \ub2e8\uacc4\uc801\uc73c\ub85c \uc775\ud788\ub294 \uac1c\ub150 \ubcf4\uc644 \uc218\uc5c5\uc774 \uc798 \ub9de\uc544 \ubcf4\uc5ec\uc694. \uc2dc\uac01 \uc790\ub8cc\uc640 \uc9e7\uc740 \ub2e8\uacc4 \uce74\ub4dc\ub85c \uc808\ucc28\ub97c \ub098\ub208 \ucf58\ud150\uce20\uac00 \uc88b\uaca0\uc5b4\uc694."}}','active');
INSERT INTO students VALUES('student_life_bus','org_yeongju_center','demo_student_life_bus','박수민','elementary_6','8811067','life_support','생활 상황에서 순서 확인과 도움 요청 표현을 연습하는 의사소통 수업이 좋겠어요.','{"ageBand": "life_support", "gradeNumber": "6", "className": "1", "interests": ["\ub3d9\ub124 \uc9c0\ub3c4", "\uc5ed\ud560\uadf9"], "readingLoad": "very_low", "choiceCountLimit": 2, "dashboard": {"attendanceRate": 91, "gradeLabel": "\ucd086", "studentTypeLabel": "\uc77c\uc0c1\uc0dd\ud65c \uc9c0\uc6d0\ud615", "trackLabel": "\uc77c\uc0c1\uc0dd\ud65c \uc9c0\uc6d0\ud615", "statusLabel": "\ud559\uc2b5", "attendanceLabel": "91%", "summaryLine": "\uc0dd\ud65c \uc0c1\ud669\uc5d0\uc11c \uc21c\uc11c\ub97c \ud655\uc778\ud558\uace0 \ub3c4\uc6c0 \uc694\uccad \ud45c\ud604\uc744 \ub9d0\ud558\ub294 \uc758\uc0ac\uc18c\ud1b5 \uc218\uc5c5\uc774 \uc798 \ub9de\uc544 \ubcf4\uc5ec\uc694.", "primaryNeedTitle": "\uc77c\uc0c1\uc0dd\ud65c \uc758\uc0ac\uc18c\ud1b5 \uc218\uc5c5", "primaryNeedDetail": "\ub0af\uc120 \uc0dd\ud65c \uc0c1\ud669\uc5d0\uc11c \ub2e8\uc11c\ub97c \ud655\uc778\ud558\uace0 \ud544\uc694\ud55c \ub3c4\uc6c0 \uc694\uccad \ubb38\uc7a5\uc744 \uc9e7\uac8c \ub9d0\ud558\ub294 \uc218\uc5c5\uc774 \uc88b\uaca0\uc5b4\uc694.", "supportStrategyTitle": "\uc0c1\ud669 \uadf8\ub9bc + \uc21c\uc11c \uce74\ub4dc + \uc5ed\ud560 \ubc1c\ud654", "supportStrategyDetail": "\uc0c1\ud669 \uadf8\ub9bc, \uc21c\uc11c \uce74\ub4dc, \uc9e7\uc740 \ubaa8\ub378 \ubb38\uc7a5, \uc2e4\uc2dc\uac04 \uc5ed\ud560 \ubc1c\ud654 \uc5f0\uc2b5\uc744 \uc870\ud569\ud55c \ucf58\ud150\uce20\uac00 \uc88b\uaca0\uc5b4\uc694.", "strengths": ["\uc0c1\ud669 \uadf8\ub9bc\uc744 \ubcf4\uba74 \uc9c0\uae08 \uc5b4\ub514\uc11c \ubb34\uc5c7\uc744 \ud574\uc57c \ud558\ub294\uc9c0 \uc798 \ud30c\uc545\ud574\uc694.", "\uc5ed\ud560 \uc5f0\uc2b5\uc5d0\uc11c\ub294 \uc9e7\uc740 \ubb38\uc7a5\uc744 \ub530\ub77c \ub9d0\ud558\ub824\ub294 \uc2dc\ub3c4\uac00 \uc88b\uc544\uc694.", "\ub3d9\ub124 \uc9c0\ub3c4\ub098 \uc2e4\uc81c \uc774\ub3d9 \uc7a5\uba74\uc774 \ub098\uc624\uba74 \uad00\uc2ec\uc744 \uc624\ub798 \uc720\uc9c0\ud574\uc694."], "weaknesses": ["\uc5ec\ub7ec \uc774\ub3d9 \ub2e8\uacc4\ub97c \ud55c \ubc88\uc5d0 \uc815\ub9ac\ud558\uba74 \uc21c\uc11c\uac00 \ud5f7\uac08\ub9b4 \uc218 \uc788\uc5b4\uc694.", "\ub3c4\uc6c0\uc774 \ud544\uc694\ud574\ub3c4 \uba3c\uc800 \ub9d0\ub85c \uc694\uccad\ud558\ub294 \uac83\uc740 \uc544\uc9c1 \ubd80\ub2f4\uc2a4\ub7ec\uc6cc\ud574\uc694.", "\ub0af\uc120 \uc7a5\uc18c\uc5d0\uc11c\ub294 \ub2e4\uc74c \ud589\ub3d9\uc744 \ud655\uc778\ud574 \uc8fc\ub294 \ub2e8\uc11c\uac00 \ud544\uc694\ud574\uc694."], "emotionalNote": "\uc0c8\ub85c\uc6b4 \uc7a5\uc18c\ub97c \uc0c1\uc0c1\ud560 \ub54c \ubd88\uc548\uc774 \uc62c\ub77c\uac00\uc9c0\ub9cc, \uc608\uace0 \uc774\ubbf8\uc9c0\uac00 \uc788\uc73c\uba74 \ucc38\uc5ec\uac00 \uc548\uc815\ub429\ub2c8\ub2e4.", "responsePattern": "\uc2dc\uac01 \uc21c\uc11c \uce74\ub4dc\uc640 \uc9e7\uc740 \ubaa8\ub378 \ubb38\uc7a5\uc744 \uba3c\uc800 \uc81c\uacf5\ud558\uba74 \uc2e4\uc81c \ub9d0\ud558\uae30 \uc2dc\ub3c4\uac00 \ub298\uc5b4\ub0a9\ub2c8\ub2e4.", "guardianCooperation": "\ubcf4\ud638\uc790\uc640 \uc13c\ud130 \uc774\ub3d9 \ub3d9\uc120\uc744 \ud568\uaed8 \ud655\uc778\ud558\uba74 \uc2e4\uc81c \uc801\uc6a9 \uac00\ub2a5\uc131\uc774 \ub192\uc2b5\ub2c8\ub2e4.", "schoolContextNote": "NEIS \ud559\uad50 \uc77c\uc815\uacfc \uc2dc\uac04\ud45c\ub97c \ud655\uc778\ud574 \uc13c\ud130 \ubc29\ubb38 \ud68c\uae30 \uc804 \ud53c\ub85c\ub3c4\uc640 \uc774\ub3d9 \uc2dc\uac04\uc744 \ud568\uaed8 \uace0\ub824\ud569\ub2c8\ub2e4.", "nextSessionFocus": ["\uc0dd\ud65c \uc0c1\ud669 \ub2e8\uc11c \ud655\uc778\ud558\uae30", "\ub3c4\uc6c0 \uc694\uccad \ubb38\uc7a5 1\uac1c \ub9d0\ud558\uae30", "\ub2e4\uc74c \ud589\ub3d9 \uc9e7\uac8c \ud655\uc778\ud558\uae30"], "aiContextSummary": "\ucd086 \uc77c\uc0c1\uc0dd\ud65c \uc9c0\uc6d0\ud615 \ud559\uc0dd. \uc0dd\ud65c \uc0c1\ud669\uc5d0\uc11c \uc21c\uc11c\ub97c \ud655\uc778\ud558\uace0 \ub3c4\uc6c0 \uc694\uccad \ud45c\ud604\uc744 \ub9d0\ud558\ub294 \uc758\uc0ac\uc18c\ud1b5 \uc218\uc5c5\uc774 \uc798 \ub9de\uc544 \ubcf4\uc5ec\uc694. \uc0c1\ud669 \uadf8\ub9bc\uacfc \uc21c\uc11c \uce74\ub4dc \ub4a4 \uc2e4\uc2dc\uac04 \uc5ed\ud560 \ubc1c\ud654 \uc5f0\uc2b5\uc73c\ub85c \uc774\uc5b4\uc9c0\ub294 \ucf58\ud150\uce20\uac00 \uc88b\uaca0\uc5b4\uc694."}}','active');
CREATE TABLE student_accounts (
	id VARCHAR NOT NULL,
	student_id VARCHAR NOT NULL,
	access_code VARCHAR NOT NULL,
	status VARCHAR NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(student_id) REFERENCES students (id),
	UNIQUE (access_code)
);
INSERT INTO student_accounts VALUES('student_account_learning','student_learning_fraction','STAR-001','active');
INSERT INTO student_accounts VALUES('student_account_life','student_life_bus','STAR-002','active');
INSERT INTO student_accounts VALUES('student_account_clock','student_learning_clock','STAR-003','active');
CREATE TABLE support_cases (
	id VARCHAR NOT NULL,
	student_id VARCHAR NOT NULL,
	owner_teacher_id VARCHAR NOT NULL,
	case_status VARCHAR NOT NULL,
	current_goal TEXT NOT NULL,
	dashboard_stage VARCHAR NOT NULL,
	support_strategy TEXT,
	opened_at VARCHAR NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(student_id) REFERENCES students (id),
	FOREIGN KEY(owner_teacher_id) REFERENCES users (id)
);
INSERT INTO support_cases VALUES('case_learning_clock','student_learning_clock','user_teacher_demo','open','시간 읽기 기초를 짧은 시각 단서와 2개 선택지로 익혀보면 좋겠어요.','material_generation','그림 먼저 보기와 2개 선택지로 첫 성공 경험을 만든 뒤 짧은 음성 안내를 연결','2026-05-02T00:00:00.000Z');
INSERT INTO support_cases VALUES('case_learning_fraction','student_learning_fraction','user_teacher_demo','open','분수의 전체-부분 관계를 단계 카드로 안정화해보면 좋겠어요.','material_review','그림 자료와 짧은 단계 설명으로 분모/분자 위치를 반복 확인','2026-05-02T00:00:00.000Z');
INSERT INTO support_cases VALUES('case_life_bus','student_life_bus','user_teacher_demo','open','생활 상황에서 순서 확인과 도움 요청 표현을 연습해보면 좋겠어요.','learning','상황 그림과 역할 연습으로 도움 요청 문장을 짧게 반복','2026-05-02T00:00:00.000Z');
CREATE TABLE case_notes (
	id VARCHAR NOT NULL,
	case_id VARCHAR NOT NULL,
	author_id VARCHAR NOT NULL,
	note_type VARCHAR NOT NULL,
	body TEXT NOT NULL,
	visibility VARCHAR NOT NULL,
	created_at VARCHAR NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(case_id) REFERENCES support_cases (id),
	FOREIGN KEY(author_id) REFERENCES users (id)
);
INSERT INTO case_notes VALUES('note_clock_001','case_learning_clock','user_teacher_demo','teacher_comment','시계 그림을 먼저 보여주면 짧은 바늘은 빠르게 찾지만, 긴 문장 지시가 나오면 첫 행동을 시작하기까지 시간이 걸림.','teacher_only','2026-05-02T00:00:00.000Z');
INSERT INTO case_notes VALUES('note_fraction_001','case_learning_fraction','user_teacher_demo','session','긴 설명보다 그림을 먼저 보여주면 집중이 좋아짐. 4/1 선택 경험 있음.','teacher_only','2026-05-02T00:00:00.000Z');
INSERT INTO case_notes VALUES('note_bus_001','case_life_bus','user_teacher_demo','consultation','새로운 장소에 갈 때 순서를 놓치면 불안해함. 도움 요청 문장 연습 필요.','teacher_only','2026-05-02T00:00:00.000Z');
CREATE TABLE memory_cards (
	id VARCHAR NOT NULL,
	student_id VARCHAR NOT NULL,
	case_id VARCHAR NOT NULL,
	version INTEGER NOT NULL,
	learning_problem_types JSON NOT NULL,
	recent_4w_response_json JSON NOT NULL,
	emotional_state_note TEXT,
	effective_explanation_styles JSON NOT NULL,
	frequent_blocking_units JSON NOT NULL,
	guardian_cooperation_status VARCHAR,
	next_session_cautions JSON NOT NULL,
	teacher_verified_at VARCHAR,
	status VARCHAR NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(student_id) REFERENCES students (id),
	FOREIGN KEY(case_id) REFERENCES support_cases (id)
);
INSERT INTO memory_cards VALUES('memory_clock_active','student_learning_clock','case_learning_clock',1,'["time_reading_sequence", "instruction_start_burden"]','{"summary": "\uadf8\ub9bc \ub2e8\uc11c\uc5d0\ub294 \ube60\ub974\uac8c \ubc18\uc751\ud558\uc9c0\ub9cc \uae34 \ubb38\uc7a5 \uc9c0\uc2dc\uc5d0\uc11c \uccab \ud589\ub3d9 \uc2dc\uc791\uc774 \ub2a6\uc5b4\uc9d0"}','쉬운 첫 문항을 성공하면 이후 선택 반응이 안정됩니다.','["scenario_image", "two_choice", "short_audio"]','["clock_hour_hand", "reading_order"]','home_short_practice_possible','["\uae34 \uc9c0\uc2dc\ubb38\uc744 \uba3c\uc800 \uc81c\uc2dc\ud558\uc9c0 \uc54a\uae30", "\uc9e7\uc740 \ubc14\ub298 \ucc3e\uae30 \uc131\uacf5 \ud6c4 \uae34 \ubc14\ub298\ub85c \ud655\uc7a5"]','2026-05-02T00:00:00.000Z','active');
INSERT INTO memory_cards VALUES('memory_fraction_active','student_learning_fraction','case_learning_fraction',1,'["concept_misunderstanding", "numerator_denominator_confusion"]','{"summary": "\uc2dc\uac01 \uc790\ub8cc \ubc18\uc751\uc740 \uc88b\uc73c\ub098 \ubd84\ubaa8/\ubd84\uc790 \uc704\uce58 \ud63c\ub3d9\uc774 \ubc18\ubcf5\ub428"}','첫 문항 성공 경험이 필요함.','["visual_example", "short_steps", "mascot_teach_back"]','["fractions", "word_problem_conditions"]','normal','["\uc804\uccb4 \uc218\ub97c \uba3c\uc800 \uc138\uace0 \uace0\ub978 \uc218\ub97c \ub098\uc911\uc5d0 \uc138\uae30", "\uae34 \ubb38\uc7a5 \uc124\uba85 \ud53c\ud558\uae30"]','2026-05-02T00:00:00.000Z','active');
INSERT INTO memory_cards VALUES('memory_bus_active','student_life_bus','case_life_bus',1,'["sequence_planning", "help_request_avoidance"]','{"summary": "\uc2dc\uac01 \uc21c\uc11c \uce74\ub4dc\uc5d0\ub294 \uc798 \ubc18\uc751\ud558\uc9c0\ub9cc \uc2e4\uc81c \ub9d0\ud558\uae30\uc5d0\uc11c \uba48\ucda4\uc774 \uc788\uc74c"}','역할극 전 이미지 예고가 효과적임.','["scenario_image", "two_choice", "roleplay"]','["daily_route", "asking_help"]','needs_followup','["\ub3c4\uc6c0 \uc694\uccad \ubb38\uc7a5\uc744 \uba3c\uc800 \uc5f0\uc2b5", "\uc120\ud0dd\uc9c0\ub294 2\uac1c \uc704\uc8fc\ub85c \uc81c\uacf5"]','2026-05-02T00:00:00.000Z','active');
CREATE TABLE planner_items (
	id VARCHAR NOT NULL,
	student_id VARCHAR NOT NULL,
	case_id VARCHAR NOT NULL,
	period_type VARCHAR NOT NULL,
	goal_text TEXT NOT NULL,
	checklist_json JSON NOT NULL,
	status VARCHAR NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(student_id) REFERENCES students (id),
	FOREIGN KEY(case_id) REFERENCES support_cases (id)
);
INSERT INTO planner_items VALUES('planner_clock_next','student_learning_clock','case_learning_clock','next_session','시간 읽기 기초를 짧은 시각 단서와 2개 선택지로 익혀보면 좋겠어요.','{"checks": ["\uc9e7\uc740 \ubc14\ub298 \ucc3e\uae30", "2\uac1c \uc120\ud0dd\uc9c0\uc5d0\uc11c \uc2dc\uac04 \uace0\ub974\uae30"]}','planned');
INSERT INTO planner_items VALUES('planner_fraction_next','student_learning_fraction','case_learning_fraction','next_session','분수의 전체-부분 관계를 단계 카드로 설명해보면 좋겠어요.','{"checks": ["\uccab \ubb38\uc81c \uc131\uacf5\uacbd\ud5d8", "\ubd84\ubaa8/\ubd84\uc790 \uc704\uce58 \uc7ac\ud655\uc778"]}','planned');
INSERT INTO planner_items VALUES('planner_bus_next','student_life_bus','case_life_bus','next_session','생활 상황에서 도움 요청 문장 1개를 말해보면 좋겠어요.','{"checks": ["\ubaa9\uc801\uc9c0 \ub9d0\ud558\uae30", "\ub3c4\uc6c0 \uc694\uccad\ud558\uae30"]}','planned');
CREATE TABLE mission_contents (
	id VARCHAR NOT NULL,
	case_id VARCHAR NOT NULL,
	student_id VARCHAR NOT NULL,
	content_type VARCHAR NOT NULL,
	title VARCHAR NOT NULL,
	session_goal TEXT NOT NULL,
	status VARCHAR NOT NULL,
	total_steps INTEGER NOT NULL,
	brief_json JSON NOT NULL,
	teacher_review_summary TEXT,
	approved_by_user_id VARCHAR,
	approved_at VARCHAR,
	published_at VARCHAR,
	PRIMARY KEY (id),
	FOREIGN KEY(case_id) REFERENCES support_cases (id),
	FOREIGN KEY(student_id) REFERENCES students (id)
);
INSERT INTO mission_contents VALUES('content_clock_001','case_learning_clock','student_learning_clock','learning_focus','시계 탐험: 약속 시간 찾기','시계 그림에서 시침과 분침 단서를 보고 약속 시간을 고른다.','published',4,'{"achievementStandard": "\uc2dc\uacc4\uc758 \uc2dc\uce68\uacfc \ubd84\uce68\uc744 \ubcf4\uace0 \uc815\uac01 \uc2dc\uac04\uc744 \uc77d\uc744 \uc218 \uc788\ub2e4.", "strategy": "\uadf8\ub9bc \ub2e8\uc11c, 2\uac1c \uc120\ud0dd\uc9c0, \uc9e7\uc740 \uc9c0\uc2dc\ubb38, 4\ub2e8\uacc4 \ub9d0\ub85c \ub2e4\uc2dc \uc124\uba85\ud558\ub294 \uc2e4\uc2dc\uac04 \ubc1c\ud654 \uc5f0\uc2b5"}','긴 설명보다 시계 그림 단서를 먼저 보고, 짧은 선택지로 첫 행동을 고르는 흐름입니다.','user_teacher_demo','2026-05-02T00:00:00.000Z','2026-05-02T00:00:00.000Z');
INSERT INTO mission_contents VALUES('content_fraction_001','case_learning_fraction','student_learning_fraction','learning_focus','분수 탐험: 빛나는 한 조각','전체 4개 중 1개를 1/4로 표현하고 말로 설명한다.','published',4,'{"achievementStandard": "\uc804\uccb4\uc640 \ubd80\ubd84\uc758 \uad00\uacc4\ub97c \ubd84\uc218\ub85c \ud45c\ud604\ud560 \uc218 \uc788\ub2e4.", "strategy": "\uc2dc\uac01 \uc790\ub8cc\uc640 \uc9e7\uc740 \uc124\uba85, 4\ub2e8\uacc4 \ub9d0\ub85c \ub2e4\uc2dc \uc124\uba85\ud558\ub294 \uc2e4\uc2dc\uac04 \ubc1c\ud654 \uc5f0\uc2b5"}','분모/분자 위치 혼동을 줄이기 위해 전체 수를 먼저 세는 흐름입니다.','user_teacher_demo','2026-05-02T00:00:00.000Z','2026-05-02T00:00:00.000Z');
INSERT INTO mission_contents VALUES('content_bus_001','case_life_bus','student_life_bus','life_support','센터 가는 길: 버스 타기','버스를 타고 센터에 갈 때 필요한 단서와 도움 요청 문장을 연습한다.','published',4,'{"strategy": "\uc0dd\ud65c \uc7a5\uba74 \uc774\ubbf8\uc9c0, \ub2e8\uc11c \ucc3e\uae30, \ud589\ub3d9 \uc120\ud0dd, 4\ub2e8\uacc4 \uc2e4\uc2dc\uac04 \uc5ed\ud560 \ubc1c\ud654 \uc5f0\uc2b5"}','버스 번호/정류장/도움 요청을 차례대로 확인하는 생활지원형 미션입니다.','user_teacher_demo','2026-05-02T00:00:00.000Z','2026-05-02T00:00:00.000Z');
CREATE TABLE content_stages (
	id VARCHAR NOT NULL,
	mission_content_id VARCHAR NOT NULL,
	step INTEGER NOT NULL,
	stage_role VARCHAR NOT NULL,
	template_type VARCHAR NOT NULL,
	student_title VARCHAR NOT NULL,
	student_instruction TEXT NOT NULL,
	template_json JSON NOT NULL,
	realtime_spec_json JSON,
	sort_order INTEGER NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(mission_content_id) REFERENCES mission_contents (id)
);
INSERT INTO content_stages VALUES('stage_clock_1','content_clock_001',1,'concept_intro','concept_intro','개념 열기','시침과 분침이 어디에 있는지 보세요.','{"imageAssetId": "asset_content_clock_001_stage_1", "audioAssetId": "asset_content_clock_001_stage_1_audio", "storyText": "\uc9c0\uc6b0\uac00 \uc57d\uc18d \uc2dc\uac04\uc5d0 \ub9de\ucdb0 \uc900\ube44\ud558\ub824\uace0 \uc2dc\uacc4\ub97c \ubcf4\uace0 \uc788\uc5b4\uc694.", "missionText": "\uba3c\uc800 \uc9e7\uc740 \ubc14\ub298\uacfc \uae34 \ubc14\ub298\uc744 \ucc3e\uc544\ubd05\uc2dc\ub2e4.", "assetBundle": {"imageAssetId": "asset_content_clock_001_stage_1", "audioAssetId": "asset_content_clock_001_stage_1_audio"}}','null',1);
INSERT INTO content_stages VALUES('stage_clock_2','content_clock_001',2,'basic_problem','scene_question','문제 1','짧은 바늘이 가리키는 숫자를 고르세요.','{"imageAssetId": "asset_content_clock_001_stage_2", "audioAssetId": "asset_content_clock_001_stage_2_audio", "question": "\uc9e7\uc740 \ubc14\ub298\uc740 \uc5b4\ub290 \uc22b\uc790\ub97c \uac00\ub9ac\ud0a4\ub098\uc694?", "choices": [{"id": "a", "text": "3"}, {"id": "b", "text": "6"}], "answer": "a", "correctFeedback": "\ub9de\uc544\uc694. \uc9e7\uc740 \ubc14\ub298\uc774 3\uc744 \uac00\ub9ac\ud0a4\uace0 \uc788\uc5b4\uc694.", "wrongFeedback": "\uc9e7\uc740 \ubc14\ub298\uc744 \uba3c\uc800 \ucc3e\uc544\ubd05\uc2dc\ub2e4.", "assetBundle": {"imageAssetId": "asset_content_clock_001_stage_2", "audioAssetId": "asset_content_clock_001_stage_2_audio"}}','null',2);
INSERT INTO content_stages VALUES('stage_clock_3','content_clock_001',3,'applied_problem','sequence_ordering','문제 2','시계를 읽는 순서를 고르세요.','{"imageAssetId": "asset_content_clock_001_stage_3", "audioAssetId": "asset_content_clock_001_stage_3_audio", "question": "\uc2dc\uacc4\ub97c \uc77d\uc744 \ub54c \ubb34\uc5c7\uc744 \uba3c\uc800 \ubcf4\uba74 \uc88b\uc744\uae4c\uc694?", "cards": [{"id": "hour", "text": "\uc9e7\uc740 \ubc14\ub298 \ubcf4\uae30"}, {"id": "minute", "text": "\uae34 \ubc14\ub298 \ubcf4\uae30"}], "answerOrder": ["hour", "minute"], "correctFeedback": "\uc88b\uc544\uc694. \uc9e7\uc740 \ubc14\ub298, \uae34 \ubc14\ub298 \uc21c\uc11c\ub85c \ubcf4\uba74 \ub418\uc5b4\uc694.", "wrongFeedback": "\uc9e7\uc740 \ubc14\ub298\uc744 \uba3c\uc800 \ubcf4\ub294 \ud750\ub984\uc73c\ub85c \ub2e4\uc2dc \uace0\ub974\uc138\uc694.", "assetBundle": {"imageAssetId": "asset_content_clock_001_stage_3", "audioAssetId": "asset_content_clock_001_stage_3_audio"}}','null',3);
INSERT INTO content_stages VALUES('stage_clock_4','content_clock_001',4,'realtime_practice','realtime_teach_back','설명해보기','별이에게 시계를 읽는 방법을 말해봅시다.','{"imageAssetId": "asset_content_clock_001_stage_4_realtime", "audioAssetId": "asset_content_clock_001_stage_4_realtime_audio", "assetBundle": {"imageAssetId": "asset_content_clock_001_stage_4_realtime", "audioAssetId": "asset_content_clock_001_stage_4_realtime_audio"}}','{"id": "rt_spec_clock_001", "stageId": "stage_clock_4", "templateType": "realtime_teach_back", "imageAssetId": "asset_content_clock_001_stage_4_realtime", "mode": "voice_or_text", "practiceTitle": "\uc2dc\uacc4 \uc77d\ub294 \ubc29\ubc95 \uc124\uba85\ud558\uae30", "situationText": "\ubcc4\uc774\uac00 \uc2dc\uacc4 \uadf8\ub9bc\uc744 \ubcf4\uace0 \uba3c\uc800 \ubb34\uc5c7\uc744 \ubd10\uc57c \ud558\ub294\uc9c0 \ubb3c\uc5b4\ubd05\ub2c8\ub2e4.", "aiRole": "\uc2dc\uacc4\ub97c \ubc30\uc6b0\ub294 \uce5c\uad6c", "openingLine": "\uc2dc\uacc4\ub97c \uc77d\uc744 \ub54c \uc5b4\ub5a4 \ubc14\ub298\uc744 \uba3c\uc800 \ubcf4\uba74 \ub418\uc5b4?", "studentGoal": "\uc9e7\uc740 \ubc14\ub298\uc744 \uba3c\uc800 \ubcf4\uace0 \uae34 \ubc14\ub298\uc744 \ubcf8\ub2e4\uace0 \uc124\uba85\ud558\uae30", "rubric": [{"id": "mention_hour_hand", "label": "\uc9e7\uc740 \ubc14\ub298\uc744 \uba3c\uc800 \ubcf8\ub2e4", "required": true}, {"id": "mention_minute_hand", "label": "\uae34 \ubc14\ub298\uc744 \ub2e4\uc74c\uc5d0 \ubcf8\ub2e4", "required": true}], "allowedFeedback": ["\uc88b\uc544\uc694. \uba3c\uc800 \ubcfc \ubc14\ub298\uc744 \ub9d0\ud588\uc5b4\uc694.", "\uc774\uc81c \uae34 \ubc14\ub298\uae4c\uc9c0 \uc774\uc5b4\uc11c \ub9d0\ud574\ubd05\uc2dc\ub2e4."], "forbidden": ["\uc9c4\ub2e8\uba85 \uc5b8\uae09 \uae08\uc9c0", "\uac1c\uc778\uc815\ubcf4 \ubb3b\uc9c0 \uc54a\uae30"], "maxTurns": 6, "maxDurationSec": 120, "postPracticeReflection": ["\uc26c\uc6e0\uc5b4\uc694", "\uc870\uae08 \ud5f7\uac08\ub838\uc5b4\uc694", "\ub2e4\uc2dc \uc5f0\uc2b5\ud558\uace0 \uc2f6\uc5b4\uc694"]}',4);
INSERT INTO content_stages VALUES('stage_fraction_1','content_fraction_001',1,'concept_intro','concept_intro','개념 열기','피자 지도를 보며 전체와 부분을 확인해요.','{"imageAssetId": "asset_content_fraction_001_stage_1", "audioAssetId": "asset_content_fraction_001_stage_1_audio", "storyText": "\ud53c\uc790 \ud55c \ud310\uc774 \uac19\uc740 \ud06c\uae30 4\uc870\uac01\uc73c\ub85c \ub098\ub258\uc5b4 \uc788\uc5b4\uc694.", "missionText": "\ube5b\ub098\ub294 \uc870\uac01\uc774 \uc804\uccb4 \uc911 \uc5bc\ub9c8\uc778\uc9c0 \ucc3e\uc544\ubd10\uc694.", "assetBundle": {"imageAssetId": "asset_content_fraction_001_stage_1", "audioAssetId": "asset_content_fraction_001_stage_1_audio"}}','null',1);
INSERT INTO content_stages VALUES('stage_fraction_2','content_fraction_001',2,'basic_problem','partition_picker','문제 1','전체 조각 수와 고른 조각 수를 차례대로 세어보세요.','{"imageAssetId": "asset_content_fraction_001_stage_2", "audioAssetId": "asset_content_fraction_001_stage_2_audio", "question": "\uc804\uccb4\ub294 \uba87 \uc870\uac01\uc778\uac00\uc694?", "choices": [{"id": "a", "text": "1\uc870\uac01"}, {"id": "b", "text": "4\uc870\uac01"}, {"id": "c", "text": "2\uc870\uac01"}], "answer": "b", "correctFeedback": "\ub9de\uc544\uc694. \uc804\uccb4\ub294 4\uc870\uac01\uc774\uc5d0\uc694.", "wrongFeedback": "\ud53c\uc790 \ud55c \ud310\uc774 \uba87 \uce78\uc73c\ub85c \ub098\ub258\uc5c8\ub294\uc9c0 \ub2e4\uc2dc \uc138\uc5b4\ubcfc\uae4c\uc694?", "assetBundle": {"imageAssetId": "asset_content_fraction_001_stage_2", "audioAssetId": "asset_content_fraction_001_stage_2_audio"}}','null',2);
INSERT INTO content_stages VALUES('stage_fraction_3','content_fraction_001',3,'applied_problem','blank_fill','문제 2','고른 조각 수와 전체 조각 수를 분수 자리에 넣어보세요.','{"imageAssetId": "asset_content_fraction_001_stage_3", "audioAssetId": "asset_content_fraction_001_stage_3_audio", "question": "\uc804\uccb4 4\uac1c \uc911 1\uac1c\ub294 __ / __ \uc774\uc5d0\uc694.", "acceptedAnswers": [{"numerator": "1", "denominator": "4"}], "correctFeedback": "\uc88b\uc544\uc694. \uc704\uc5d0\ub294 \uace0\ub978 \uac83 1, \uc544\ub798\uc5d0\ub294 \uc804\uccb4 4\uac00 \uc640\uc694.", "wrongFeedback": "\uc704\uc5d0\ub294 \uace0\ub978 \uc870\uac01 \uc218, \uc544\ub798\uc5d0\ub294 \uc804\uccb4 \uc870\uac01 \uc218\ub97c \ub123\uc5b4\uc694.", "assetBundle": {"imageAssetId": "asset_content_fraction_001_stage_3", "audioAssetId": "asset_content_fraction_001_stage_3_audio"}}','null',3);
INSERT INTO content_stages VALUES('stage_fraction_4','content_fraction_001',4,'realtime_practice','realtime_teach_back','설명해보기','별이에게 왜 1/4인지 말로 설명해보세요.','{"imageAssetId": "asset_content_fraction_001_stage_4_realtime", "audioAssetId": "asset_content_fraction_001_stage_4_realtime_audio", "assetBundle": {"imageAssetId": "asset_content_fraction_001_stage_4_realtime", "audioAssetId": "asset_content_fraction_001_stage_4_realtime_audio"}}','{"id": "rt_spec_fraction_001", "stageId": "stage_fraction_4", "templateType": "realtime_teach_back", "imageAssetId": "asset_content_fraction_001_stage_4_realtime", "mode": "voice_or_text", "practiceTitle": "\ubcc4\uc774\uc5d0\uac8c \ubd84\uc218 \uc124\uba85\ud558\uae30", "situationText": "\ubcc4\uc774\uac00 \ube5b\ub098\ub294 \ud53c\uc790 \uc870\uac01\uc744 \ubcf4\uace0 \uc65c 1/4\uc778\uc9c0 \uad81\uae08\ud574\ud574\uc694.", "aiRole": "\ubcc4\uc774", "openingLine": "\uc65c 4/1\uc774 \uc544\ub2c8\ub77c 1/4\uc778\uc9c0 \uc54c\ub824\uc904\ub798?", "studentGoal": "\uc804\uccb4 4\uac1c \uc911 \uace0\ub978 \uac83\uc774 1\uac1c\ub77c\uc11c 1/4\uc774\ub77c\uace0 \uc124\uba85\ud558\uae30", "rubric": [{"id": "mention_whole", "label": "\uc804\uccb4\uac00 4\uac1c\uc784\uc744 \ub9d0\ud55c\ub2e4", "required": true}, {"id": "mention_part", "label": "\uace0\ub978 \uac83\uc774 1\uac1c\uc784\uc744 \ub9d0\ud55c\ub2e4", "required": true}, {"id": "connect_fraction", "label": "1/4\ub85c \uc5f0\uacb0\ud55c\ub2e4", "required": true}], "allowedFeedback": ["\uc88b\uc544\uc694. \uc804\uccb4\uac00 \uba87 \uac1c\uc778\uc9c0 \ub9d0\ud588\uc5b4\uc694.", "\uace0\ub978 \uac83\uc774 \uba87 \uac1c\uc778\uc9c0\ub3c4 \ub9d0\ud574\ubcfc\uae4c\uc694?", "\uc774\uc81c 1/4\uc774\ub77c\ub294 \ud45c\ud604\uae4c\uc9c0 \uc774\uc5b4\uc11c \ub9d0\ud574\ubd10\uc694."], "forbidden": ["\uc0c8 \ubb38\uc81c\ub97c \ub9cc\ub4e4\uc9c0 \uc54a\uae30", "\ud559\uc0dd\uc5d0\uac8c \uc9c4\ub2e8 \ub77c\ubca8 \ub9d0\ud558\uc9c0 \uc54a\uae30", "\uac1c\uc778\uc815\ubcf4 \uc5b8\uae09\ud558\uc9c0 \uc54a\uae30"], "maxTurns": 6, "maxDurationSec": 120, "postPracticeReflection": ["\uc26c\uc6e0\uc5b4\uc694", "\uc870\uae08 \ud5f7\uac08\ub838\uc5b4\uc694", "\ub2e4\uc2dc \uc5f0\uc2b5\ud558\uace0 \uc2f6\uc5b4\uc694"]}',4);
INSERT INTO content_stages VALUES('stage_bus_1','content_bus_001',1,'scenario_intro','scenario_intro','상황 만나기','센터에 가야 하는 상황을 살펴보세요.','{"imageAssetId": "asset_content_bus_001_stage_1", "audioAssetId": "asset_content_bus_001_stage_1_audio", "storyText": "\uc218\ubbfc\uc774\uac00 \uc6b0\ub9ac \ub3d9\ub124 \uc13c\ud130\uc5d0 \uac00\ub824\uace0 \ubc84\uc2a4 \uc815\ub958\uc7a5\uc5d0 \uc654\uc5b4\uc694.", "missionText": "\ubb34\uc5c7\uc744 \uba3c\uc800 \ud655\uc778\ud574\uc57c \ud560\uae4c\uc694?", "assetBundle": {"imageAssetId": "asset_content_bus_001_stage_1", "audioAssetId": "asset_content_bus_001_stage_1_audio"}}','null',1);
INSERT INTO content_stages VALUES('stage_bus_2','content_bus_001',2,'clue_identification','scene_observation','단서 찾기','버스를 타기 전에 중요한 단서를 골라보세요.','{"question": "\uc13c\ud130\uc5d0 \uac00\ub824\uba74 \ubb34\uc5c7\uc744 \uba3c\uc800 \ud655\uc778\ud558\uba74 \uc88b\uc744\uae4c\uc694?", "imageAssetId": "asset_content_bus_001_stage_2", "audioAssetId": "asset_content_bus_001_stage_2_audio", "choices": [{"id": "a", "text": "\ubc84\uc2a4 \ubc88\ud638"}, {"id": "b", "text": "\ud558\ub298 \uc0c9"}], "answer": "a", "correctFeedback": "\uc88b\uc544\uc694. \ubc84\uc2a4 \ubc88\ud638\ub97c \uba3c\uc800 \ud655\uc778\ud574\uc694.", "wrongFeedback": "\uc13c\ud130\ub85c \uac00\ub294 \ubc84\uc2a4\uc778\uc9c0 \uc54c\ub824\uc8fc\ub294 \ub2e8\uc11c\ub97c \ucc3e\uc544\ubcfc\uae4c\uc694?", "assetBundle": {"imageAssetId": "asset_content_bus_001_stage_2", "audioAssetId": "asset_content_bus_001_stage_2_audio"}}','null',2);
INSERT INTO content_stages VALUES('stage_bus_3','content_bus_001',3,'action_selection','sequence_ordering','행동 고르기','센터에 가는 순서를 차례대로 골라보세요.','{"question": "\uc13c\ud130\uc5d0 \uac00\ub294 \uc21c\uc11c\ub97c \ub9de\ucdb0\ubcf4\uc138\uc694.", "imageAssetId": "asset_content_bus_001_stage_3", "audioAssetId": "asset_content_bus_001_stage_3_audio", "cards": [{"id": "check_bus", "text": "\ubc84\uc2a4 \ubc88\ud638 \ud655\uc778"}, {"id": "take_bus", "text": "\ubc84\uc2a4 \ud0c0\uae30"}], "answerOrder": ["check_bus", "take_bus"], "correctFeedback": "\uc88b\uc544\uc694. \uba3c\uc800 \ud655\uc778\ud558\uace0, \uadf8\ub2e4\uc74c \ubc84\uc2a4\ub97c \ud0c0\uc694.", "wrongFeedback": "\ubc84\uc2a4\ub97c \ud0c0\uae30 \uc804\uc5d0 \ud655\uc778\ud574\uc57c \ud560 \uc77c\uc744 \uc55e\uc73c\ub85c \uc62e\uaca8\ubcfc\uae4c\uc694?", "assetBundle": {"imageAssetId": "asset_content_bus_001_stage_3", "audioAssetId": "asset_content_bus_001_stage_3_audio"}}','null',3);
INSERT INTO content_stages VALUES('stage_bus_4','content_bus_001',4,'realtime_practice','realtime_roleplay','한 번 해보기','AI 안내 직원에게 센터 가는 길을 물어보세요.','{"imageAssetId": "asset_content_bus_001_stage_4_realtime", "audioAssetId": "asset_content_bus_001_stage_4_realtime_audio", "assetBundle": {"imageAssetId": "asset_content_bus_001_stage_4_realtime", "audioAssetId": "asset_content_bus_001_stage_4_realtime_audio"}}','{"id": "rt_spec_bus_001", "stageId": "stage_bus_4", "templateType": "realtime_roleplay", "imageAssetId": "asset_content_bus_001_stage_4_realtime", "mode": "voice_or_text", "practiceTitle": "\uc815\ub958\uc7a5\uc5d0\uc11c \ub3c4\uc6c0 \uc694\uccad\ud558\uae30", "situationText": "\ud559\uc0dd\uc774 \uc13c\ud130\uc5d0 \uac00\ub824\uace0 \ubc84\uc2a4 \uc815\ub958\uc7a5\uc5d0\uc11c \uc548\ub0b4 \uc9c1\uc6d0\uc5d0\uac8c \ub3c4\uc6c0\uc744 \uc694\uccad\ud569\ub2c8\ub2e4.", "aiRole": "\uc815\ub958\uc7a5 \uc548\ub0b4 \uc9c1\uc6d0", "openingLine": "\uc5b4\ub514\ub85c \uac00\ub824\uace0 \ud558\ub098\uc694? \uc81c\uac00 \ub3c4\uc640\uc904\uac8c\uc694.", "studentGoal": "\uc13c\ud130\uc5d0 \uac00\uc57c \ud55c\ub2e4\uace0 \ub9d0\ud558\uace0 \uc5b4\ub5a4 \ubc84\uc2a4\ub97c \ud0c0\uc57c \ud558\ub294\uc9c0 \ub3c4\uc6c0 \uc694\uccad\ud558\uae30", "rubric": [{"id": "state_destination", "label": "\ubaa9\uc801\uc9c0\ub97c \ub9d0\ud55c\ub2e4", "required": true}, {"id": "ask_help", "label": "\ub3c4\uc6c0\uc744 \uc694\uccad\ud55c\ub2e4", "required": true}, {"id": "confirm_next_action", "label": "\ub2e4\uc74c \ud589\ub3d9\uc744 \ud655\uc778\ud55c\ub2e4", "required": true}], "allowedFeedback": ["\uc88b\uc544\uc694. \uc5b4\ub514\ub85c \uac00\ub294\uc9c0 \ub9d0\ud588\uc5b4\uc694.", "\uc5b4\ub5a4 \ub3c4\uc6c0\uc744 \ubc1b\uace0 \uc2f6\uc740\uc9c0\ub3c4 \ub9d0\ud574\ubcfc\uae4c\uc694?"], "forbidden": ["\uc0c8\ub85c\uc6b4 \uc774\ub3d9 \ubb38\uc81c \ub9cc\ub4e4\uc9c0 \uc54a\uae30", "\ud559\uc0dd \uac1c\uc778\uc815\ubcf4 \ubb3b\uc9c0 \uc54a\uae30", "\ubd88\uc548\uac10\uc744 \ud0a4\uc6b0\ub294 \ud45c\ud604 \uae08\uc9c0"], "maxTurns": 6, "maxDurationSec": 120, "postPracticeReflection": ["\ud560 \uc218 \uc788\uc744 \uac83 \uac19\uc544\uc694", "\uc870\uae08 \ub5a8\ub824\uc694", "\ub2e4\uc2dc \uc5f0\uc2b5\ud558\uace0 \uc2f6\uc5b4\uc694"]}',4);
CREATE TABLE content_assets (
	id VARCHAR NOT NULL,
	mission_content_id VARCHAR NOT NULL,
	stage_id VARCHAR,
	asset_role VARCHAR NOT NULL,
	asset_type VARCHAR NOT NULL,
	provider VARCHAR NOT NULL,
	model VARCHAR NOT NULL,
	prompt_json JSON,
	source_text TEXT,
	storage_url VARCHAR NOT NULL,
	preview_url VARCHAR,
	qa_status VARCHAR NOT NULL,
	approval_status VARCHAR NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(mission_content_id) REFERENCES mission_contents (id)
);
INSERT INTO content_assets VALUES('asset_content_clock_001_hero','content_clock_001',NULL,'hero','image','openai','gpt-image-2','{"visualRole": "hero", "textRenderingPolicy": "scene_only_no_problem_text", "forbiddenInlineText": ["\ubb38\uc81c \ubb38\uc7a5", "\uc120\ud0dd\uc9c0", "\uc815\ub2f5", "\ud78c\ud2b8", "\uae34 \uc124\uba85", "\ubcf5\uc7a1\ud55c \uc218\uc2dd"]}',NULL,'/assets/demo/clock-mission-hero.png','/assets/demo/clock-mission-hero.png','passed','approved');
INSERT INTO content_assets VALUES('asset_content_clock_001_stage_1','content_clock_001','stage_clock_1','stage_1','image','openai','gpt-image-2','{"visualRole": "stage_1", "textRenderingPolicy": "scene_only_no_problem_text", "forbiddenInlineText": ["\ubb38\uc81c \ubb38\uc7a5", "\uc120\ud0dd\uc9c0", "\uc815\ub2f5", "\ud78c\ud2b8", "\uae34 \uc124\uba85", "\ubcf5\uc7a1\ud55c \uc218\uc2dd"]}',NULL,'/assets/demo/clock-mission-stage-1.png','/assets/demo/clock-mission-stage-1.png','passed','approved');
INSERT INTO content_assets VALUES('asset_content_clock_001_stage_2','content_clock_001','stage_clock_2','stage_2','image','openai','gpt-image-2','{"visualRole": "stage_2", "textRenderingPolicy": "scene_only_no_problem_text", "forbiddenInlineText": ["\ubb38\uc81c \ubb38\uc7a5", "\uc120\ud0dd\uc9c0", "\uc815\ub2f5", "\ud78c\ud2b8", "\uae34 \uc124\uba85", "\ubcf5\uc7a1\ud55c \uc218\uc2dd"]}',NULL,'/assets/demo/clock-mission-stage-2.png','/assets/demo/clock-mission-stage-2.png','passed','approved');
INSERT INTO content_assets VALUES('asset_content_clock_001_stage_3','content_clock_001','stage_clock_3','stage_3','image','openai','gpt-image-2','{"visualRole": "stage_3", "textRenderingPolicy": "scene_only_no_problem_text", "forbiddenInlineText": ["\ubb38\uc81c \ubb38\uc7a5", "\uc120\ud0dd\uc9c0", "\uc815\ub2f5", "\ud78c\ud2b8", "\uae34 \uc124\uba85", "\ubcf5\uc7a1\ud55c \uc218\uc2dd"]}',NULL,'/assets/demo/clock-mission-stage-3.png','/assets/demo/clock-mission-stage-3.png','passed','approved');
INSERT INTO content_assets VALUES('asset_content_clock_001_stage_4_realtime','content_clock_001','stage_clock_4','stage_4_realtime','image','openai','gpt-image-2','{"visualRole": "stage_4_realtime", "textRenderingPolicy": "scene_only_no_problem_text", "forbiddenInlineText": ["\ubb38\uc81c \ubb38\uc7a5", "\uc120\ud0dd\uc9c0", "\uc815\ub2f5", "\ud78c\ud2b8", "\uae34 \uc124\uba85", "\ubcf5\uc7a1\ud55c \uc218\uc2dd"]}',NULL,'/assets/demo/clock-mission-stage-4.png','/assets/demo/clock-mission-stage-4.png','passed','approved');
INSERT INTO content_assets VALUES('asset_content_clock_001_hero_audio','content_clock_001',NULL,'hero','audio','elevenlabs','elevenlabs-tts','null','시계 그림을 보고 약속 시간을 찾아봅시다.','/assets/demo/audio/clock-hero.mp3','/assets/demo/audio/clock-hero.mp3','passed','approved');
INSERT INTO content_assets VALUES('asset_content_clock_001_stage_1_audio','content_clock_001','stage_clock_1','stage_1','audio','elevenlabs','elevenlabs-tts','null','시침과 분침이 어디에 있는지 보세요.','/assets/demo/audio/clock-stage-1.mp3','/assets/demo/audio/clock-stage-1.mp3','passed','approved');
INSERT INTO content_assets VALUES('asset_content_clock_001_stage_2_audio','content_clock_001','stage_clock_2','stage_2','audio','elevenlabs','elevenlabs-tts','null','짧은 바늘이 가리키는 숫자를 고르세요.','/assets/demo/audio/clock-stage-2.mp3','/assets/demo/audio/clock-stage-2.mp3','passed','approved');
INSERT INTO content_assets VALUES('asset_content_clock_001_stage_3_audio','content_clock_001','stage_clock_3','stage_3','audio','elevenlabs','elevenlabs-tts','null','짧은 바늘, 긴 바늘 순서로 보세요.','/assets/demo/audio/clock-stage-3.mp3','/assets/demo/audio/clock-stage-3.mp3','passed','approved');
INSERT INTO content_assets VALUES('asset_content_clock_001_stage_4_realtime_audio','content_clock_001','stage_clock_4','stage_4_realtime','audio','elevenlabs','elevenlabs-tts','null','별이에게 시계를 읽는 방법을 말해봅시다.','/assets/demo/audio/clock-stage-4-opening.mp3','/assets/demo/audio/clock-stage-4-opening.mp3','passed','approved');
INSERT INTO content_assets VALUES('asset_content_fraction_001_hero','content_fraction_001',NULL,'hero','image','openai','gpt-image-2','{"visualRole": "hero", "textRenderingPolicy": "scene_only_no_problem_text", "forbiddenInlineText": ["\ubb38\uc81c \ubb38\uc7a5", "\uc120\ud0dd\uc9c0", "\uc815\ub2f5", "\ud78c\ud2b8", "\uae34 \uc124\uba85", "\ubcf5\uc7a1\ud55c \uc218\uc2dd"]}',NULL,'/generated/fraction-mission/fraction-pizza.png','/generated/fraction-mission/fraction-pizza.png','passed','approved');
INSERT INTO content_assets VALUES('asset_content_fraction_001_stage_1','content_fraction_001','stage_fraction_1','stage_1','image','openai','gpt-image-2','{"visualRole": "stage_1", "textRenderingPolicy": "scene_only_no_problem_text", "forbiddenInlineText": ["\ubb38\uc81c \ubb38\uc7a5", "\uc120\ud0dd\uc9c0", "\uc815\ub2f5", "\ud78c\ud2b8", "\uae34 \uc124\uba85", "\ubcf5\uc7a1\ud55c \uc218\uc2dd"]}',NULL,'/generated/fraction-mission/fraction-pizza.png','/generated/fraction-mission/fraction-pizza.png','passed','approved');
INSERT INTO content_assets VALUES('asset_content_fraction_001_stage_2','content_fraction_001','stage_fraction_2','stage_2','image','openai','gpt-image-2','{"visualRole": "stage_2", "textRenderingPolicy": "scene_only_no_problem_text", "forbiddenInlineText": ["\ubb38\uc81c \ubb38\uc7a5", "\uc120\ud0dd\uc9c0", "\uc815\ub2f5", "\ud78c\ud2b8", "\uae34 \uc124\uba85", "\ubcf5\uc7a1\ud55c \uc218\uc2dd"]}',NULL,'/generated/fraction-mission/fraction-pizza.png','/generated/fraction-mission/fraction-pizza.png','passed','approved');
INSERT INTO content_assets VALUES('asset_content_fraction_001_stage_3','content_fraction_001','stage_fraction_3','stage_3','image','openai','gpt-image-2','{"visualRole": "stage_3", "textRenderingPolicy": "scene_only_no_problem_text", "forbiddenInlineText": ["\ubb38\uc81c \ubb38\uc7a5", "\uc120\ud0dd\uc9c0", "\uc815\ub2f5", "\ud78c\ud2b8", "\uae34 \uc124\uba85", "\ubcf5\uc7a1\ud55c \uc218\uc2dd"]}',NULL,'/generated/fraction-mission/fraction-pizza.png','/generated/fraction-mission/fraction-pizza.png','passed','approved');
INSERT INTO content_assets VALUES('asset_content_fraction_001_stage_4_realtime','content_fraction_001','stage_fraction_4','stage_4_realtime','image','openai','gpt-image-2','{"visualRole": "stage_4_realtime", "textRenderingPolicy": "scene_only_no_problem_text", "forbiddenInlineText": ["\ubb38\uc81c \ubb38\uc7a5", "\uc120\ud0dd\uc9c0", "\uc815\ub2f5", "\ud78c\ud2b8", "\uae34 \uc124\uba85", "\ubcf5\uc7a1\ud55c \uc218\uc2dd"]}',NULL,'/generated/fraction-mission/fraction-pizza.png','/generated/fraction-mission/fraction-pizza.png','passed','approved');
INSERT INTO content_assets VALUES('asset_content_fraction_001_hero_audio','content_fraction_001',NULL,'hero','audio','elevenlabs','elevenlabs-tts','null','오늘은 빛나는 한 조각으로 분수를 배워볼 거예요.','/examples/generated/fraction-mission/audio/hero.mp3','/examples/generated/fraction-mission/audio/hero.mp3','passed','approved');
INSERT INTO content_assets VALUES('asset_content_fraction_001_stage_1_audio','content_fraction_001','stage_fraction_1','stage_1','audio','elevenlabs','elevenlabs-tts','null','피자 지도를 보며 전체와 부분을 확인해요.','/examples/generated/fraction-mission/audio/stage-1.mp3','/examples/generated/fraction-mission/audio/stage-1.mp3','passed','approved');
INSERT INTO content_assets VALUES('asset_content_fraction_001_stage_2_audio','content_fraction_001','stage_fraction_2','stage_2','audio','elevenlabs','elevenlabs-tts','null','전체 조각 수를 먼저 세어보세요.','/examples/generated/fraction-mission/audio/stage-2.mp3','/examples/generated/fraction-mission/audio/stage-2.mp3','passed','approved');
INSERT INTO content_assets VALUES('asset_content_fraction_001_stage_3_audio','content_fraction_001','stage_fraction_3','stage_3','audio','elevenlabs','elevenlabs-tts','null','고른 조각 수와 전체 조각 수를 분수 자리에 넣어보세요.','/examples/generated/fraction-mission/audio/stage-3.mp3','/examples/generated/fraction-mission/audio/stage-3.mp3','passed','approved');
INSERT INTO content_assets VALUES('asset_content_fraction_001_stage_4_realtime_audio','content_fraction_001','stage_fraction_4','stage_4_realtime','audio','elevenlabs','elevenlabs-tts','null','이제 별이에게 왜 1/4인지 말로 설명해볼 거예요.','/examples/generated/fraction-mission/audio/stage-4-opening.mp3','/examples/generated/fraction-mission/audio/stage-4-opening.mp3','passed','approved');
INSERT INTO content_assets VALUES('asset_content_bus_001_hero','content_bus_001',NULL,'hero','image','openai','gpt-image-2','{"visualRole": "hero", "textRenderingPolicy": "scene_only_no_problem_text", "forbiddenInlineText": ["\ubb38\uc81c \ubb38\uc7a5", "\uc120\ud0dd\uc9c0", "\uc815\ub2f5", "\ud78c\ud2b8", "\uae34 \uc124\uba85", "\ubcf5\uc7a1\ud55c \uc218\uc2dd"]}',NULL,'/generated/bus-mission/bus-mission.png','/generated/bus-mission/bus-mission.png','passed','approved');
INSERT INTO content_assets VALUES('asset_content_bus_001_stage_1','content_bus_001','stage_bus_1','stage_1','image','openai','gpt-image-2','{"visualRole": "stage_1", "textRenderingPolicy": "scene_only_no_problem_text", "forbiddenInlineText": ["\ubb38\uc81c \ubb38\uc7a5", "\uc120\ud0dd\uc9c0", "\uc815\ub2f5", "\ud78c\ud2b8", "\uae34 \uc124\uba85", "\ubcf5\uc7a1\ud55c \uc218\uc2dd"]}',NULL,'/generated/bus-mission/bus-mission.png','/generated/bus-mission/bus-mission.png','passed','approved');
INSERT INTO content_assets VALUES('asset_content_bus_001_stage_2','content_bus_001','stage_bus_2','stage_2','image','openai','gpt-image-2','{"visualRole": "stage_2", "textRenderingPolicy": "scene_only_no_problem_text", "forbiddenInlineText": ["\ubb38\uc81c \ubb38\uc7a5", "\uc120\ud0dd\uc9c0", "\uc815\ub2f5", "\ud78c\ud2b8", "\uae34 \uc124\uba85", "\ubcf5\uc7a1\ud55c \uc218\uc2dd"]}',NULL,'/generated/bus-mission/bus-mission.png','/generated/bus-mission/bus-mission.png','passed','approved');
INSERT INTO content_assets VALUES('asset_content_bus_001_stage_3','content_bus_001','stage_bus_3','stage_3','image','openai','gpt-image-2','{"visualRole": "stage_3", "textRenderingPolicy": "scene_only_no_problem_text", "forbiddenInlineText": ["\ubb38\uc81c \ubb38\uc7a5", "\uc120\ud0dd\uc9c0", "\uc815\ub2f5", "\ud78c\ud2b8", "\uae34 \uc124\uba85", "\ubcf5\uc7a1\ud55c \uc218\uc2dd"]}',NULL,'/generated/bus-mission/bus-mission.png','/generated/bus-mission/bus-mission.png','passed','approved');
INSERT INTO content_assets VALUES('asset_content_bus_001_stage_4_realtime','content_bus_001','stage_bus_4','stage_4_realtime','image','openai','gpt-image-2','{"visualRole": "stage_4_realtime", "textRenderingPolicy": "scene_only_no_problem_text", "forbiddenInlineText": ["\ubb38\uc81c \ubb38\uc7a5", "\uc120\ud0dd\uc9c0", "\uc815\ub2f5", "\ud78c\ud2b8", "\uae34 \uc124\uba85", "\ubcf5\uc7a1\ud55c \uc218\uc2dd"]}',NULL,'/generated/bus-mission/bus-mission.png','/generated/bus-mission/bus-mission.png','passed','approved');
INSERT INTO content_assets VALUES('asset_content_bus_001_hero_audio','content_bus_001',NULL,'hero','audio','elevenlabs','elevenlabs-tts','null','오늘은 센터에 가는 길을 차근차근 연습해요.','/assets/demo/audio/bus-hero.mp3','/assets/demo/audio/bus-hero.mp3','passed','approved');
INSERT INTO content_assets VALUES('asset_content_bus_001_stage_1_audio','content_bus_001','stage_bus_1','stage_1','audio','elevenlabs','elevenlabs-tts','null','센터에 가야 하는 상황을 살펴보세요.','/assets/demo/audio/bus-stage-1.mp3','/assets/demo/audio/bus-stage-1.mp3','passed','approved');
INSERT INTO content_assets VALUES('asset_content_bus_001_stage_2_audio','content_bus_001','stage_bus_2','stage_2','audio','elevenlabs','elevenlabs-tts','null','버스를 타기 전에 중요한 단서를 골라보세요.','/assets/demo/audio/bus-stage-2.mp3','/assets/demo/audio/bus-stage-2.mp3','passed','approved');
INSERT INTO content_assets VALUES('asset_content_bus_001_stage_3_audio','content_bus_001','stage_bus_3','stage_3','audio','elevenlabs','elevenlabs-tts','null','센터에 가는 순서를 차례대로 골라보세요.','/assets/demo/audio/bus-stage-3.mp3','/assets/demo/audio/bus-stage-3.mp3','passed','approved');
INSERT INTO content_assets VALUES('asset_content_bus_001_stage_4_realtime_audio','content_bus_001','stage_bus_4','stage_4_realtime','audio','elevenlabs','elevenlabs-tts','null','이제 안내 직원에게 센터 가는 길을 물어보는 연습을 해볼 거예요.','/assets/demo/audio/bus-stage-4-opening.mp3','/assets/demo/audio/bus-stage-4-opening.mp3','passed','approved');
CREATE TABLE content_attempts (
	id VARCHAR NOT NULL,
	mission_content_id VARCHAR NOT NULL,
	student_id VARCHAR NOT NULL,
	status VARCHAR NOT NULL,
	current_step INTEGER NOT NULL,
	started_at VARCHAR NOT NULL,
	completed_at VARCHAR,
	score_json JSON,
	PRIMARY KEY (id),
	FOREIGN KEY(mission_content_id) REFERENCES mission_contents (id),
	FOREIGN KEY(student_id) REFERENCES students (id)
);
INSERT INTO content_attempts VALUES('attempt_fraction_20260502','content_fraction_001','student_learning_fraction','completed',4,'2026-05-02T09:10:00.000Z','2026-05-02T09:24:00.000Z','{"completionRate": 1, "accuracyRate": 0.5, "supportLevel": "light_hint"}');
INSERT INTO content_attempts VALUES('attempt_bus_20260502','content_bus_001','student_life_bus','completed',4,'2026-05-02T10:05:00.000Z','2026-05-02T10:18:00.000Z','{"completionRate": 1, "accuracyRate": 1, "supportLevel": "modeled_prompt"}');
CREATE TABLE activity_events (
	id VARCHAR NOT NULL,
	attempt_id VARCHAR,
	student_id VARCHAR NOT NULL,
	stage_id VARCHAR,
	event_type VARCHAR NOT NULL,
	payload_json JSON NOT NULL,
	occurred_at VARCHAR NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(attempt_id) REFERENCES content_attempts (id),
	FOREIGN KEY(student_id) REFERENCES students (id)
);
INSERT INTO activity_events VALUES('event_fraction_s1_viewed','attempt_fraction_20260502','student_learning_fraction','stage_fraction_1','stage_viewed','{"durationSec": 96, "engagement": "focused_on_visual"}','2026-05-02T09:10:20.000Z');
INSERT INTO activity_events VALUES('event_fraction_s2_wrong','attempt_fraction_20260502','student_learning_fraction','stage_fraction_2','answer_submitted','{"answer": {"choiceId": "a"}, "isCorrect": false, "hintUsed": true, "pattern": "counted_selected_part_first"}','2026-05-02T09:14:10.000Z');
INSERT INTO activity_events VALUES('event_fraction_s3_correct','attempt_fraction_20260502','student_learning_fraction','stage_fraction_3','answer_submitted','{"answer": {"numerator": "1", "denominator": "4"}, "isCorrect": true, "hintUsed": false}','2026-05-02T09:18:35.000Z');
INSERT INTO activity_events VALUES('event_fraction_reflection','attempt_fraction_20260502','student_learning_fraction',NULL,'post_practice_reflection','{"reflectionChoice": "\uc870\uae08 \ud5f7\uac08\ub838\uc5b4\uc694", "shortText": "\uc804\uccb4 \uc870\uac01 \uc218\ub97c \uba3c\uc800 \uc138\uba74 \uc26c\uc6e0\uc5b4\uc694."}','2026-05-02T09:24:05.000Z');
INSERT INTO activity_events VALUES('event_bus_s1_viewed','attempt_bus_20260502','student_life_bus','stage_bus_1','stage_viewed','{"durationSec": 74, "engagement": "responded_to_route_image"}','2026-05-02T10:05:18.000Z');
INSERT INTO activity_events VALUES('event_bus_s2_correct','attempt_bus_20260502','student_life_bus','stage_bus_2','answer_submitted','{"answer": {"choiceId": "a"}, "isCorrect": true, "hintUsed": false}','2026-05-02T10:08:30.000Z');
INSERT INTO activity_events VALUES('event_bus_s3_correct','attempt_bus_20260502','student_life_bus','stage_bus_3','answer_submitted','{"answer": {"order": ["check_bus", "take_bus"]}, "isCorrect": true, "hintUsed": true}','2026-05-02T10:12:50.000Z');
INSERT INTO activity_events VALUES('event_bus_reflection','attempt_bus_20260502','student_life_bus',NULL,'post_practice_reflection','{"reflectionChoice": "\ub2e4\uc2dc \uc5f0\uc2b5\ud558\uace0 \uc2f6\uc5b4\uc694", "shortText": "\ubc84\uc2a4 \ubc88\ud638\ub294 \uc54c\uaca0\ub294\ub370 \ub9d0\ub85c \ubb3c\uc5b4\ubcf4\ub294 \uac74 \ub354 \uc5f0\uc2b5\ud558\uace0 \uc2f6\uc5b4\uc694."}','2026-05-02T10:18:05.000Z');
CREATE TABLE realtime_practice_sessions (
	id VARCHAR NOT NULL,
	attempt_id VARCHAR NOT NULL,
	mission_content_id VARCHAR NOT NULL,
	stage_id VARCHAR NOT NULL,
	student_id VARCHAR NOT NULL,
	provider VARCHAR NOT NULL,
	model VARCHAR NOT NULL,
	status VARCHAR NOT NULL,
	spec_snapshot_json JSON NOT NULL,
	started_at VARCHAR,
	ended_at VARCHAR,
	turn_count INTEGER NOT NULL,
	duration_sec INTEGER NOT NULL,
	rubric_result_json JSON,
	transcript_summary TEXT,
	PRIMARY KEY (id),
	FOREIGN KEY(attempt_id) REFERENCES content_attempts (id),
	FOREIGN KEY(mission_content_id) REFERENCES mission_contents (id),
	FOREIGN KEY(student_id) REFERENCES students (id)
);
INSERT INTO realtime_practice_sessions VALUES('rt_session_fraction_20260502','attempt_fraction_20260502','content_fraction_001','stage_fraction_4','student_learning_fraction','openai','gpt-realtime','completed','{"stageId": "stage_fraction_4", "templateType": "realtime_teach_back", "maxTurns": 6}','2026-05-02T09:20:00.000Z','2026-05-02T09:23:40.000Z',4,220,'{"mention_whole": true, "mention_part": true, "connect_fraction": true, "supportNeeded": "\ubd84\ubaa8\ub97c \ub5a0\uc62c\ub9ac\ub294 \uc9e7\uc740 \ub2e8\uc11c 1\ud68c"}','시각 자료를 보며 전체 4조각 중 고른 조각 1개를 1/4로 설명했고, 분모 단서가 한 번 필요했습니다.');
INSERT INTO realtime_practice_sessions VALUES('rt_session_bus_20260502','attempt_bus_20260502','content_bus_001','stage_bus_4','student_life_bus','openai','gpt-realtime','completed','{"stageId": "stage_bus_4", "templateType": "realtime_roleplay", "maxTurns": 6}','2026-05-02T10:14:00.000Z','2026-05-02T10:17:40.000Z',5,220,'{"state_destination": true, "ask_help": true, "confirm_next_action": false, "supportNeeded": "\ub2e4\uc74c \ud589\ub3d9 \ud655\uc778 \ubb38\uc7a5 \ubaa8\ub378\ub9c1"}','목적지를 말하고 도움을 요청했지만, 다음에 무엇을 하면 되는지 확인하는 문장은 교사의 예시가 필요했습니다.');
CREATE TABLE review_summaries (
	id VARCHAR NOT NULL,
	attempt_id VARCHAR NOT NULL,
	student_id VARCHAR NOT NULL,
	completion_rate NUMERIC NOT NULL,
	accuracy_rate NUMERIC NOT NULL,
	short_summary TEXT NOT NULL,
	wrong_pattern_json JSON NOT NULL,
	realtime_result_json JSON NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(attempt_id) REFERENCES content_attempts (id),
	FOREIGN KEY(student_id) REFERENCES students (id)
);
INSERT INTO review_summaries VALUES('review_fraction_20260502','attempt_fraction_20260502','student_learning_fraction',1,0.5,'4단계를 모두 완료했습니다. 그림 자료에는 안정적으로 반응했고, 전체 조각 수를 먼저 세도록 짧게 안내하자 1/4 설명이 가능했습니다.','{"answerCount": 2, "correctCount": 1, "wrongCount": 1, "patterns": ["\uc804\uccb4 \uc870\uac01 \uc218\ubcf4\ub2e4 \uace0\ub978 \uc870\uac01 \uc218\ub97c \uba3c\uc800 \uc138\uba70 \ubd84\ubaa8/\ubd84\uc790 \uc704\uce58\ub97c \ud5f7\uac08\ub9bc"]}','{"sessionId": "rt_session_fraction_20260502", "rubricPassed": ["mention_whole", "mention_part", "connect_fraction"], "nextSupport": "\ub2e4\uc74c \ud68c\uae30 \uc2dc\uc791 \uc2dc \uc804\uccb4 \uc870\uac01 \uc218\ub97c \uba3c\uc800 \uc138\uace0, \uadf8\ub2e4\uc74c \uace0\ub978 \uc870\uac01 \uc218\ub97c \uc138\ub294 \uc21c\uc11c\ub97c \ubc18\ubcf5\ud569\ub2c8\ub2e4."}');
INSERT INTO review_summaries VALUES('review_bus_20260502','attempt_bus_20260502','student_life_bus',1,1,'4단계를 모두 완료했습니다. 이동 경로 그림과 2지선다 단서에는 잘 반응했고, 도움 요청 역할극은 확인 문장 연습이 더 필요합니다.','{"answerCount": 2, "correctCount": 2, "wrongCount": 0, "patterns": ["\ub2e4\uc74c \ud589\ub3d9\uc744 \ud655\uc778\ud558\ub294 \ubb38\uc7a5\uc740 \uc608\uc2dc\ub97c \ub4e4\uc740 \ub4a4 \ub530\ub77c \ub9d0\ud568"]}','{"sessionId": "rt_session_bus_20260502", "rubricPassed": ["state_destination", "ask_help"], "rubricNeedsPractice": ["confirm_next_action"], "nextSupport": "\uc9e7\uc740 \ud655\uc778 \ubb38\uc7a5 \ud55c \uac00\uc9c0\ub97c \uba3c\uc800 \uc5f0\uc2b5\ud569\ub2c8\ub2e4. \uc608: ''\uc774\uc81c \uc5b4\ub5a4 \ubc84\uc2a4\ub97c \ud0c0\uba74 \ub3fc\uc694?''"}');
CREATE INDEX ix_school_profiles_office_code ON school_profiles (office_code);
CREATE INDEX ix_school_calendar_events_event_date ON school_calendar_events (event_date);
CREATE INDEX ix_school_calendar_events_school_code ON school_calendar_events (school_code);
CREATE INDEX ix_school_calendar_events_office_code ON school_calendar_events (office_code);
CREATE INDEX ix_school_timetable_slots_office_code ON school_timetable_slots (office_code);
CREATE INDEX ix_school_timetable_slots_grade ON school_timetable_slots (grade);
CREATE INDEX ix_school_timetable_slots_school_code ON school_timetable_slots (school_code);
CREATE INDEX ix_school_timetable_slots_timetable_date ON school_timetable_slots (timetable_date);
CREATE INDEX ix_school_timetable_slots_class_name ON school_timetable_slots (class_name);
CREATE INDEX ix_agent_runs_agent_type ON agent_runs (agent_type);
CREATE INDEX ix_agent_runs_error_code ON agent_runs (error_code);
CREATE INDEX ix_agent_runs_prompt_version ON agent_runs (prompt_version);
CREATE INDEX ix_agent_runs_status ON agent_runs (status);
CREATE INDEX ix_audit_logs_actor_user_id ON audit_logs (actor_user_id);
CREATE INDEX ix_audit_logs_student_id ON audit_logs (student_id);
CREATE INDEX ix_audit_logs_resource_id ON audit_logs (resource_id);
CREATE INDEX ix_audit_logs_action ON audit_logs (action);
CREATE INDEX ix_audit_logs_resource_type ON audit_logs (resource_type);
CREATE INDEX ix_users_organization_id ON users (organization_id);
CREATE INDEX ix_users_role ON users (role);
CREATE INDEX ix_students_school_code ON students (school_code);
CREATE INDEX ix_students_organization_id ON students (organization_id);
CREATE INDEX ix_students_student_type ON students (student_type);
CREATE INDEX ix_student_accounts_student_id ON student_accounts (student_id);
CREATE INDEX ix_support_cases_student_id ON support_cases (student_id);
CREATE INDEX ix_support_cases_owner_teacher_id ON support_cases (owner_teacher_id);
CREATE INDEX ix_case_notes_author_id ON case_notes (author_id);
CREATE INDEX ix_case_notes_case_id ON case_notes (case_id);
CREATE INDEX ix_memory_cards_case_id ON memory_cards (case_id);
CREATE INDEX ix_memory_cards_student_id ON memory_cards (student_id);
CREATE INDEX ix_planner_items_case_id ON planner_items (case_id);
CREATE INDEX ix_planner_items_student_id ON planner_items (student_id);
CREATE INDEX ix_mission_contents_student_id ON mission_contents (student_id);
CREATE INDEX ix_mission_contents_status ON mission_contents (status);
CREATE INDEX ix_mission_contents_case_id ON mission_contents (case_id);
CREATE INDEX ix_content_stages_mission_content_id ON content_stages (mission_content_id);
CREATE INDEX ix_content_assets_asset_role ON content_assets (asset_role);
CREATE INDEX ix_content_assets_stage_id ON content_assets (stage_id);
CREATE INDEX ix_content_assets_mission_content_id ON content_assets (mission_content_id);
CREATE INDEX ix_content_attempts_student_id ON content_attempts (student_id);
CREATE INDEX ix_content_attempts_mission_content_id ON content_attempts (mission_content_id);
CREATE INDEX ix_activity_events_stage_id ON activity_events (stage_id);
CREATE INDEX ix_activity_events_event_type ON activity_events (event_type);
CREATE INDEX ix_activity_events_attempt_id ON activity_events (attempt_id);
CREATE INDEX ix_activity_events_student_id ON activity_events (student_id);
CREATE INDEX ix_realtime_practice_sessions_mission_content_id ON realtime_practice_sessions (mission_content_id);
CREATE INDEX ix_realtime_practice_sessions_stage_id ON realtime_practice_sessions (stage_id);
CREATE INDEX ix_realtime_practice_sessions_attempt_id ON realtime_practice_sessions (attempt_id);
CREATE INDEX ix_realtime_practice_sessions_student_id ON realtime_practice_sessions (student_id);
CREATE INDEX ix_review_summaries_student_id ON review_summaries (student_id);
CREATE INDEX ix_review_summaries_attempt_id ON review_summaries (attempt_id);
COMMIT;
