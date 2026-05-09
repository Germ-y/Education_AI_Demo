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
INSERT INTO school_profiles VALUES('school_yeongju_gaheung_elementary','R10','8811067','영주가흥초등학교','초등학교','경상북도 영주시','경상북도 영주시 대동로70번길 8-9','neis_open_api');
INSERT INTO school_profiles VALUES('school_8811046','R10','8811046','영주중앙초등학교','초등학교','경상북도','경상북도 영주시 중앙로 126','neis_open_api');
INSERT INTO school_profiles VALUES('school_yeongju_middle','R10','8811058','영주중학교','중학교','경상북도 영주시','경상북도 영주시 남간로 29','neis_open_api');
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
INSERT INTO school_calendar_events VALUES('calendar_yeongju_middle_20260501','8811058','R10','2026','2026-05-01','노동절','','공휴일','["1", "2", "3"]','neis_school_schedule','2026-05-02T00:00:00.000Z');
INSERT INTO school_calendar_events VALUES('calendar_yeongju_gaheung_20260501','8811067','R10','2026','2026-05-01','노동절','','공휴일','["1", "2", "3", "4", "5", "6"]','neis_school_schedule','2026-05-02T00:00:00.000Z');
INSERT INTO school_calendar_events VALUES('calendar_yeongju_jungang_20260502','8811046','R10','2026','2026-05-02','토요휴업일','','휴업일','["1", "2", "3", "4", "5", "6"]','neis_school_schedule','2026-05-02T00:00:00.000Z');
INSERT INTO school_calendar_events VALUES('calendar_yeongju_middle_20260502','8811058','R10','2026','2026-05-02','토요휴업일','','휴업일','["1", "2", "3"]','neis_school_schedule','2026-05-02T00:00:00.000Z');
INSERT INTO school_calendar_events VALUES('calendar_yeongju_gaheung_20260502','8811067','R10','2026','2026-05-02','토요휴업일','','휴업일','["1", "2", "3", "4", "5", "6"]','neis_school_schedule','2026-05-02T00:00:00.000Z');
INSERT INTO school_calendar_events VALUES('calendar_yeongju_middle_20260504','8811058','R10','2026','2026-05-04','재량휴업일','','휴업일','["1", "2", "3"]','neis_school_schedule','2026-05-02T00:00:00.000Z');
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
INSERT INTO school_timetable_slots VALUES('timetable_yeongju_middle_20260501_2_1_1','8811058','R10','2026','1','2026-05-01','2','1',1,'역사','neis_mis_timetable','2026-05-02T00:00:00.000Z');
INSERT INTO school_timetable_slots VALUES('timetable_yeongju_middle_20260501_2_1_2','8811058','R10','2026','1','2026-05-01','2','1',2,'동아리활동','neis_mis_timetable','2026-05-02T00:00:00.000Z');
INSERT INTO school_timetable_slots VALUES('timetable_yeongju_middle_20260501_2_1_3','8811058','R10','2026','1','2026-05-01','2','1',3,'진로와 직업','neis_mis_timetable','2026-05-02T00:00:00.000Z');
INSERT INTO school_timetable_slots VALUES('timetable_yeongju_middle_20260501_2_1_4','8811058','R10','2026','1','2026-05-01','2','1',4,'국어','neis_mis_timetable','2026-05-02T00:00:00.000Z');
INSERT INTO school_timetable_slots VALUES('timetable_yeongju_middle_20260501_2_1_5','8811058','R10','2026','1','2026-05-01','2','1',5,'과학','neis_mis_timetable','2026-05-02T00:00:00.000Z');
INSERT INTO school_timetable_slots VALUES('timetable_yeongju_middle_20260501_2_1_6','8811058','R10','2026','1','2026-05-01','2','1',6,'도덕','neis_mis_timetable','2026-05-02T00:00:00.000Z');
INSERT INTO school_timetable_slots VALUES('timetable_yeongju_jungang_20260501_3_1_1','8811046','R10','2026','1','2026-05-01','3','1',1,'국어','neis_els_timetable','2026-05-02T00:00:00.000Z');
INSERT INTO school_timetable_slots VALUES('timetable_yeongju_jungang_20260501_3_1_2','8811046','R10','2026','1','2026-05-01','3','1',2,'수학','neis_els_timetable','2026-05-02T00:00:00.000Z');
INSERT INTO school_timetable_slots VALUES('timetable_yeongju_jungang_20260501_3_1_3','8811046','R10','2026','1','2026-05-01','3','1',3,'사회','neis_els_timetable','2026-05-02T00:00:00.000Z');
INSERT INTO school_timetable_slots VALUES('timetable_yeongju_jungang_20260501_3_1_4','8811046','R10','2026','1','2026-05-01','3','1',4,'과학','neis_els_timetable','2026-05-02T00:00:00.000Z');
INSERT INTO school_timetable_slots VALUES('timetable_yeongju_jungang_20260501_3_1_5','8811046','R10','2026','1','2026-05-01','3','1',5,'창의적체험활동','neis_els_timetable','2026-05-02T00:00:00.000Z');
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
INSERT INTO public_data_sources VALUES('source_curriculum_seed','curriculum_seed','교육과정 성취기준 seed',NULL,'manual_seed',1);
INSERT INTO public_data_sources VALUES('source_neis','neis_open_api','나이스 교육정보 개방 포털','https://open.neis.go.kr/','api_key',1);
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
CREATE TABLE student_accounts (
	id VARCHAR NOT NULL, 
	student_id VARCHAR NOT NULL, 
	access_code VARCHAR NOT NULL, 
	status VARCHAR NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(student_id) REFERENCES students (id), 
	UNIQUE (access_code)
);
CREATE TABLE support_cases (
	id VARCHAR NOT NULL, 
	student_id VARCHAR NOT NULL, 
	owner_teacher_id VARCHAR NOT NULL, 
	case_status VARCHAR NOT NULL, 
	current_goal TEXT NOT NULL, 
	opened_at VARCHAR NOT NULL, dashboard_stage VARCHAR DEFAULT 'initial_review', support_strategy TEXT, 
	PRIMARY KEY (id), 
	FOREIGN KEY(student_id) REFERENCES students (id), 
	FOREIGN KEY(owner_teacher_id) REFERENCES users (id)
);
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
CREATE TABLE student_support_intake_sources (
	id VARCHAR NOT NULL, 
	student_id VARCHAR NOT NULL, 
	source_type VARCHAR NOT NULL, 
	payload_json JSON NOT NULL, 
	created_at VARCHAR NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(student_id) REFERENCES students (id)
);
CREATE TABLE student_support_profiles (
	id VARCHAR NOT NULL, 
	student_id VARCHAR NOT NULL, 
	source_intake_id VARCHAR, 
	status VARCHAR NOT NULL, 
	profile_json JSON NOT NULL, 
	generated_by VARCHAR NOT NULL, 
	teacher_confirmed_by_user_id VARCHAR, 
	created_at VARCHAR NOT NULL, 
	confirmed_at VARCHAR, 
	PRIMARY KEY (id), 
	FOREIGN KEY(student_id) REFERENCES students (id)
);
CREATE TABLE student_context_briefs (
	id VARCHAR NOT NULL, 
	student_id VARCHAR NOT NULL, 
	brief_text TEXT NOT NULL, 
	student_type VARCHAR NOT NULL, 
	reading_load VARCHAR NOT NULL, 
	choice_count INTEGER NOT NULL, 
	recent_success_patterns JSON NOT NULL, 
	recent_difficulty_patterns JSON NOT NULL, 
	recommended_scaffolds JSON NOT NULL, 
	avoid_topic_regression JSON NOT NULL, 
	source_watermark VARCHAR NOT NULL, 
	dirty BOOLEAN NOT NULL, 
	status VARCHAR NOT NULL, 
	source_json JSON NOT NULL, 
	model VARCHAR NOT NULL, 
	refreshed_at VARCHAR, 
	created_at VARCHAR NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(student_id) REFERENCES students (id)
);
CREATE TABLE teacher_report_drafts (
	id VARCHAR NOT NULL, 
	review_summary_id VARCHAR NOT NULL, 
	student_id VARCHAR NOT NULL, 
	content_id VARCHAR NOT NULL, 
	status VARCHAR NOT NULL, 
	body_markdown TEXT NOT NULL, 
	next_learning_suggestions JSON NOT NULL, 
	memory_candidates JSON NOT NULL, 
	input_snapshot_json JSON NOT NULL, 
	model VARCHAR NOT NULL, 
	created_at VARCHAR NOT NULL, 
	completed_at VARCHAR, 
	PRIMARY KEY (id), 
	FOREIGN KEY(review_summary_id) REFERENCES review_summaries (id), 
	FOREIGN KEY(student_id) REFERENCES students (id), 
	FOREIGN KEY(content_id) REFERENCES mission_contents (id)
);
CREATE TABLE teacher_reports (
	id VARCHAR NOT NULL, 
	draft_id VARCHAR, 
	review_summary_id VARCHAR NOT NULL, 
	student_id VARCHAR NOT NULL, 
	content_id VARCHAR NOT NULL, 
	teacher_body TEXT NOT NULL, 
	selected_memory_candidates JSON NOT NULL, 
	created_by_user_id VARCHAR NOT NULL, 
	created_at VARCHAR NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(review_summary_id) REFERENCES review_summaries (id), 
	FOREIGN KEY(student_id) REFERENCES students (id), 
	FOREIGN KEY(content_id) REFERENCES mission_contents (id)
);
CREATE INDEX ix_school_profiles_office_code ON school_profiles (office_code);
CREATE INDEX ix_school_calendar_events_office_code ON school_calendar_events (office_code);
CREATE INDEX ix_school_calendar_events_event_date ON school_calendar_events (event_date);
CREATE INDEX ix_school_calendar_events_school_code ON school_calendar_events (school_code);
CREATE INDEX ix_school_timetable_slots_office_code ON school_timetable_slots (office_code);
CREATE INDEX ix_school_timetable_slots_school_code ON school_timetable_slots (school_code);
CREATE INDEX ix_school_timetable_slots_grade ON school_timetable_slots (grade);
CREATE INDEX ix_school_timetable_slots_class_name ON school_timetable_slots (class_name);
CREATE INDEX ix_school_timetable_slots_timetable_date ON school_timetable_slots (timetable_date);
CREATE INDEX ix_agent_runs_status ON agent_runs (status);
CREATE INDEX ix_agent_runs_agent_type ON agent_runs (agent_type);
CREATE INDEX ix_agent_runs_error_code ON agent_runs (error_code);
CREATE INDEX ix_agent_runs_prompt_version ON agent_runs (prompt_version);
CREATE INDEX ix_audit_logs_actor_user_id ON audit_logs (actor_user_id);
CREATE INDEX ix_audit_logs_student_id ON audit_logs (student_id);
CREATE INDEX ix_audit_logs_resource_id ON audit_logs (resource_id);
CREATE INDEX ix_audit_logs_action ON audit_logs (action);
CREATE INDEX ix_audit_logs_resource_type ON audit_logs (resource_type);
CREATE INDEX ix_users_role ON users (role);
CREATE INDEX ix_users_organization_id ON users (organization_id);
CREATE INDEX ix_students_school_code ON students (school_code);
CREATE INDEX ix_students_student_type ON students (student_type);
CREATE INDEX ix_students_organization_id ON students (organization_id);
CREATE INDEX ix_student_accounts_student_id ON student_accounts (student_id);
CREATE INDEX ix_support_cases_student_id ON support_cases (student_id);
CREATE INDEX ix_support_cases_owner_teacher_id ON support_cases (owner_teacher_id);
CREATE INDEX ix_case_notes_author_id ON case_notes (author_id);
CREATE INDEX ix_case_notes_case_id ON case_notes (case_id);
CREATE INDEX ix_memory_cards_case_id ON memory_cards (case_id);
CREATE INDEX ix_memory_cards_student_id ON memory_cards (student_id);
CREATE INDEX ix_planner_items_case_id ON planner_items (case_id);
CREATE INDEX ix_planner_items_student_id ON planner_items (student_id);
CREATE INDEX ix_mission_contents_case_id ON mission_contents (case_id);
CREATE INDEX ix_mission_contents_student_id ON mission_contents (student_id);
CREATE INDEX ix_mission_contents_status ON mission_contents (status);
CREATE INDEX ix_content_stages_mission_content_id ON content_stages (mission_content_id);
CREATE INDEX ix_content_assets_stage_id ON content_assets (stage_id);
CREATE INDEX ix_content_assets_mission_content_id ON content_assets (mission_content_id);
CREATE INDEX ix_content_assets_asset_role ON content_assets (asset_role);
CREATE INDEX ix_content_attempts_mission_content_id ON content_attempts (mission_content_id);
CREATE INDEX ix_content_attempts_student_id ON content_attempts (student_id);
CREATE INDEX ix_activity_events_stage_id ON activity_events (stage_id);
CREATE INDEX ix_activity_events_attempt_id ON activity_events (attempt_id);
CREATE INDEX ix_activity_events_event_type ON activity_events (event_type);
CREATE INDEX ix_activity_events_student_id ON activity_events (student_id);
CREATE INDEX ix_realtime_practice_sessions_mission_content_id ON realtime_practice_sessions (mission_content_id);
CREATE INDEX ix_realtime_practice_sessions_stage_id ON realtime_practice_sessions (stage_id);
CREATE INDEX ix_realtime_practice_sessions_attempt_id ON realtime_practice_sessions (attempt_id);
CREATE INDEX ix_realtime_practice_sessions_student_id ON realtime_practice_sessions (student_id);
CREATE INDEX ix_review_summaries_attempt_id ON review_summaries (attempt_id);
CREATE INDEX ix_review_summaries_student_id ON review_summaries (student_id);
CREATE INDEX ix_student_support_intake_sources_student_id ON student_support_intake_sources (student_id);
CREATE INDEX ix_student_support_intake_sources_source_type ON student_support_intake_sources (source_type);
CREATE INDEX ix_student_support_profiles_source_intake_id ON student_support_profiles (source_intake_id);
CREATE INDEX ix_student_support_profiles_teacher_confirmed_by_user_id ON student_support_profiles (teacher_confirmed_by_user_id);
CREATE INDEX ix_student_support_profiles_student_id ON student_support_profiles (student_id);
CREATE INDEX ix_student_support_profiles_status ON student_support_profiles (status);
CREATE INDEX ix_student_context_briefs_status ON student_context_briefs (status);
CREATE INDEX ix_student_context_briefs_student_id ON student_context_briefs (student_id);
CREATE INDEX ix_teacher_report_drafts_status ON teacher_report_drafts (status);
CREATE INDEX ix_teacher_report_drafts_student_id ON teacher_report_drafts (student_id);
CREATE INDEX ix_teacher_report_drafts_content_id ON teacher_report_drafts (content_id);
CREATE INDEX ix_teacher_report_drafts_review_summary_id ON teacher_report_drafts (review_summary_id);
CREATE INDEX ix_teacher_reports_created_by_user_id ON teacher_reports (created_by_user_id);
CREATE INDEX ix_teacher_reports_student_id ON teacher_reports (student_id);
CREATE INDEX ix_teacher_reports_draft_id ON teacher_reports (draft_id);
CREATE INDEX ix_teacher_reports_review_summary_id ON teacher_reports (review_summary_id);
CREATE INDEX ix_teacher_reports_content_id ON teacher_reports (content_id);
COMMIT;
