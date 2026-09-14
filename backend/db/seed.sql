-- Seed for v2026.09 — matches dashboard/fx.html:13 and dashboard/js/data.js:9
INSERT OR IGNORE INTO tenants VALUES ('NA','Nile Agro Trading','growth','2026-09-01T00:00:00Z');
INSERT OR IGNORE INTO tenants VALUES ('DEMO','Demo Trading','starter','2026-09-01T00:00:00Z');

INSERT OR IGNORE INTO statutory_tables VALUES ('v2026.09','0.08','0.17','50000.00','[{"limit":"100000.00","rate":"0.05"},{"limit":"200000.00","rate":"0.10"},{"limit":"400000.00","rate":"0.15"},{"limit":"999999999.00","rate":"0.20"}]','2026-09-01T00:00:00Z');

INSERT OR IGNORE INTO fx_history VALUES ('2026-09-25','USD','2610.5000','locked','owner');
INSERT OR IGNORE INTO fx_history VALUES ('2026-09-25','SAR','696.1000','locked','owner');
INSERT OR IGNORE INTO fx_history VALUES ('2026-09-25','AED','710.8500','locked','owner');
INSERT OR IGNORE INTO fx_history VALUES ('2026-09-18','USD','2585.0000','CBOS','');
INSERT OR IGNORE INTO fx_history VALUES ('2026-09-18','SAR','689.2000','CBOS','');
INSERT OR IGNORE INTO fx_history VALUES ('2026-09-18','AED','703.9000','CBOS','');
INSERT OR IGNORE INTO fx_history VALUES ('2026-09-11','USD','2540.7500','CBOS','');
INSERT OR IGNORE INTO fx_history VALUES ('2026-09-11','SAR','677.4000','CBOS','');
INSERT OR IGNORE INTO fx_history VALUES ('2026-09-11','AED','691.8000','CBOS','');

INSERT OR IGNORE INTO employees VALUES ('SD-0042','NA','Amal O. Hassan','19884402','2019-03-11','USD','1400.00','220.00','Y','1002844551','BANKAK','2026-09-01T00:00:00Z');
INSERT OR IGNORE INTO employees VALUES ('SD-0043','NA','Mohamed A. Idris','77120931','2021-07-02','SDG','850000.00','120000.00','Y','88210042','FAISAL','2026-09-01T00:00:00Z');
INSERT OR IGNORE INTO employees VALUES ('SD-0044','NA','Sara K. Elamin','55190277','2023-11-19','SAR','5200.00','800.00','N','44019283','OMDUR','2026-09-01T00:00:00Z');
INSERT OR IGNORE INTO employees VALUES ('SD-0045','NA','Yousif T. Bakhit','33018845','2014-01-05','AED','4800.00','650.00','Y','77120019','KHARTOUM','2026-09-01T00:00:00Z');

-- Demo owner user (password: admin123 hashed via bcrypt, placeholder)
INSERT OR IGNORE INTO users VALUES ('u_owner_na','NA','owner@nileagro.sd','$2b$12$LJ3m4ysu8h6R0B4X3Z5uOe5J5y5y5y5y5y5y5y5y5y5y5y5y5y5y','owner','2026-09-01T00:00:00Z');
