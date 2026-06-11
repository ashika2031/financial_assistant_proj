-- Seed data: 20+ Prologis-style industrial / logistics properties

INSERT INTO properties (address, metro_area, sq_footage, property_type) VALUES
  ('1 Logistics Blvd, Chicago, IL 60601',          'Chicago',          450000, 'Industrial'),
  ('2200 Distribution Dr, Dallas, TX 75201',        'Dallas',           380000, 'Industrial'),
  ('500 Commerce Way, Los Angeles, CA 90012',       'Los Angeles',      620000, 'Industrial'),
  ('88 Industrial Park Rd, Atlanta, GA 30301',      'Atlanta',          290000, 'Industrial'),
  ('3300 Warehouse Ave, New Jersey, NJ 07001',      'New York/NJ',      510000, 'Industrial'),
  ('700 Gateway Blvd, Newark, NJ 07102',            'New York/NJ',      340000, 'Industrial'),
  ('1400 Freight Ln, Seattle, WA 98101',            'Seattle',          275000, 'Industrial'),
  ('900 Supply Chain Dr, Denver, CO 80201',         'Denver',           220000, 'Industrial'),
  ('2100 Cargo Ct, Memphis, TN 38101',              'Memphis',          490000, 'Industrial'),
  ('560 Fulfillment Rd, Phoenix, AZ 85001',         'Phoenix',          315000, 'Industrial'),
  ('1010 Commerce Park, Houston, TX 77001',         'Houston',          430000, 'Industrial'),
  ('3800 Intermodal Way, Louisville, KY 40201',     'Louisville',       560000, 'Industrial'),
  ('250 Trade Center Blvd, Miami, FL 33101',        'Miami',            185000, 'Industrial'),
  ('4400 Airport Logistics Dr, Dallas, TX 75261',   'Dallas',           395000, 'Industrial'),
  ('1600 E-Commerce Pkwy, Columbus, OH 43201',      'Columbus',         480000, 'Industrial'),
  ('770 Inland Empire Dr, Riverside, CA 92501',     'Inland Empire',    720000, 'Industrial'),
  ('2900 Last Mile Rd, Boston, MA 02101',           'Boston',           142000, 'Industrial'),
  ('1100 Distribution Ctr, Kansas City, MO 64101',  'Kansas City',      365000, 'Industrial'),
  ('6200 Port Logistics Ave, Baltimore, MD 21201',  'Baltimore',        310000, 'Industrial'),
  ('3100 Cold Chain Dr, Minneapolis, MN 55401',     'Minneapolis',      198000, 'Industrial'),
  ('450 Data Center Rd, Ashburn, VA 20147',         'Washington DC',    125000, 'Office'),
  ('8800 Corporate Campus, San Jose, CA 95101',     'San Francisco',    235000, 'Office');

-- Annual financials for each property (FY 2023)
INSERT INTO financials (property_id, fiscal_year, fiscal_quarter, revenue, net_income, expenses) VALUES
  (1,  2023, NULL, 12500000.00,  4200000.00,  8300000.00),
  (2,  2023, NULL, 10800000.00,  3600000.00,  7200000.00),
  (3,  2023, NULL, 18200000.00,  6500000.00, 11700000.00),
  (4,  2023, NULL,  8500000.00,  2800000.00,  5700000.00),
  (5,  2023, NULL, 15100000.00,  5300000.00,  9800000.00),
  (6,  2023, NULL,  9900000.00,  3200000.00,  6700000.00),
  (7,  2023, NULL,  7800000.00,  2500000.00,  5300000.00),
  (8,  2023, NULL,  6200000.00,  1900000.00,  4300000.00),
  (9,  2023, NULL, 14200000.00,  4900000.00,  9300000.00),
  (10, 2023, NULL,  9100000.00,  3000000.00,  6100000.00),
  (11, 2023, NULL, 12300000.00,  4100000.00,  8200000.00),
  (12, 2023, NULL, 16500000.00,  5800000.00, 10700000.00),
  (13, 2023, NULL,  5200000.00,  1600000.00,  3600000.00),
  (14, 2023, NULL, 11400000.00,  3800000.00,  7600000.00),
  (15, 2023, NULL, 14100000.00,  4800000.00,  9300000.00),
  (16, 2023, NULL, 21500000.00,  7800000.00, 13700000.00),
  (17, 2023, NULL,  4100000.00,  1200000.00,  2900000.00),
  (18, 2023, NULL, 10200000.00,  3400000.00,  6800000.00),
  (19, 2023, NULL,  8900000.00,  2900000.00,  6000000.00),
  (20, 2023, NULL,  5600000.00,  1700000.00,  3900000.00),
  (21, 2023, NULL,  6800000.00,  2100000.00,  4700000.00),
  (22, 2023, NULL,  7200000.00,  2400000.00,  4800000.00);

-- Q4 2023 quarterly financials (subset)
INSERT INTO financials (property_id, fiscal_year, fiscal_quarter, revenue, net_income, expenses) VALUES
  (1,  2023, 'Q4', 3200000.00, 1100000.00, 2100000.00),
  (2,  2023, 'Q4', 2750000.00,  940000.00, 1810000.00),
  (3,  2023, 'Q4', 4600000.00, 1650000.00, 2950000.00),
  (4,  2023, 'Q4', 2100000.00,  700000.00, 1400000.00),
  (5,  2023, 'Q4', 3800000.00, 1350000.00, 2450000.00);

-- Press releases
INSERT INTO press_releases (title, publish_date, category, summary, content, source_url) VALUES
(
  'Prologis Acquires 3.2M SF Logistics Portfolio in Inland Empire',
  '2024-03-15',
  'Acquisition',
  'Prologis expands Southern California footprint with major industrial portfolio acquisition.',
  'Prologis, Inc. (NYSE: PLD) today announced the acquisition of a 12-building, 3.2 million square foot logistics portfolio located in the Inland Empire region of Southern California for approximately $680 million. The portfolio is 97% leased to a diverse mix of e-commerce and third-party logistics tenants. The acquisition strengthens Prologis'' position in one of the most supply-constrained industrial markets in the United States.',
  'https://ir.prologis.com/press-releases'
),
(
  'Prologis Reports Q4 2023 Earnings: Revenue Up 12% Year-Over-Year',
  '2024-01-23',
  'Earnings',
  'Strong quarterly performance driven by record leasing activity and rent growth.',
  'Prologis reported fourth quarter 2023 revenues of $1.93 billion, a 12.4% increase compared to Q4 2022. Net income attributable to common stockholders was $698 million, or $0.95 per diluted share. Core Funds from Operations (Core FFO) was $1.26 per diluted share. The company achieved record net effective rent change of 68% on new and renewal leases signed during the quarter.',
  'https://ir.prologis.com/press-releases'
),
(
  'Prologis Announces $2B Sustainability-Linked Bond Offering',
  '2024-02-08',
  'Finance',
  'Green bond proceeds will fund renewable energy and sustainable building initiatives.',
  'Prologis priced a $2.0 billion dual-tranche sustainability-linked bond offering comprising $1.0 billion of 10-year notes at 5.10% and $1.0 billion of 30-year notes at 5.45%. Net proceeds will be used to fund projects consistent with the company''s Green Finance Framework, including solar installations across 200 million square feet of rooftop and LED lighting retrofit programs.',
  'https://ir.prologis.com/press-releases'
),
(
  'Prologis and Amazon Renew 15M SF Logistics Partnership',
  '2024-04-02',
  'Partnership',
  'Long-term renewal strengthens Prologis'' largest tenant relationship.',
  'Prologis announced a long-term lease renewal with Amazon covering approximately 15 million square feet across 65 facilities in 24 markets. The agreement includes rental escalations aligned with market rates and a commitment to develop an additional 5 million square feet of new build-to-suit logistics facilities over the next three years.',
  'https://ir.prologis.com/press-releases'
),
(
  'Prologis Expands European Presence with €500M Germany Acquisition',
  '2024-05-14',
  'Acquisition',
  'Six-property portfolio near Frankfurt and Munich logistics corridors acquired.',
  'Prologis completed the acquisition of a six-property logistics portfolio in Germany totaling approximately 2.1 million square feet for €500 million. Properties are located in key distribution corridors near Frankfurt Airport and Munich, with average lease terms of 7.2 years and a weighted average occupancy rate of 99%.',
  'https://ir.prologis.com/press-releases'
),
(
  'Prologis Q1 2024 Earnings: Occupancy at 97.4%, Guidance Raised',
  '2024-04-17',
  'Earnings',
  'Record occupancy and 54% rent change on new leases support raised full-year guidance.',
  'Prologis reported first quarter 2024 revenues of $1.96 billion, up 10.2% year-over-year. Global occupancy reached 97.4%, near all-time highs. The company raised its 2024 Core FFO guidance to $5.42-$5.50 per diluted share, reflecting continued strong demand from e-commerce, retail, and manufacturing tenants across all major markets.',
  'https://ir.prologis.com/press-releases'
);
