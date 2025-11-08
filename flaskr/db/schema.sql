/* Schema for PostgreSql v15 */
DROP TABLE IF EXISTS ecad_elements;
DROP TABLE IF EXISTS stations;
DROP TABLE IF EXISTS data_files;
DROP TABLE IF EXISTS measurements;
DROP TABLE IF EXISTS providers_magnitudes;
DROP TABLE IF EXISTS magnitudes;
DROP TABLE IF EXISTS providers;

CREATE TABLE providers (
  id SERIAL PRIMARY KEY,
  name TEXT UNIQUE NOT NULL,
  description TEXT NOT NULL,
  url TEXT NOT NULL,
  update_data_period INTEGER NOT NULL,
  acknowledgment TEXT NULL
);

INSERT INTO providers (name, description, url, update_data_period, acknowledgment) VALUES ('ecad', 'European Climate Assesment & Dataset', 'https://www.ecad.eu/dailydata/predefinedseries.php', 15, 'Klein Tank, A.M.G. and Coauthors, 2002. Daily dataset of 20th-century surface air temperature and precipitation series for the European Climate Assessment. Int. J. of Climatol., 22, 1441-1453. Data and metadata available at https://www.ecad.eu');

CREATE TABLE providers_extra_data (
  id SERIAL PRIMARY KEY,
  provider_id INTEGER NOT NULL,
  key TEXT NOT NULL,
  value TEXT NOT NULL,
  FOREIGN KEY (provider_id) REFERENCES providers(id)
);

-- Ecad
INSERT INTO providers_extra_data (provider_id, key, value) VALUES ((SELECT id FROM providers WHERE name = 'ecad'), 'sources_pickle_file_name', 'sources_pickle_file');
INSERT INTO providers_extra_data (provider_id, key, value) VALUES ((SELECT id FROM providers WHERE name = 'ecad'), 'ecad_date_file_name', 'date_timestamp.txt');

CREATE TABLE magnitudes (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL
);

INSERT INTO magnitudes (name) VALUES ('temperature');

-- Implement the many-to-many relationship between providers and magnitudes
CREATE TABLE providers_magnitudes (
   provider_id INTEGER REFERENCES providers(id),
   magnitude_id INTEGER REFERENCES magnitudes(id),
   PRIMARY KEY (provider_id, magnitude_id)
);

INSERT INTO providers_magnitudes (provider_id, magnitude_id) VALUES ((select id from providers where name = 'ecad'), (select id from magnitudes where name = 'temperature'));

CREATE TABLE measurements (
  id SERIAL PRIMARY KEY,
  magnitude_id INTEGER NOT NULL,
  name TEXT NOT NULL,
  last_download TEXT NULL,
  last_try TEXT NULL,
  FOREIGN KEY (magnitude_id) REFERENCES magnitudes (id)
);

INSERT INTO measurements (magnitude_id, name, last_download) VALUES ((SELECT t1.magnitude_id FROM providers_magnitudes t1, providers t2 WHERE t1.provider_id = t2.id AND t2.name = 'ecad'), 'max', '14-07-2024');
INSERT INTO measurements (magnitude_id, name, last_download) VALUES ((SELECT t1.magnitude_id FROM providers_magnitudes t1, providers t2 WHERE t1.provider_id = t2.id AND t2.name = 'ecad'), 'mean', '14-07-2024');
INSERT INTO measurements (magnitude_id, name, last_download) VALUES ((SELECT t1.magnitude_id FROM providers_magnitudes t1, providers t2 WHERE t1.provider_id = t2.id AND t2.name = 'ecad'), 'min', '14-07-2024');

CREATE TABLE data_files (
  id SERIAL PRIMARY KEY,
  provider_id INTEGER NOT NULL,
  magnitude_id INTEGER NOT NULL,
  measurement_id INTEGER NOT NULL,
  url TEXT NOT NULL,
  FOREIGN KEY (provider_id) REFERENCES providers (id),
  FOREIGN KEY (magnitude_id) REFERENCES magnitudes (id),
  FOREIGN KEY (measurement_id) REFERENCES measurements (id)
);

-- Data files for ecad temperature max
INSERT INTO data_files (provider_id, magnitude_id, measurement_id, url) VALUES (
(SELECT id FROM providers WHERE name = 'ecad'),
(SELECT pm.magnitude_id FROM providers_magnitudes pm, magnitudes m, providers p WHERE pm.magnitude_id = m.id AND m.name = 'temperature' AND pm.provider_id = p.id and p.name = 'ecad'),
(SELECT me.id FROM measurements me, providers_magnitudes pm, magnitudes m, providers p WHERE me.magnitude_id = pm.magnitude_id AND pm.provider_id = p.id AND pm.magnitude_id = m.id AND p.name = 'ecad' AND m.name = 'temperature' AND me.name = 'max'),
'https://knmi-ecad-assets-prd.s3.amazonaws.com/download/ECA_nonblend_tx.zip'
);

-- Data files for ecad temperature min
INSERT INTO data_files (provider_id, magnitude_id, measurement_id, url) VALUES (
(SELECT id FROM providers WHERE name = 'ecad'),
(SELECT pm.magnitude_id FROM providers_magnitudes pm, magnitudes m, providers p WHERE pm.magnitude_id = m.id AND m.name = 'temperature' AND pm.provider_id = p.id and p.name = 'ecad'),
(SELECT me.id FROM measurements me, providers_magnitudes pm, magnitudes m, providers p WHERE me.magnitude_id = pm.magnitude_id AND pm.provider_id = p.id AND pm.magnitude_id = m.id AND p.name = 'ecad' AND m.name = 'temperature' AND me.name = 'min'),
'https://knmi-ecad-assets-prd.s3.amazonaws.com/download/ECA_nonblend_tn.zip'
);

-- Data files for ecad temperature mean
INSERT INTO data_files (provider_id, magnitude_id, measurement_id, url) VALUES (
(SELECT id FROM providers WHERE name = 'ecad'),
(SELECT pm.magnitude_id FROM providers_magnitudes pm, magnitudes m, providers p WHERE pm.magnitude_id = m.id AND m.name = 'temperature' AND pm.provider_id = p.id and p.name = 'ecad'),
(SELECT me.id FROM measurements me, providers_magnitudes pm, magnitudes m, providers p WHERE me.magnitude_id = pm.magnitude_id AND pm.provider_id = p.id AND pm.magnitude_id = m.id AND p.name = 'ecad' AND m.name = 'temperature' AND me.name = 'mean'),
'https://knmi-ecad-assets-prd.s3.amazonaws.com/download/ECA_nonblend_tg.zip'
);

CREATE TABLE stations (
  id SERIAL PRIMARY KEY,
  provider_id INTEGER NOT NULL,
  station_id INTEGER NOT NULL,
  name TEXT NOT NULL,
  cn TEXT NOT NULL,
  lat TEXT NOT NULL,
  lon TEXT NOT NULL,
  height INTEGER NOT NULL,
  popup TEXT NULL,
  FOREIGN KEY (provider_id) REFERENCES providers(id)
);

CREATE TABLE ecad_elements (
  id SERIAL PRIMARY KEY,
  provider_id INTEGER NOT NULL,
  magnitude_id INTEGER NOT NULL,
  measurement_id INTEGER NOT NULL,
  element_id TEXT NOT NULL,
  description TEXT NOT NULL,
  unit TEXT NOT NULL,
  factor NUMERIC(3, 2) NOT NULL
);

