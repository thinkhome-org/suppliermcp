-- Full supplier descriptions exceed PostgreSQL's B-tree key limit; retain the text unchanged.
DROP INDEX catalog_values_field;
CREATE INDEX catalog_values_field ON catalog_values(field,md5(value));
